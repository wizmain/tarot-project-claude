# INTEND - 타로 AI 리딩 서비스

## 문제정의 (Problem)

### 현재 상황
1. **기존 온라인 타로 서비스의 한계**
   - 정적이고 반복적인 해석: 카드 조합에 대한 고정된 텍스트만 제공
   - 맥락 이해 부족: 사용자의 질문과 상황을 고려하지 못하는 일반적인 해석
   - 개인화 부재: 동일한 카드에 대해 모든 사용자에게 같은 답변 제공
   - 품질 개선 불가: 사용자 피드백을 반영한 학습 메커니즘 없음

2. **AI 활용의 문제점**
   - 단일 AI 모델 의존: 특정 서비스 장애시 전체 서비스 중단
   - 비용 관리 어려움: AI API 비용 증가에 대한 대응책 부족
   - 일관성 없는 품질: 체계적인 프롬프트 관리 및 최적화 시스템 부재
   - 확장성 제약: 새로운 AI 모델 추가 시 높은 통합 비용

3. **사용자 경험 문제**
   - 낮은 신뢰도: 부정확하거나 모호한 해석
   - 참여도 부족: 흥미를 유지시킬 기능 부재
   - 접근성 제약: 전문 타로 리더의 높은 비용과 시간 제약

### 해결 과제
**다중 AI 모델을 활용하여 고품질의 개인화된 타로 리딩을 제공하고, 사용자 피드백을 통해 지속적으로 학습하며, 안정적이고 확장 가능한 서비스를 구축한다.**

---

## 구현 의도 및 목표 (2025-10-29 업데이트)

- **응답 속도 3초 이내 확보**: OpenAI `gpt-4o-mini`를 주력 엔진으로 사용하고 스트리밍 응답을 기본값으로 설정해 첫 토큰을 평균 1초 내 수신한다. 실패 시 Anthropic Claude, Google Gemini 순으로 자동 폴백해 SLA(95% < 3초)를 유지한다.
- **풍부한 리딩 구성**: 스프레드별 프롬프트 스캐폴드와 카드 메타데이터를 조합하는 `PromptScaffold`를 도입해 카드 상징 설명, 상황 해석, 실행 조언 섹션을 구조화한다. 모델 출력은 `ReadingFormatter`가 검증·보강해 요약, 카드 인사이트, 행동 제안을 항상 포함한다.
- **피드백 기반 개인화**: Firestore `users/{uid}` 문서에 선호 톤, 최근 만족도, 피드백 태그를 누적하고 `PersonaSummaryService`가 80토큰 이하 요약을 실시간 프롬프트 앞에 주입한다. 피드백 수집 파이프라인은 정기 배치로 통계를 갱신해 온도·길이·콘텐츠 깊이를 자동 조정한다.
- **관측 및 최적화**: `/readings` 엔드포인트에서 Provider 선택, 지연 시간, 토큰 사용량, 개인화 플래그를 로그/BigQuery에 축적하고 5% 초과 SLA 위반 시 알림을 발생시켜 즉시 프롬프트/우선순위를 조정한다.

---

## 성공기준 (Acceptance Criteria)

### Phase 1: MVP (필수 요구사항)

#### AC-1: 타로 카드 시스템
- [ ] 78장의 타로 카드 데이터가 데이터베이스에 저장되어 있어야 한다
  - 테스트: `SELECT COUNT(*) FROM cards`가 78을 반환
- [ ] 각 카드는 정방향/역방향 의미를 포함해야 한다
  - 테스트: 모든 카드에 `upright_meaning`, `reversed_meaning` 필드가 존재하고 NULL이 아님
- [ ] 카드 랜덤 선택 시 중복이 발생하지 않아야 한다
  - 테스트: 1000회 반복 테스트에서 동일 세션 내 카드 중복률 0%

#### AC-2: AI Provider 추상화
- [ ] 최소 2개의 AI 모델(OpenAI, Claude)을 지원해야 한다
  - 테스트: 각 provider로 동일 요청 시 200 OK 응답 수신
- [ ] Provider 전환이 동적으로 가능해야 한다
  - 테스트: 설정 변경 후 재시작 없이 다른 provider로 요청 성공
- [ ] Fallback 메커니즘이 작동해야 한다
  - 테스트: Primary provider 실패 시 3초 이내 secondary provider로 자동 전환

