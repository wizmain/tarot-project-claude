# 타로 AI 리딩 서비스 - 시스템 아키텍처

## 문서 정보
- **버전**: 1.0
- **작성일**: 2025-10-22
- **최종 수정일**: 2025-10-22
- **작성자**: Development Team

---

## 목차
1. [시스템 개요](#시스템-개요)
2. [전체 시스템 구성도](#전체-시스템-구성도)
3. [백엔드 아키텍처](#백엔드-아키텍처)
4. [프론트엔드 아키텍처](#프론트엔드-아키텍처)
5. [데이터 흐름](#데이터-흐름)
6. [데이터베이스 스키마](#데이터베이스-스키마)
7. [보안 아키텍처](#보안-아키텍처)
8. [배포 아키텍처](#배포-아키텍처)

---

## 시스템 개요

타로 AI 리딩 서비스는 사용자에게 AI 기반 타로 카드 리딩을 제공하는 웹 애플리케이션입니다.

### 핵심 기능
- 타로 카드 조회 및 검색
- AI 기반 타로 리딩 (원카드, 쓰리카드, 켈틱크로스 등)
- 다중 AI 프로바이더 지원 (OpenAI GPT-4, Anthropic Claude)
- 사용자 인증 및 회원 관리
- 리딩 이력 관리
- 피드백 및 통계 시스템

### 기술 스택
- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS
- **Backend**: FastAPI, Python 3.11+, SQLAlchemy
- **Database**: PostgreSQL 14
- **Cache**: Redis
- **AI**: OpenAI GPT-4, Anthropic Claude 3.5 Sonnet
- **Auth**: JWT, Firebase Auth, Auth0 (Multi-provider)

---

## 전체 시스템 구성도

```mermaid
graph TB
    subgraph "Client Layer"
        Client[Web Browser<br/>Next.js 14 + React]
    end

    subgraph "Frontend Layer"
        NextJS[Next.js Application<br/>Port 3000]
        UI[UI Components<br/>TarotCard, ReadingForm]
        State[State Management<br/>React Hooks]
    end

    subgraph "Backend Layer - FastAPI"
        API[FastAPI Application<br/>Port 8000]

        subgraph "API Routes"
            CardsRoute[/api/v1/cards]
            ReadingsRoute[/api/v1/readings]
            AuthRoute[/api/v1/auth]
            FeedbackRoute[/api/v1/feedback]
            AdminRoute[/api/v1/admin]
        end

        subgraph "Business Logic"
            CardRepo[Card Repository]
            ReadingRepo[Reading Repository]
            FeedbackRepo[Feedback Repository]
            UserRepo[User Repository]

            AIOrch[AI Orchestrator]
            PromptEngine[Prompt Engine]
            ContextBuilder[Context Builder]
            ResponseParser[Response Parser]

            AuthOrch[Auth Orchestrator]
            AuthFactory[Auth Provider Factory]
        end

        subgraph "AI Providers"
            OpenAI[OpenAI Provider<br/>GPT-4]
            Claude[Claude Provider<br/>Claude 3.5 Sonnet]
        end

        subgraph "Auth Providers"
            JWT[JWT Provider]
            Firebase[Firebase Provider]
            Auth0[Auth0 Provider]
        end
    end

    subgraph "Data Layer"
        PostgreSQL[(PostgreSQL<br/>Database)]
        Redis[(Redis<br/>Cache)]
    end

    subgraph "External Services"
        OpenAIAPI[OpenAI API]
        ClaudeAPI[Anthropic API]
        FirebaseAuth[Firebase Auth]
        Auth0Service[Auth0 Service]
    end

    Client --> NextJS
    NextJS --> UI
    NextJS --> State
    NextJS --> API

    API --> CardsRoute
    API --> ReadingsRoute
    API --> AuthRoute
    API --> FeedbackRoute
    API --> AdminRoute

    CardsRoute --> CardRepo
    ReadingsRoute --> ReadingRepo
    ReadingsRoute --> AIOrch
    FeedbackRoute --> FeedbackRepo
    AdminRoute --> FeedbackRepo
    AuthRoute --> AuthOrch

    AIOrch --> PromptEngine
    AIOrch --> ContextBuilder
    AIOrch --> ResponseParser
    AIOrch --> OpenAI
    AIOrch --> Claude

    OpenAI --> OpenAIAPI
    Claude --> ClaudeAPI

    AuthOrch --> AuthFactory
    AuthFactory --> JWT
    AuthFactory --> Firebase
    AuthFactory --> Auth0

    Firebase --> FirebaseAuth
    Auth0 --> Auth0Service

    CardRepo --> PostgreSQL
    ReadingRepo --> PostgreSQL
    FeedbackRepo --> PostgreSQL
    UserRepo --> PostgreSQL

    CardRepo --> Redis
    AIOrch --> Redis

    style Client fill:#e1f5ff
    style NextJS fill:#61dafb
    style API fill:#009688
    style PostgreSQL fill:#336791
    style Redis fill:#dc382d
    style OpenAIAPI fill:#10a37f
    style ClaudeAPI fill:#191919
```

---

## 백엔드 아키텍처

### 레이어드 아키텍처

```mermaid
graph TD
    subgraph "Presentation Layer"
        Routes[API Routes<br/>FastAPI Routers]
        Schemas[Pydantic Schemas<br/>Request/Response Models]
    end

    subgraph "Application Layer"
        Services[Services Layer<br/>Orchestrators]
        Dependencies[Dependencies<br/>Auth, DB Session]
    end

    subgraph "Domain Layer"
        Repositories[Repositories<br/>Data Access]
        Models[SQLAlchemy Models<br/>Domain Entities]
    end

    subgraph "Infrastructure Layer"
        Database[Database<br/>PostgreSQL]
        Cache[Cache<br/>Redis]
        External[External APIs<br/>OpenAI, Claude]
    end

    Routes --> Schemas
    Routes --> Dependencies
    Routes --> Services
    Services --> Repositories
    Repositories --> Models
    Models --> Database
    Services --> Cache
    Services --> External

    style Routes fill:#4caf50
    style Services fill:#2196f3
    style Repositories fill:#ff9800
    style Database fill:#9c27b0
```

### 디렉토리 구조

```
backend/
├── src/
│   ├── api/                    # API Layer
│   │   ├── routes/             # API 엔드포인트
│   │   │   ├── cards.py        # 카드 API
│   │   │   ├── readings.py     # 리딩 API
│   │   │   ├── auth.py         # 인증 API
│   │   │   ├── feedback.py     # 피드백 API
│   │   │   └── admin.py        # 관리자 API
│   │   ├── repositories/       # 데이터 액세스
│   │   │   ├── card_repository.py
│   │   │   ├── reading_repository.py
│   │   │   ├── feedback_repository.py
│   │   │   └── user_repository.py
│   │   └── dependencies/       # FastAPI Dependencies
│   │       └── auth.py         # 인증 의존성
│   ├── auth/                   # 인증 시스템
│   │   ├── orchestrator.py     # Auth Orchestrator
│   │   ├── factory.py          # Provider Factory
│   │   └── providers/          # Auth Providers
│   │       ├── jwt_provider.py
│   │       ├── firebase_provider.py
│   │       └── auth0_provider.py
│   ├── ai/                     # AI 시스템
│   │   ├── orchestrator.py     # AI Orchestrator
│   │   ├── providers/          # AI Providers
│   │   │   ├── openai_provider.py
│   │   │   └── claude_provider.py
│   │   └── prompt_engine/      # 프롬프트 엔진
│   │       ├── template_engine.py
│   │       ├── context_builder.py
│   │       └── response_parser.py
│   ├── models/                 # SQLAlchemy Models
│   │   ├── card.py
│   │   ├── reading.py
│   │   ├── feedback.py
│   │   └── user.py
│   ├── schemas/                # Pydantic Schemas
│   │   ├── card_schema.py
│   │   ├── reading_schema.py
│   │   ├── feedback_schema.py
│   │   └── auth_schema.py
│   ├── core/                   # Core Infrastructure
│   │   ├── config.py           # Configuration
│   │   ├── database.py         # Database Connection
│   │   ├── cache.py            # Redis Cache
│   │   └── logging.py          # Logging Setup
│   └── tarot/                  # 타로 비즈니스 로직
│       ├── cards/              # 카드 데이터
│       └── spreads/            # 스프레드 정의
├── alembic/                    # Database Migrations
├── tests/                      # Unit & Integration Tests
├── scripts/                    # Utility Scripts
├── prompts/                    # AI 프롬프트 템플릿
└── main.py                     # Application Entry Point
```

### 주요 컴포넌트 설명

#### 1. API Routes (프레젠테이션 계층)
- FastAPI 라우터를 통한 RESTful API 제공
- Pydantic을 이용한 요청/응답 검증
- OpenAPI (Swagger) 자동 문서화

#### 2. Repositories (데이터 접근 계층)
- 데이터베이스 CRUD 작업 추상화
- SQLAlchemy ORM을 통한 타입 안전한 쿼리
- 통계 및 집계 쿼리 메서드

#### 3. AI Orchestrator (비즈니스 로직 계층)
- 다중 AI 프로바이더 통합
- 프롬프트 생성 및 컨텍스트 빌딩
- AI 응답 파싱 및 검증
- 캐싱을 통한 성능 최적화

#### 4. Auth Orchestrator (인증 계층)
- 다중 인증 프로바이더 지원
- JWT 토큰 생성 및 검증
- Firebase/Auth0 연동

---

## 프론트엔드 아키텍처

### 컴포넌트 구조

```mermaid
graph TD
    subgraph "Next.js Application"
        App[App Router<br/>Next.js 14]

        subgraph "Pages"
            HomePage[Home Page<br/>/]
            CardsPage[Cards Page<br/>/cards]
            ReadingPage[Reading Page<br/>/readings]
            HistoryPage[History Page<br/>/history]
        end

        subgraph "Components"
            TarotCard[TarotCard<br/>카드 컴포넌트]
            ReadingForm[ReadingForm<br/>리딩 폼]
            SpreadLayout[SpreadLayout<br/>스프레드 레이아웃]
            FeedbackForm[FeedbackForm<br/>피드백 폼]
        end

        subgraph "Hooks"
            UseAuth[useAuth<br/>인증 훅]
            UseReading[useReading<br/>리딩 훅]
            UseCards[useCards<br/>카드 훅]
        end

        subgraph "Services"
            APIClient[API Client<br/>axios/fetch]
            AuthService[Auth Service]
            ReadingService[Reading Service]
        end
    end

    App --> HomePage
    App --> CardsPage
    App --> ReadingPage
    App --> HistoryPage

    HomePage --> TarotCard
    ReadingPage --> ReadingForm
    ReadingPage --> SpreadLayout
    ReadingPage --> FeedbackForm

    ReadingForm --> UseAuth
    ReadingForm --> UseReading
    CardsPage --> UseCards

    UseAuth --> AuthService
    UseReading --> ReadingService

    AuthService --> APIClient
    ReadingService --> APIClient

    style App fill:#61dafb
    style APIClient fill:#ff6b6b
```

### 디렉토리 구조

```
frontend/
├── app/                        # Next.js App Router
│   ├── page.tsx               # 홈페이지
│   ├── cards/                 # 카드 페이지
│   ├── readings/              # 리딩 페이지
│   └── history/               # 이력 페이지
├── components/                 # React 컴포넌트
│   ├── tarot/                 # 타로 관련 컴포넌트
│   │   ├── TarotCard.tsx
│   │   ├── SpreadLayout.tsx
│   │   └── ReadingResult.tsx
│   ├── forms/                 # 폼 컴포넌트
│   │   ├── ReadingForm.tsx
│   │   └── FeedbackForm.tsx
│   └── common/                # 공통 컴포넌트
│       ├── Button.tsx
│       └── Modal.tsx
├── hooks/                      # Custom React Hooks
│   ├── useAuth.ts
│   ├── useReading.ts
│   └── useCards.ts
├── services/                   # API 서비스
│   ├── api.ts                 # API Client
│   ├── auth.service.ts
│   └── reading.service.ts
├── types/                      # TypeScript 타입 정의
│   ├── card.types.ts
│   └── reading.types.ts
└── public/                     # 정적 파일
    └── cards/                 # 카드 이미지
```

---

## 데이터 흐름

### 타로 리딩 요청 플로우

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend<br/>(Next.js)
    participant API as Backend API<br/>(FastAPI)
    participant Auth as Auth System
    participant Repo as Reading Repository
    participant AIOrch as AI Orchestrator
    participant PE as Prompt Engine
    participant AI as AI Provider<br/>(OpenAI/Claude)
    participant DB as PostgreSQL
    participant Cache as Redis

    User->>FE: 리딩 요청<br/>(질문 + 스프레드 타입)
    FE->>API: POST /api/v1/readings<br/>(Authorization: Bearer token)

    API->>Auth: 토큰 검증
    Auth-->>API: 사용자 정보

    API->>Repo: 리딩 생성 요청
    Repo->>DB: 카드 랜덤 추출
    DB-->>Repo: 카드 데이터

    Repo->>DB: Reading 레코드 생성
    DB-->>Repo: Reading ID

    Repo-->>API: Reading 데이터

    API->>AIOrch: AI 해석 요청
    AIOrch->>Cache: 캐시 확인
    Cache-->>AIOrch: Cache Miss

    AIOrch->>PE: 프롬프트 생성
    PE-->>AIOrch: 완성된 프롬프트

    AIOrch->>AI: API 호출
    AI-->>AIOrch: AI 응답

    AIOrch->>Cache: 결과 캐싱
    AIOrch-->>API: 해석 결과

    API->>Repo: Reading 업데이트<br/>(interpretation)
    Repo->>DB: UPDATE readings
    DB-->>Repo: Success

    Repo-->>API: 완성된 Reading
    API-->>FE: 200 OK<br/>Reading 데이터
    FE-->>User: 리딩 결과 표시
```

### 피드백 제출 플로우

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend
    participant API as Backend API
    participant Auth as Auth System
    participant FBRepo as Feedback Repository
    participant DB as PostgreSQL

    User->>FE: 피드백 제출<br/>(rating, helpful, accurate)
    FE->>API: POST /api/v1/feedback<br/>(reading_id + feedback)

    API->>Auth: 토큰 검증
    Auth-->>API: 사용자 정보

    API->>FBRepo: 피드백 생성
    FBRepo->>DB: Reading 존재 확인
    DB-->>FBRepo: Reading 데이터

    FBRepo->>DB: Feedback 레코드 생성
    DB-->>FBRepo: Feedback ID

    FBRepo-->>API: Feedback 데이터
    API-->>FE: 201 Created
    FE-->>User: 피드백 감사 메시지
```

### 관리자 통계 조회 플로우

```mermaid
sequenceDiagram
    actor Admin
    participant FE as Admin Dashboard
    participant API as Backend API
    participant Auth as Auth System
    participant FBRepo as Feedback Repository
    participant DB as PostgreSQL

    Admin->>FE: 통계 페이지 접속
    FE->>API: GET /api/v1/admin/stats<br/>(Authorization: Bearer token)

    API->>Auth: 관리자 권한 확인
    Auth-->>API: Superuser 검증 완료

    API->>FBRepo: 전체 통계 조회
    FBRepo->>DB: Aggregation Query<br/>(COUNT, AVG, SUM)
    DB-->>FBRepo: 통계 데이터

    FBRepo-->>API: 집계 결과
    API-->>FE: 200 OK<br/>통계 데이터
    FE-->>Admin: 대시보드 표시
```

---

## 데이터베이스 스키마

### ERD (Entity Relationship Diagram)

```mermaid
erDiagram
    USERS ||--o{ READINGS : creates
    USERS ||--o{ FEEDBACK : submits
    READINGS ||--|| FEEDBACK : has
    READINGS ||--o{ READING_CARDS : contains
    CARDS ||--o{ READING_CARDS : used_in

    USERS {
        uuid id PK
        string email UK
        string provider_id
        boolean is_superuser
        datetime created_at
        datetime updated_at
    }

    CARDS {
        int id PK
        string name UK
        string name_ko
        enum suit
        int number
        enum arcana_type
        string description
        string keywords
        string image_url
    }

    READINGS {
        uuid id PK
        uuid user_id FK
        string question
        enum spread_type
        string interpretation
        string ai_provider
        enum category
        datetime created_at
    }

    READING_CARDS {
        uuid id PK
        uuid reading_id FK
        int card_id FK
        int position
        boolean is_reversed
        string position_meaning
    }

    FEEDBACK {
        uuid id PK
        uuid reading_id FK
        uuid user_id FK
        int rating
        boolean helpful
        boolean accurate
        text comment
        datetime created_at
    }
```

### 주요 테이블 설명

#### 1. users (사용자)
- 인증된 사용자 정보 저장
- 다중 인증 프로바이더 지원 (provider_id)
- 관리자 플래그 (is_superuser)

#### 2. cards (타로 카드)
- 78장의 타로 카드 마스터 데이터
- 메이저/마이너 아르카나 분류
- 한글/영문 이름, 키워드, 설명

#### 3. readings (리딩 기록)
- 사용자의 타로 리딩 이력
- AI 해석 결과 저장
- 스프레드 타입별 분류

#### 4. reading_cards (리딩 카드 매핑)
- Reading과 Card의 다대다 관계
- 카드 위치(position), 정/역방향 정보
- 위치별 의미

#### 5. feedback (피드백)
- 리딩에 대한 사용자 평가
- 만족도 점수 (1-5)
- 도움됨/정확함 Boolean 플래그

---

## 보안 아키텍처

### 인증 플로우

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend
    participant API as Backend API
    participant AuthOrch as Auth Orchestrator
    participant Provider as Auth Provider
    participant DB as Database

    User->>FE: 로그인 시도
    FE->>API: POST /api/v1/auth/login<br/>(email, password)

    API->>AuthOrch: 인증 요청
    AuthOrch->>Provider: authenticate()
    Provider->>DB: 사용자 조회
    DB-->>Provider: 사용자 데이터

    Provider->>Provider: 비밀번호 검증<br/>(bcrypt)
    Provider-->>AuthOrch: 인증 성공

    AuthOrch->>Provider: 토큰 생성
    Provider->>Provider: JWT 생성<br/>(HS256)
    Provider-->>AuthOrch: Access Token<br/>Refresh Token

    AuthOrch-->>API: 토큰 정보
    API-->>FE: 200 OK<br/>{access_token, refresh_token}
    FE->>FE: 토큰 저장<br/>(localStorage)
```

### 권한 검증 플로우

```mermaid
flowchart TD
    Start[API 요청] --> HasToken{Authorization<br/>Header 존재?}
    HasToken -->|No| Unauthorized[401 Unauthorized]
    HasToken -->|Yes| ValidateToken[JWT 토큰 검증]

    ValidateToken --> TokenValid{토큰 유효?}
    TokenValid -->|No| Unauthorized
    TokenValid -->|Yes| GetUser[사용자 정보 조회]

    GetUser --> UserExists{사용자 존재?}
    UserExists -->|No| Unauthorized
    UserExists -->|Yes| CheckActive{is_active?}

    CheckActive -->|No| Forbidden[403 Forbidden<br/>계정 비활성화]
    CheckActive -->|Yes| CheckAdmin{관리자 권한<br/>필요?}

    CheckAdmin -->|No| Success[200 OK<br/>요청 처리]
    CheckAdmin -->|Yes| IsSuperuser{is_superuser?}

    IsSuperuser -->|No| Forbidden2[403 Forbidden<br/>권한 없음]
    IsSuperuser -->|Yes| Success

    style Start fill:#4caf50
    style Success fill:#4caf50
    style Unauthorized fill:#f44336
    style Forbidden fill:#ff9800
    style Forbidden2 fill:#ff9800
```

### 보안 기능

1. **비밀번호 보안**
   - bcrypt 해싱 (cost factor: 12)
   - Salt 자동 생성

2. **JWT 토큰**
   - HS256 알고리즘
   - Access Token: 60분 유효
   - Refresh Token: 7일 유효

3. **API 보안**
   - CORS 설정 (허용 도메인 제한)
   - Rate Limiting (추후 구현 예정)
   - Input Validation (Pydantic)

4. **데이터베이스 보안**
   - SQL Injection 방지 (SQLAlchemy ORM)
   - 환경 변수로 인증 정보 관리
   - 연결 풀링

---

## 배포 아키텍처

### 개발 환경

```mermaid
graph TD
    subgraph "Local Development"
        Dev[Developer Machine]

        subgraph "Backend"
            BE[FastAPI<br/>localhost:8000]
            BEDB[(PostgreSQL<br/>localhost:5432)]
            BECache[(Redis<br/>localhost:6379)]
        end

        subgraph "Frontend"
            FE[Next.js<br/>localhost:3000]
        end

        Dev --> BE
        Dev --> FE
        BE --> BEDB
        BE --> BECache
        FE --> BE
    end

    style Dev fill:#4caf50
    style BE fill:#2196f3
    style FE fill:#61dafb
```

### 프로덕션 환경 (계획)

```mermaid
graph TD
    subgraph "Client"
        Users[Users]
    end

    subgraph "CDN"
        CloudFront[CloudFront/Vercel CDN]
    end

    subgraph "Application Layer"
        LB[Load Balancer]

        subgraph "Frontend Servers"
            FE1[Next.js Instance 1]
            FE2[Next.js Instance 2]
        end

        subgraph "Backend Servers"
            BE1[FastAPI Instance 1]
            BE2[FastAPI Instance 2]
        end
    end

    subgraph "Data Layer"
        PG[(PostgreSQL<br/>Primary)]
        PGR[(PostgreSQL<br/>Replica)]
        RedisCluster[(Redis Cluster)]
    end

    subgraph "External Services"
        OpenAI[OpenAI API]
        Claude[Claude API]
        Monitoring[Monitoring<br/>Sentry/CloudWatch]
    end

    Users --> CloudFront
    CloudFront --> LB
    LB --> FE1
    LB --> FE2
    FE1 --> BE1
    FE2 --> BE2

    BE1 --> PG
    BE2 --> PG
    BE1 --> PGR
    BE2 --> PGR
    BE1 --> RedisCluster
    BE2 --> RedisCluster

    BE1 --> OpenAI
    BE2 --> OpenAI
    BE1 --> Claude
    BE2 --> Claude

    BE1 --> Monitoring
    BE2 --> Monitoring
    FE1 --> Monitoring
    FE2 --> Monitoring

    style Users fill:#4caf50
    style LB fill:#ff9800
    style PG fill:#336791
    style RedisCluster fill:#dc382d
```

---

## 기술 스택 상세

### Backend
```yaml
Runtime:
  - Python 3.11+

Framework:
  - FastAPI 0.104+
  - Uvicorn (ASGI Server)

ORM & Database:
  - SQLAlchemy 2.0+
  - Alembic (Migration)
  - asyncpg (PostgreSQL Driver)

Validation:
  - Pydantic 2.0+

Authentication:
  - PyJWT
  - python-jose
  - passlib (bcrypt)
  - firebase-admin
  - authlib (Auth0)

AI Integration:
  - openai
  - anthropic
  - tiktoken

Cache:
  - redis-py

Testing:
  - pytest
  - pytest-asyncio
  - httpx (async client)

Code Quality:
  - black (formatter)
  - flake8 (linter)
  - mypy (type checker)
```

### Frontend
```yaml
Framework:
  - Next.js 14+
  - React 18+

Language:
  - TypeScript 5+

Styling:
  - Tailwind CSS 3+
  - Framer Motion (animations)

HTTP Client:
  - axios / fetch

State Management:
  - React Hooks
  - Context API

Testing:
  - Jest
  - React Testing Library

Code Quality:
  - ESLint
  - Prettier
```

### Infrastructure
```yaml
Database:
  - PostgreSQL 14+

Cache:
  - Redis 7+

Deployment (Planned):
  - Docker
  - Docker Compose
  - AWS / Vercel
  - GitHub Actions (CI/CD)

Monitoring (Planned):
  - Sentry (Error Tracking)
  - CloudWatch (Logging)
  - Prometheus + Grafana (Metrics)
```

---

## 성능 최적화

### 1. 캐싱 전략
- **카드 데이터**: Redis에 전체 카드 목록 캐싱 (TTL: 24시간)
- **AI 응답**: 동일한 카드 조합 + 질문 유사도 기반 캐싱 (TTL: 1시간)
- **사용자 세션**: Redis에 JWT 토큰 정보 캐싱

### 2. 데이터베이스 최적화
- **인덱싱**: user_id, reading_id, created_at 등 자주 조회되는 컬럼
- **Pagination**: 대량 데이터 조회 시 페이지네이션 적용
- **연결 풀**: SQLAlchemy connection pooling (pool_size: 10)

### 3. API 최적화
- **비동기 처리**: FastAPI의 async/await 활용
- **응답 압축**: gzip 압축
- **Lazy Loading**: 필요한 데이터만 조회

---

## 확장성 고려사항

### 수평 확장 (Horizontal Scaling)
- Stateless API 설계 (세션 정보는 Redis에 저장)
- Load Balancer를 통한 다중 인스턴스 운영
- Database Read Replica를 통한 읽기 성능 향상

### 수직 확장 (Vertical Scaling)
- Database 인스턴스 사양 업그레이드
- Redis 메모리 증설
- AI API Rate Limit 증가

### 마이크로서비스 전환 (향후 계획)
- Auth Service 분리
- AI Service 분리
- Reading Service 분리

---

## 버전 히스토리

| 버전 | 날짜 | 변경 사항 |
|------|------|-----------|
| 1.0 | 2025-10-22 | 초기 아키텍처 문서 작성 |

---

## 참고 문서
- [PROJECT_PLAN.md](./PROJECT_PLAN.md) - 프로젝트 계획
- [INTEND.md](./INTEND.md) - 요구사항 명세
- [TASK.md](./TASK.md) - 작업 목록
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
