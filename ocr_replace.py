"""
OCR 후처리 스크립트 (2단계)
parse.py로 변환된 Markdown 내 이미지를 OCR 텍스트로 교체합니다.

처리 내용:
  - 섹션번호 이미지 → 숫자 텍스트 (e.g. 3.3.2.8)
  - 텍스트 블록 이미지 → OCR 텍스트
  - 작은 장식 이미지 (화살표 등) → 제거
  - 큰 다이어그램 이미지 → 유지
  - 페이지 구분자 (--- / <!-- page: N -->) 제거

사용법:
  python ocr_replace.py <PDF경로>
  python ocr_replace.py /path/to/doc.pdf --output-dir ./output
  python ocr_replace.py /path/to/doc.pdf --md ./output/doc/doc.md  # MD 직접 지정
"""

import argparse
import os
import re
import sys
from pathlib import Path

import pytesseract
from PIL import Image, ImageEnhance, ImageOps

os.environ["PATH"] = "/opt/homebrew/bin:" + os.environ.get("PATH", "")

BASE_DIR               = Path(__file__).parent
DIAGRAM_SIZE_THRESHOLD = 5_000   # 5 KB 이상 → 다이어그램으로 유지
SECTION_NUM_SIZE       = 2_000   # 2 KB 이하 → 섹션번호 전용 OCR
IMAGE_PATTERN          = re.compile(r"!\[([^\]]*)\]\((images/imageFile\d+\.png)\)")


# ─── OCR 함수 ────────────────────────────────────────────────────────────────

def _preprocess(img_path: Path, scale: int, border: int, contrast: float) -> Image.Image:
    img = Image.open(img_path).convert("RGBA")
    bg  = Image.new("RGBA", img.size, (255, 255, 255, 255))
    img = Image.alpha_composite(bg, img).convert("L")
    w, h = img.size
    img = img.resize((w * scale, h * scale), Image.LANCZOS)
    img = ImageOps.expand(img, border=border, fill=255)
    return ImageEnhance.Contrast(img).enhance(contrast)


