# Tarot AI Reading Service

AI 기반 타로 카드 리딩 서비스입니다. OpenAI GPT-4와 Anthropic Claude를 활용하여 심층적이고 개인화된 타로 리딩을 제공합니다.

> **📝 배포 관련 문서**: Backend URL 변경 및 배포 시 [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)를 참조하세요.

## 주요 기능

### 1. 타로 리딩
- **원카드 리딩**: 간단한 질문에 대한 빠른 답변
- **쓰리카드 리딩**: 과거-현재-미래 또는 상황-행동-결과 스프레드
- **AI 기반 해석**: GPT-4와 Claude를 활용한 맥락적이고 심층적인 해석
- **실시간 카드 드로우**: 애니메이션과 함께 카드를 섞고 뽑는 인터랙티브한 경험

### 2. 리딩 히스토리
- **전체 리딩 저장**: 모든 리딩이 자동으로 데이터베이스에 저장됩니다
- **상세 리딩 조회**: 과거 리딩을 언제든지 다시 확인할 수 있습니다
- **필터링 및 검색**: 스프레드 타입별로 리딩을 필터링할 수 있습니다
- **페이지네이션**: 많은 리딩도 쉽게 탐색할 수 있습니다

### 3. 카드 컬렉션
- **78장 완전한 타로 덱**: Major Arcana 22장 + Minor Arcana 56장
- **상세 카드 정보**: 각 카드의 의미, 키워드, 상징 등
- **검색 및 필터링**: 카드 이름, 아르카나 타입, 수트별 검색
- **인터랙티브 모달**: 클릭으로 카드 상세 정보 확인
- **SVG 카드 이미지**: 아름답고 색상으로 구분된 카드 이미지

### 4. 멀티 AI 프로바이더
- **OpenAI GPT-4**: 깊이 있고 창의적인 해석
- **Anthropic Claude**: 구조화되고 신중한 분석
- **자동 폴백**: 한 프로바이더 실패 시 자동으로 다른 프로바이더 사용
- **토큰 관리**: 효율적인 토큰 사용과 비용 최적화

## 기술 스택

### Backend
- **FastAPI**: 현대적이고 빠른 Python 웹 프레임워크
- **PostgreSQL**: 관계형 데이터베이스
- **SQLAlchemy**: ORM 및 데이터베이스 관리
- **Alembic**: 데이터베이스 마이그레이션
- **Redis**: 캐싱 및 성능 최적화
- **Pydantic V2**: 데이터 검증 및 직렬화
- **OpenAI API**: GPT-4 모델 사용
- **Anthropic API**: Claude 모델 사용
- **Jinja2**: 프롬프트 템플릿 엔진

### Frontend
- **Next.js 14**: React 기반 프레임워크 (App Router)
- **TypeScript**: 타입 안전성
- **Tailwind CSS**: 유틸리티 기반 스타일링
- **Framer Motion**: 애니메이션
- **React Hooks**: 상태 관리

## 프로젝트 구조

```
tarot-project-claude/
├── backend/                    # FastAPI 백엔드
│   ├── alembic/               # 데이터베이스 마이그레이션
│   ├── prompts/               # AI 프롬프트 템플릿
│   │   ├── reading/           # 리딩 프롬프트
│   │   └── templates/         # 공통 템플릿
│   ├── scripts/               # 유틸리티 스크립트
│   │   ├── seed_cards.py      # 카드 데이터 시딩
│   │   └── generate_card_images.py  # SVG 이미지 생성
│   ├── src/                   # 소스 코드
│   │   ├── ai/                # AI 프로바이더 및 엔진
│   │   │   ├── providers/     # OpenAI, Claude 구현
│   │   │   └── prompt_engine/ # 프롬프트 관리
│   │   ├── api/               # API 엔드포인트
│   │   ├── core/              # 핵심 설정
│   │   ├── models/            # SQLAlchemy 모델
│   │   ├── schemas/           # Pydantic 스키마
│   │   └── tarot/             # 타로 로직
│   │       ├── cards/         # 카드 관리
│   │       └── spreads/       # 스프레드 관리
│   ├── tests/                 # 테스트
│   ├── venv/                  # Python 가상환경
│   ├── .env                   # 환경 변수 (gitignore)
│   ├── .env.example           # 환경 변수 예시
│   ├── requirements.txt       # Python 의존성
│   └── main.py                # 애플리케이션 진입점
│
├── frontend/                  # Next.js 프론트엔드
│   ├── public/                # 정적 파일
│   │   └── images/cards/      # 타로 카드 SVG 이미지
│   ├── src/
│   │   ├── app/               # Next.js 14 App Router
│   │   │   ├── cards/         # 카드 컬렉션 페이지
│   │   │   ├── history/       # 리딩 히스토리
│   │   │   │   └── [id]/      # 리딩 상세
│   │   │   ├── reading/       # 리딩 페이지
│   │   │   │   ├── one-card/  # 원카드 리딩
│   │   │   │   └── three-card/# 쓰리카드 리딩
│   │   │   ├── layout.tsx     # 루트 레이아웃
│   │   │   └── page.tsx       # 홈페이지
│   │   ├── components/        # React 컴포넌트
│   │   │   ├── CardDeck.tsx   # 카드 덱 컴포넌트
│   │   │   └── TarotCard.tsx  # 타로 카드 컴포넌트
│   │   ├── lib/               # 유틸리티
│   │   │   └── api.ts         # API 클라이언트
│   │   └── types/             # TypeScript 타입
│   ├── .env.local.example     # 환경 변수 예시
│   ├── package.json           # npm 의존성
│   ├── tailwind.config.js     # Tailwind 설정
│   └── tsconfig.json          # TypeScript 설정
│
└── README.md                  # 이 파일
```

