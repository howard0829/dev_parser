# 개발환경 설치 가이드

아무것도 설치되지 않은 macOS 환경에서 이 프로젝트를 실행하기 위한 단계별 가이드입니다.

> **전제 조건**: macOS (Apple Silicon 또는 Intel), 인터넷 연결

---

## 1. Homebrew 설치

패키지 관리자 Homebrew가 없다면 먼저 설치합니다.

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Apple Silicon(M1/M2/M3) Mac이라면 설치 후 PATH를 등록합니다.

```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc
source ~/.zshrc
```

설치 확인:

```bash
brew --version
```

---

## 2. Java 21 설치

OpenDataLoader PDF는 Java 기반입니다. Homebrew로 OpenJDK 21을 설치합니다.

```bash
brew install openjdk@21
```

PATH에 Java를 추가합니다.

```bash
echo 'export PATH="/opt/homebrew/opt/openjdk@21/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

설치 확인:

```bash
java --version
# openjdk 21.x.x ...
```

---

## 3. Python 3.11 이상 설치

```bash
brew install python@3.11
```

설치 확인:

```bash
python3 --version
# Python 3.11.x
```

---

## 4. Tesseract OCR 설치

이미지 내 텍스트를 인식하기 위한 OCR 엔진입니다.

```bash
brew install tesseract
```

설치 확인:

```bash
tesseract --version
# tesseract 5.x.x
```

> 기본 설치에는 영어(`eng`) 언어팩이 포함됩니다. 다국어가 필요하면 `brew install tesseract-lang`을 추가로 실행합니다.

---

## 5. 프로젝트 클론 / 디렉토리 이동

```bash
cd /Users/howard/Project/Parser/OpenDataLoader
# 또는 원하는 경로로 이동
```

---

## 6. Python 가상환경 생성 및 의존성 설치

```bash
# 가상환경 생성
python3 -m venv .venv

# 가상환경 활성화
source .venv/bin/activate

# 의존성 설치
pip install -U pip
pip install -r requirements.txt

# OCR 라이브러리 설치
pip install pytesseract pillow numpy
```

설치 확인:

```bash
python -c "import opendataloader_pdf; print('OK')"
python -c "import pytesseract; print(pytesseract.get_tesseract_version())"
```

---

## 7. 입력 PDF 배치

변환할 PDF 파일을 준비합니다.

---

## 8. 실행

### Step 1: PDF → Markdown 변환

```bash
source .venv/bin/activate
python parse.py <PDF경로>
```

완료되면 `output/<PDF-stem>/` 디렉토리에 아래 파일이 생성됩니다.

```
output/<PDF-stem>/
├── <PDF-stem>.md       # Markdown
├── <PDF-stem>.json     # 구조 JSON
└── images/             # 추출 이미지 (PNG)
```

### Step 2: OCR 후처리

```bash
python ocr_replace.py <PDF경로>
```

완료되면 최종 파일이 생성됩니다.

```
output/<PDF-stem>/
└── <PDF-stem>-ocr.md   # OCR 처리 + Figure 헤딩 변환 완료 Markdown
```

---

## 전체 명령어 요약

```bash
# 1. 의존성 (최초 1회)
brew install openjdk@21 tesseract
echo 'export PATH="/opt/homebrew/opt/openjdk@21/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc

# 2. Python 환경 (최초 1회)
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
pip install pytesseract pillow numpy

# 3. 실행
source .venv/bin/activate
python parse.py <PDF경로>        # Step 1
python ocr_replace.py <PDF경로>  # Step 2
```

---

## 환경별 예상 소요 시간

| 단계 | Apple M 시리즈 | Intel Mac |
|---|---|---|
| Step 1 (PDF 변환) | ~60초 | ~90초 |
| Step 2 (OCR 1,100장) | ~3분 | ~5분 |

---

## 문제 해결

### `java: command not found`
Java PATH가 설정되지 않은 경우입니다.
```bash
export PATH="/opt/homebrew/opt/openjdk@21/bin:$PATH"
```

### `tesseract: command not found`
Homebrew PATH가 등록되지 않은 경우입니다.
```bash
eval "$(/opt/homebrew/bin/brew shellenv)"
```

### `FileNotFoundError: PDF not found`
인수로 전달한 PDF 경로가 잘못된 경우입니다. 실제 PDF 경로를 확인하세요.

### OCR 결과가 없거나 부정확한 경우
- Tesseract 버전이 4.x 미만이면 정확도가 낮을 수 있습니다. `brew upgrade tesseract`로 업그레이드하세요.
- `ocr_replace.py`의 `SECTION_NUM_SIZE` / `DIAGRAM_SIZE_THRESHOLD` 값을 조정해 분류 기준을 변경할 수 있습니다.