def ocr_section_number(img_path: Path) -> str:
    w, h = Image.open(img_path).size
    img  = _preprocess(img_path, scale=max(6, 600 // max(w, 1)), border=20, contrast=3.0)

    for cfg in [
        "--psm 6 --oem 3 -c tessedit_char_whitelist=0123456789.",
        "--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789.",
        "--psm 6 --oem 3",
        "--psm 11 --oem 3",
    ]:
        raw     = pytesseract.image_to_string(img, config=cfg, lang="eng").strip()
        cleaned = re.sub(r"[^0-9.]", "", raw)
        if cleaned and len(cleaned) >= 3:
            return cleaned
    return ""


def ocr_text_block(img_path: Path) -> str:
    w, h  = Image.open(img_path).size
    scale = max(2, 400 // max(w, 1)) if w < 400 else 1
    img   = _preprocess(img_path, scale=scale, border=10, contrast=2.0)

    text = pytesseract.image_to_string(img, config="--psm 6 --oem 3", lang="eng").strip()
    if not text:
        text = pytesseract.image_to_string(img, config="--psm 11 --oem 3", lang="eng").strip()

    text = re.sub(r"[^\x09\x0A\x0D\x20-\x7E]", "", text)
    text = re.sub(r" {2,}", " ", text)
    text = "\n".join(line.rstrip() for line in text.splitlines())
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def is_meaningful(text: str) -> bool:
    return len(re.sub(r"[^a-zA-Z0-9]", "", text)) >= 3


# ─── 후처리 함수 ─────────────────────────────────────────────────────────────

def merge_section_numbers(content: str) -> tuple[str, int]:
    """OCR로 복원된 섹션번호 단독 라인을 바로 뒤 헤딩에 병합.

    변환 전:  5.2.3.4\n\n#### Command Completion
    변환 후:  #### 5.2.3.4 Command Completion
    """
    sec_re     = re.compile(r"^[0-9]+\.[0-9][0-9.]*$")
    heading_re = re.compile(r"^(#{1,6})\s+(.+)$")
    lines, result, count, i = content.splitlines(), [], 0, 0

    while i < len(lines):
        line = lines[i]
        if sec_re.match(line.strip()):
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines):
                m = heading_re.match(lines[j])
                if m and not re.match(r"^[0-9]+\.[0-9]", m.group(2).strip()):
                    result.append(f"{m.group(1)} {line.strip()} {m.group(2).strip()}")
                    i = j + 1
                    count += 1
                    continue
        result.append(line)
        i += 1

    return "\n".join(result), count


def remove_page_markers(content: str) -> str:
    """페이지 구분자(--- / <!-- page: N -->)를 제거."""
    content = re.sub(r"<!-- page: \d+ -->\n?", "", content)
    content = re.sub(r"^---$\n?", "", content, flags=re.MULTILINE)
    return re.sub(r"\n{3,}", "\n\n", content)


def apply_figure_headings(content: str) -> tuple[str, int]:
    """Figure 캡션 라인을 ###### 헤딩으로 변환 (단독 라인 + 잘못 파싱된 테이블 행)."""
    table_caption_re = re.compile(r"^\|(Figure \d+:.*?)\s*\|[\s|]*$")
    separator_re     = re.compile(r"^\|[-|: ]+\|")
    standalone_re    = re.compile(r"^(Figure \d+:.+)$")
    lines, result, count, i = content.splitlines(), [], 0, 0

    while i < len(lines):
        line = lines[i]

        m = table_caption_re.match(line)
        if m:
            result.append(f"###### {m.group(1).strip()}")
            i += 2 if (i + 1 < len(lines) and separator_re.match(lines[i + 1])) else i + 1
            count += 1
            continue

        m = standalone_re.match(line)
        if m:
            if re.search(r"\.{4,}", line):
                result.append(line)
            else:
                result.append(f"###### {line.strip()}")
                count += 1
            i += 1
            continue

        result.append(line)
        i += 1

    return "\n".join(result), count


# ─── 메인 처리 ───────────────────────────────────────────────────────────────

def process_markdown(md_path: Path, image_dir: Path, output_path: Path) -> None:
    content = md_path.read_text(encoding="utf-8")
    total   = len(IMAGE_PATTERN.findall(content))
    stats   = {"replaced": 0, "kept": 0, "removed": 0}
    done    = [0]

    print(f"[INFO] 이미지 {total:,}개 처리 중...")

    def replace_image(match: re.Match) -> str:
        img_path = image_dir / Path(match.group(2)).name
        done[0] += 1
        if done[0] % 100 == 0:
            print(f"  진행: {done[0]}/{total}", flush=True)

        if not img_path.exists():
            return match.group(0)

        size = img_path.stat().st_size
        if size >= DIAGRAM_SIZE_THRESHOLD:
            stats["kept"] += 1
            return match.group(0)

        ocr_text = ocr_section_number(img_path) if size <= SECTION_NUM_SIZE else ocr_text_block(img_path)

        if is_meaningful(ocr_text):
            stats["replaced"] += 1
            lines = ocr_text.splitlines()
            return "\n".join(f"> {l}" if l else ">" for l in lines) if len(lines) > 1 else ocr_text

        stats["removed"] += 1
        return ""

    result = IMAGE_PATTERN.sub(replace_image, content)
    result = re.sub(r"\n{4,}", "\n\n\n", result)

    result = remove_page_markers(result)
    print(f"  페이지 구분자 제거 완료")

    result, sec_count = merge_section_numbers(result)
    print(f"  섹션번호 병합: {sec_count}개")

    result, fig_count = apply_figure_headings(result)
    print(f"  Figure 헤딩 : {fig_count}개")

    print(f"\n[통계] 교체 {stats['replaced']:,} / 유지 {stats['kept']:,} / 제거 {stats['removed']:,}")

    output_path.write_text(result, encoding="utf-8")


def find_raw_md(output_dir: Path, stem: str) -> Path | None:
    """parse.py가 생성한 원본 Markdown 파일 탐색."""
    direct = output_dir / f"{stem}.md"
    if direct.exists():
        return direct
    candidates = [f for f in output_dir.glob("*.md") if not f.name.endswith("-ocr.md")]
    return candidates[0] if candidates else None


def main() -> None:
    p = argparse.ArgumentParser(description="기술 문서 Markdown OCR 후처리 (2단계)")
    p.add_argument("pdf", type=Path, help="원본 PDF 경로 (출력 디렉토리 탐색용)")
    p.add_argument("--output-dir", type=Path, default=BASE_DIR / "output",
                   help="출력 루트 디렉토리 (기본: ./output)")
    p.add_argument("--md", type=Path, default=None,
                   help="Markdown 파일 직접 지정 (생략 시 자동 탐색)")
    args = p.parse_args()

    input_pdf  = args.pdf.expanduser().resolve()
    stem       = input_pdf.stem
    output_dir = args.output_dir / stem
    image_dir  = output_dir / "images"

    md_path = args.md.expanduser().resolve() if args.md else find_raw_md(output_dir, stem)
    if not md_path or not md_path.exists():
        print(f"[ERROR] Markdown not found in {output_dir}", file=sys.stderr)
        print(f"        먼저 parse.py를 실행하거나 --md 옵션으로 경로를 지정하세요.", file=sys.stderr)
        sys.exit(1)

    output_md = output_dir / f"{md_path.stem}-ocr.md"

    print(f"[INFO] 입력  : {md_path.name}")
    print(f"[INFO] 출력  : {output_md.name}")
    print()

    process_markdown(md_path, image_dir, output_md)

    in_mb  = md_path.stat().st_size  / 1024**2
    out_mb = output_md.stat().st_size / 1024**2
    print(f"\n[완료] {in_mb:.2f} MB → {out_mb:.2f} MB")
    print(f"  {output_md}")


if __name__ == "__main__":
    main()
