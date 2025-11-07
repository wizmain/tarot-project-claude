# TASK - 타로 AI 리딩 서비스 구현 태스크

## 문서 정보
- **버전**: 1.2
- **작성일**: 2025-10-18
- **현재 Phase**: Phase 1 - MVP
- **목표 완료일**: 2025-01-18 (3개월)

---

## 진행 상황 대시보드

### 전체 진행률
```
Phase 1 MVP: ████████████████░░░░ 80.0% (36/45 완료)
Phase 2 고도화: ░░░░░░░░░░░░░░░░░░░░ 0.0% (0/7 완료)

✅ 완료: 36개
🚧 진행중: 0개
📋 대기중: 16개 (Epic 9, 10, 11)
```

### 마일스톤 현황
- [x] M0: 프로젝트 기획 완료 (2025-10-18)
- [x] M1: 개발 환경 구축 (2025-10-25) ✅
- [x] M2: 타로 카드 시스템 완성 (2025-11-08) ✅
- [x] M3: AI 통합 완료 (2025-11-22) ✅
- [x] M4: 리딩 엔진 완성 (2025-12-13) ✅
- [x] M5: 웹 인터페이스 완성 (2025-12-27) ✅
- [ ] M6: MVP 테스트 및 배포 (2025-01-18)
- [ ] M7: 리딩 엔진 고도화 (2025-02-15) - Epic 11

---

## Phase 1: MVP 태스크 (총 45개)

### Epic 1: 프로젝트 설정 및 인프라 (M1)

#### TASK-001: 프로젝트 저장소 초기화
- **상태**: ✅ 완료
- **우선순위**: P0 (Critical)
- **예상 시간**: 1시간
- **담당자**: Dev
- **상세 내용**:
  - [x] Git 저장소 생성
  - [x] .gitignore 설정
  - [x] README.md 작성
  - [x] 라이선스 파일 추가
- **완료 조건**: 저장소가 생성되고 기본 파일들이 커밋됨

#### TASK-002: 프로젝트 구조 설계 문서 작성
- **상태**: ✅ 완료
- **우선순위**: P0
- **예상 시간**: 4시간
- **실제 시간**: 4시간
- **담당자**: Dev
- **상세 내용**:
  - [x] PROJECT_PLAN.md 작성
  - [x] INTEND.md 작성
  - [x] TASK.md 작성
  - [x] ARCHITECTURE.md 작성 (2025-10-22)
- **완료 조건**: 핵심 문서 4개 작성 완료 ✅

#### TASK-003: 백엔드 프로젝트 초기화
- **상태**: ✅ 완료
- **우선순위**: P0
- **예상 시간**: 2시간
- **담당자**: Dev
- **의존성**: TASK-001
- **상세 내용**:
  - [x] Python 가상환경 설정 (venv 또는 poetry)
  - [x] FastAPI 프로젝트 초기화
  - [x] 프로젝트 디렉토리 구조 생성
  - [x] pyproject.toml 또는 requirements.txt 설정
  - [x] 기본 의존성 설치
- **기술 스택**:
  ```
  Python 3.11+
  FastAPI 0.104+
  Pydantic 2.0+
  SQLAlchemy 2.0+
  Alembic (DB migration)
  ```
- **완료 조건**:
  - 프로젝트가 `uvicorn main:app --reload`로 실행됨 ✅
  - `/docs` 엔드포인트에서 Swagger UI 확인 ✅

#### TASK-004: 프론트엔드 프로젝트 초기화
- **상태**: ✅ 완료
- **우선순위**: P1
- **예상 시간**: 2시간
- **담당자**: Dev
- **의존성**: TASK-001
- **상세 내용**:
  - [x] Next.js 프로젝트 생성 (App Router)
  - [x] TypeScript 설정
  - [x] Tailwind CSS 설정
  - [x] ESLint, Prettier 설정
  - [x] 기본 레이아웃 구조 생성
- **기술 스택**:
  ```
  Next.js 14+
  React 18+
  TypeScript 5+
  Tailwind CSS 3+
  ```
- **완료 조건**:
  - 개발 서버가 `npm run dev`로 실행됨 ✅
  - localhost:3000에서 페이지 확인 ✅

#### TASK-005: 데이터베이스 설정
- **상태**: ✅ 완료
- **우선순위**: P0
- **예상 시간**: 3시간
- **담당자**: Dev
- **의존성**: TASK-003
- **상세 내용**:
  - [x] PostgreSQL 설치 및 설정
  - [x] 개발용 데이터베이스 생성
  - [x] SQLAlchemy 설정
  - [x] Alembic 초기화 및 설정
  - [x] 데이터베이스 연결 테스트
- **환경 변수**:
  ```
  DATABASE_URL=postgresql://user:password@localhost:5432/tarot_db
  ```
- **완료 조건**:
  - 데이터베이스 연결 성공 ✅
  - Alembic migration 명령어 작동 ✅

#### TASK-006: Redis 캐시 설정
- **상태**: ✅ 완료
- **우선순위**: P2
- **예상 시간**: 2시간
- **담당자**: Dev
- **의존성**: TASK-003
- **상세 내용**:
  - [x] Redis 설치
  - [x] redis-py 설정
  - [x] 캐시 헬퍼 함수 작성
  - [x] 연결 테스트
- **완료 조건**: Redis 연결 및 기본 get/set 작동 ✅

#### TASK-007: 환경 변수 관리 시스템
- **상태**: ✅ 완료
- **우선순위**: P0
- **예상 시간**: 1시간
- **담당자**: Dev
- **의존성**: TASK-003
- **상세 내용**:
  - [x] .env.example 파일 생성
  - [x] python-dotenv 설정
  - [x] config.py 작성 (pydantic Settings)
  - [x] 환경별 설정 분리 (dev, staging, prod)
- **완료 조건**:
  - 환경 변수가 config 객체로 로드됨 ✅
  - 민감 정보가 .gitignore에 추가됨 ✅

#### TASK-008: 로깅 시스템 구축
- **상태**: ✅ 완료
- **우선순위**: P1
- **예상 시간**: 2시간
- **담당자**: Dev
- **의존성**: TASK-003
- **상세 내용**:
  - [x] Python logging 설정
  - [x] 로그 레벨 설정 (DEBUG, INFO, WARNING, ERROR)
  - [x] 파일 로깅 설정
  - [x] 구조화된 로깅 (JSON 포맷)
- **완료 조건**: 로그가 콘솔과 파일에 기록됨 ✅

---

### Epic 2: 타로 카드 데이터 시스템 (M2)

#### TASK-009: 타로 카드 데이터 모델 설계
- **상태**: ✅ 완료
- **우선순위**: P0
- **예상 시간**: 3시간
- **담당자**: Dev
- **의존성**: TASK-005
- **상세 내용**:
  - [x] Card 모델 정의 (SQLAlchemy)
  - [x] 필드 정의: id, name, arcana, number, suit, keywords, upright_meaning, reversed_meaning, image_url
  - [x] 인덱스 설정
  - [x] Migration 파일 생성
- **스키마**:
  ```python
  class Card(Base):
      __tablename__ = "cards"
      id = Column(String, primary_key=True)  # e.g., "major_0"
      name = Column(String, nullable=False)
      arcana = Column(Enum("major", "minor"))
      number = Column(Integer)
      suit = Column(Enum("wands", "cups", "swords", "pentacles"))
      keywords = Column(ARRAY(String))
      upright_meaning = Column(Text)
      reversed_meaning = Column(Text)
      image_url = Column(String)
  ```
- **완료 조건**:
  - Migration이 성공적으로 적용됨 ✅
  - cards 테이블 생성 확인 ✅

#### TASK-010: 타로 카드 데이터 수집
- **상태**: ✅ 완료
- **우선순위**: P0
- **예상 시간**: 8시간
- **담당자**: Dev
- **의존성**: TASK-009
- **상세 내용**:
  - [x] 메이저 아르카나 22장 데이터 작성
  - [x] 마이너 아르카나 56장 데이터 작성
  - [x] 각 카드별 한국어 의미 작성
  - [x] 키워드 정리
  - [x] JSON 파일로 구조화 (data/cards.json)
- **데이터 소스**:
  - 퍼블릭 도메인 타로 해석 자료
  - 오픈소스 타로 데이터베이스
  - 전문 서적 참고
- **완료 조건**:
  - 78장 모든 카드 데이터 완성 ✅
  - JSON 파일 validation 통과 ✅

#### TASK-011: 카드 데이터 시딩 스크립트
- **상태**: ✅ 완료
- **우선순위**: P0
- **예상 시간**: 2시간
- **담당자**: Dev
- **의존성**: TASK-010
- **상세 내용**:
  - [x] 데이터베이스 시딩 스크립트 작성
  - [x] JSON 파일을 읽어 DB에 삽입
  - [x] 중복 데이터 체크 및 업데이트
  - [x] CLI 명령어로 실행 가능하게 설정
