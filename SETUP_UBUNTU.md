# 개발환경 설치 가이드 (Ubuntu 22.04)

아무것도 설치되지 않은 Ubuntu 22.04 환경에서 이 프로젝트를 실행하기 위한 단계별 가이드입니다.

---

## 1. 시스템 패키지 업데이트

```bash
sudo apt update && sudo apt upgrade -y
```

---

## 2. Java 21 설치

OpenDataLoader PDF는 Java 기반입니다.

```bash
sudo apt install -y openjdk-21-jdk
```

설치 확인:

```bash
java --version
# openjdk 21.x.x ...
```

Ubuntu 22.04 기본 저장소에 Java 21이 없는 경우 아래 방법을 사용합니다.

```bash
# Adoptium(Eclipse Temurin) 저장소 추가
sudo apt install -y wget apt-transport-https gnupg
wget -qO - https://packages.adoptium.net/artifactory/api/gpg/key/public | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/adoptium.gpg
echo "deb https://packages.adoptium.net/artifactory/deb $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/adoptium.list
sudo apt update
sudo apt install -y temurin-21-jdk
```

---

## 3. Python 3.11 설치

Ubuntu 22.04에는 Python 3.10이 기본입니다. 3.11을 설치합니다.

```bash
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev
```

설치 확인:

```bash
python3.11 --version
# Python 3.11.x
```

---

## 4. Tesseract OCR 설치

이미지 내 텍스트를 인식하기 위한 OCR 엔진입니다.

```bash
sudo apt install -y tesseract-ocr tesseract-ocr-eng
```

설치 확인:

```bash
tesseract --version
# tesseract 4.x.x 또는 5.x.x
```

> Ubuntu 22.04 저장소에는 Tesseract 4.x가 제공됩니다. 5.x를 원하는 경우 아래를 실행합니다.

```bash
sudo add-apt-repository ppa:alex-p/tesseract-ocr5 -y
sudo apt update
sudo apt install -y tesseract-ocr
```

---

## 5. 이미지 처리 라이브러리 의존성 설치

Pillow 빌드에 필요한 시스템 라이브러리입니다.

```bash
sudo apt install -y \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    zlib1g-dev
```

---

## 6. 프로젝트 디렉토리 이동

```bash
cd /path/to/OpenDataLoader
```

---

## 7. Python 가상환경 생성 및 의존성 설치

```bash
# 가상환경 생성
python3.11 -m venv .venv

# 가상환경 활성화
source .venv/bin/activate

# pip 업그레이드
pip install -U pip

# 의존성 설치
pip install -r requirements.txt

# OCR 라이브러리 설치
pip install pytesseract pillow numpy
```

설치 확인:

```bash
python -c "import opendataloader_pdf; print('OpenDataLoader OK')"
python -c "import pytesseract; print('Tesseract version:', pytesseract.get_tesseract_version())"
```

---

## 8. Java PATH 설정 (필요한 경우)

`java` 명령이 인식되지 않으면 PATH를 등록합니다.

```bash
echo 'export JAVA_HOME=/usr/lib/jvm/temurin-21-amd64' >> ~/.bashrc
echo 'export PATH="$JAVA_HOME/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

> Java 설치 경로는 `update-java-alternatives -l` 명령으로 확인합니다.

---

## 9. 실행

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
# 1. 시스템 패키지 (최초 1회, sudo 필요)
sudo apt update && sudo apt upgrade -y
sudo apt install -y openjdk-21-jdk
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y && sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev
sudo apt install -y tesseract-ocr tesseract-ocr-eng
sudo apt install -y libjpeg-dev libpng-dev libtiff-dev libfreetype6-dev liblcms2-dev libwebp-dev zlib1g-dev

# 2. Python 환경 (최초 1회)
python3.11 -m venv .venv
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

| 단계 | 사양 (4코어 / 16GB RAM 기준) |
|---|---|
| Step 1 (PDF 변환) | ~90초 |
| Step 2 (OCR 1,100장) | ~5분 |

---

## 문제 해결

### `java: command not found`
Java가 PATH에 등록되지 않은 경우입니다.
```bash
export JAVA_HOME=$(dirname $(dirname $(readlink -f $(which java))))
export PATH="$JAVA_HOME/bin:$PATH"
```

### `tesseract: command not found`
Tesseract 설치를 확인합니다.
```bash
sudo apt install -y tesseract-ocr
```

### `error: could not find library 'libjpeg'` (Pillow 설치 실패)
이미지 처리 시스템 라이브러리가 없는 경우입니다.
```bash
sudo apt install -y libjpeg-dev libpng-dev zlib1g-dev
pip install --no-cache-dir pillow
```

### `FileNotFoundError: PDF not found`
인수로 전달한 PDF 경로가 잘못된 경우입니다. 실제 PDF 경로를 확인하세요.

### OCR 결과가 없거나 부정확한 경우
Ubuntu 22.04 기본 저장소의 Tesseract 4.x는 5.x 대비 정확도가 낮을 수 있습니다.
```bash
sudo add-apt-repository ppa:alex-p/tesseract-ocr5 -y
sudo apt update && sudo apt install -y tesseract-ocr
```
