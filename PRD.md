# Product Requirements Document (PRD)
# 타로 리딩 엔진 API - 고도화 버전

## 문서 정보
- **버전**: 2.0
- **작성일**: 2025-10-30
- **프로젝트**: 타로 AI 리딩 서비스
- **문서 유형**: Product Requirements Document

---

## 1. 제품 개요

### 1.1 목표
기존 타로 리딩 서비스에 **고급 AI 기능**, **실시간 스트리밍**, **다국어 지원**, **RAG 지식 검색**을 통합하여 사용자 경험과 리딩 품질을 획기적으로 향상시킨다.

### 1.2 핵심 가치 제안
- ⚡ **빠른 응답**: P95 < 6초, 스트리밍 시작 < 3초
- 🎯 **높은 품질**: RAG 기반 컨텍스트 강화 및 전문 지식 통합
- 🌍 **국제화**: 한국어 기본, 영어/일본어/스페인어 자동 번역
- 📊 **관측 가능성**: OpenTelemetry 기반 전체 트레이싱
- 🔒 **보안 & 개인정보**: GDPR/한국 개인정보법 준수

### 1.3 대상 사용자
- **일반 사용자**: 타로 리딩을 통해 인사이트를 얻고자 하는 사람들
- **글로벌 사용자**: 다양한 언어권 사용자
- **파워 유저**: 히스토리 관리 및 재번역을 원하는 사용자

---

## 2. 기능 요구사항

### 2.1 타로 리딩 엔진 API

#### 2.1.1 입력 스펙
```typescript
interface ReadingRequest {
  spread_id: string;              // "one_card" | "three_card_past_present_future" | "three_card_situation_action_outcome"
  cards?: Card[];                 // 선택적 카드 지정 (비어있으면 자동 선택)
  question: string;               // 사용자 질문 (5-500자)
  locale: string;                 // 기본 "ko", 지원: "en", "ja", "es"
  user_profile?: {
    preferences?: string;
    history_summary?: string;
  };
  category?: string;              // "love" | "career" | "finance" | "health" | "personal_growth" | "spirituality"
}
```

#### 2.1.2 출력 스펙
```typescript
interface ReadingResponse {
  id: string;                     // Reading UUID
  theme: string;                  // 리딩 주제 한 줄
  card_insights: CardInsight[];   // 카드별 해석
  card_relationships?: string;    // 카드 간 관계 (3장 이상)
  overall_reading: string;        // 종합 리딩
  action_items: string[];         // 실천 가능한 조언
  translations?: {
    [locale: string]: Translation;
  };
  llm_usage: LLMUsage[];          // LLM 사용 기록
  confidence: number;             // 리딩 신뢰도 (0-1)
  created_at: string;             // ISO 8601 timestamp
}

interface CardInsight {
  card_id: number;
  position: string;
  orientation: "upright" | "reversed";
  interpretation: string;         // 해석 (200자 이상)
  key_message: string;            // 핵심 메시지 (50자 이내)
  keywords: string[];             // 키워드 3-5개
}

interface Translation {
  theme: string;
  card_insights: CardInsight[];
  overall_reading: string;
  action_items: string[];
}

interface LLMUsage {
  id: string;
  provider: string;               // "openai" | "anthropic"
  model: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  estimated_cost: number;         // USD
  latency_seconds: number;
  purpose: string;                // "main_reading" | "fallback" | "retry"
}
```

---

### 2.2 RAG 지식 검색 시스템

#### 2.2.1 목표
- 78장 타로 카드의 상세 의미, 상징, 역사적 배경을 벡터 검색으로 제공
- 스프레드별 위치 해석 가이드
- 카드 조합 패턴 지식
- 카테고리별(연애, 직업 등) 해석 컨텍스트

#### 2.2.2 기술 스택
- **벡터 DB**: ChromaDB 또는 Qdrant
- **임베딩 모델**: `sentence-transformers/all-MiniLM-L6-v2` (다국어 지원)
- **검색 방식**: Top-k 유사도 검색 (k=3-5)

#### 2.2.3 지식 베이스 구성
```
data/knowledge_base/
├── cards/
│   ├── major_arcana/          # 22장 메이저 아르카나
│   │   ├── 00_the_fool.json
│   │   ├── 01_the_magician.json
│   │   └── ...
│   └── minor_arcana/          # 56장 마이너 아르카나
│       ├── wands/
│       ├── cups/
│       ├── swords/
│       └── pentacles/
├── spreads/
│   ├── one_card.json
│   ├── three_card.json
│   └── celtic_cross.json
├── combinations/              # 카드 조합 패턴
│   ├── major_pairs.json       # 메이저 카드 조합
│   └── suit_combinations.json
└── categories/                # 카테고리별 해석 가이드
    ├── love.json
    ├── career.json
    └── ...
```