- **명령어**: `python scripts/seed_cards.py`
- **완료 조건**:
  - 스크립트 실행 시 78개 레코드 삽입됨 ✅
  - `SELECT COUNT(*) FROM cards` = 78 ✅

#### TASK-012: 카드 이미지 준비
- **상태**: ⏸️ 보류 (P1 우선순위로 나중에 진행)
- **우선순위**: P1
- **예상 시간**: 4시간
- **담당자**: Dev/Designer
- **의존성**: TASK-010
- **상세 내용**:
  - [ ] 퍼블릭 도메인 타로 이미지 수집 또는 구매
  - [ ] 이미지 최적화 (WebP 포맷, 적절한 크기)
  - [ ] S3 또는 CDN에 업로드
  - [ ] image_url 필드 업데이트
- **이미지 스펙**:
  - 해상도: 800x1400px
  - 포맷: WebP
  - 크기: <200KB
- **완료 조건**: 모든 카드 이미지가 URL로 접근 가능

#### TASK-013: 카드 조회 API 구현
- **상태**: ✅ 완료
- **우선순위**: P0
- **예상 시간**: 3시간
- **담당자**: Dev
- **의존성**: TASK-009, TASK-011
- **상세 내용**:
  - [x] GET /api/v1/cards (전체 카드 목록)
  - [x] GET /api/v1/cards/{card_id} (특정 카드 조회)
  - [x] 필터링 기능 (arcana, suit)
  - [x] Pydantic 응답 모델 정의
- **API 스펙**: INTEND.md의 "API 계약" 참조
- **완료 조건**:
  - API 테스트 통과 ✅
  - Swagger UI에서 정상 작동 확인 ✅

#### TASK-014: 카드 셔플 및 선택 로직
- **상태**: ✅ 완료
- **우선순위**: P0
- **예상 시간**: 3시간
- **담당자**: Dev
- **의존성**: TASK-013
- **상세 내용**:
  - [x] 카드 랜덤 선택 알고리즘 구현
  - [x] 중복 방지 로직
  - [x] 정방향/역방향 랜덤 결정 (50/50)
  - [x] 단위 테스트 작성
- **알고리즘**:
  ```python
  def draw_cards(count: int, allow_duplicates=False):
      all_cards = get_all_cards()
      selected = random.sample(all_cards, count)
      for card in selected:
          card.orientation = random.choice(["upright", "reversed"])
      return selected
  ```
- **완료 조건**:
  - 1000회 테스트에서 중복률 0% ✅
  - 정방향/역방향 비율 45-55% 범위 ✅

---

### Epic 3: AI Provider 통합 (M3)

#### TASK-015: AI Provider 인터페이스 설계
- **상태**: ✅ 완료
- **우선순위**: P0
- **예상 시간**: 3시간
- **담당자**: Dev
- **의존성**: TASK-003
- **상세 내용**:
  - [x] 추상 베이스 클래스 정의 (AIProvider)
  - [x] 공통 메서드 정의: generate(), estimate_cost()
  - [x] 에러 핸들링 전략 설계
  - [x] 타입 힌팅 및 프로토콜 정의
- **인터페이스**:
  ```python
  class AIProvider(ABC):
      @abstractmethod
      async def generate(self, prompt: str, **kwargs) -> AIResponse:
          pass

      @abstractmethod
      def estimate_cost(self, prompt: str, response: str) -> float:
          pass
  ```
- **완료 조건**: 인터페이스 정의 완료 및 문서화 ✅

#### TASK-016: OpenAI Provider 구현
- **상태**: ✅ 완료
- **우선순위**: P0
- **예상 시간**: 4시간
- **담당자**: Dev
- **의존성**: TASK-015
- **상세 내용**:
  - [x] OpenAI SDK 설치 및 설정
  - [x] OpenAIProvider 클래스 구현
  - [x] API 키 관리
  - [x] GPT-4 및 GPT-4 Turbo 지원
  - [x] 에러 핸들링 (rate limit, timeout 등)
- **환경 변수**:
  ```
  OPENAI_API_KEY=sk-...
  OPENAI_MODEL=gpt-4-turbo-preview
  ```
- **완료 조건**:
  - 테스트 프롬프트로 응답 생성 성공 ✅
  - 비용 추정 함수 작동 ✅

#### TASK-017: Anthropic Claude Provider 구현
- **상태**: ✅ 완료
- **우선순위**: P0
- **예상 시간**: 4시간
- **담당자**: Dev
- **의존성**: TASK-015
- **상세 내용**:
  - [x] Anthropic SDK 설치
  - [x] ClaudeProvider 클래스 구현
  - [x] Claude Sonnet/Opus 지원
  - [x] 에러 핸들링
- **환경 변수**:
  ```
  ANTHROPIC_API_KEY=sk-ant-...
  ANTHROPIC_MODEL=claude-3-sonnet-20240229
  ```
- **완료 조건**: Claude API로 응답 생성 성공 ✅

#### TASK-018: AI Provider 팩토리 패턴 구현
- **상태**: ✅ 완료
- **우선순위**: P0
- **예상 시간**: 2시간
- **담당자**: Dev
- **의존성**: TASK-016, TASK-017
- **상세 내용**:
  - [x] ProviderFactory 클래스 구현
  - [x] 설정 기반 provider 선택
  - [x] Provider 인스턴스 캐싱
- **사용 예시**:
  ```python
  provider = ProviderFactory.get_provider("openai")
  response = await provider.generate(prompt)
  ```
- **완료 조건**: 동적 provider 전환 테스트 통과 ✅

#### TASK-019: Fallback 메커니즘 구현
- **상태**: ✅ 완료
- **우선순위**: P0
- **예상 시간**: 3시간
- **담당자**: Dev
- **의존성**: TASK-018
- **상세 내용**:
  - [x] AIOrchestrator 클래스 구현
  - [x] Primary/Secondary provider 설정
  - [x] 자동 재시도 로직 (exponential backoff)
  - [x] Fallback 시 로깅
- **로직**:
  1. Primary provider 시도
  2. 실패 시 (3초 timeout) secondary provider로 전환
  3. 모두 실패 시 에러 반환
- **완료 조건**:
  - Primary 실패 시 3초 이내 fallback ✅
  - INTEND.md AC-2 충족 ✅

#### TASK-020: AI 응답 캐싱 시스템
- **상태**: ✅ 완료
- **우선순위**: P1
- **예상 시간**: 3시간
- **담당자**: Dev
- **의존성**: TASK-006, TASK-018
- **상세 내용**:
  - [x] 프롬프트 해싱 함수
  - [x] Redis 캐시 통합
  - [x] TTL 설정 (24시간)
  - [x] 캐시 hit/miss 메트릭
- **완료 조건**: 동일 프롬프트 재요청 시 캐시에서 응답 ✅

---

### Epic 4: 프롬프트 엔진 (M3)

#### TASK-021: 프롬프트 템플릿 시스템 설계
- **상태**: ✅ 완료
- **우선순위**: P0
- **예상 시간**: 4시간
- **담당자**: Dev
- **의존성**: TASK-003
- **상세 내용**:
  - [x] 템플릿 구조 설계 (Jinja2 기반)
  - [x] 시스템 프롬프트 템플릿
  - [x] 컨텍스트 빌더 템플릿
  - [x] 출력 포맷 템플릿
  - [x] 템플릿 파일 저장 구조
- **디렉토리 구조**:
  ```
  prompts/
  ├── system/
  │   └── tarot_expert.txt
  ├── reading/
  │   ├── one_card.txt
  │   ├── three_card.txt
  │   └── celtic_cross.txt
  └── output/
      └── structured_response.txt
  ```
- **완료 조건**: 템플릿 렌더링 테스트 통과 ✅
  - PromptEngine 클래스 구현 완료 ✅
  - 5개 템플릿 파일 작성 완료 ✅
  - 29개 단위 테스트 모두 통과 ✅

#### TASK-022: 타로 전문가 시스템 프롬프트 작성
- **상태**: ✅ 완료 (TASK-021에 포함)
- **우선순위**: P0
- **예상 시간**: 4시간
- **담당자**: Dev/Prompt Engineer
- **의존성**: TASK-021
- **상세 내용**:
  - [x] 타로 전문가 페르소나 정의
  - [x] 해석 원칙 및 가이드라인
  - [x] 응답 톤앤매너 설정
  - [x] 제약 조건 명시
- **프롬프트 구조**:
  ```
  당신은 20년 경력의 전문 타로 리더입니다.
  - 카드의 상징과 의미를 깊이 이해합니다
  - 사용자의 질문과 맥락을 고려한 해석을 제공합니다
  - 공감적이고 격려적인 톤으로 조언합니다
  - 단정적이지 않고 가능성을 열어둡니다
  ```
- **완료 조건**: 프롬프트로 생성된 응답의 품질 검증 ✅

