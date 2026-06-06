"""
PDF → Markdown 전체 파이프라인 실행 스크립트 (1단계 + 2단계 통합)

parse.py(변환)와 ocr_replace.py(OCR 후처리)를 순차로 한 번에 실행합니다.

사용법:
  python run.py <PDF경로>
  python run.py /path/to/doc.pdf --output-dir ./output
  python run.py /path/to/doc.pdf --skip-parse   # 1단계 건너뛰고 OCR만
"""

import argparse
import sys
import time
from pathlib import Path

from parse import convert_pdf
from ocr_replace import find_raw_md, process_markdown

BASE_DIR = Path(__file__).parent


def main() -> None:
    p = argparse.ArgumentParser(description="기술 문서 PDF → Markdown 전체 파이프라인")
    p.add_argument("pdf", type=Path, help="입력 PDF 경로")
    p.add_argument("--output-dir", type=Path, default=BASE_DIR / "output",
                   help="출력 루트 디렉토리 (기본: ./output)")
    p.add_argument("--skip-parse", action="store_true",
                   help="1단계(parse) 건너뛰고 OCR 후처리만 실행")
    args = p.parse_args()

    input_pdf = args.pdf.expanduser().resolve()
    if not input_pdf.exists():
        print(f"[ERROR] PDF not found: {input_pdf}", file=sys.stderr)
        sys.exit(1)

    output_dir = args.output_dir / input_pdf.stem
    image_dir  = output_dir / "images"
    start      = time.time()

    # ─── 1단계: PDF → Markdown ───────────────────────────────────────────────
    if not args.skip_parse:
        print("=" * 60)
        print("[STEP 1] PDF → Markdown 변환")
        print("=" * 60)
        print(f"[INFO] 입력  : {input_pdf.name} ({input_pdf.stat().st_size / 1024**2:.1f} MB)")
        print(f"[INFO] 출력  : {output_dir}\n")
        convert_pdf(input_pdf, output_dir, image_dir)
        print(f"\n[STEP 1 완료] {time.time() - start:.1f}초\n")

    # ─── 2단계: OCR 후처리 ───────────────────────────────────────────────────
    print("=" * 60)
    print("[STEP 2] OCR 후처리 + 헤딩 구조화")
    print("=" * 60)
    md_path = find_raw_md(output_dir, input_pdf.stem)
    if not md_path or not md_path.exists():
        print(f"[ERROR] Markdown not found in {output_dir}", file=sys.stderr)
        print(f"        1단계가 정상 실행됐는지 확인하세요.", file=sys.stderr)
        sys.exit(1)

    output_md = output_dir / f"{md_path.stem}-ocr.md"
    print(f"[INFO] 입력  : {md_path.name}")
    print(f"[INFO] 출력  : {output_md.name}\n")
    process_markdown(md_path, image_dir, output_md)

    in_mb  = md_path.stat().st_size   / 1024**2
    out_mb = output_md.stat().st_size / 1024**2
    print(f"\n[전체 완료] {time.time() - start:.1f}초  |  {in_mb:.2f} MB → {out_mb:.2f} MB")
    print(f"  {output_md}")


if __name__ == "__main__":
    main()