#### AC-3: 기본 스프레드 구현
- [ ] 원카드 리딩이 작동해야 한다
  - 테스트: 원카드 요청 시 1장의 카드와 해석을 포함한 응답 반환
- [ ] 쓰리카드 리딩이 작동해야 한다
  - 테스트: 쓰리카드 요청 시 3장의 카드와 각각의 해석, 종합 리딩을 포함한 응답 반환
- [ ] 스프레드별 포지션 의미가 정확해야 한다
  - 테스트: 쓰리카드의 포지션이 "과거-현재-미래" 또는 "상황-행동-결과"로 레이블됨

#### AC-4: 리딩 응답 품질
- [ ] AI 응답 시간이 5초 이내여야 한다 (95 percentile)
  - 테스트: 100회 요청의 95%가 5초 이내 응답
- [ ] 응답은 구조화된 JSON 형식이어야 한다
  - 테스트: JSON schema validation 통과
- [ ] 한국어로 된 자연스러운 해석을 제공해야 한다
  - 테스트: 언어 감지 API로 한국어 확인 (신뢰도 > 95%)

#### AC-5: 피드백 시스템
- [ ] 사용자가 리딩 결과에 평점(1-5점)을 남길 수 있어야 한다
  - 테스트: 피드백 POST 요청 시 데이터베이스에 저장되고 200 OK 반환
- [ ] 피드백 데이터가 저장되고 조회 가능해야 한다
  - 테스트: 저장된 피드백을 GET 요청으로 조회 시 올바른 데이터 반환
- [ ] 평균 만족도 점수를 계산할 수 있어야 한다
  - 테스트: 통계 API 호출 시 평균 점수가 정확하게 계산됨

#### AC-6: API 안정성
- [ ] API 가용성이 99% 이상이어야 한다
  - 테스트: 월별 uptime 모니터링 결과 99% 이상
- [ ] 동시 요청 처리가 가능해야 한다
  - 테스트: 10개의 동시 요청이 모두 정상 처리됨
- [ ] 에러가 발생해도 서비스가 중단되지 않아야 한다
  - 테스트: AI provider 에러 시 graceful degradation으로 에러 메시지 반환

### Phase 2: 최적화 (추가 요구사항)

#### AC-7: DSPy 프롬프트 최적화
- [ ] 프롬프트 버전 관리가 가능해야 한다
  - 테스트: 프롬프트 버전 CRUD API가 정상 작동
- [ ] A/B 테스팅이 가능해야 한다
  - 테스트: 동일 요청에 대해 두 개의 다른 프롬프트 버전이 번갈아 사용됨
- [ ] 성능 지표 추적이 가능해야 한다
  - 테스트: 프롬프트별 평균 만족도, 응답 시간이 대시보드에 표시됨

#### AC-8: 응답 품질 개선
- [ ] 사용자 만족도가 80% 이상이어야 한다
  - 테스트: 월별 평균 평점이 4.0/5.0 이상
- [ ] 응답 시간이 3초 이내로 단축되어야 한다 (95 percentile)
  - 테스트: 100회 요청의 95%가 3초 이내 응답

#### AC-9: 다중 AI 모델 지원
- [ ] 4개 이상의 AI 모델을 지원해야 한다
  - 테스트: OpenAI, Claude, Gemini, Cohere 각각으로 요청 성공
- [ ] Load balancing이 작동해야 한다
  - 테스트: 100개 요청이 설정된 비율대로 각 provider에 분산됨

---

## 논스코프 (Non-Goals)

### Phase 1에서 다루지 않는 것
1. **모바일 네이티브 앱 개발**
   - 이유: 웹 우선 접근, MVP는 반응형 웹으로 충분
   - 대안: Phase 3에서 고려

2. **실제 타로 리더와의 1:1 상담 매칭**
   - 이유: 비즈니스 모델 검증 필요, 운영 복잡도 증가
   - 대안: Phase 3에서 프리미엄 기능으로 추가

3. **커뮤니티 및 SNS 기능**
   - 이유: 핵심 가치 검증 우선, 리소스 분산 방지
   - 대안: Phase 2-3에서 점진적 추가

4. **결제 시스템 통합**
   - 이유: MVP는 무료 서비스로 검증
   - 대안: Phase 2에서 프리미엄 기능과 함께 추가

5. **다국어 지원**
   - 이유: 초기 타겟은 한국어 사용자
   - 대안: Phase 3에서 글로벌 확장 시 추가