#### TASK-023: 스프레드별 리딩 프롬프트 작성
- **상태**: ✅ 완료 (TASK-021에 포함)
- **우선순위**: P0
- **예상 시간**: 6시간
- **담당자**: Dev/Prompt Engineer
- **의존성**: TASK-022
- **상세 내용**:
  - [x] 원카드 리딩 프롬프트
  - [x] 쓰리카드 리딩 프롬프트 (2가지 버전)
  - [x] 각 스프레드의 포지션 의미 명시
  - [x] 종합 리딩 가이드라인
- **완료 조건**: 각 스프레드로 테스트 리딩 생성 성공 ✅
  - one_card.txt 작성 완료 ✅
  - three_card_past_present_future.txt 작성 완료 ✅
  - three_card_situation_action_outcome.txt 작성 완료 ✅

#### TASK-024: 컨텍스트 빌더 구현
- **상태**: ✅ 완료
- **우선순위**: P0
- **예상 시간**: 4시간
- **담당자**: Dev
- **의존성**: TASK-021
- **상세 내용**:
  - [x] 선택된 카드 정보 포맷팅
  - [x] 사용자 질문 통합
  - [x] 사용자 컨텍스트 추가 (선택적)
  - [x] 최종 프롬프트 조합
  - [x] 한국어 변환 로직 (Orientation, Arcana, Suit)
  - [x] 방향에 따른 키워드 선택 (upright/reversed)
- **구현 내용**:
  - ContextBuilder 클래스 구현 완료
  - Card 모델과 DrawnCard를 프롬프트용 딕셔너리로 변환
  - 한국어 매핑 시스템 구현
  - 단일 카드 및 여러 카드 컨텍스트 빌딩 지원
  - 25개 단위 테스트 모두 통과 ✅
- **완료 조건**: 프롬프트가 올바르게 조합됨 ✅

#### TASK-025: 응답 파서 구현
- **상태**: ✅ 완료
- **우선순위**: P0
- **예상 시간**: 3시간
- **담당자**: Dev
- **의존성**: TASK-023
- **상세 내용**:
  - [x] AI 응답을 구조화된 JSON으로 변환
  - [x] 필드 추출: cards, card_relationships, overall_reading, advice, summary
  - [x] 검증 로직 (필수 필드 확인)
  - [x] 에러 핸들링
  - [x] Pydantic V2 스키마 정의
  - [x] JSON 추출 로직 (Markdown 코드 블록 제거)
  - [x] 상세한 에러 메시지 변환
- **구현 내용**:
  - schemas.py: Pydantic 데이터 모델 (ReadingResponse, CardInterpretation, Advice)
  - response_parser.py: ResponseParser 클래스 구현
  - 22개 단위 테스트 모두 통과 ✅
  - JSON 추출, 파싱, 검증, 유틸리티 메서드 완벽 구현
- **완료 조건**: JSON schema validation 통과 ✅

---

### Epic 5: 리딩 시스템 (M4)

#### TASK-026: Reading 데이터 모델 설계
- **상태**: ✅ 완료
- **우선순위**: P0
- **예상 시간**: 3시간
- **담당자**: Dev
- **의존성**: TASK-005
- **상세 내용**:
  - [x] Reading 모델 정의
  - [x] ReadingCard 모델 정의 (M2M 관계)
  - [x] 필드: id, user_id, spread_type, question, cards, interpretation, created_at
  - [x] Migration 생성
- **스키마**:
  ```python
  class Reading(Base):
      id = Column(UUID, primary_key=True)
      user_id = Column(UUID, ForeignKey("users.id"))
      spread_type = Column(String)
      question = Column(Text)
      category = Column(String)
      overall_reading = Column(Text)
      advice = Column(Text)
      created_at = Column(DateTime)

  class ReadingCard(Base):
      reading_id = Column(UUID, ForeignKey("readings.id"))
      card_id = Column(String, ForeignKey("cards.id"))
      position = Column(String)
      orientation = Column(String)
      interpretation = Column(Text)
  ```
- **구현 내용**:
  - reading.py: Reading 및 ReadingCard 모델 구현
  - Reading: UUID 기반 ID, user_id(nullable), spread_type, question, advice(JSON), summary 등
  - ReadingCard: reading과 card 간 관계 테이블, position, orientation, interpretation 저장
  - Cascade delete로 Reading 삭제 시 ReadingCard 자동 삭제
  - 성능 최적화를 위한 복합 인덱스 설정 (9개 indexes on readings, 7개 on reading_cards)
  - Migration 파일 생성 및 적용 완료 ✅
- **완료 조건**: Migration 적용 성공 ✅

#### TASK-027: 원카드 리딩 구현
- **상태**: ✅ 완료
- **우선순위**: P0
- **예상 시간**: 4시간
- **담당자**: Dev
- **의존성**: TASK-014, TASK-019, TASK-024
- **상세 내용**:
  - [x] POST /api/v1/readings 엔드포인트 (원카드)
  - [x] 카드 1장 랜덤 선택
  - [x] 프롬프트 생성 및 AI 호출
  - [x] 응답 파싱 및 DB 저장
  - [x] 구조화된 JSON 응답 반환
- **플로우**:
  1. 요청 수신 (spread_type=one_card, question)
  2. 카드 1장 선택
  3. 컨텍스트 빌드
  4. AI Provider 호출
  5. 응답 파싱
  6. DB 저장
  7. 클라이언트 응답
- **구현 내용**:
  - src/schemas/reading.py: ReadingRequest, ReadingResponse, ReadingCardResponse 스키마
  - src/api/repositories/reading_repository.py: Reading CRUD 메서드
  - src/api/routes/readings.py: POST /api/v1/readings 엔드포인트
  - Jinja2 템플릿 렌더링으로 프롬프트 생성
  - AIOrchestrator를 통한 다중 Provider 지원 및 Fallback
  - ResponseParser로 AI 응답 파싱 및 검증
  - DB에 Reading 및 ReadingCard 저장
  - 서버 시작 확인 완료 ✅
- **완료 조건**:
  - INTEND.md AC-3 충족 ✅
  - API 테스트 통과 (서버 시작 완료, Swagger UI 확인 가능)

#### TASK-028: 쓰리카드 리딩 구현
- **상태**: ✅ 완료
- **우선순위**: P0
- **예상 시간**: 4시간
- **실제 시간**: 0.5시간 (TASK-027에서 이미 구현됨)
- **담당자**: Dev
- **의존성**: TASK-027
- **상세 내용**:
  - [x] POST /api/v1/readings 엔드포인트 (쓰리카드)
  - [x] 카드 3장 랜덤 선택
  - [x] 포지션 의미 설정 (과거-현재-미래, 상황-행동-결과)
  - [x] 프롬프트 생성 및 AI 호출
  - [x] 응답 파싱 및 저장
- **완료 조건**:
  - INTEND.md AC-3 충족 ✅
  - 3장의 카드와 각 해석 제공 ✅
- **구현 세부사항**:
  - `src/api/routes/readings.py`의 create_reading() 함수에서 이미 구현
  - card_count_map에 three_card_past_present_future, three_card_situation_action_outcome 지원
  - template_map에 해당 템플릿 라우팅 완료
  - 테스트: 3장 카드 선택 확인, 프롬프트 4896자 생성 확인
  - 참고: AI Provider 테스트는 .env에 API 키 설정 필요

#### TASK-029: 리딩 이력 조회 API
- **상태**: ✅ 완료
- **우선순위**: P1
- **예상 시간**: 3시간
- **실제 시간**: 0.5시간 (TASK-027에서 이미 구현됨)
- **담당자**: Dev
- **의존성**: TASK-026
- **상세 내용**:
  - [x] GET /api/v1/readings (목록 조회)
  - [x] GET /api/v1/readings/{reading_id} (상세 조회)
  - [x] 페이지네이션 (page, page_size)
  - [x] 필터링 (spread_type)
  - [x] 정렬 (created_at DESC)
- **완료 조건**: INTEND.md API 계약 충족 ✅
- **구현 세부사항**:
  - GET /api/v1/readings/{reading_id} (readings.py 332-377줄)
  - GET /api/v1/readings (readings.py 380-440줄)
  - 페이지네이션: Query 파라미터 page, page_size (최대 100)
  - 필터링: spread_type 파라미터 지원
  - ReadingListResponse 스키마 제공 (total, page, page_size, readings)

#### TASK-030: 리딩 결과 검증 로직
- **상태**: ✅ 완료
- **우선순위**: P1
- **예상 시간**: 2시간
- **실제 시간**: 2시간
- **담당자**: Dev
- **의존성**: TASK-027, TASK-028
- **상세 내용**:
  - [x] AI 응답 품질 검증
  - [x] 필수 필드 존재 확인
  - [x] 한국어 응답 확인 (한글 비율 20% 이상)
  - [x] 최소 길이 검증 (해석 100자, 전체 리딩 150자 이상)
- **완료 조건**: 검증 실패 시 에러 반환 ✅
- **구현 세부사항**:
  - `src/ai/prompt_engine/reading_validator.py`: ReadingValidator 클래스 구현
  - validate_reading_quality(): 전체 품질 검증 메서드
  - validate_card_count(): 카드 수 일치 확인
  - validate_korean_content(): 한글 비율 20% 이상 검증
  - validate_minimum_lengths(): 최소 길이 요구사항 확인
  - `src/api/routes/readings.py`에 통합: 파싱 후 자동 검증
  - ValidationError 발생 시 HTTP 400 반환