## 설치 및 실행

### 사전 요구사항

- **Python 3.11+**
- **Node.js 20+**
- **PostgreSQL 14+**
- **Redis** (선택사항, 캐싱용)
- **OpenAI API Key**
- **Anthropic API Key**

### 1. 저장소 클론

```bash
git clone <repository-url>
cd tarot-project-claude
```

### 2. 백엔드 설정

```bash
cd backend

# Python 가상환경 생성
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install --upgrade pip
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일을 열어 다음 값들을 설정:
# - DATABASE_URL
# - OPENAI_API_KEY
# - ANTHROPIC_API_KEY
# - REDIS_URL (선택사항)

# PostgreSQL 데이터베이스 생성
createdb tarot_db

# 데이터베이스 마이그레이션
alembic upgrade head

# 카드 데이터 시딩
python scripts/seed_cards.py --clear

# 카드 이미지 생성 (선택사항)
python scripts/generate_card_images.py

# 서버 실행
python main.py
```

백엔드 서버가 `http://localhost:8000`에서 실행됩니다.

### 3. 프론트엔드 설정

```bash
cd frontend

# 의존성 설치
npm install

# 환경 변수 설정 (필요한 경우)
cp .env.local.example .env.local

# 개발 서버 실행
npm run dev
```

프론트엔드가 `http://localhost:3000`에서 실행됩니다.

## API 엔드포인트

### 카드 관리
- `GET /api/v1/cards` - 카드 목록 조회 (페이지네이션, 필터링)
- `GET /api/v1/cards/{card_id}` - 특정 카드 조회
- `GET /api/v1/cards/suit/{suit}` - 수트별 카드 조회
- `GET /api/v1/cards/arcana/{arcana_type}` - 아르카나 타입별 조회
- `GET /api/v1/cards/random/draw?count={n}` - 랜덤 카드 뽑기

### 리딩 관리
- `POST /api/v1/readings` - 새 리딩 생성
- `GET /api/v1/readings` - 리딩 목록 조회
- `GET /api/v1/readings/{reading_id}` - 특정 리딩 조회

### 시스템
- `GET /health` - 헬스 체크
- `GET /api/v1/status` - 시스템 상태
- `GET /docs` - API 문서 (Swagger UI)

## 환경 변수

### Backend (.env)

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/tarot_db

# AI Providers
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# Redis (선택사항)
REDIS_URL=redis://localhost:6379/0
ENABLE_CACHE=false

