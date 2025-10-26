# KSAT Agent - Frontend

KSAT(수능 언어 영역) 문항을 자동으로 생성하는 AI 에이전트의 Streamlit 프론트엔드 애플리케이션입니다.

## 기능

- **직관적인 UI**: 사용자 친화적인 인터페이스로 문항 생성 파라미터를 쉽게 설정
- **실시간 진행 상황**: SSE(Server-Sent Events)를 통한 실시간 생성 진행 상황 표시
- **결과 뷰어**: 생성된 문항을 수능 시험지 스타일로 시각화
- **이력 관리**: 이전에 생성한 문항 세트를 조회하고 다운로드

## 기술 스택

- **Streamlit**: Python 기반 웹 애플리케이션 프레임워크
- **Requests**: HTTP 클라이언트 (백엔드 API 통신)
- **Pandas**: 데이터 처리 및 시각화

## 환경 설정

### 백엔드 API URL 설정

`app.py` 파일에서 백엔드 API URL을 설정합니다:

```python
# 백엔드 API URL (환경에 맞게 수정)
BACKEND_URL = "http://localhost:8000"  # 로컬 개발
# BACKEND_URL = "https://your-backend-url.run.app"  # 프로덕션
```

또는 Streamlit Cloud에서 Secrets를 사용하여 설정할 수 있습니다.

`.streamlit/secrets.toml` 파일을 생성하고 다음 내용을 추가:

```toml
BACKEND_URL = "https://your-backend-url.run.app"
```

그리고 `app.py`에서 다음과 같이 사용:

```python
BACKEND_URL = st.secrets.get("BACKEND_URL", "http://localhost:8000")
```

## 로컬 실행

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 백엔드 서버 실행

백엔드 서버가 실행 중인지 확인합니다. (기본: `http://localhost:8000`)

### 3. Streamlit 앱 실행

```bash
streamlit run app.py
```

앱이 브라우저에서 자동으로 열립니다. (기본: `http://localhost:8501`)

## Streamlit Cloud 배포

### 1. GitHub 레포지토리 생성

이 디렉토리를 GitHub 레포지토리로 푸시합니다.

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/wnsgml9807/KSAT-demo-frontend.git
git push -u origin main
```

### 2. Streamlit Cloud 배포

1. [Streamlit Cloud](https://streamlit.io/cloud)에 로그인
2. "New app" 클릭
3. GitHub 레포지토리 선택: `wnsgml9807/KSAT-demo-frontend`
4. Main file path: `app.py`
5. Advanced settings > Secrets에 백엔드 URL 추가:
   ```toml
   BACKEND_URL = "https://your-backend-url.run.app"
   ```
6. "Deploy!" 클릭

### 3. 배포 후 확인

배포가 완료되면 Streamlit Cloud에서 제공하는 URL을 통해 앱에 접근할 수 있습니다.

## 주요 기능 설명

### 1. 문항 생성 페이지

- **분야 선택**: 인문예술, 법, 경제, 과학기술 중 선택
- **유형 선택**: 단일형 또는 (가),(나) 분리형
- **주제 입력**: 원하는 주제를 자유롭게 입력 (선택사항)
- **출제 포인트**: 핵심 출제 포인트를 선택 (선택사항)
- **문항 구성**: 문항 번호, 유형, 스타일, 정답을 설정

### 2. 생성 결과 뷰어

- **소재 카드**: 생성된 논리 구조 및 문항 설계 확인
- **지문**: 수능 시험지 스타일로 렌더링된 지문
- **문항**: 각 문항의 발문, 선지, 해설 확인
- **다운로드**: JSON 형식으로 결과 다운로드

### 3. 이력 조회

- 이전에 생성한 문항 세트 목록 조회
- 생성일자, 대분야, 주제, 문항 수 등의 메타데이터 확인
- 클릭하여 상세 내용 조회

## 프로젝트 구조

```
frontend/
├── app.py                    # Streamlit 애플리케이션 메인 파일
├── logo_kangnam_202111.png   # 로고 이미지
├── .streamlit/
│   └── config.toml           # Streamlit 설정 파일
├── requirements.txt          # Python 의존성
└── README.md
```

## 문제 해결

### 백엔드 연결 오류

- 백엔드 URL이 올바른지 확인
- 백엔드 서버가 실행 중인지 확인
- CORS 설정이 올바른지 확인

### Streamlit Cloud 배포 오류

- `requirements.txt`에 모든 의존성이 포함되어 있는지 확인
- Python 버전 호환성 확인 (Python 3.10 권장)
- Secrets가 올바르게 설정되어 있는지 확인

## 라이선스

© 2024 KSAT Agent Team. All rights reserved.

