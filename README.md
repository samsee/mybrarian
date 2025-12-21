# 📚 MyBrarian - 통합 도서 검색 시스템

ISBN 또는 도서명으로 여러 소스를 통합 검색하여 원하는 책의 이용 가능 여부를 한 번에 확인할 수 있는 통합 도서 검색 시스템입니다.

## ✨ 주요 기능

- 🔍 **통합 검색**: 도서명 또는 ISBN으로 여러 소스를 한 번에 검색
- 📚 **다양한 소스 지원**:
  - 내 보유 장서 (OneDrive)
  - 공공도서관 (도서관 정보나루 API)
  - 알라딘 온라인 서점
  - 리디북스 셀렉트
  - 부커스
  - 구글 플레이북
- ⚡ **병렬 검색**: 모든 소스를 동시에 검색하여 빠른 결과 제공
- 🎯 **우선순위 기반 정렬**: 사용자가 설정한 우선순위에 따라 결과 정렬
- 🌐 **Web API 제공**: FastAPI 기반의 RESTful API
- 🖥️ **CLI 지원**: 명령줄에서 간편하게 검색

## 🛠️ 기술 스택

- **언어**: Python 3.10+
- **패키지 관리**: uv
- **프레임워크**: FastAPI, Uvicorn
- **라이브러리**:
  - `requests`, `beautifulsoup4` - 웹 스크래핑
  - `playwright` - 동적 웹페이지 처리
  - `aiohttp` - 비동기 HTTP 요청
  - `pydantic` - 데이터 검증
  - `pyyaml` - 설정 파일 관리

## 📦 설치 방법

### 1. 저장소 클론

```bash
git clone https://github.com/yourusername/mybrarian.git
cd mybrarian
```

### 2. uv 설치 (선택사항)

이 프로젝트는 `uv`를 패키지 관리자로 사용합니다. uv가 설치되어 있지 않다면 먼저 설치하세요.

**Windows:**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