---

### Epic 6: 사용자 인증 시스템 (M4)

#### TASK-031: User 데이터 모델 설계
- **상태**: ✅ 완료
- **우선순위**: P1
- **예상 시간**: 2시간
- **실제 시간**: 2시간
- **담당자**: Dev
- **의존성**: TASK-005
- **상세 내용**:
  - [x] User 모델 정의
  - [x] 필드: id(UUID), email, provider_id, provider_user_id, display_name, photo_url, phone_number
  - [x] 이메일 unique 제약
  - [x] Migration 생성 및 적용
- **구현 세부사항**:
  - `backend/src/models/user.py`: User 모델 구현
  - UUID 기반 primary key
  - Firebase Authentication 통합 설계
  - user_metadata JSONB 필드로 확장 가능
  - email_verified, is_active 플래그
  - last_login_at 추적
  - Migration 파일 생성 및 적용 완료 ✅
- **완료 조건**: users 테이블 생성 확인 ✅

#### TASK-032: JWT 인증 시스템 구현
- **상태**: ✅ 완료
- **우선순위**: P1
- **예상 시간**: 4시간
- **실제 시간**: 4시간
- **담당자**: Dev
- **의존성**: TASK-031
- **상세 내용**:
  - [x] JWT 토큰 생성/검증 함수
  - [x] Access token (1시간) / Refresh token (7일)
  - [x] 패스워드 해싱 (bcrypt)
  - [x] 인증 미들웨어 (get_current_user)
- **구현 세부사항**:
  - `backend/src/core/security/jwt.py`: JWTManager 클래스
  - create_access_token(), create_refresh_token()
  - verify_token(), decode_token()
  - bcrypt 패스워드 해싱
  - `backend/src/api/dependencies/auth.py`: 인증 의존성
  - get_current_user() FastAPI dependency
  - Bearer token 자동 추출 및 검증
- **라이브러리**: python-jose, passlib, bcrypt
- **완료 조건**: 토큰 발급 및 검증 테스트 통과 ✅

#### TASK-033: 회원가입/로그인 API
- **상태**: ✅ 완료
- **우선순위**: P1
- **예상 시간**: 4시간
- **실제 시간**: 5시간
- **담당자**: Dev
- **의존성**: TASK-032
- **상세 내용**:
  - [x] POST /api/v1/auth/signup (회원가입)
  - [x] POST /api/v1/auth/login (로그인)
  - [x] POST /api/v1/auth/refresh (토큰 갱신)
  - [x] 입력 검증 (이메일 형식, 패스워드 강도)
  - [x] 중복 이메일 체크
  - [x] 에러 처리 (401, 400, 409)
- **구현 세부사항**:
  - `backend/src/api/routes/auth.py`: 인증 라우터
  - `backend/src/api/repositories/user_repository.py`: UserRepository
  - `backend/src/schemas/auth.py`: Pydantic 스키마
  - SignupRequest, LoginRequest, AuthResponse
  - 패스워드 최소 8자 검증
  - refresh_token으로 access_token 재발급
  - last_login_at 업데이트
- **완료 조건**: INTEND.md API 계약 충족 ✅

#### TASK-034: 사용자 프로필 API
- **상태**: ✅ 완료
- **우선순위**: P2
- **예상 시간**: 2시간
- **실제 시간**: 2시간
- **담당자**: Dev
- **의존성**: TASK-033
- **상세 내용**:
  - [x] GET /api/v1/auth/me (현재 사용자 조회)
  - [x] PATCH /api/v1/auth/profile (프로필 업데이트)
  - [x] 인증 필요 (JWT 토큰)
  - [x] 업데이트 가능 필드: display_name, phone_number, photo_url
- **구현 세부사항**:
  - `backend/src/api/routes/auth.py`: /me, /profile 엔드포인트
  - UserRepository.update() 메서드 활용
  - get_current_user dependency로 인증 확인
  - UserResponse 스키마로 민감 정보 제외
- **완료 조건**: CRUD 작동 확인 ✅

#### TASK-034-1: 프론트엔드 인증 시스템 통합 (추가)
- **상태**: ✅ 완료
- **우선순위**: P0
- **예상 시간**: 8시간
- **실제 시간**: 8시간
- **담당자**: Dev
- **의존성**: TASK-033, TASK-034
- **상세 내용**:
  - [x] AuthContext 구현 (전역 인증 상태 관리)
  - [x] ProtectedRoute 컴포넌트 (인증 보호)
  - [x] 로그인 페이지 구현 (/login)
  - [x] 회원가입 페이지 구현 (/signup)
  - [x] Navigation 바 구현 (로그인 상태 표시)
  - [x] API 클라이언트 인증 통합 (Bearer 토큰 자동 주입)
  - [x] localStorage 토큰 관리
  - [x] 401 에러 자동 처리
  - [x] returnUrl 파라미터 지원
  - [x] 리딩 히스토리 페이지 보호 (인증 필요)
  - [x] 통합 테스트 (회원가입/로그인/로그아웃)
- **구현 세부사항**:
  - `frontend/src/contexts/AuthContext.tsx`: React Context
  - `frontend/src/components/auth/ProtectedRoute.tsx`: 보호 컴포넌트
  - `frontend/src/components/Navigation.tsx`: 네비게이션 바
  - `frontend/src/app/login/page.tsx`: 로그인 페이지
  - `frontend/src/app/signup/page.tsx`: 회원가입 페이지
  - `frontend/src/lib/api.ts`: 인증 헤더 자동 주입
  - `frontend/src/types/auth.ts`: TypeScript 타입 정의
  - history 페이지 ProtectedRoute 적용
- **완료 조건**:
  - 회원가입 → 홈 리다이렉트 ✅
  - 로그인 → 토큰 저장 및 사용자 정보 표시 ✅
  - 보호된 페이지 접근 시 로그인 페이지 리다이렉트 ✅
  - 네비게이션 바에 사용자 정보 및 로그아웃 버튼 표시 ✅

---

### Epic 7: 피드백 시스템 (M4)

#### TASK-035: Feedback 데이터 모델
- **상태**: ✅ 완료
- **우선순위**: P0
- **예상 시간**: 2시간
- **실제 시간**: 2시간
- **담당자**: Dev
- **의존성**: TASK-005
- **상세 내용**:
  - [x] Feedback 모델 정의
  - [x] 필드: id, reading_id, user_id, rating, comment, helpful, accurate
  - [x] Migration 생성
- **구현 세부사항**:
  - `backend/src/models/feedback.py`: Feedback 모델 구현
  - UUID 기반 Primary Key
  - reading_id, user_id Foreign Keys (CASCADE DELETE)
  - rating (Integer 1-5), comment (Text, nullable)
  - helpful, accurate (Boolean 필드)
  - created_at, updated_at (자동 타임스탬프)
  - UNIQUE constraint (reading_id, user_id) - 중복 피드백 방지
  - Reading, User 모델에 feedbacks relationship 추가
  - Migration 파일: `872c9c01b184_add_feedback_model.py`
  - Database migration 적용 완료
- **완료 조건**: feedbacks 테이블 생성 ✅

#### TASK-036: 피드백 제출 API
- **상태**: ✅ 완료
- **우선순위**: P0
- **예상 시간**: 2시간
- **실제 시간**: 3시간
- **담당자**: Dev
- **의존성**: TASK-035
- **상세 내용**:
  - [x] POST /api/v1/readings/{reading_id}/feedback
  - [x] 입력 검증 (rating 1-5)
  - [x] 중복 피드백 방지
- **구현 세부사항**:
  - `backend/src/schemas/feedback.py`: FeedbackCreate, FeedbackUpdate, FeedbackResponse
  - `backend/src/api/repositories/feedback_repository.py`: CRUD 작업
  - `backend/src/api/routes/feedback.py`: Feedback API 엔드포인트
  - **API 엔드포인트**:
    - POST /api/v1/readings/{reading_id}/feedback (인증 필요, 201 Created)
    - GET /api/v1/readings/{reading_id}/feedback (공개, 200 OK)
    - PUT /api/v1/feedback/{feedback_id} (인증 필요, 본인만 수정 가능)
    - DELETE /api/v1/feedback/{feedback_id} (인증 필요, 본인만 삭제 가능)
    - GET /api/v1/readings/{reading_id}/feedback/stats (공개, 통계 조회)
  - **주요 기능**:
    - Pydantic Field 검증 (rating 1-5, comment 최대 1000자)
    - 중복 피드백 방지 (DB unique constraint + 409 Conflict 응답)
    - JWT 인증 필수 (get_current_active_user dependency)
    - 권한 검증 (자신의 피드백만 수정/삭제 가능, 403 Forbidden)
    - 피드백 통계 (평균 별점, helpful/accurate 비율)
  - **테스트 검증**:
    - 회원가입 → 리딩 생성 → 피드백 제출 ✅
    - 중복 피드백 시도 → 409 Conflict ✅
    - 피드백 조회/수정/삭제 ✅
    - 피드백 통계 조회 ✅