#### 2.2.4 API 명세
```python
# 내부 API (외부 노출 안 함)
def search_card_knowledge(card_id: int, query: str, k: int = 3) -> List[Document]:
    """카드 관련 지식 검색"""
    pass

def enrich_context(cards: List[Card], spread_type: str, category: str) -> Dict:
    """프롬프트 컨텍스트 강화"""
    pass
```

---

### 2.3 다중 LLM 라우팅

#### 2.3.1 Tier 기반 라우터
```python
class LLMRouter:
    TIERS = {
        "tier1": {
            "provider": "anthropic",
            "model": "claude-3-haiku-20240307",
            "timeout": 60,
            "cost_per_1k_tokens": 0.00025
        },
        "tier2": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "timeout": 60,
            "cost_per_1k_tokens": 0.00015
        }
    }
```

#### 2.3.2 Fallback 전략
1. **Primary (Tier 1)** 시도 → 60초 timeout
2. 실패 시 **Secondary (Tier 2)** 로 즉시 전환
3. 모두 실패 시 사용자에게 에러 메시지 + 재시도 안내

#### 2.3.3 비용 최적화
- 캐싱 우선: 동일 질문 + 카드 조합 → Redis 캐시 (TTL 24시간)
- 캐시 히트율 목표: 80% 이상
- 예상 월 비용: $500 이하 (1만 리딩 기준)

---

### 2.4 스트리밍 전달 (SSE)

#### 2.4.1 목표
- 리딩 생성 과정을 실시간으로 프론트엔드에 전달
- 첫 응답 < 3초 (사용자 체감 속도 개선)
- 전체 응답 < 6초 (P95)

#### 2.4.2 SSE 이벤트 프로토콜
```
event: progress
data: {"status": "drawing_cards", "progress": 10}

event: card_drawn
data: {"card": {...}, "position": "past"}

event: rag_search
data: {"status": "searching", "progress": 30}

event: llm_generation
data: {"status": "generating", "progress": 50}

event: card_interpretation
data: {"card_id": 1, "text": "바보 카드는...", "progress": 70}

event: overall_reading
data: {"text": "종합적으로...", "progress": 90}

event: complete
data: {"reading_id": "xxx", "total_time": 5.2}

event: error
data: {"error": "LLM timeout", "retry": true}
```

#### 2.4.3 API 엔드포인트
```python
@router.post("/api/v1/readings/stream")
async def create_reading_stream(request: ReadingRequest) -> StreamingResponse:
    """스트리밍 방식 리딩 생성"""
    pass
```

---

### 2.5 번역 모듈

#### 2.5.1 번역 전략
- **기본 언어**: 한국어 (모든 리딩은 한국어로 먼저 생성)
- **지원 언어**: 영어(en), 일본어(ja), 스페인어(es)
- **번역 방식**:
  - **Option A**: LLM 기반 번역 (Claude/GPT) - 문맥 이해 우수
  - **Option B**: Google Translate API - 빠르고 저렴
  - **권장**: Hybrid (캐시된 응답은 Google, 새 응답은 LLM)

#### 2.5.2 번역 품질 요구사항
- 타로 전문 용어 정확도
- 문화적 뉘앙스 보존
- 조언 섹션의 자연스러운 번역

#### 2.5.3 데이터베이스 스키마
```sql
-- readings 테이블에 추가
ALTER TABLE readings ADD COLUMN translations JSONB DEFAULT '{}';
-- 형식: {"en": {...}, "ja": {...}, "es": {...}}
```

#### 2.5.4 API 명세
```python
@router.post("/api/v1/readings/{reading_id}/translate")
async def translate_reading(
    reading_id: str,
    target_language: str,  # "en" | "ja" | "es"
    force_refresh: bool = False
) -> TranslatedReadingResponse:
    """리딩 번역 생성 또는 캐시 반환"""
    pass
```

---

### 2.6 히스토리 & 재번역

#### 2.6.1 히스토리 조회 API
```python
@router.get("/api/v1/readings")
async def get_readings(
    user_id: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
    spread_type: Optional[str] = None,
    locale: Optional[str] = None
) -> ReadingListResponse:
    """리딩 히스토리 조회"""
    pass

@router.get("/api/v1/readings/{reading_id}")
async def get_reading(reading_id: str, locale: str = "ko") -> ReadingResponse:
    """특정 리딩 조회 (locale에 따라 번역 반환)"""
    pass
```

#### 2.6.2 재번역 로직
1. `translations` 필드에 해당 언어가 있는지 확인
2. 있으면 즉시 반환 (캐시 히트)
3. 없으면 번역 생성 → 저장 → 반환
4. `force_refresh=true` 시 캐시 무시하고 재생성