6. **실시간 알림 시스템**
   - 이유: 필수 기능 아님, 복잡도 증가
   - 대안: Phase 2에서 이메일 알림부터 시작

7. **블록체인 기반 NFT 카드**
   - 이유: 범위 벗어남, 기술 복잡도 높음
   - 대안: 향후 별도 프로젝트로 검토

8. **음성 인식 기반 질문 입력**
   - 이유: MVP에 불필요한 복잡도
   - 대안: Phase 3에서 접근성 개선 시 고려

9. **오프라인 모드 지원**
   - 이유: AI 서버 연결 필수, 기술적 제약
   - 대안: 고려하지 않음

10. **타로 카드 판매/커머스 기능**
    - 이유: 핵심 비즈니스 모델 아님
    - 대안: 파트너십으로 간접 수익화 고려

---

## 제약 (Constraints)

### 성능 제약 (Performance)

#### 응답 시간
- **AI 응답 시간**: 5초 이내 (MVP), 3초 이내 (Phase 2)
- **페이지 로드 시간**: 2초 이내 (First Contentful Paint)
- **API 응답 시간**: 100ms 이내 (AI 호출 제외)

#### 확장성
- **동시 사용자**: 초기 1,000명, Phase 2까지 10,000명 지원
- **일일 리딩 횟수**: 최대 50,000건
- **데이터베이스 용량**: 초기 100GB, 자동 확장 가능

#### 가용성
- **Uptime**: 99% 이상 (MVP), 99.9% 이상 (Phase 2)
- **Recovery Time Objective (RTO)**: 4시간 이내
- **Recovery Point Objective (RPO)**: 1시간 이내

### 보안 제약 (Security)

#### 인증 및 권한
- **인증 방식**: JWT 기반 토큰 인증 필수
- **토큰 만료**: Access token 1시간, Refresh token 7일
- **패스워드**: 최소 8자, 영문/숫자/특수문자 조합 (bcrypt 해싱)
- **API Rate Limiting**: IP당 분당 60회, 사용자당 분당 30회

#### 데이터 보호
- **전송 암호화**: TLS 1.3 필수
- **저장 암호화**: 개인정보 AES-256 암호화
- **개인정보 보호**: GDPR/PIPA 준수
- **데이터 보관**: 사용자 요청 시 30일 이내 삭제 가능

#### API 보안
- **CORS**: 허용된 도메인만 접근 가능
- **SQL Injection 방지**: ORM Prepared Statement 사용
- **XSS 방지**: 입력값 sanitization 필수
- **CSRF 방지**: CSRF 토큰 검증

### 라이선스 제약 (License)

#### AI 서비스
- **OpenAI**: 상업적 이용 가능, 사용량 기반 과금
- **Anthropic Claude**: 상업적 이용 가능, 사용량 기반 과금
- **Google Gemini**: 상업적 이용 가능, 할당량 제한
- **제약사항**: AI 생성 콘텐츠에 대한 책임 명시 필요

#### 오픈소스 라이브러리
- **FastAPI**: MIT License (상업적 이용 가능)
- **DSPy**: MIT License (상업적 이용 가능)
- **React/Next.js**: MIT License (상업적 이용 가능)
- **제약사항**: MIT 라이선스 명시 및 저작권 고지 필수

#### 타로 카드 이미지
- **이미지 출처**: 저작권 없는 퍼블릭 도메인 또는 구매한 라이선스
- **제약사항**: 각 카드 이미지의 라이선스 개별 확인 필요
- **대안**: 자체 디자인 제작 또는 라이선스 구매

### 호환성 제약 (Compatibility)

#### 브라우저 지원
- **필수 지원**: Chrome 90+, Safari 14+, Firefox 88+, Edge 90+
- **모바일 브라우저**: iOS Safari 14+, Chrome Mobile 90+
- **제외**: Internet Explorer (지원 종료)

#### 디바이스 지원
- **데스크톱**: Windows 10+, macOS 10.15+, Linux (Ubuntu 20.04+)
- **모바일**: iOS 14+, Android 9+
- **화면 크기**: 320px ~ 2560px 반응형 지원

#### API 버전 관리
- **버전 정책**: Semantic Versioning (Major.Minor.Patch)
- **하위 호환성**: Minor 버전은 하위 호환 유지
- **Deprecated API**: 최소 6개월 사전 공지 후 제거