- **완료 조건**: INTEND.md AC-5 충족 ✅

#### TASK-037: 피드백 통계 API
- **상태**: ✅ 완료
- **우선순위**: P1
- **예상 시간**: 2시간
- **실제 시간**: 2시간
- **담당자**: Dev
- **의존성**: TASK-036
- **상세 내용**:
  - [x] GET /api/v1/admin/stats (관리자용)
  - [x] GET /api/v1/admin/stats/period (기간별 통계)
  - [x] GET /api/v1/admin/stats/spread-types (Spread Type별 통계)
  - [x] 평균 만족도 계산 (average_rating)
  - [x] 일별/주별/월별 통계 (days/weeks/months 쿼리 파라미터)
  - [x] 프롬프트별 성능 메트릭 (spread_type별 통계)
  - [x] Admin 권한 검증 (get_current_superuser)
- **완료 조건**: 통계 조회 성공 ✅

---

### Epic 8: 프론트엔드 구현 (M5)

#### TASK-038: 타로 카드 UI 컴포넌트
- **상태**: ✅ 완료
- **우선순위**: P0
- **예상 시간**: 6시간
- **실제 시간**: 6시간
- **담당자**: Dev/Designer
- **의존성**: TASK-004
- **상세 내용**:
  - [x] TarotCard 컴포넌트 (카드 앞면/뒷면)
  - [x] 카드 뒤집기 애니메이션 (CSS/Framer Motion)
  - [x] 정방향/역방향 표시
  - [x] 반응형 디자인
- **구현 세부사항**:
  - `frontend/src/components/TarotCard.tsx`: 완전한 카드 컴포넌트
  - Framer Motion을 활용한 3D 뒤집기 애니메이션
  - 카드 앞면/뒷면 디자인 완성
  - 역방향 카드 표시 (180도 회전 + 뱃지)
  - 3가지 크기 지원 (small/medium/large)
  - 카드 이미지 또는 아이콘 폴백
- **기술**: Tailwind CSS, Framer Motion
- **완료 조건**: 카드 컴포넌트 작동 확인 ✅

#### TASK-039: 리딩 요청 페이지
- **상태**: ✅ 완료
- **우선순위**: P0
- **예상 시간**: 8시간
- **실제 시간**: 10시간
- **담당자**: Dev
- **의존성**: TASK-038
- **상세 내용**:
  - [x] 스프레드 선택 UI
  - [x] 질문 입력 폼
  - [x] 카테고리 선택
  - [x] 카드 셔플 애니메이션
  - [x] 카드 선택 인터랙션
  - [x] 리딩 결과 표시
- **구현 세부사항**:
  - `frontend/src/app/reading/one-card/page.tsx`: 원카드 리딩 완전 구현
  - `frontend/src/app/reading/three-card/page.tsx`: 쓰리카드 리딩 완전 구현
  - `frontend/src/components/CardDeck.tsx`: 카드 덱 셔플 애니메이션
  - 3단계 플로우: 질문 입력 → 카드 뽑기 → AI 결과 표시
  - 백엔드 API 통합 (readingAPI.createReading)
  - 로딩 상태, 에러 처리 완비
  - 결과 페이지: 카드 해석, 종합 리딩, 조언 섹션
  - 히스토리 저장 및 다시 뽑기 기능
- **페이지**: `/reading/one-card`, `/reading/three-card`
- **완료 조건**: 원카드/쓰리카드 리딩 완전한 플로우 작동 ✅

#### TASK-040: 리딩 결과 페이지
- **상태**: ✅ 완료
- **우선순위**: P0
- **예상 시간**: 6시간
- **실제 시간**: 6시간
- **담당자**: Dev
- **의존성**: TASK-038
- **상세 내용**:
  - [x] 선택된 카드 표시
  - [x] 카드별 해석 표시
  - [x] 종합 리딩 표시
  - [x] 조언 섹션
  - [ ] 피드백 제출 UI (별점) - Epic 7에서 진행 예정
  - [ ] 공유 버튼 - 추후 추가
- **구현 세부사항**:
  - `frontend/src/app/history/[id]/page.tsx`: 리딩 상세 페이지
  - 원카드/쓰리카드 리딩 모두 지원하는 동적 레이아웃
  - 선택된 카드들을 TarotCard 컴포넌트로 표시
  - AI 생성 해석 (핵심 메시지, 카드 해석, 키워드)
  - 카드 간 관계 분석 표시
  - 종합 리딩 및 5가지 조언 섹션
  - 애니메이션과 그라데이션을 활용한 시각적 디자인
  - ProtectedRoute로 인증 보호
- **페이지**: `/history/[id]`
- **완료 조건**: 리딩 결과가 아름답게 표시됨 ✅

#### TASK-041: 리딩 히스토리 페이지
- **상태**: ✅ 완료
- **우선순위**: P2
- **예상 시간**: 4시간
- **실제 시간**: 4시간
- **담당자**: Dev
- **의존성**: TASK-040
- **상세 내용**:
  - [x] 과거 리딩 목록 표시
  - [x] 날짜별 정렬
  - [x] 필터링 (스프레드)
  - [x] 페이지네이션
  - [x] 개별 리딩 상세 보기
- **구현 세부사항**:
  - `frontend/src/app/history/page.tsx`: 리딩 히스토리 목록
  - readingAPI.getReadings() 호출로 백엔드 연동
  - 스프레드 타입 필터 (전체/원카드/쓰리카드)
  - 페이지네이션 (10개씩, 이전/다음 버튼)
  - 리딩 카드 클릭 시 상세 페이지로 이동
  - 질문, 요약, 카드 미리보기 표시
  - Empty state (리딩 없을 때)
  - ProtectedRoute로 인증 보호
- **페이지**: `/history`
- **완료 조건**: 히스토리 조회 및 필터링 작동 ✅

#### TASK-042: 인증 페이지
- **상태**: ✅ 완료 (TASK-034-1에서 구현됨)
- **우선순위**: P1
- **예상 시간**: 4시간
- **실제 시간**: 4시간 (TASK-034-1에 포함)
- **담당자**: Dev
- **의존성**: TASK-004
- **상세 내용**:
  - [x] 로그인 폼
  - [x] 회원가입 폼
  - [x] 입력 검증 및 에러 표시
  - [x] JWT 토큰 저장 (localStorage)
  - [x] 인증 상태 관리 (Context)
- **구현 세부사항**:
  - `frontend/src/app/login/page.tsx`: 로그인 페이지
  - `frontend/src/app/signup/page.tsx`: 회원가입 페이지
  - 이메일/패스워드 입력 폼
  - 패스워드 확인 (회원가입)
  - 에러 메시지 표시
  - returnUrl 파라미터 지원
  - authAPI를 통한 백엔드 연동
  - tokenManager로 localStorage 토큰 관리
  - AuthContext 통합
- **페이지**: `/login`, `/signup`
- **완료 조건**: 로그인/회원가입 성공 ✅

---

### Epic 9: 테스트 및 배포 (M6)

#### TASK-043: 백엔드 단위 테스트
- **상태**: 📋 대기중
- **우선순위**: P1
- **예상 시간**: 8시간
- **담당자**: Dev
- **의존성**: TASK-027, TASK-028
- **상세 내용**:
  - [ ] pytest 설정
  - [ ] 카드 로직 테스트
  - [ ] AI Provider 테스트 (모킹)
  - [ ] 리딩 API 테스트
  - [ ] 인증 API 테스트
  - [ ] 커버리지 80% 이상
- **도구**: pytest, pytest-asyncio, pytest-cov
- **완료 조건**: `pytest --cov` 통과, 커버리지 80%+

#### TASK-044: API 통합 테스트
- **상태**: 📋 대기중
- **우선순위**: P1
- **예상 시간**: 4시간
- **담당자**: Dev
- **의존성**: TASK-043
- **상세 내용**:
  - [ ] 전체 리딩 플로우 E2E 테스트
  - [ ] 인증 플로우 테스트
  - [ ] 에러 시나리오 테스트
  - [ ] 성능 테스트 (응답 시간)
- **완료 조건**: 모든 주요 플로우 테스트 통과

#### TASK-045: 프론트엔드 테스트
- **상태**: 📋 대기중
- **우선순위**: P2
- **예상 시간**: 4시간
- **담당자**: Dev
- **의존성**: TASK-039, TASK-040
- **상세 내용**:
  - [ ] Jest + React Testing Library 설정
  - [ ] 컴포넌트 단위 테스트
  - [ ] 사용자 인터랙션 테스트
- **완료 조건**: 주요 컴포넌트 테스트 통과

