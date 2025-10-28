# Tarot AI Reading Service - Backend

FastAPI 기반 타로 AI 리딩 서비스 백엔드

## 기술 스택

- **Python**: 3.9+
- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL + SQLAlchemy
- **Cache**: Redis
- **AI Providers**: OpenAI, Anthropic Claude
- **Authentication**: JWT

## 프로젝트 구조

```
backend/
├── src/
│   ├── api/              # API 엔드포인트
│   ├── models/           # 데이터베이스 모델
│   ├── schemas/          # Pydantic 스키마
│   ├── ai/
│   │   ├── providers/    # AI Provider 구현
│   │   └── prompt_engine/# 프롬프트 엔진
│   ├── tarot/
│   │   ├── cards/        # 카드 관련 로직
│   │   └── spreads/      # 스프레드 로직
│   └── core/             # 핵심 설정 및 유틸
├── tests/                # 테스트 코드
├── scripts/              # 유틸리티 스크립트
├── data/                 # 데이터 파일
├── prompts/              # 프롬프트 템플릿
├── main.py               # 애플리케이션 진입점
└── requirements.txt      # Python 의존성
```

## 설치 및 실행

### 1. 가상환경 설정

```bash
# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화 (macOS/Linux)
source venv/bin/activate

# 가상환경 활성화 (Windows)
venv\Scripts\activate
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정

```bash
# .env.example을 .env로 복사
cp .env.example .env

# .env 파일 편집하여 실제 값 입력
# - DATABASE_URL
# - REDIS_URL
# - SECRET_KEY (보안 키)
# - OPENAI_API_KEY
# - ANTHROPIC_API_KEY
```

### 4. 서버 실행

```bash
# 개발 서버 실행 (자동 리로드)
python main.py

# 또는 uvicorn 직접 실행
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API 문서

서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API 엔드포인트

### 헬스 체크

```bash
# 루트 엔드포인트
GET /

# 헬스 체크
GET /health

# API 상태
GET /api/v1/status
```

### 예시 응답

```json
{
  "message": "Welcome to Tarot AI Reading Service",
  "version": "0.1.0",
  "status": "healthy"
}
```

## 개발 가이드

### 코드 품질 도구

```bash
# 코드 포맷팅 (Black)
black .

# 임포트 정렬 (isort)
isort .

# 린팅 (Flake8)
flake8 .

# 타입 체크 (MyPy)
mypy src/
```

### 테스트 실행

```bash
# 모든 테스트 실행
pytest

# 커버리지 포함
pytest --cov=src --cov-report=html

# 특정 테스트 파일 실행
pytest tests/test_api.py
```

## 데이터베이스 마이그레이션

```bash
# 마이그레이션 생성
alembic revision --autogenerate -m "migration message"

# 마이그레이션 적용
alembic upgrade head

# 마이그레이션 롤백
alembic downgrade -1
```

## 환경 변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `APP_NAME` | 애플리케이션 이름 | Tarot AI Reading Service |
| `APP_VERSION` | 애플리케이션 버전 | 0.1.0 |
| `DEBUG` | 디버그 모드 | True |
| `DATABASE_URL` | PostgreSQL 연결 URL | - |
| `REDIS_URL` | Redis 연결 URL | - |
| `SECRET_KEY` | JWT 시크릿 키 | - |
| `OPENAI_API_KEY` | OpenAI API 키 | - |
| `ANTHROPIC_API_KEY` | Anthropic API 키 | - |
| `DEFAULT_AI_PROVIDER` | 기본 AI 제공자 | openai |

## 현재 구현 상태

### ✅ 완료
- [x] 프로젝트 초기 설정
- [x] FastAPI 기본 애플리케이션
- [x] 환경 변수 관리
- [x] CORS 설정
- [x] 기본 API 엔드포인트
- [x] Swagger UI 문서화
- [x] 데이터베이스 모델 (Cards, Readings, ReadingCards)
- [x] 타로 카드 데이터 시스템 (78장 완전 구현)
- [x] AI Provider 통합 (OpenAI, Anthropic Claude)
- [x] 멀티 프로바이더 오케스트레이터
- [x] 프롬프트 엔진 (Jinja2 템플릿)
- [x] 리딩 시스템 (원카드, 쓰리카드)
- [x] 카드 셔플 및 드로우 시스템
- [x] 카드 이미지 생성 (SVG)
- [x] 리딩 히스토리 저장
- [x] 테스트 코드

### 🚧 향후 계획
- [ ] 사용자 인증 및 권한 관리
- [ ] 더 많은 스프레드 타입 (Celtic Cross, etc.)
- [ ] 피드백 시스템
- [ ] 리딩 공유 기능
- [ ] 성능 모니터링 및 로깅 개선

## 트러블슈팅

### 서버가 시작되지 않는 경우

1. 가상환경이 활성화되었는지 확인
2. 모든 의존성이 설치되었는지 확인: `pip list`
3. 포트 8000이 사용 중인지 확인: `lsof -i :8000`

### 데이터베이스 연결 오류

1. PostgreSQL이 실행 중인지 확인
2. DATABASE_URL이 올바른지 확인
3. 데이터베이스가 생성되었는지 확인

## 라이선스

MIT License

## 문서

- [프로젝트 기획](../PROJECT_PLAN.md)
- [의도 문서](../INTEND.md)
- [태스크 관리](../TASK.md)
