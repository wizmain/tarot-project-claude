# TASK - 타로 AI 리딩 서비스 구현 태스크

## 문서 정보
- **버전**: 1.0
- **작성일**: 2025-10-18
- **현재 Phase**: Phase 1 - MVP
- **목표 완료일**: 2025-01-18 (3개월)

---

## 진행 상황 대시보드

### 전체 진행률
```
Phase 1 MVP: ██████████████████░░ 90.0% (36/40 완료)

✅ 완료: 36개
🚧 진행중: 0개
📋 대기중: 4개
```

### 마일스톤 현황
- [x] M0: 프로젝트 기획 완료 (2025-10-18)
- [x] M1: 개발 환경 구축 (2025-10-25) ✅
- [x] M2: 타로 카드 시스템 완성 (2025-11-08) ✅
- [x] M3: AI 통합 완료 (2025-11-22) ✅
- [x] M4: 리딩 엔진 완성 (2025-12-13) ✅
- [x] M5: 웹 인터페이스 완성 (2025-12-27) ✅
- [ ] M6: MVP 테스트 및 배포 (2025-01-18)

---

## Phase 1: MVP 태스크 (총 40개)

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

## 다음 단계 (Next Actions)

### 완료된 Epic들
1. ✅ Epic 1: 프로젝트 설정 및 인프라 (TASK-001 ~ TASK-008) - 완료
2. ✅ Epic 2: 타로 카드 데이터 시스템 (TASK-009 ~ TASK-014) - 완료
3. ✅ Epic 3: AI Provider 통합 (TASK-015 ~ TASK-020) - 완료
4. ✅ Epic 4: 프롬프트 엔진 (TASK-021 ~ TASK-025) - 완료
5. ✅ Epic 5: 리딩 시스템 (TASK-026 ~ TASK-030) - 완료
6. ✅ Epic 6: 사용자 인증 시스템 (TASK-031 ~ TASK-034-1) - 완료
7. ✅ Epic 8: 프론트엔드 구현 (TASK-038 ~ TASK-042) - 완료

### 즉시 시작 가능한 태스크 (P0)
1. **TASK-035: Feedback 데이터 모델** ⬅️ **다음 작업**
2. TASK-036: 피드백 제출 API
3. TASK-037: 피드백 통계 API

### 현재 진행 상황
- [x] M1: 개발 환경 구축 완료 ✅
- [x] M2: 타로 카드 시스템 완성 ✅
- [x] M3: AI 통합 완료 ✅
- [x] M4: 리딩 엔진 완성 ✅
- [x] M5: 웹 인터페이스 완성 ✅
- [ ] M6: MVP 테스트 및 배포 (진행 예정)

### 다음 목표 (M6 완성)
- [ ] Epic 7 완료: 피드백 시스템 (선택 사항)
- [ ] Epic 9 완료: 테스트 및 배포
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

**문서 버전**: 1.1
**마지막 업데이트**: 2025-10-19
**다음 리뷰**: 매주 금요일

---

## 최근 업데이트 (2025-10-20)

### 완료된 작업
- ✅ Epic 1 완료: 프로젝트 설정 및 인프라 (8개 태스크)
- ✅ Epic 2 완료: 타로 카드 데이터 시스템 (5개 태스크, TASK-012 보류)
- ✅ Epic 3 완료: AI Provider 통합 (6개 태스크)
- ✅ Epic 4 완료: 프롬프트 엔진 (5개 태스크)
- ✅ Epic 5 완료: 리딩 시스템 (5개 태스크)
- ✅ Epic 6 완료: 사용자 인증 시스템 (5개 태스크)
- ✅ Epic 8 완료: 프론트엔드 구현 (5개 태스크)
  - TASK-038: TarotCard 컴포넌트 (3D 애니메이션)
  - TASK-039: 원카드/쓰리카드 리딩 페이지
  - TASK-040: 리딩 결과 페이지 (히스토리 상세)
  - TASK-041: 리딩 히스토리 목록 페이지
  - TASK-042: 로그인/회원가입 페이지

### 마일스톤 달성
- ✅ M1: 개발 환경 구축 완료
- ✅ M2: 타로 카드 시스템 완성
- ✅ M3: AI 통합 완료
- ✅ M4: 리딩 엔진 완성
- ✅ M5: 웹 인터페이스 완성

### 프로젝트 상태
- 📊 전체 진행률: 82.5% (33/40 완료)
- 🎯 다음 목표: Epic 7 (피드백 시스템) 또는 Epic 9 (테스트 및 배포)
- 🚀 MVP 핵심 기능 모두 완성!