#### 데이터베이스
- **PostgreSQL**: 13.0 이상
- **Redis**: 6.0 이상
- **Vector DB**: Pinecone 최신 버전 또는 Weaviate 1.19+

### 비즈니스 제약 (Business)

#### 비용 제약
- **AI API 비용**: 월 $500 이내 (MVP), 리딩당 평균 비용 $0.05 이하
- **인프라 비용**: 월 $200 이내 (MVP)
- **총 운영 비용**: 월 $1,000 이내 (MVP)

#### 법적 제약
- **서비스 성격**: 엔터테인먼트 목적 명시 필수
- **면책 조항**: 의료/법률/재무 조언 아님을 명확히 고지
- **미성년자 보호**: 19세 미만 서비스 이용 제한 고려
- **점술 관련 규제**: 한국 법률 검토 및 준수

#### 운영 제약
- **개발 기간**: Phase 1 MVP는 3개월 이내
- **팀 규모**: 초기 1-2명 개발자로 운영 가능해야 함
- **유지보수**: 주당 최대 10시간 투입으로 유지 가능해야 함

---

## API 계약 (Contract) 요약

### Base URL
```
Production: https://api.tarot-ai.com/v1
Development: http://localhost:8000/v1
```

### 인증
```
Authorization: Bearer {access_token}
```

### 공통 응답 형식
```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "timestamp": "2025-10-18T12:00:00Z"
}
```

### 핵심 API 엔드포인트

#### 1. 리딩 요청
```http
POST /readings
Content-Type: application/json
Authorization: Bearer {token}

Request:
{
  "spread_type": "one_card" | "three_card" | "celtic_cross",
  "question": "string (optional)",
  "category": "general" | "love" | "career" | "finance" | "health",
  "user_context": {
    "birth_date": "1990-01-01",
    "zodiac": "aquarius"
  }
}

Response (200):
{
  "reading_id": "uuid",
  "spread_type": "one_card",
  "cards": [
    {
      "card_id": "major_0",
      "name": "The Fool",
      "position": "present",
      "orientation": "upright" | "reversed",
      "image_url": "string",
      "interpretation": "string"
    }
  ],
  "overall_reading": "string",
  "advice": "string",
  "created_at": "timestamp"
}
```

#### 2. 리딩 이력 조회
```http
GET /readings?limit=10&offset=0
Authorization: Bearer {token}

Response (200):
{
  "readings": [ ... ],
  "total": 42,
  "limit": 10,
  "offset": 0
}
```

#### 3. 특정 리딩 조회
```http
GET /readings/{reading_id}
Authorization: Bearer {token}

Response (200):
{
  "reading_id": "uuid",
  "spread_type": "three_card",
  "cards": [ ... ],
  "overall_reading": "string",
  "created_at": "timestamp"
}
```

#### 4. 피드백 제출
```http
POST /readings/{reading_id}/feedback
Content-Type: application/json
Authorization: Bearer {token}

Request:
{
  "rating": 5,  // 1-5
  "comment": "string (optional)",
  "helpful": true,
  "accurate": true
}

Response (200):
{
  "feedback_id": "uuid",
  "reading_id": "uuid",
  "rating": 5
}
```

#### 5. 카드 정보 조회
```http
GET /cards
Response (200):
{
  "cards": [
    {
      "card_id": "major_0",
      "name": "The Fool",
      "arcana": "major",
      "number": 0,
      "keywords": ["new beginnings", "spontaneity"],
      "upright_meaning": "string",
      "reversed_meaning": "string",
      "image_url": "string"
    }
  ]
}

GET /cards/{card_id}
Response (200):
{
  "card_id": "major_0",
  "name": "The Fool",
  ...
}
```

#### 6. 사용자 인증
```http
POST /auth/register
Content-Type: application/json

Request:
{
  "email": "user@example.com",
  "password": "string",
  "username": "string"
}

Response (201):
{
  "user_id": "uuid",
  "email": "user@example.com",
  "access_token": "string",
  "refresh_token": "string"
}

POST /auth/login
POST /auth/refresh
POST /auth/logout
```

#### 7. 사용자 프로필
```http
GET /users/me
PUT /users/me
DELETE /users/me
Authorization: Bearer {token}
```

#### 8. 통계 및 모니터링 (Admin)
```http
GET /admin/stats
Authorization: Bearer {admin_token}

Response (200):
{
  "total_readings": 1234,
  "total_users": 567,
  "avg_rating": 4.2,
  "readings_today": 89,
  "active_users_today": 45
}
```