# Server
APP_NAME=Tarot AI Reading Service
DEBUG=false
API_VERSION=v1

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
```

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 데이터베이스 스키마

### Cards 테이블
- `id`: UUID (Primary Key)
- `name`: 영문 카드 이름
- `name_ko`: 한글 카드 이름
- `arcana_type`: Major/Minor Arcana
- `suit`: Wands/Cups/Swords/Pentacles (Minor Arcana만)
- `number`: 카드 번호
- `keywords_upright`: 정방향 키워드 (배열)
- `keywords_reversed`: 역방향 키워드 (배열)
- `meaning_upright`: 정방향 의미
- `meaning_reversed`: 역방향 의미
- `description`: 카드 설명
- `symbolism`: 상징
- `image_url`: 이미지 URL

### Readings 테이블
- `id`: UUID (Primary Key)
- `spread_type`: 스프레드 타입
- `question`: 사용자 질문
- `summary`: 리딩 요약
- `overall_reading`: 전체 리딩
- `card_relationships`: 카드 간 관계 (쓰리카드만)
- `advice`: 조언 (JSON)
- `category`: 카테고리
- `created_at`: 생성 시간

### Reading_Cards 테이블
- `id`: UUID (Primary Key)
- `reading_id`: 리딩 ID (Foreign Key)
- `card_id`: 카드 ID (Foreign Key)
- `position`: 카드 위치
- `orientation`: upright/reversed
- `key_message`: 핵심 메시지
- `interpretation`: AI 해석

## AI 프롬프트 시스템

### 프롬프트 템플릿
프로젝트는 Jinja2 템플릿 엔진을 사용하여 동적 프롬프트를 생성합니다:

- `prompts/templates/base.txt`: 기본 시스템 프롬프트
- `prompts/reading/one_card.txt`: 원카드 리딩 프롬프트
- `prompts/reading/three_card_past_present_future.txt`: 쓰리카드 (과거/현재/미래)
- `prompts/reading/three_card_situation_action_outcome.txt`: 쓰리카드 (상황/행동/결과)

### 프롬프트 엔진 기능
- 템플릿 로딩 및 렌더링
- 토큰 카운팅 및 최적화
- 컨텍스트 빌더
- 응답 파서

## 테스트

### 백엔드 테스트 실행

```bash
cd backend
source venv/bin/activate

# 전체 테스트 실행
pytest

# 커버리지와 함께 실행
pytest --cov=src tests/

# 특정 테스트 파일 실행
pytest tests/test_card_model.py -v
```

### 테스트 구조
- `tests/test_card_model.py`: 카드 모델 테스트
- `tests/test_card_shuffle.py`: 카드 셔플 테스트
- `tests/test_openai_provider.py`: OpenAI 프로바이더 테스트
- `tests/test_claude_provider.py`: Claude 프로바이더 테스트
- `tests/test_orchestrator.py`: AI 오케스트레이터 테스트
- `tests/test_prompt_engine.py`: 프롬프트 엔진 테스트
- `tests/test_reading_validator.py`: 리딩 검증 테스트

## 개발

### 코드 포맷팅

```bash
# 백엔드
cd backend
black src/
isort src/
flake8 src/

# 프론트엔드
cd frontend
npm run format
npm run lint
```

### 데이터베이스 마이그레이션

```bash
cd backend
source venv/bin/activate

# 새 마이그레이션 생성
alembic revision --autogenerate -m "description"

# 마이그레이션 적용
alembic upgrade head

# 이전 버전으로 롤백
alembic downgrade -1
```

### 카드 데이터 재시딩

```bash
cd backend
source venv/bin/activate

# 기존 카드 삭제 후 재시딩
python scripts/seed_cards.py --clear

# 카드만 추가 (중복 방지)
python scripts/seed_cards.py
```

## 주요 특징

### 1. 멀티 프로바이더 AI 시스템
- OpenAI와 Anthropic을 모두 지원하는 유연한 아키텍처
- 자동 폴백으로 높은 가용성 보장
- 각 프로바이더의 강점을 활용한 최적화된 프롬프트

### 2. 구조화된 AI 응답
- Pydantic을 사용한 타입 안전한 응답 검증
- 일관된 데이터 구조로 프론트엔드 통합 간소화
- JSON 스키마 기반 응답 파싱

### 3. 확장 가능한 스프레드 시스템
- 플러그인 형식의 스프레드 타입 추가 가능
- 각 스프레드별 맞춤 프롬프트 템플릿
- 쉽게 새로운 스프레드 추가 가능

### 4. 성능 최적화
- Redis 캐싱으로 반복 쿼리 최적화
- 데이터베이스 인덱싱
- 프론트엔드 코드 스플리팅
- 이미지 최적화 (SVG 사용)

### 5. 사용자 경험
- 부드러운 애니메이션 (Framer Motion)
- 반응형 디자인 (모바일 친화적)
- 다크 모드 지원
- 직관적인 UI/UX

## 향후 계획

- [ ] 사용자 인증 및 개인화
- [ ] 더 많은 스프레드 타입 (Celtic Cross, etc.)
- [ ] 카드 북마크 기능
- [ ] 리딩 공유 기능
- [ ] 다국어 지원
- [ ] 모바일 앱 (React Native)
- [ ] Docker 컨테이너화
- [ ] CI/CD 파이프라인
- [ ] 성능 모니터링 (Sentry, etc.)

## 라이선스

This project is licensed under the MIT License.

## 기여

기여를 환영합니다! Pull Request를 보내주세요.

## 문의

문제가 발생하거나 질문이 있으시면 Issues를 통해 연락주세요.

---

**Powered by OpenAI GPT-4 & Anthropic Claude**