자세한 설치 방법은 [uv 공식 문서](https://docs.astral.sh/uv/getting-started/installation/)를 참고하세요.

### 3. 의존성 설치

```bash
# 가상환경 생성 및 의존성 설치 (한 번에)
uv sync
```

### 4. Playwright 브라우저 설치

일부 소스(리디북스, 부커스 등)는 동적 웹페이지를 처리하기 위해 Playwright가 필요합니다.

```bash
uv run playwright install chromium
```

## ⚙️ 설정 방법

### 1. 환경 변수 설정

`.env.example` 파일을 복사하여 `.env` 파일을 생성하고 필요한 정보를 입력합니다.

```bash
cp .env.example .env
```

`.env` 파일 예시:
```env
# 알라딘 API 키 (필수)
ALADIN_API_KEY=your_aladin_api_key_here

# 도서관 정보나루 API 키(rhdrhd)
LIBRARY_API_KEY=your_library_api_key_here

# 검색할 도서관 코드 (쉼표로 구분)
TARGET_LIBRARIES=111003,111019,111027

# 내 장서 경로 (OneDrive 등)
ONEDRIVE_BOOKS_PATH=C:/Users/YourUsername/OneDrive/Books

# 로그인이 필요한 서비스 (선택사항)
RIDI_USERNAME=your_username
RIDI_PASSWORD=your_password

# 부커스 전자도서관 (기관용)
BOOKERS_ORG_NAME=your_organization_name
BOOKERS_ORG_CODE=your_organization_code
BOOKERS_USERNAME=your_username
BOOKERS_PASSWORD=your_password

# 앱 설정
DEBUG=False
LOG_LEVEL=INFO
CACHE_ENABLED=True
CACHE_TTL=3600
REQUEST_TIMEOUT=10
```

### 2. API 키 발급

#### 알라딘 API 키
1. [알라딘 개발자센터](https://www.aladin.co.kr/ttb/wblog_manage.aspx) 접속
2. 회원가입 및 로그인
3. TTB키 발급 신청
4. 발급받은 키를 `.env` 파일의 `ALADIN_API_KEY`에 입력

#### 도서관 정보나루 API 키
1. [도서관 정보나루](https://www.data4library.kr) 접속
2. 회원가입 및 로그인
3. 마이페이지 > 인증키 발급
4. 발급받은 키를 `.env` 파일의 `LIBRARY_API_KEY`에 입력

#### 도서관 코드 찾기
1. [국립중앙도서관 검색](https://librarian.nl.go.kr/LI/contents/L10404000000.do) 접속
2. 원하는 도서관 검색
3. 도서관 코드(6자리 숫자) 확인
4. `.env` 파일의 `TARGET_LIBRARIES`에 쉼표로 구분하여 입력

**주요 도서관 코드 예시:**
- 국립중앙도서관: `011001`
- 서울도서관: `111314`
- 경기도서관: `141674`

#### 부커스 기관 코드 찾기 (선택사항)
부커스는 기관용 전자도서관 서비스로, 기관 계정이 필요합니다.

1. 부커스 로그인 페이지에서 기관명을 입력하면 자동완성 목록이 나타납니다
2. 개발자 도구(F12)를 열고 Network 탭으로 이동
3. 기관명을 입력하여 자동완성 목록에서 선택
4. Network 탭에서 로그인 요청을 확인하여 `um_uis_code` 값을 찾습니다
5. 찾은 코드를 `.env` 파일의 `BOOKERS_ORG_CODE`에 입력

### 3. 우선순위 설정

`config.yaml.example` 파일을 복사하여 `config.yaml` 파일을 생성하고 검색 소스의 우선순위를 설정합니다.

```bash
cp config.yaml.example config.yaml
```

`config.yaml` 예시:
```yaml
sources:
  - name: "내 보유 장서"
    priority: 1
    enabled: true
  - name: "공공도서관"
    priority: 2
    enabled: true
    libraries:
      - "111003"  # 국립중앙도서관
      - "111019"  # 서울시립도서관
  - name: "리디북스 셀렉트"
    priority: 3
    enabled: true
  - name: "부커스"
    priority: 5
    enabled: true
  - name: "구글 플레이북"
    priority: 6
    enabled: false
  - name: "알라딘 서점"
    priority: 7
    enabled: true

search:
  timeout: 10
  parallel: true
  max_results_per_source: 5

cache:
  enabled: true
  ttl: 3600
```

## 🚀 사용 방법

### 1. Web API 서버 실행

```bash
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

서버가 실행되면 다음 주소로 접속할 수 있습니다:
- API 서버: http://localhost:8000
- API 문서 (Swagger): http://localhost:8000/docs
- API 문서 (ReDoc): http://localhost:8000/redoc

### 2. API 사용 예시

#### 도서 검색

**요청:**
```bash
curl "http://localhost:8000/search?q=클린코드"
```

**응답:**
```json
{
  "query": "클린코드",
  "results": [
    {
      "source": "내 보유 장서",
      "available": true,
      "location": "C:/Users/YourName/OneDrive/Books/클린코드.pdf",
      "details": {
        "format": "PDF",
        "size": "15.2 MB"
      }
    },
    {
      "source": "공공도서관",
      "available": true,
      "library": "국립중앙도서관",
      "status": "대출가능",
      "details": {
        "isbn": "9788966261161",
        "author": "로버트 C. 마틴",
        "publisher": "인사이트"
      }
    },
    {
      "source": "알라딘 서점",
      "available": true,
      "price": 29700,
      "url": "https://www.aladin.co.kr/shop/...",
      "details": {
        "isbn": "9788966261161",
        "discount_rate": 10
      }
    }
  ],
  "total_sources": 7,
  "searched_sources": 5,
  "search_time": 2.34
}
```

#### ISBN으로 검색

```bash
curl "http://localhost:8000/search?q=9788966261161"
```

#### 검색 소스 목록 조회

```bash
curl "http://localhost:8000/sources"
```

**응답:**
```json
{
  "sources": [
    {
      "name": "내 보유 장서",
      "priority": 1,
      "enabled": true,
      "status": "active"
    },
    {
      "name": "공공도서관",
      "priority": 2,
      "enabled": true,
      "status": "active"
    },
    ...
  ]
}
```

#### 설정 조회 및 수정

**조회:**
```bash
curl "http://localhost:8000/config"
```

**수정:**
```bash
curl -X PUT "http://localhost:8000/config" \
  -H "Content-Type: application/json" \
  -d '{
    "sources": [
      {
        "name": "내 보유 장서",
        "priority": 1,
        "enabled": true
      }
    ]
  }'
```

### 3. CLI 사용

```bash
# 도서 검색
uv run mybrarian search "클린코드"

# ISBN으로 검색
uv run mybrarian search 9788966261161

# 특정 소스만 검색 (알라딘)
uv run mybrarian search-aladin "클린코드"

# 특정 소스만 검색 (공공도서관)
uv run mybrarian search-library "클린코드"

# 특정 소스만 검색 (내 보유 장서)
uv run mybrarian search-local "클린코드"

# 또는 가상환경 활성화 후 실행
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

mybrarian search "클린코드"
```

## 📂 프로젝트 구조

```
mybrarian/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI 앱
│   ├── config.py            # 설정 관리
│   ├── models.py            # 데이터 모델
│   ├── cli.py               # CLI 인터페이스
│   └── sources/             # 검색 소스 모듈
│       ├── __init__.py
│       ├── aladin.py            # 알라딘 API
│       ├── library.py           # 공공도서관
│       ├── ridibooks_select.py  # 리디북스 셀렉트
│       ├── bookers.py           # 부커스
│       ├── google_play.py       # 구글 플레이북
│       └── my_books.py          # 보유 장서
├── tests/                   # 테스트 코드
├── .env.example             # 환경변수 템플릿
├── .gitignore
├── config.yaml.example      # 설정 파일 템플릿
├── pyproject.toml           # 프로젝트 설정 및 의존성
├── uv.lock                  # 의존성 잠금 파일
├── CLAUDE.md                # 개발 진행 상황
└── README.md
```

## 🔧 고급 설정

### 캐싱 설정

검색 결과를 캐싱하여 동일한 검색의 반복 시 속도를 향상시킬 수 있습니다.

```yaml
# config.yaml
cache:
  enabled: true
  ttl: 3600  # 1시간 (초 단위)
```

### 타임아웃 설정

각 소스별 검색 타임아웃을 설정할 수 있습니다.

```yaml
# config.yaml
search:
  timeout: 10  # 초 단위
  parallel: true  # 병렬 검색 활성화
```

### 로깅 설정

```env
# .env
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

## 🧪 테스트

```bash
# 전체 테스트 실행
uv run pytest

# 특정 모듈 테스트
uv run pytest tests/test_aladin.py

# 커버리지 확인
uv run pytest --cov=src tests/
```

## 🐛 트러블슈팅

### Playwright 관련 오류

**문제:** `playwright._impl._api_types.Error: Executable doesn't exist`

**해결:**
```bash
uv run playwright install chromium
```

### ModuleNotFoundError 오류

**문제:** `ModuleNotFoundError: No module named 'xxx'`

**해결:**
```bash
# 의존성 재설치
uv sync

# 특정 패키지 추가
uv add <package-name>
```

### API 키 오류

**문제:** `401 Unauthorized` 또는 API 키 관련 오류

**해결:**
1. `.env` 파일에 올바른 API 키가 입력되었는지 확인
2. API 키에 공백이나 특수문자가 잘못 포함되지 않았는지 확인
3. API 키의 유효기간이 만료되지 않았는지 확인

### 도서관 검색이 되지 않음

**문제:** 특정 도서관에서 검색이 되지 않음

**해결:**
1. `config.yaml`의 도서관 코드가 올바른지 확인
2. 해당 도서관의 API 지원 여부 확인
3. 도서관 정보나루 사이트에서 도서관 상태 확인

## 🤝 기여하기

이슈나 풀 리퀘스트는 언제나 환영합니다!

1. 이 저장소를 Fork 합니다
2. Feature 브랜치를 생성합니다 (`git checkout -b feature/AmazingFeature`)
3. 변경사항을 커밋합니다 (`git commit -m 'Add some AmazingFeature'`)
4. 브랜치에 Push 합니다 (`git push origin feature/AmazingFeature`)
5. Pull Request를 생성합니다

## 📄 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 [LICENSE](LICENSE.txt) 파일을 참고하세요.

## 💬 문의

프로젝트에 대한 질문이나 제안사항이 있으시면 이슈를 생성해 주세요.

---

**Made with ❤️ by MyBrarian Team**