---

### 2.7 OpenTelemetry 통합

#### 2.7.1 추적 대상
- HTTP 요청 (FastAPI 자동)
- 데이터베이스 쿼리 (SQLAlchemy)
- AI Provider 호출 (Custom span)
- RAG 검색 (Custom span)
- 번역 작업 (Custom span)

#### 2.7.2 커스텀 메트릭
```python
from opentelemetry import trace, metrics

tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)

# 메트릭 정의
reading_duration = meter.create_histogram(
    "tarot.reading.duration",
    description="Reading generation duration in seconds"
)

llm_token_usage = meter.create_counter(
    "tarot.llm.tokens",
    description="Total LLM tokens consumed"
)

cache_hit_rate = meter.create_gauge(
    "tarot.cache.hit_rate",
    description="Cache hit rate percentage"
)
```

#### 2.7.3 Span 예시
```python
with tracer.start_as_current_span("generate_reading") as span:
    span.set_attribute("spread_type", request.spread_type)
    span.set_attribute("locale", request.locale)

    with tracer.start_as_current_span("rag_search"):
        # RAG 검색 작업
        pass

    with tracer.start_as_current_span("llm_generation"):
        span.set_attribute("provider", "openai")
        span.set_attribute("model", "gpt-4o-mini")
        # LLM 호출
        pass
```

---

## 3. 비기능 요구사항 (NFR)

### 3.1 성능
| 지표 | 목표 | 측정 방법 |
|------|------|----------|
| P95 응답 시간 | < 6초 | OpenTelemetry histogram |
| 스트리밍 시작 시간 | < 3초 | 첫 SSE 이벤트 발송 시간 |
| 캐시 히트율 | > 80% | Redis monitor |
| 동시 처리량 | 100 req/min | Load testing (Locust) |

### 3.2 가용성
- **목표**: 99.5% 이상
- **전략**:
  - 다중 AI Provider fallback
  - Health check 엔드포인트 강화
  - Kubernetes liveness/readiness probes
  - Circuit breaker 패턴 (선택 사항)

### 3.3 확장성
- **목표**: 1만 일별 리딩까지 무중단 확장
- **아키텍처**:
  - Cloud Run 자동 스케일링
  - Firestore (읽기/쓰기 무제한)
  - Redis Cluster (필요 시)
  - 비동기 큐 (Celery + Redis, 필요 시)

### 3.4 보안 & 개인정보
- **GDPR/한국 개인정보법 준수**:
  - 개인정보 최소 수집 원칙
  - 사용자 데이터 삭제 API (`DELETE /api/v1/users/me`)
  - 데이터 다운로드 API (Right to Access)
  - 쿠키 동의 관리 (프론트엔드)
- **암호화**:
  - 민감 데이터 (질문, 컨텍스트) AES-256 암호화
  - 암호화 키: Google Secret Manager
- **인증**:
  - Firebase Auth (익명 인증 지원)
  - JWT 토큰 (Access + Refresh)

### 3.5 관측성
- **로깅**: 구조화된 JSON 로그 (Cloud Logging)
- **트레이싱**: OpenTelemetry → Cloud Trace
- **메트릭**: Prometheus → Grafana (또는 Cloud Monitoring)
- **비용 추적**: LLM 사용량 실시간 대시보드

---

## 4. 데이터 모델

### 4.1 Core Entities

#### Reading
```python
class Reading(Base):
    __tablename__ = "readings"

    id: str                      # UUID
    user_id: Optional[str]       # Firebase UID (nullable for anonymous)
    spread_type: str
    question: str                # Encrypted
    user_context: Optional[str]  # Encrypted
    category: Optional[str]

    # AI 생성 결과
    theme: str
    card_relationships: Optional[str]
    overall_reading: str
    advice: dict                 # JSON
    summary: str
    translations: dict           # JSON: {"en": {...}, "ja": {...}}
    confidence: float

    # 메타데이터
    created_at: datetime
    updated_at: datetime
```

#### ReadingCard
```python
class ReadingCard(Base):
    __tablename__ = "reading_cards"

    id: str                      # UUID
    reading_id: str              # FK to readings
    card_id: int                 # FK to cards
    position: str                # "single", "past", "present", "future", etc.
    orientation: str             # "upright" | "reversed"
    interpretation: str          # AI 생성 해석
    key_message: str
    keywords: list               # JSON array
```

#### LLMUsageLog
```python
class LLMUsageLog(Base):
    __tablename__ = "llm_usage_logs"

    id: str                      # UUID
    reading_id: str              # FK to readings
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float        # USD
    latency_seconds: float
    purpose: str                 # "main_reading" | "fallback" | "retry" | "translation"
    created_at: datetime
```