### 에러 응답 형식
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Invalid spread type",
    "details": { ... }
  },
  "timestamp": "2025-10-18T12:00:00Z"
}
```

### 에러 코드
- `400 BAD_REQUEST`: 잘못된 요청 파라미터
- `401 UNAUTHORIZED`: 인증 실패
- `403 FORBIDDEN`: 권한 없음
- `404 NOT_FOUND`: 리소스 없음
- `429 RATE_LIMIT_EXCEEDED`: 요청 제한 초과
- `500 INTERNAL_SERVER_ERROR`: 서버 오류
- `503 SERVICE_UNAVAILABLE`: AI 서비스 일시 중단

---

## 용어집 (Glossary)

### 타로 관련 용어

#### 카드 구성
- **타로 카드 (Tarot Card)**: 78장으로 구성된 카드 덱
- **메이저 아르카나 (Major Arcana)**: 22장의 주요 카드 (0-21번)
- **마이너 아르카나 (Minor Arcana)**: 56장의 부수 카드 (4개 슈트 × 14장)
- **슈트 (Suit)**: 완드(Wands), 컵(Cups), 소드(Swords), 펜타클(Pentacles)

#### 리딩 용어
- **스프레드 (Spread)**: 카드를 배치하는 방식/배열법
- **포지션 (Position)**: 스프레드 내에서 각 카드가 놓이는 위치와 의미
- **오리엔테이션 (Orientation)**: 카드의 방향 (정방향/역방향)
- **정방향 (Upright)**: 카드가 정상 방향으로 나온 경우
- **역방향 (Reversed)**: 카드가 거꾸로 나온 경우
- **시그니피케이터 (Significator)**: 질문자를 상징하는 카드

#### 해석 용어
- **리딩 (Reading)**: 타로 카드 점을 보는 행위 전체
- **인터프리테이션 (Interpretation)**: 개별 카드의 의미 해석
- **오버롤 리딩 (Overall Reading)**: 전체 카드 조합의 종합 해석
- **인튜이션 (Intuition)**: 직관적 해석
- **컨텍스트 (Context)**: 질문과 상황 맥락

### 기술 용어

#### AI 관련
- **LLM (Large Language Model)**: 대규모 언어 모델
- **프롬프트 (Prompt)**: AI에게 전달하는 지시사항/입력
- **프롬프트 엔지니어링 (Prompt Engineering)**: 효과적인 프롬프트 작성 기법
- **컨텍스트 윈도우 (Context Window)**: AI가 한 번에 처리할 수 있는 텍스트 길이
- **토큰 (Token)**: AI가 처리하는 텍스트의 최소 단위
- **임베딩 (Embedding)**: 텍스트를 숫자 벡터로 변환한 것

#### DSPy 관련
- **DSPy**: Declarative Self-improving Python, 프롬프트 자동 최적화 프레임워크
- **GEPA**: Guided Exploration and Preference Alignment, 사용자 선호도 학습 방법론
- **옵티마이저 (Optimizer)**: 프롬프트 성능을 개선하는 알고리즘
- **메트릭 (Metric)**: 프롬프트 성능을 측정하는 지표

#### 시스템 용어
- **Provider**: AI 서비스 제공자 (OpenAI, Claude 등)
- **Fallback**: 주요 시스템 실패 시 대체 시스템으로 전환
- **Load Balancing**: 요청을 여러 서버에 분산
- **Rate Limiting**: 요청 횟수 제한
- **Caching**: 응답 결과 임시 저장

---

## 페르소나 (Persona)

### 1. 민지 (Minji) - 20대 직장인

**프로필**
- 나이: 27세
- 직업: 마케팅 담당자
- 거주지: 서울
- 기술 수준: 중상

**특징**
- 출퇴근길에 모바일로 타로 점을 자주 봄
- 연애, 직장 고민에 대한 조언을 구함
- 새로운 앱과 서비스 얼리어답터
- SNS에 타로 결과를 공유하는 것을 좋아함

**목표**
- 빠르고 간편하게 타로 점을 보고 싶음
- 신뢰할 수 있는 해석을 원함
- 예쁜 카드 디자인과 UI를 선호

**페인포인트**
- 기존 타로 앱들의 부정확하고 반복적인 해석에 실망
- 실제 타로 리더를 찾기는 비용과 시간이 많이 듦
- 과도한 광고와 유료화에 거부감

**사용 시나리오**
1. 출근길 지하철에서 "오늘의 운세" 원카드 리딩
2. 점심시간에 "새로운 프로젝트 결과"에 대한 쓰리카드 리딩
3. 주말에 친구들과 함께 연애운 점 보며 재미

### 2. 수현 (Soohyun) - 30대 주부

**프로필**
- 나이: 34세
- 직업: 전업주부, 블로거
- 거주지: 경기도
- 기술 수준: 중

**특징**
- 타로, 사주, 별자리에 관심이 많음
- 가족의 건강과 자녀 교육에 대한 고민
- 시간 여유가 있어 깊이 있는 리딩 선호
- 타로 커뮤니티 활동 적극적

**목표**
- 가족의 앞날에 대한 통찰을 얻고 싶음
- 켈틱 크로스 같은 상세한 스프레드를 원함
- 과거 리딩 기록을 보며 패턴 분석

**페인포인트**
- 매번 오프라인 타로샵을 방문하기 어려움
- 온라인 타로는 너무 간단하고 피상적
- 개인화된 해석이 부족함

**사용 시나리오**
1. 아이 교육 문제에 대한 켈틱 크로스 리딩
2. 남편의 이직에 대한 조언 구하기
3. 과거 리딩 기록을 돌아보며 일기처럼 활용

### 3. 재훈 (Jaehoon) - 대학생

**프로필**
- 나이: 22세
- 직업: 대학생 (심리학과)
- 거주지: 부산
- 기술 수준: 높음

**특징**
- 타로에 대한 학문적 관심
- 심리학과 타로의 연결고리 탐구
- 예산이 제한적 (무료 서비스 선호)
- 친구들에게 타로 점을 봐주는 취미

**목표**
- 타로 해석 방법을 배우고 싶음
- 다양한 스프레드 실험
- 타로의 심리학적 의미 탐구

**페인포인트**
- 타로 공부 비용이 부담스러움
- 전문 서적이나 강의는 너무 비쌈
- 연습할 수 있는 플랫폼 부족

**사용 시나리오**
1. 다양한 스프레드 종류 실험하며 학습
2. AI 해석과 자신의 해석 비교
3. 친구들에게 점 봐줄 때 참고 자료로 활용

### 4. 영희 (Younghee) - 50대 자영업자

**프로필**
- 나이: 53세
- 직업: 카페 운영
- 거주지: 인천
- 기술 수준: 낮음

**특징**
- 타로를 오래 믿어온 신뢰자
- 복잡한 기술보다 간단한 사용법 선호
- 사업 운세, 재물운에 관심
- 입소문과 지인 추천으로 서비스 선택

**목표**
- 사업 의사결정에 참고하고 싶음
- 간단하고 명확한 답변 원함
- 믿을 수 있는 해석

**페인포인트**
- 복잡한 인터페이스는 사용하기 어려움
- 작은 글씨와 복잡한 디자인 불편
- 젊은 층 위주의 서비스 디자인

**사용 시나리오**
1. 새로운 메뉴 출시 전 원카드 리딩
2. 월초에 이달의 사업운 체크
3. 중요한 계약 전 의사결정 참고

### 5. 지훈 (Jihoon) - 40대 IT 전문가

**프로필**
- 나이: 42세
- 직업: 개발자 / 스타트업 대표
- 거주지: 서울 강남
- 기술 수준: 매우 높음

**특징**
- 타로 자체보다 AI 기술에 관심
- 프리미엄 서비스 기꺼이 지불
- 데이터와 통계 기반 의사결정 선호
- 새로운 기술 트렌드에 민감

**목표**
- AI 타로의 정확도와 기술 수준 평가
- 비즈니스 의사결정 보조 도구로 활용
- 투자 가치 있는 서비스인지 판단

**페인포인트**
- 대부분의 타로 서비스는 너무 단순
- AI 품질이 낮은 서비스에 실망
- 개인정보 보안에 민감

**사용 시나리오**
1. 신규 사업 아이템에 대한 켈틱 크로스 리딩
2. API 품질과 응답 속도 테스트
3. 프리미엄 기능으로 업그레이드하여 심화 기능 사용

---

**문서 버전**: 1.0
**작성일**: 2025-10-18
**마지막 수정일**: 2025-10-18
**문서 소유자**: Project Team
**검토 주기**: 매 Phase 시작 전