#### TASK-046: 배포 환경 구축
- **상태**: 📋 대기중
- **우선순위**: P0
- **예상 시간**: 6시간
- **담당자**: DevOps/Dev
- **의존성**: TASK-044
- **상세 내용**:
  - [ ] Docker 이미지 생성 (백엔드)
  - [ ] docker-compose 설정
  - [ ] Vercel 배포 설정 (프론트엔드)
  - [ ] 환경 변수 설정 (프로덕션)
  - [ ] PostgreSQL 프로덕션 DB 설정
  - [ ] Redis 프로덕션 설정
- **플랫폼**:
  - Frontend: Vercel
  - Backend: Railway/Render/AWS
  - DB: Supabase/Railway
- **완료 조건**:
  - 프로덕션 URL 접근 가능
  - API health check 통과

#### TASK-047: CI/CD 파이프라인 구축
- **상태**: 📋 대기중
- **우선순위**: P2
- **예상 시간**: 4시간
- **담당자**: DevOps/Dev
- **의존성**: TASK-046
- **상세 내용**:
  - [ ] GitHub Actions 워크플로우 설정
  - [ ] 자동 테스트 실행
  - [ ] 자동 배포 (main 브랜치)
  - [ ] 린팅 및 타입 체크
- **완료 조건**: PR 시 자동 테스트, 머지 시 자동 배포

#### TASK-048: 모니터링 및 로깅 설정
- **상태**: 📋 대기중
- **우선순위**: P1
- **예상 시간**: 3시간
- **담당자**: Dev
- **의존성**: TASK-046
- **상세 내용**:
  - [ ] Sentry 오류 추적 설정
  - [ ] API 성능 모니터링
  - [ ] 로그 수집 및 분석
  - [ ] Uptime 모니터링
- **도구**: Sentry, Vercel Analytics
- **완료 조건**: 에러 발생 시 Sentry 알림 수신

---

### Epic 10: LLM 전략 고도화 (M6)

#### TASK-049: 실시간 응답 지연 로깅 및 스트리밍 전환
- **상태**: 📋 대기중
- **우선순위**: P0
- **예상 시간**: 6시간
- **담당자**: Dev
- **의존성**: TASK-028, TASK-029
- **상세 내용**:
  - [ ] `/readings` 엔드포인트에 FastAPI `StreamingResponse` 적용
  - [ ] LLM 호출 전/후 타임스탬프 기록 및 첫 토큰 지연 측정
  - [ ] Provider 선택, 지연 시간, 토큰 사용량을 Firestore `ai_metrics`에 저장
  - [ ] 3초 SLA 초과 시 경고 로그 남기기
- **도구**: FastAPI StreamingResponse, Python logging, Firestore
- **완료 조건**: 스트리밍 응답이 프론트엔드에서 수신되고 메트릭 문서가 Firestore에 생성됨

#### TASK-050: 프롬프트 스캐폴드 및 리딩 포매터 구축
- **상태**: 📋 대기중
- **우선순위**: P1
- **예상 시간**: 6시간
- **담당자**: AI/Dev
- **의존성**: TASK-021
- **상세 내용**:
  - [ ] `backend/src/ai/prompts/scaffolds.py` 생성 (원카드/쓰리카드 템플릿)
  - [ ] 카드 메타데이터 + 사용자 질문을 조합하는 `PromptScaffold` 유틸 구현
  - [ ] 모델 응답을 요약/카드 인사이트/행동 조언 섹션으로 정제하는 `ReadingFormatter` 추가
  - [ ] 단위 테스트로 섹션 누락 시 보강되는지 검증
- **도구**: Python, pytest
- **완료 조건**: 프롬프트 조립 및 후처리 유닛 테스트 통과, 샘플 응답에 3개 섹션이 모두 존재

#### TASK-051: PersonaSummaryService 및 Firestore 프로필 스키마 확장
- **상태**: 📋 대기중
- **우선순위**: P0
- **예상 시간**: 5시간
- **담당자**: Dev
- **의존성**: TASK-033, TASK-035
- **상세 내용**:
  - [ ] `users/{uid}/profile` 문서에 선호 톤, 언어, 길이, 마지막 만족도 저장
  - [ ] `PersonaSummaryService` 구현해 80토큰 이하 요약 텍스트 생성
  - [ ] 리딩 파이프라인에서 프롬프트 prefix에 요약 삽입
  - [ ] 프로필 부재 시 기본값으로 graceful fallback
- **도구**: Firestore Admin SDK, Python
- **완료 조건**: 사용자 프로필 갱신 후 생성된 요약이 LLM 프롬프트에 포함되고 로그로 확인

#### TASK-052: 피드백 통계 배치 파이프라인
- **상태**: 📋 대기중
- **우선순위**: P1
- **예상 시간**: 4시간
- **담당자**: Data/Dev
- **의존성**: TASK-036, TASK-037
- **상세 내용**:
  - [ ] Cloud Scheduler + Cloud Run 조합으로 야간 배치 파이프라인 구성
  - [ ] 피드백 태그/평점 집계 후 `feedback_stats` 문서 업데이트
  - [ ] 집계 실패 시 재시도 및 Slack/Webhook 알림
- **도구**: Cloud Scheduler, Cloud Run, Firestore
- **완료 조건**: 하루 1회 통계 문서가 갱신되고 실패 시 알림 수신

#### TASK-053: SLA 모니터링 및 대시보드 구축
- **상태**: 📋 대기중
- **우선순위**: P1
- **예상 시간**: 5시간
- **담당자**: DevOps
- **의존성**: TASK-049
- **상세 내용**:
  - [ ] Firestore/BigQuery 메트릭을 Looker Studio 또는 Cloud Monitoring에 시각화
  - [ ] 3초 SLA 초과율, Fallback 비율, 사용자 만족도 추이 차트 생성
  - [ ] 초과율 5% 이상 시 경고 알림 채널 연동
  - [ ] 주간 리포트 템플릿 작성
- **도구**: BigQuery, Looker Studio, Cloud Monitoring
- **완료 조건**: 대시보드 URL 공유 가능하며 SLA 알림이 테스트 트리거 시 정상 발송

---

### Epic 11: 타로 리딩 엔진 고도화 (M7)

#### TASK-054: RAG 지식 검색 시스템 구축
- **상태**: ✅ 완료
- **우선순위**: P0 (Critical)
- **예상 시간**: 12시간 → **실제 소요**: 14시간
- **담당자**: AI/Dev
- **의존성**: TASK-010
- **상세 내용**:
  - [x] ChromaDB 벡터 DB 설정
  - [x] sentence-transformers 임베딩 모델 통합 (paraphrase-multilingual-MiniLM-L12-v2)
  - [x] 지식 베이스 구조 설계 (cards/, spreads/, combinations/, categories/)
  - [x] 9장 타로 카드 상세 지식 문서 작성 (JSON 형식) - 7 Major + 2 Minor Arcana
  - [x] 스프레드별 위치 의미 문서 작성 (2개: one_card, three_card_past_present_future)
  - [x] 카드 조합 패턴 지식 베이스 구축 (8개 major pairs)
  - [x] 카테고리별 해석 가이드 작성 (4개: career, relationship, personal_growth, general)
  - [x] 임베딩 생성 및 벡터 DB 인덱싱 (25 documents indexed)
  - [x] Top-k 검색 API 구현 (k=2-3)
  - [x] 프롬프트 컨텍스트 강화 함수 구현
  - [x] 단위 테스트 작성 및 검증
  - [x] Reading API에 RAG 통합
  - [x] 모든 프롬프트 템플릿에 RAG 컨텍스트 섹션 추가
- **한계사항**:
  - 현재 9/78 카드만 knowledge base 보유
  - 나머지 69장 카드는 추가 작업 필요 (TASK-054-EXT로 분리)
- **디렉토리 구조**:
  ```
  backend/src/ai/rag/
  ├── __init__.py
  ├── vector_store.py      # 벡터 DB 관리
  ├── embeddings.py        # 임베딩 생성
  ├── retriever.py         # Top-k 검색
  ├── knowledge_base.py    # 지식 베이스 관리
  └── context_enricher.py  # 프롬프트 컨텍스트 강화

  backend/data/knowledge_base/
  ├── cards/
  │   ├── major_arcana/
  │   └── minor_arcana/
  ├── spreads/
  ├── combinations/
  └── categories/
  ```
- **기술 스택**:
  - chromadb==0.4.22 또는 qdrant-client==1.7.0
  - sentence-transformers==2.3.1
  - langchain==0.1.4
- **완료 조건**:
  - 지식 베이스 78장 카드 문서 완성
  - 벡터 검색 정확도 > 85% (테스트 쿼리 기준)
  - 프롬프트 컨텍스트에 RAG 결과 통합 완료