---

## 5. API 엔드포인트

### 5.1 리딩 생성
```
POST /api/v1/readings
Content-Type: application/json

Request Body: ReadingRequest
Response: ReadingResponse (201 Created)
```

### 5.2 스트리밍 리딩
```
POST /api/v1/readings/stream
Content-Type: application/json

Request Body: ReadingRequest
Response: text/event-stream (SSE)
```

### 5.3 리딩 조회
```
GET /api/v1/readings/{reading_id}?locale=ko
Response: ReadingResponse (200 OK)
```

### 5.4 리딩 목록
```
GET /api/v1/readings?page=1&page_size=10&spread_type=one_card&locale=ko
Response: ReadingListResponse (200 OK)
```

### 5.5 번역 생성
```
POST /api/v1/readings/{reading_id}/translate
Content-Type: application/json

Request Body:
{
  "target_language": "en",
  "force_refresh": false
}

Response: ReadingResponse with translations (200 OK)
```

---

## 6. 개발 우선순위

### High Priority (P0) - 사용자 경험 핵심
1. ✅ **SSE 스트리밍 구현** (첫 응답 < 3초)
2. ✅ **RAG 지식 검색** (리딩 품질 향상)
3. ✅ **번역 모듈** (국제화 필수)

### Medium Priority (P1) - 운영 안정성
4. **OpenTelemetry 통합** (관측 가능성)
5. **성능 최적화** (P95 < 6초)
6. **히스토리 재번역 API**

### Low Priority (P2) - 법적 요구사항
7. **데이터 암호화** (GDPR 대응)
8. **GDPR API** (데이터 삭제/다운로드)

---

## 7. 성공 지표 (KPI)

| 지표 | 목표 | 현재 | 달성 방법 |
|------|------|------|----------|
| P95 응답 시간 | < 6초 | ~4초 | 이미 달성 ✅ |
| 스트리밍 시작 | < 3초 | N/A | SSE 구현 필요 |
| 가용성 | 99.5% | ~99% | Fallback 강화 완료 ✅ |
| 캐시 히트율 | > 80% | ~60% | RAG 캐싱 추가 필요 |
| 일 처리량 | 10,000 리딩 | ~100 | 스케일링 테스트 필요 |
| 비용/리딩 | < $0.10 | $0.15 | 캐싱 + 저렴한 모델 |
| 사용자 만족도 | > 4.5/5.0 | N/A | 피드백 시스템 활성화 |

---

## 8. 제약사항 및 리스크

### 8.1 기술적 제약
- **LLM API Rate Limit**: OpenAI 60 RPM, Claude 50 RPM
  - 완화: 캐싱 강화, 계정 증설
- **번역 비용**: LLM 기반 번역 시 비용 증가
  - 완화: Google Translate Hybrid 전략

### 8.2 비즈니스 리스크
- **AI 비용 폭증**: 1만 리딩 시 월 $500 초과 가능
  - 완화: 캐시 히트율 80% 달성, Tier 2 모델 활용
- **번역 품질 불만**: 기계 번역 특유의 부자연스러움
  - 완화: 전문 번역가 검수 + LLM 번역 (최소 주요 언어)

---

## 9. 릴리스 계획

### Phase 1: 코어 기능 (Week 1-2)
- RAG 시스템 구축
- SSE 스트리밍 구현
- 번역 모듈 (LLM 기반)

### Phase 2: 최적화 (Week 3-4)
- 성능 튜닝 (P95 < 6초)
- 캐싱 전략 고도화
- OpenTelemetry 통합

### Phase 3: 안정화 (Week 5-6)
- 보안 강화 (암호화)
- GDPR API 구현
- 부하 테스트 및 스케일링 검증

### Phase 4: 출시 (Week 7)
- 프로덕션 배포
- 모니터링 대시보드 구축
- 사용자 피드백 수집

---

## 10. 참고 문서

- [TASK.md](/Users/wizmain/Documents/workspace/tarot-project-claude/TASK.md) - 구현 태스크 목록
- [ARCHITECTURE.md](/Users/wizmain/Documents/workspace/tarot-project-claude/ARCHITECTURE.md) - 시스템 아키텍처
- [PROJECT_PLAN.md](/Users/wizmain/Documents/workspace/tarot-project-claude/PROJECT_PLAN.md) - 프로젝트 기획
- [INTEND.md](/Users/wizmain/Documents/workspace/tarot-project-claude/INTEND.md) - 초기 의도 문서

---

**문서 버전**: 2.0
**마지막 업데이트**: 2025-10-30
**작성자**: Development Team
**승인자**: Product Owner
