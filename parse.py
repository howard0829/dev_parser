"""
기술 문서 PDF → Markdown 변환 스크립트 (1단계)
opendataloader_pdf 사용

사용법:
  python parse.py <PDF경로>
  python parse.py /path/to/doc.pdf --output-dir ./output

출력: output/<PDF-stem>/
  ├── <PDF-stem>.md       # 변환된 Markdown
  ├── <PDF-stem>.json     # 구조 디버깅용 JSON
  └── images/             # 추출된 이미지
"""

import argparse
import os
import sys
import time
from pathlib import Path

# Java PATH 설정 (OS별 자동 감지)
# macOS (Homebrew): /opt/homebrew/opt/openjdk@21/bin
# Ubuntu (apt/Adoptium): /usr/lib/jvm/temurin-21-*/bin 또는 시스템 PATH에 이미 포함
import platform
if platform.system() == "Darwin":
    # macOS: Homebrew로 설치된 Java 21 경로 추가
    os.environ["PATH"] = "/opt/homebrew/opt/openjdk@21/bin:" + os.environ.get("PATH", "")

import opendataloader_pdf

BASE_DIR = Path(__file__).parent


def convert_pdf(input_pdf: Path, output_dir: Path, image_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    image_dir.mkdir(parents=True, exist_ok=True)

    opendataloader_pdf.convert(
        input_path              = str(input_pdf),
        output_dir              = str(output_dir),
        format                  = ["markdown", "json"],
        table_method            = "cluster",
        reading_order           = "xycut",
        markdown_page_separator = "\n\n",
        image_output            = "external",
        image_format            = "png",
        image_dir               = str(image_dir),
        include_header_footer   = True,
        detect_strikethrough    = True,
        use_struct_tree         = True,
        replace_invalid_chars   = " ",
        quiet                   = False,
    )


def main() -> None:
    p = argparse.ArgumentParser(description="기술 문서 PDF → Markdown 변환 (1단계)")
    p.add_argument("pdf", type=Path, help="입력 PDF 경로")
    p.add_argument("--output-dir", type=Path, default=BASE_DIR / "output",
                   help="출력 루트 디렉토리 (기본: ./output)")
    args = p.parse_args()

    input_pdf = args.pdf.expanduser().resolve()
    if not input_pdf.exists():
        print(f"[ERROR] PDF not found: {input_pdf}", file=sys.stderr)
        sys.exit(1)

    output_dir = args.output_dir / input_pdf.stem
    image_dir  = output_dir / "images"

    print(f"[INFO] 입력  : {input_pdf.name} ({input_pdf.stat().st_size / 1024**2:.1f} MB)")
    print(f"[INFO] 출력  : {output_dir}")
    print()

    start = time.time()
    convert_pdf(input_pdf, output_dir, image_dir)
    elapsed = time.time() - start

    print(f"\n[완료] {elapsed:.1f}초")
    print("\n[출력 파일]")
    for f in sorted(output_dir.rglob("*")):
        if f.is_file():
            print(f"  {f.relative_to(output_dir)}  ({f.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
