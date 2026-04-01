# 기술 문서 PDF → Markdown 파서

한컴 **OpenDataLoader PDF v2.x** 를 사용해 기술 문서 PDF를 정밀하게 Markdown으로 변환하는 파이프라인입니다.
OCR 후처리를 통해 이미지로 렌더링된 텍스트(섹션번호, 레이블 등)를 모두 실제 문자로 복원하고, 섹션번호와 Figure 캡션을 올바른 Markdown 헤딩 구조로 정리합니다.

---

## 처리 파이프라인

```
python parse.py <PDF경로>
python ocr_replace.py <PDF경로>
```

```
PDF
 │
 ▼  [Step 1] parse.py
 │  OpenDataLoader PDF → Markdown + JSON + 이미지 추출
 │
 ▼  [Step 2] ocr_replace.py
    Tesseract OCR 후처리
      ├─ 섹션번호 이미지 (< 2 KB)    → 숫자 텍스트 (예: 5.2.3.4)
      ├─ 텍스트 블록 이미지 (< 5 KB) → OCR 텍스트 (인용 블록)
      ├─ 다이어그램 이미지 (≥ 5 KB)  → 이미지 유지
      ├─ 화살표/장식 이미지           → 제거
      ├─ 섹션번호 + 헤딩 병합         → #### 5.2.3.4 Command Completion
      └─ Figure 캡션 라인            → ###### Figure N: 제목
```

---

## 프로젝트 구조

```
OpenDataLoader/
├── parse.py            # Step 1: PDF → Markdown 변환
├── ocr_replace.py      # Step 2: OCR 후처리 + 헤딩 구조화
├── requirements.txt    # Python 의존성
├── README.md           # 프로젝트 설명 (이 파일)
├── SETUP.md            # macOS 개발환경 설치 가이드
├── SETUP_UBUNTU.md     # Ubuntu 22.04 개발환경 설치 가이드
├── .venv/              # Python 가상환경 (git 제외)
└── output/
    └── <PDF-stem>/
        ├── <PDF-stem>.md        # Step 1 원본 변환 Markdown
        ├── <PDF-stem>-ocr.md    # Step 2 최종 Markdown (OCR + 헤딩 구조화)
        ├── <PDF-stem>.json      # 구조 데이터 (디버깅용)
        └── images/
            └── imageFile*.png   # 추출된 이미지 (다이어그램 등)
```

---

## 변환 결과 예시

| 문서 | 입력 | 출력 (Step 1) | 이미지 | OCR 교체 / 유지 / 제거 |
|---|---|---|---|---|
| NVMe Base Spec Rev 2.3 | 12 MB, 784p | 2.5 MB | 1,106개 | 876 / 30 / 200 |
| Datacenter NVMe SSD Spec v2.6 | 4.2 MB, 211p | 438 KB | 31개 | 2 / 20 / 9 |

---

## parse.py 주요 옵션

| 옵션 | 값 | 이유 |
|---|---|---|
| `table_method` | `cluster` | NVMe 특유의 복잡한 병합 셀 표(레지스터 맵 등) 처리 |
| `reading_order` | `xycut` | 다단 레이아웃 읽기 순서 복원 |
| `use_struct_tree` | `True` | Tagged PDF 구조 트리 활용, 의미 구조 보존 |
| `markdown_page_separator` | `<!-- page: N -->` | 페이지 추적 및 RAG 청킹 지원 |
| `detect_strikethrough` | `True` | Deprecated 항목 `~~취소선~~` 처리 |
| `include_header_footer` | `True` | 섹션 번호가 헤더에 표시되는 경우 포함 |

---

## ocr_replace.py 처리 전략

### 이미지 분류 기준

| 크기 | 분류 | 처리 |
|---|---|---|
| ≥ 5 KB | 다이어그램 | OCR 시도 없이 이미지 유지 |
| 2 KB ~ 5 KB | 텍스트 블록 | PSM 6 OCR → `>` 인용 블록 |
| < 2 KB | 섹션번호/레이블 | 고배율 업스케일 + whitelist OCR → 인라인 텍스트 |
| < 5 KB, OCR 실패 | 화살표/장식 | 제거 |

### 섹션번호 OCR 전처리

1. RGBA → 흰 배경 합성 → 그레이스케일
2. LANCZOS 고배율 업스케일 (최소 6×)
3. 20px 패딩 추가 (Tesseract 인식률 향상)
4. 대비 3.0× 강화
5. `tessedit_char_whitelist=0123456789.` 적용

### 섹션번호 헤딩 병합 규칙

PDF에서 섹션번호가 이미지로 렌더링된 경우, OCR 복원 후 다음 패턴이 발생합니다.

```
# 변환 전
5.2.3.4
(빈 줄)
#### Command Completion

# 변환 후
#### 5.2.3.4 Command Completion
```

- 섹션번호 단독 라인(`숫자.숫자...`) + 빈 줄 + `#` 헤딩 → 헤딩에 번호 병합
- 헤딩이 이미 번호로 시작하는 경우 (`## 1.1 Overview` 등) → 중복 방지, 건드리지 않음

### Figure 헤딩 변환 규칙

- `Figure N: 제목` (단독 라인) → `###### Figure N: 제목`
- `|Figure N: 제목 | | |` (테이블 첫 행으로 잘못 파싱) → `###### Figure N: 제목` + 구분자 제거
- TOC 라인 (`....` 포함) → 변환 안 함
- 본문 참조 (`Figure N shows ...`, 콜론 없음) → 변환 안 함

---

## 개발환경 설치 가이드

| OS | 가이드 |
|---|---|
| macOS | [SETUP.md](SETUP.md) |
| Ubuntu 22.04 | [SETUP_UBUNTU.md](SETUP_UBUNTU.md) |

---

## 사용법

```bash
# Step 1: PDF → Markdown 변환
python parse.py <PDF경로>

# Step 2: OCR 후처리
python ocr_replace.py <PDF경로>
```

예시:

```bash
python parse.py "/path/to/Datacenter NVMe SSD Specification v2.6.pdf"
python ocr_replace.py "/path/to/Datacenter NVMe SSD Specification v2.6.pdf"
```

출력 디렉토리를 지정하려면 `--output-dir` 옵션을 사용합니다.

```bash
python parse.py /path/to/doc.pdf --output-dir ./output
```