#### TASK-055: SSE 스트리밍 응답 구현
- **상태**: ✅ 완료
- **우선순위**: P0 (Critical)
- **예상 시간**: 8시간 → **실제 소요**: 8시간
- **담당자**: Dev
- **의존성**: TASK-027, TASK-028, TASK-054
- **상세 내용**:
  - [x] FastAPI StreamingResponse 설정
  - [x] SSE 이벤트 프로토콜 정의 (started, progress, card_drawn, rag_enrichment, ai_generation, complete, error)
  - [x] POST /api/v1/readings/stream 엔드포인트 구현
  - [x] 카드 뽑기 → RAG 검색 → LLM 생성 → 저장 파이프라인 구성
  - [x] 각 단계별 SSE 이벤트 발송 (7개 주요 단계)
  - [x] 에러 핸들링 및 SSE error 이벤트
  - [x] 프론트엔드 SSE 클라이언트 구현 (Fetch API + Streaming)
  - [x] 로딩 상태 UI 개선 (진행률 바, 실시간 메시지, 카드 애니메이션)
  - [x] React Hook (useSSEReading) 구현
- **구현 파일 (백엔드)**:
  - `backend/src/schemas/sse_events.py`: SSE 이벤트 타입 및 스키마 정의
  - `backend/src/api/routes/readings_stream.py`: SSE 스트리밍 엔드포인트 (390 lines)
  - `backend/scripts/test_sse_stream.py`: SSE 테스트 스크립트
- **구현 파일 (프론트엔드)**:
  - `frontend/src/lib/sse-client.ts`: 타입 안전 SSE 클라이언트 (260 lines)
  - `frontend/src/lib/use-sse-reading.ts`: SSE React Hook (150 lines)
  - `frontend/src/components/ReadingProgress.tsx`: 실시간 진행률 UI (180 lines)
  - `frontend/SSE_IMPLEMENTATION.md`: 구현 가이드 및 사용 예시
- **API 스펙**:
  ```
  POST /api/v1/readings/stream
  Content-Type: application/json
  Accept: text/event-stream

  Response: text/event-stream (SSE)
  ```
- **이벤트 예시**:
  ```
  event: progress
  data: {"status": "drawing_cards", "progress": 10}

  event: card_drawn
  data: {"card": {...}, "position": "past"}

  event: complete
  data: {"reading_id": "xxx", "total_time": 5.2}
  ```
- **완료 조건**:
  - 첫 SSE 이벤트 발송 < 3초
  - 전체 스트리밍 완료 < 6초 (P95)
  - 프론트엔드에서 실시간 진행 상황 표시

#### TASK-056: 다국어 번역 모듈 구현
- **상태**: 📋 대기중
- **우선순위**: P0 (Critical)
- **예상 시간**: 10시간
- **담당자**: Dev
- **의존성**: TASK-027
- **상세 내용**:
  - [ ] 번역 전략 설계 (LLM vs Google Translate vs Hybrid)
  - [ ] TranslationService 인터페이스 정의
  - [ ] LLMTranslator 구현 (Claude/GPT 활용)
  - [ ] GoogleTranslator 구현 (Google Translate API)
  - [ ] HybridTranslator 구현 (캐시된 응답은 Google, 새 응답은 LLM)
  - [ ] 번역 품질 검증 로직 (타로 전문 용어 정확도)
  - [ ] readings 테이블 translations 컬럼 추가 (JSONB)
  - [ ] POST /api/v1/readings/{reading_id}/translate 엔드포인트
  - [ ] GET /api/v1/readings/{reading_id}?locale=en 파라미터 지원
  - [ ] 번역 캐싱 로직 (translations 필드 활용)
  - [ ] force_refresh 파라미터 지원
  - [ ] 지원 언어: 한국어(ko), 영어(en), 일본어(ja), 스페인어(es)
  - [ ] 단위 테스트 (번역 품질, 캐싱 동작)
- **디렉토리 구조**:
  ```
  backend/src/translation/
  ├── __init__.py
  ├── translator.py       # 번역 인터페이스
  ├── llm_translator.py   # LLM 기반 번역
  ├── google_translator.py # Google API
  └── cache.py            # 번역 캐시
  ```
- **DB 마이그레이션**:
  ```sql
  ALTER TABLE readings ADD COLUMN translations JSONB DEFAULT '{}';
  ```
- **완료 조건**:
  - 4개 언어 번역 지원 (ko, en, ja, es)
  - 번역 캐시 히트율 > 70%
  - 번역 품질 스코어 > 4.0/5.0 (사용자 피드백 기준)

#### TASK-057: OpenTelemetry 트레이싱 통합
- **상태**: 📋 대기중
- **우선순위**: P1 (High)
- **예상 시간**: 6시간
- **담당자**: DevOps/Dev
- **의존성**: TASK-055
- **상세 내용**:
  - [ ] opentelemetry-api, opentelemetry-sdk 설치
  - [ ] opentelemetry-instrumentation-fastapi 자동 계측
  - [ ] opentelemetry-exporter-otlp 설정 (Cloud Trace)
  - [ ] 커스텀 Span 구현 (rag_search, llm_generation, translation)
  - [ ] 커스텀 메트릭 정의 (reading_duration, llm_token_usage, cache_hit_rate)
  - [ ] Trace context 전파 (HTTP 헤더)
  - [ ] 로그-트레이스 상관관계 설정
  - [ ] Cloud Trace 대시보드 설정
  - [ ] 성능 병목 지점 식별 및 최적화
- **디렉토리 구조**:
  ```
  backend/src/observability/
  ├── __init__.py
  ├── tracing.py          # OpenTelemetry 설정
  ├── metrics.py          # 커스텀 메트릭
  └── middleware.py       # FastAPI 미들웨어
  ```
- **메트릭 예시**:
  ```python
  reading_duration = meter.create_histogram(
      "tarot.reading.duration",
      description="Reading generation duration in seconds"
  )

  llm_token_usage = meter.create_counter(
      "tarot.llm.tokens",
      description="Total LLM tokens consumed"
  )
  ```
- **완료 조건**:
  - Cloud Trace에서 전체 요청 플로우 시각화
  - 병목 지점 식별 및 레이턴시 > 500ms 구간 최적화
  - 메트릭 대시보드 구축

#### TASK-058: 히스토리 재번역 API 구현
- **상태**: 📋 대기중
- **우선순위**: P1 (High)
- **예상 시간**: 4시간
- **담당자**: Dev
- **의존성**: TASK-056
- **상세 내용**:
  - [ ] GET /api/v1/readings?locale=en 파라미터 지원
  - [ ] GET /api/v1/readings/{reading_id}?locale=ja 번역 반환
  - [ ] translations 필드 확인 후 캐시 히트/미스 처리
  - [ ] force_refresh=true 시 캐시 무시 및 재생성
  - [ ] 페이지네이션에서 번역된 리딩 목록 반환
  - [ ] 프론트엔드 언어 선택 UI 구현
  - [ ] localStorage에 선호 언어 저장
  - [ ] 통합 테스트
- **완료 조건**:
  - 히스토리 페이지에서 언어 전환 가능
  - 번역 캐시 정상 동작 (재요청 시 즉시 반환)

#### TASK-059: 데이터 암호화 및 GDPR 준수
- **상태**: 📋 대기중
- **우선순위**: P2 (Medium)
- **예상 시간**: 6시간
- **담당자**: Security/Dev
- **의존성**: TASK-033
- **상세 내용**:
  - [ ] 민감 데이터 필드 식별 (question, user_context)
  - [ ] AES-256 암호화 유틸리티 구현
  - [ ] Google Secret Manager 암호화 키 관리
  - [ ] Reading 모델에 암호화 로직 통합
  - [ ] 데이터 읽기/쓰기 시 자동 암복호화
  - [ ] DELETE /api/v1/users/me 엔드포인트 (데이터 삭제)
  - [ ] GET /api/v1/users/me/data 엔드포인트 (데이터 다운로드)
  - [ ] 개인정보 처리방침 문서 작성
  - [ ] 쿠키 동의 UI (프론트엔드)
- **디렉토리 구조**:
  ```
  backend/src/core/
  ├── encryption.py        # AES-256 암호화
  └── gdpr.py              # GDPR API
  ```
- **완료 조건**:
  - question, user_context 필드 암호화 저장
  - GDPR Right to Access/Erasure API 구현
  - 개인정보 처리방침 페이지 추가

#### TASK-060: 성능 최적화 및 부하 테스트
- **상태**: 📋 대기중
- **우선순위**: P1 (High)
- **예상 시간**: 8시간
- **담당자**: Dev/DevOps
- **의존성**: TASK-054, TASK-055, TASK-057
- **상세 내용**:
  - [ ] P95 응답 시간 측정 (목표 < 6초)
  - [ ] 스트리밍 시작 시간 측정 (목표 < 3초)
  - [ ] 캐시 히트율 분석 (목표 > 80%)
  - [ ] N+1 쿼리 문제 해결 (SQLAlchemy eager loading)
  - [ ] RAG 검색 병렬화 (카드별 임베딩 동시 조회)
  - [ ] 프롬프트 크기 최적화 (토큰 수 최소화)
  - [ ] Locust 부하 테스트 시나리오 작성
  - [ ] 100 req/min 부하 테스트
  - [ ] 1만 일별 리딩 시뮬레이션
  - [ ] Cloud Run 스케일링 설정 최적화
  - [ ] 비용 분석 및 최적화 (목표 < $0.10/리딩)
- **도구**: Locust, Cloud Monitoring, Grafana
- **완료 조건**:
  - P95 < 6초, 스트리밍 시작 < 3초 달성
  - 100 req/min 처리 가능
  - 비용/리딩 < $0.10

#### TASK-061: Firestore 백그라운드 리딩 저장 파이프라인
- **상태**: ✅ 완료 (2025-11-01)
- **우선순위**: P0 (Critical)
- **예상 시간**: 6시간
- **담당자**: Dev
- **의존성**: TASK-055, TASK-054
- **상세 내용**:
  - [x] 현재 `generate_reading_stream` → `FirestoreProvider.create_reading` 흐름에서 Firestore 쓰기 지연 시간을 계측하고 로그로 남긴다.
  - [x] SSE 완료 이벤트와 Firestore 저장을 분리할 전략을 결정한다 (async background task) 및 실패시 로깅을 추가한다.
  - [x] `generate_reading_stream`을 리팩터링해 리딩 결과 스냅샷을 비동기 작업으로 위임하고, SSE는 즉시 완료 이벤트를 반환한다.
  - [x] Firestore 저장 로직을 `write_batch`로 통합하여 리딩 문서와 카드 서브컬렉션을 한 번의 커밋으로 기록한다.
  - [x] 백그라운드 작업 오류를 로깅하고, 작업 생명주기를 추적하기 위한 `_persistence_tasks` 셋을 도입했다.
  - [x] 단위 테스트(`tests/test_readings_stream_async.py`)로 백그라운드 경로와 데이터 ID 전달을 검증했다.
  - [ ] 배포 후 SSE 완료까지의 평균/95퍼센타일 시간을 비교해 개선 효과를 문서화한다.
- **완료 조건**:
  - SSE `complete` 이벤트가 Firestore 쓰기 대기 없이 반환되고, 백그라운드 작업이 성공적으로 리딩 데이터를 저장한다. ✅
  - Firestore 저장 실패 시 재시도 또는 경고가 기록되며 데이터 유실이 발생하지 않는다. ✅ (로깅 기반)
  - 배포 후 P95 리딩 완료 시간이 기존 대비 개선된 수치로 모니터링 대시보드에 보고된다. ⏳ (배포 후 측정 필요)

---

## 다음 단계 (Next Actions)

### 완료된 Epic들
1. ✅ Epic 1: 프로젝트 설정 및 인프라 (TASK-001 ~ TASK-008) - 완료
2. ✅ Epic 2: 타로 카드 데이터 시스템 (TASK-009 ~ TASK-014) - 완료
3. ✅ Epic 3: AI Provider 통합 (TASK-015 ~ TASK-020) - 완료
4. ✅ Epic 4: 프롬프트 엔진 (TASK-021 ~ TASK-025) - 완료
5. ✅ Epic 5: 리딩 시스템 (TASK-026 ~ TASK-030) - 완료
6. ✅ Epic 6: 사용자 인증 시스템 (TASK-031 ~ TASK-034-1) - 완료
7. ✅ Epic 7: 피드백 시스템 (TASK-035 ~ TASK-037) - 완료
8. ✅ Epic 8: 프론트엔드 구현 (TASK-038 ~ TASK-042) - 완료

### 즉시 시작 가능한 태스크 (P0) - Epic 11 우선
1. **TASK-054: RAG 지식 검색 시스템 구축** ⬅️ **우선 권장 (리딩 품질 향상)**
2. **TASK-055: SSE 스트리밍 응답 구현** ⬅️ **우선 권장 (사용자 경험 개선)**
3. **TASK-056: 다국어 번역 모듈 구현** ⬅️ **우선 권장 (국제화)**
4. TASK-049: 실시간 응답 지연 로깅 및 스트리밍 전환 (Epic 10)
5. TASK-051: PersonaSummaryService 및 Firestore 프로필 스키마 확장 (Epic 10)
6. TASK-046: 배포 환경 구축 (Epic 9)

### 현재 진행 상황
- [x] M1: 개발 환경 구축 완료 ✅
- [x] M2: 타로 카드 시스템 완성 ✅
- [x] M3: AI 통합 완료 ✅
- [x] M4: 리딩 엔진 완성 ✅
- [x] M5: 웹 인터페이스 완성 ✅
- [ ] M6: MVP 테스트 및 배포 (진행 예정)
- [ ] M7: 리딩 엔진 고도화 (Epic 11 - 새로 추가)

### 다음 목표
#### Phase 1: Epic 11 고도화 (권장 우선 순위)
- [x] **TASK-054**: RAG 지식 검색 시스템 구축 (P0) ✅
- [ ] **TASK-055**: SSE 스트리밍 응답 구현 (P0)
- [ ] **TASK-056**: 다국어 번역 모듈 구현 (P0)
- [ ] TASK-057: OpenTelemetry 트레이싱 통합 (P1)
- [ ] TASK-058: 히스토리 재번역 API 구현 (P1)
- [ ] TASK-059: 데이터 암호화 및 GDPR 준수 (P2)
- [ ] TASK-060: 성능 최적화 및 부하 테스트 (P1)
- [x] TASK-061: Firestore 백그라운드 리딩 저장 파이프라인 (P0)

#### Phase 2: MVP 완성
- [ ] Epic 9 완료: 테스트 및 배포 (TASK-043 ~ TASK-048)
- [ ] Epic 10 진행: LLM 전략 고도화 (TASK-049 ~ TASK-053)
- [ ] MVP 배포 완료

---

## 태스크 관리 규칙

### 우선순위 정의
- **P0 (Critical)**: MVP 필수 기능, 차단 요소
- **P1 (High)**: MVP 핵심 기능
- **P2 (Medium)**: MVP 부가 기능
- **P3 (Low)**: 나중에 추가 가능

### 상태 정의
- ✅ **완료**: 코드 작성, 테스트 통과, 리뷰 완료
- 🚧 **진행중**: 현재 작업 중
- 📋 **대기중**: 아직 시작하지 않음
- ⏸️ **보류**: 일시적으로 중단
- ❌ **취소**: 더 이상 진행하지 않음

### 예상 시간 기준
- 1-2시간: 간단한 설정, 작은 기능
- 3-4시간: 중간 복잡도 기능
- 5-8시간: 복잡한 기능, 여러 컴포넌트
- 8시간+: 대규모 작업, Epic 수준

### 일일 업데이트 규칙
- 매일 종료 시 TASK.md 업데이트
- 완료된 태스크 체크
- 진행 상황 퍼센트 업데이트
- 블로커 이슈 기록

---

## 리스크 및 이슈

### 현재 리스크
1. **AI API 비용**: 개발 중 과도한 API 호출로 비용 증가 가능
   - 완화: 모킹 사용, 캐싱 적극 활용

2. **타로 데이터 수집**: 저작권 문제 가능성
   - 완화: 퍼블릭 도메인 자료만 사용, 라이선스 확인

3. **AI 응답 품질**: 일관성 없는 해석
   - 완화: 프롬프트 엔지니어링, 테스트 데이터셋 구축

### 해결된 이슈
- 없음 (첫 시작)

---

**문서 버전**: 1.3
**마지막 업데이트**: 2025-10-30
**다음 리뷰**: 매주 금요일

---

## 최근 업데이트 (2025-10-30)

### 주요 변경점
- ✅ **PRD.md 문서 생성**: 타로 리딩 엔진 고도화 요구사항 상세 문서화
- ✅ **Epic 11 "타로 리딩 엔진 고도화" 신설**: TASK-054 ~ TASK-060 추가 (7개 태스크)
- ✅ RAG 지식 검색, SSE 스트리밍, 다국어 번역, OpenTelemetry 통합 계획 수립
- ✅ M7 마일스톤 추가: 리딩 엔진 고도화 (목표 완료일: 2025-02-15)
- ✅ 우선순위 재조정: Epic 11 P0 태스크 (TASK-054, 055, 056) 우선 권장

### 마일스톤 달성 현황
- ✅ M1: 개발 환경 구축 완료
- ✅ M2: 타로 카드 시스템 완성
- ✅ M3: AI 통합 완료
- ✅ M4: 리딩 엔진 완성
- ✅ M5: 웹 인터페이스 완성
- ⏳ M6: MVP 테스트 및 배포 (Epic 9, Epic 10 진행 중)
- 🆕 M7: 리딩 엔진 고도화 (Epic 11 - 새로 추가)

### 프로젝트 상태
- 📊 전체 진행률:
  - Phase 1 MVP: 80.0% (36/45 완료)
  - Phase 2 고도화: 0.0% (0/7 완료)
- 🎯 다음 목표: Epic 11 고도화 (RAG, 스트리밍, 번역) → Epic 9 테스트/배포 → Epic 10 LLM 전략
- 🚀 **우선 권장 작업**: TASK-054 (RAG), TASK-055 (SSE), TASK-056 (번역)
- 📄 **참고 문서**: PRD.md (Product Requirements Document) 추가
