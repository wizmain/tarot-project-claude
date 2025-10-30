# Tarot AI 프로젝트 진행 상황

## 진행 현황 요약 (2025-10-29)

- Firestore로 카드·피드백 데이터는 마이그레이션됐지만 리딩 생성 경로는 여전히 SQLAlchemy 레이어를 거쳐 Cloud Run에서 PostgreSQL 접속 오류가 발생하고 있습니다.
- `AI_PROVIDER_PRIORITY=openai,anthropic`가 Cloud Run에 반영되어 OpenAI가 기본, Anthropic이 폴백으로 동작하며 재배포 완료 후 로그에서 모델명이 확인됩니다.
- LLM 호출 타임아웃을 180초로 확장하고, OpenAI/Anthropic 호출 시 모델·파라미터를 INFO 로그로 남기도록 수정했습니다.
- 프런트 카드 선택 UI는 “선택 완료” 버튼을 1회만 누를 수 있도록 개선되어 중복 요청을 방지하며, 로딩 중에는 자동으로 비활성화됩니다.
- 빠른 응답과 개인화를 위한 LLM 전략(빠른/심화 모드, 스트리밍, 사용자 프로필 요약, 템플릿 캐싱)은 문서화 완료 상태이며 구현 및 모니터링 작업은 아직 시작하지 않았습니다.

### 다음 단계
1. `backend/src/api/dependencies/auth.py`, `backend/src/api/routes/readings.py`, `backend/src/api/repositories/*`에서 남아 있는 SQLAlchemy 의존성을 Firestore 전용 구현으로 교체하고 통합 테스트를 추가합니다.
2. 리딩 생성 경로를 Firestore 전용 구현으로 교체한 뒤, Cloud Run에서 PostgreSQL 관련 오류가 사라졌는지 검증합니다.
3. LLM 호출 로그(모델·토큰·지연 시간)를 기반으로 SLA를 정의하고, 전략 문서에 있는 스트리밍/개인화 기능 구현을 착수합니다.

## 최근 작업 (2025-10-29)

### 작업: LLM 타임아웃 및 호출 로그 개선

- OpenAI/Anthropic Provider에 요청 직전 모델명·`max_tokens`·온도를 INFO 레벨로 기록하도록 로깅을 추가했습니다.
- `AI_PROVIDER_TIMEOUT`을 180초로 늘리고 Cloud Run 재배포를 완료해 장기 응답 지연 상황에서도 폴백 시나리오가 유지되도록 했습니다.
- 쓰리카드 리딩에서 응답이 중간에 잘리는 문제를 줄이기 위해 `max_tokens` 상한을 2,200으로 상향 조정했습니다.
- 카드 선택 컴포넌트는 “선택 완료” 클릭 후 인터랙션을 잠그고, 오류 시에만 자동 복구하도록 변경해 중복 요청을 방지합니다.
- 위 변경 사항을 포함한 백엔드/프런트엔드가 `tarot-backend-00037-jfj`, `tarot-aacbf.web.app`로 배포되었습니다.

### 문제: 원카드 리딩 페이지에서 "Load failed" 에러 발생 (HTTPS Mixed Content)

**증상:**
- URL: `https://tarot-frontend-414870328191.asia-northeast3.run.app/reading/one-card`
- 카드 선택 화면에서 "카드 로딩에 실패했습니다" 에러 메시지 표시
- 브라우저 콘솔에 Mixed Content 에러 발생:
  ```
  Mixed Content: The page at 'https://...' was loaded over HTTPS,
  but requested an insecure resource 'http://tarot-backend-...'.
  This request has been blocked; the content must be served over HTTPS.
  ```

**근본 원인:**
- 프론트엔드는 HTTPS로 제공되지만 번들된 JavaScript에 HTTP API URL이 하드코딩됨
- `NEXT_PUBLIC_API_URL` 환경 변수가 빌드 타임에 JavaScript 번들에 임베딩됨
- 브라우저의 Mixed Content 정책으로 인해 HTTP 요청 차단
- Next.js의 강력한 빌드 캐싱으로 인해 코드 변경사항이 새로운 번들로 반영되지 않음

### 시도한 해결 방법들

#### 1차 시도: 환경 변수 및 빌드 설정 확인
- `cloudbuild.yaml`: HTTPS URL 설정 확인 ✅
- `Dockerfile`: 환경 변수 전달 확인 ✅
- `next.config.js`: generateBuildId 추가 (캐시 버스팅 시도)
- **결과:** 실패 - JavaScript 청크 해시가 변경되지 않음

#### 2차 시도: constants.ts 및 api.ts 수정
- `src/lib/constants.ts`: getApiBaseUrl() 함수 추가, HTTPS 강제 변환 로직
- `src/lib/api.ts`: 동일한 getApiBaseUrl() 함수 추가
- **결과:** 실패 - 배포된 JavaScript에 반영되지 않음

#### 3차 시도: CardSelector 컴포넌트 직접 수정
- `src/components/CardSelector.tsx`: API_BASE_URL에 .replace() 추가
  ```typescript
  const apiUrl = API_BASE_URL.replace('http://', 'https://');
  ```
- **결과:** 실패 - JavaScript 청크 해시가 `292-4b0f015ccc1b6204.js`로 동일

#### 4차 시도: API_BASE_URL import 제거
- CardSelector에서 `API_BASE_URL` import 완전 제거
- 환경 감지 로직을 컴포넌트 내부에서 직접 구현
  ```typescript
  const isProduction = typeof window !== 'undefined' &&
                      (window.location.hostname.includes('run.app') ||
                       window.location.hostname.includes('vercel.app'));
  const apiUrl = isProduction
    ? 'https://tarot-backend-414870328191.asia-northeast3.run.app'
    : 'http://localhost:8000';
  ```
- **결과:** 실패 - JavaScript 청크 해시 여전히 동일 (`292-4b0f015ccc1b6204.js`)

#### 5차 시도: 코드 구조 대폭 변경
- console.log 추가 (디버깅 및 코드 크기 변경)
- 변수명 변경 (`apiUrl` → `BACKEND_URL`)
- 추가 변수 선언 (`isCloudRun`, `isVercel`)
- 주석 추가
```typescript
// FIXED: Always use HTTPS in production environment
const isCloudRun = typeof window !== 'undefined' &&
                  window.location.hostname.includes('run.app');
const isVercel = typeof window !== 'undefined' &&
                window.location.hostname.includes('vercel.app');
const isProduction = isCloudRun || isVercel;

const BACKEND_URL = isProduction
  ? 'https://tarot-backend-414870328191.asia-northeast3.run.app'
  : 'http://localhost:8000';

console.log('[CardSelector] Environment check:', {
  isProduction, isCloudRun,
  hostname: typeof window !== 'undefined' ? window.location.hostname : 'SSR',
  BACKEND_URL
});
```
- **결과:** 실패 - JavaScript 청크 해시 **여전히 동일** (`941-fe90a16880c243c3.js`)
- **빌드 ID:** 3666d071, 리비전: tarot-frontend-00016

#### 6차 시도: 완전히 단순화된 하드코딩 방식
- **발견:** 리비전 00016 배포 후에도 JavaScript 청크 `292-4b0f015ccc1b6204.js`가 여전히 HTTP URL 포함
- **검증:** `curl` 명령으로 확인 - 배포된 JS 파일에 `run.app` 문자열 없음
- **결론:** Next.js가 코드 변경을 인식하지 못하고 이전 번들 재사용

**새로운 접근 방식:**
- 모든 환경 감지 로직 완전히 제거
- HTTPS URL을 직접 하드코딩
- **결과:** 실패 - 여전히 이전 청크 해시 유지

#### 7차 시도: 중앙화된 환경 설정 시스템 구축 ✅ **성공!**

**문제 재분석:**
- Next.js의 deterministic chunk hashing이 파일 내용 기반으로 작동
- 의존성 파일(constants.ts, api.ts)이 변경되지 않으면 dependent 파일의 청크도 변경 안 됨
- Docker 빌드 캐시와 Next.js 빌드 캐시가 중복으로 작동

**해결 방법:**
1. **중앙화된 환경 설정 생성** (`frontend/src/config/env.ts`)
   - 모든 환경 변수를 한곳에서 관리
   - 프로덕션 환경에서 자동으로 HTTP → HTTPS 변환
   - 빌드 타임 검증 로직 추가
   ```typescript
   export const getApiBaseUrl = (): string => {
     const envVar = process.env.NEXT_PUBLIC_API_URL;
     if (envVar) {
       return getCurrentEnvironment() === 'production'
         ? envVar.replace('http://', 'https://')
         : envVar;
     }
     // ... fallback logic
   };
   ```

2. **Dockerfile 캐시 무효화 강화**
   - `.next`, `.next/cache`, `node_modules/.cache` 삭제
   - `npm cache clean --force` 실행
   - 소스 파일 타임스탬프 업데이트하여 새로운 content hash 강제 생성
   ```dockerfile
   RUN rm -rf .next .next/cache node_modules/.cache
   RUN npm cache clean --force
   RUN npm run build
   ```

3. **소스 코드 수정으로 새로운 번들 강제 생성**
   - `src/config/env.ts`: 빌드 타임스탬프 주석 추가
   - `src/lib/api.ts`: 헤더 주석 업데이트
   - 파일 내용 변경으로 webpack chunk hash 변경 유도

**배포 결과:**
- **리비전:** tarot-frontend-00022-6cg
- **Docker Image SHA:** `5daea252c2726dea74cd7aced4386a3c2c80e071ba39331b1df1a12b887a80ba`
- **새로운 JavaScript 번들:**
  - `362-a297d217a595bbd0.js` (이전: `362-1099f3c10a618b79.js`) ✅
  - `292-a3eafd9725e972cc.js` (이전: `292-4b0f015ccc1b6204.js`) ✅
- **검증:** curl로 확인 시 새 번들이 HTTPS URL만 포함 ✅

**상태:** **배포 완료 - 사용자 테스트 대기 중**

### 기술적 발견 사항

1. **Next.js 빌드 캐싱 문제**
   - Next.js가 파일 내용을 기반으로 JavaScript 청크 해시를 생성
   - 의미 있는 코드 변경이 없으면 같은 해시 사용
   - `--no-cache` Docker 플래그는 Docker 레이어 캐시만 무효화

2. **JavaScript 청크 구조**
   - `chunks/941-fe90a16880c243c3.js` (31.7 kB): shared chunk, API utilities 포함
   - `chunks/292-4b0f015ccc1b6204.js`: CardSelector 컴포넌트 포함
   - CardSelector 수정이 `292` 청크를 변경해야 함

3. **환경 변수 임베딩**
   - `NEXT_PUBLIC_*` 환경 변수는 빌드 타임에 JavaScript 번들에 임베딩됨
   - 런타임에 환경 변수를 변경해도 이미 빌드된 JavaScript에는 영향 없음

4. **Cloud Run 배포**
   - 리비전 tarot-frontend-00013, 00014, 00015 배포됨
   - 각 배포마다 새로운 Docker 이미지 생성
   - 하지만 Next.js 빌드 결과는 동일한 청크 해시 유지

### 배포 이력

| 리비전 | 빌드 ID | 변경 사항 | JavaScript 청크 해시 | 결과 |
|--------|---------|-----------|---------------------|------|
| 00013 | f96cd9b4 | constants.ts, api.ts에 HTTPS 강제 | 941-fe90a16880c243c3 | 실패 |
| 00014 | 9bd363e4 | CardSelector에 .replace() 추가 | 941-fe90a16880c243c3 | 실패 |
| 00015 | bcc33b07 | API_BASE_URL import 제거 | 941-fe90a16880c243c3 | 실패 |
| 00016 | (진행중) | 코드 구조 대폭 변경, console.log 추가 | (대기 중) | 테스트 대기 |

### 사용자 액션 필요 ⚠️

**배포 완료 - 실제 브라우저 테스트 필요:**

배포는 성공적으로 완료되었으나, Playwright 브라우저의 강력한 캐시로 인해 자동 테스트로는 검증이 어렵습니다.
서버는 새로운 JavaScript 번들(HTTPS URL 포함)을 정상적으로 제공하고 있으므로,
실제 사용자 브라우저에서 테스트가 필요합니다.

**테스트 방법:**
1. **시크릿/프라이빗 브라우징 창** 열기 (캐시 없이 시작)
2. URL 접속: `https://tarot-frontend-414870328191.asia-northeast3.run.app/reading/one-card`
3. **개발자 도구 열기:** Ctrl+Shift+I (Windows/Linux) 또는 Cmd+Option+I (Mac)
4. **Console 탭** 확인
5. "Mixed Content" 오류가 **없으면 성공** ✅

**캐시 문제가 있는 경우:**
- 브라우저 설정에서 "캐시된 이미지 및 파일" 삭제 (Ctrl+Shift+Delete)
- Hard Refresh: Ctrl+Shift+R (Windows/Linux) 또는 Cmd+Shift+R (Mac)

**예상 결과:**
- ✅ 카드가 정상적으로 로드됨
- ✅ Mixed Content 오류 없음
- ✅ HTTPS 연결로 백엔드 API 호출 성공

## 파일 변경 이력

### 수정된 파일

1. **frontend/src/components/CardSelector.tsx**
   - `API_BASE_URL` import 제거
   - 런타임 환경 감지 로직 추가
   - Cloud Run/Vercel 환경에서 하드코딩된 HTTPS URL 사용
   - 디버깅을 위한 console.log 추가

2. **frontend/src/lib/constants.ts**
   - `getApiBaseUrl()` 함수 추가
   - production 환경에서 HTTP를 HTTPS로 강제 변환

3. **frontend/src/lib/api.ts**
   - `getApiBaseUrl()` 함수 추가
   - production 환경에서 HTTP를 HTTPS로 강제 변환

4. **frontend/next.config.js**
   - `generateBuildId` 함수 추가 (timestamp 기반 unique ID)

5. **frontend/package.json**
   - 버전 0.1.0 → 0.1.1

### 배포 설정

- **Backend URL**: `https://tarot-backend-414870328191.asia-northeast3.run.app`
- **Frontend URL**: `https://tarot-frontend-414870328191.asia-northeast3.run.app`
- **Region**: asia-northeast3
- **Platform**: Google Cloud Run

## 주요 교훈

1. **Next.js는 매우 공격적으로 빌드를 캐시함**
   - 파일 내용이 실질적으로 변경되지 않으면 같은 해시 사용
   - 단순히 주석이나 포맷을 바꾸는 것만으로는 부족

2. **환경 변수는 빌드 타임에 결정됨**
   - `process.env.NEXT_PUBLIC_*`는 번들링 시 값이 하드코딩됨
   - 배포 후 환경 변수를 변경해도 소용없음

3. **브라우저의 Mixed Content 정책은 엄격함**
   - HTTPS 페이지에서 HTTP 리소스 로딩 완전 차단
   - 개발자 도구에서도 우회 불가

4. **디버깅을 위해 console.log는 매우 유용**
   - 실제 배포 환경에서 어떤 값이 사용되는지 확인 가능
   - production 빌드에서도 일시적으로 활성화 필요

## 참고 자료

- [Next.js Environment Variables](https://nextjs.org/docs/app/building-your-application/configuring/environment-variables)
- [MDN: Mixed Content](https://developer.mozilla.org/en-US/docs/Web/Security/Mixed_content)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)

---

## LLM 사용 기록 추적 기능 구현 (2025-10-30)

### 완료된 작업 ✅

리딩마다 사용된 LLM 모델의 메트릭(토큰, 비용, 시간)을 자동으로 추적하고 저장하는 기능이 구현되었습니다.

#### Step 1: 데이터 모델 추가
- **파일:** `backend/src/database/provider.py`
- `LLMUsageLog` 클래스 추가 (80줄)
  - id, reading_id, provider, model
  - prompt_tokens, completion_tokens, total_tokens
  - estimated_cost, latency_seconds, purpose
- `Reading` 클래스에 `llm_usage` 필드 추가

#### Step 2: PostgreSQL 마이그레이션
- **파일:** `backend/alembic/versions/d298ff1ee6ff_add_llm_usage_logs_table.py`
- `llm_usage_logs` 테이블 생성
- 인덱스: reading_id, created_at, provider
- 외래 키: readings(id) ON DELETE CASCADE

#### Step 3: Database Provider 인터페이스 확장
- **파일:** `backend/src/database/provider.py`, `backend/src/database/firestore_provider.py`
- `create_llm_usage_log()` 메서드 추가
- `get_llm_usage_logs()` 메서드 추가
- Firestore: readings 문서의 llm_usage 배열로 저장

#### Step 4: AI Orchestrator 메트릭 수집
- **파일:** `backend/src/ai/models.py`, `backend/src/ai/orchestrator.py`
- `OrchestratorResponse` 모델 추가
  - response: 성공한 응답
  - all_attempts: 모든 시도 (primary, fallback, retry)
  - total_cost: 총 비용
- `AIOrchestrator.generate()` 반환 타입 변경

#### Step 5: Reading API 로직 수정
- **파일:** `backend/src/api/routes/readings.py`
- 리딩 생성 후 자동으로 LLM 로그 저장
- 모든 시도(성공/실패)를 purpose 태그와 함께 기록
- 로그에 총 비용 및 시도 횟수 출력

#### Step 6: API 응답에 LLM 메트릭 포함
- **파일:** `backend/src/schemas/reading.py`, `backend/src/api/routes/readings.py`
- `LLMUsageResponse` 스키마 추가
- `ReadingResponse`에 `llm_usage` 필드 추가
- `_build_reading_response()` 함수에서 LLM 로그 자동 포함

### 추적되는 정보

| 항목 | 타입 | 설명 |
|------|------|------|
| provider | string | AI 제공자 (openai, anthropic) |
| model | string | 사용된 모델명 |
| prompt_tokens | integer | 입력 토큰 수 |
| completion_tokens | integer | 출력 토큰 수 |
| total_tokens | integer | 총 토큰 수 |
| estimated_cost | float | 예상 비용 (USD) |
| latency_seconds | float | 소요 시간 (초) |
| purpose | string | 호출 목적 (main_reading, retry, fallback) |

### API 응답 예시

```json
{
  "id": "reading_xyz",
  "question": "새로운 프로젝트를 시작해야 할까요?",
  "cards": [...],
  "llm_usage": [
    {
      "id": "log_abc123",
      "provider": "openai",
      "model": "gpt-4-turbo-preview",
      "prompt_tokens": 450,
      "completion_tokens": 800,
      "total_tokens": 1250,
      "estimated_cost": 0.0325,
      "latency_seconds": 3.25,
      "purpose": "main_reading"
    }
  ]
}
```

### 변경된 파일 목록

1. `backend/src/database/provider.py` (+80줄)
2. `backend/src/database/firestore_provider.py` (+73줄)
3. `backend/src/schemas/reading.py` (+38줄)
4. `backend/src/ai/models.py` (+38줄)
5. `backend/src/ai/orchestrator.py` (~20줄 수정)
6. `backend/src/api/routes/readings.py` (~35줄 수정)
7. `backend/alembic/versions/d298ff1ee6ff_add_llm_usage_logs_table.py` (신규)

---

## LLM 사용 기록 대시보드 계획 (2025-10-30)

### 개요

관리자가 LLM 사용 현황을 모니터링하고 비용을 관리할 수 있는 대시보드 화면 구현 계획입니다.

### 🎯 주요 목표

1. **비용 모니터링**: 일별/월별 LLM 사용 비용 추적
2. **성능 분석**: 응답 시간, 토큰 사용량, 모델별 성능
3. **사용 패턴**: 시간대별, 모델별 사용 현황
4. **예산 관리**: 예상 월간 비용, 경고 알림

### 📱 화면 구성

#### 메인 대시보드 (/dashboard)

**상단 요약 카드 (3개)**
- 💰 Total Cost: 총 비용 ($12.45) + 변화율 (↑ 15%)
- 📈 Total Calls: 총 호출 수 (1,234) + 변화율 (↑ 8%)
- ⚡ Avg Latency: 평균 응답시간 (3.2s) + 변화율 (↓ 5%)

**차트 섹션**
1. **Daily Cost Trend**: 최근 30일 비용 추세 (Line Chart)
2. **Model Usage**: 모델별 사용 비율 (Pie Chart)
3. **Latency Distribution**: 응답시간 분포 (Histogram)

**테이블 섹션**
- **Recent LLM Calls**: 최근 호출 기록
  - 컬럼: Time, Model, Cost, Tokens, Latency, Status
  - 페이지네이션 지원
  - 필터: 날짜 범위, 모델, 비용 범위

### 🔌 백엔드 API 엔드포인트

#### 1. 요약 통계
```
GET /api/v1/analytics/llm-usage/summary
- 총 비용, 호출 수, 평균 응답시간
- 이전 기간 대비 변화율
- 모델별 집계
```

#### 2. 일별 추세
```
GET /api/v1/analytics/llm-usage/daily-trend?start_date=2025-10-01&end_date=2025-10-30
- 기간별 일일 통계
- 차트 렌더링용 데이터
```

#### 3. 모델별 분석
```
GET /api/v1/analytics/llm-usage/model-breakdown
- 모델별 상세 통계
- 호출 수, 비용, 토큰, 성공률
```

#### 4. 최근 기록
```
GET /api/v1/analytics/llm-usage/recent?page=1&page_size=20
- 페이지네이션 지원
- 필터링 가능
```

#### 5. CSV 내보내기
```
GET /api/v1/analytics/llm-usage/export?start_date=2025-10-01&end_date=2025-10-30
- CSV 파일 다운로드
- 모든 필드 포함
```

### 🎨 프론트엔드 컴포넌트 구조

```
frontend/src/
├── app/
│   └── dashboard/
│       └── page.tsx                    # 대시보드 메인 페이지
├── components/
│   └── dashboard/
│       ├── DashboardLayout.tsx         # 레이아웃
│       ├── SummaryCards.tsx            # 요약 카드
│       ├── DailyCostChart.tsx          # 일별 비용 차트
│       ├── ModelUsagePieChart.tsx      # 모델 사용 비율
│       ├── LatencyHistogram.tsx        # 응답시간 분포
│       ├── RecentCallsTable.tsx        # 최근 호출 테이블
│       ├── DateRangeFilter.tsx         # 날짜 필터
│       └── ExportButton.tsx            # CSV 내보내기
├── hooks/
│   └── useLLMAnalytics.ts              # 데이터 fetching
└── types/
    └── analytics.ts                    # TypeScript 타입
```

### 📊 데이터 시각화 라이브러리

**선택: Recharts + shadcn/ui**

**이유:**
- ✅ Next.js/React 완벽 호환
- ✅ TypeScript 지원
- ✅ 기존 shadcn/ui 디자인 시스템과 조화
- ✅ Responsive 디자인
- ✅ SSR 지원

**설치:**
```bash
npm install recharts
npm install date-fns  # 날짜 포맷팅
```

### 🚀 구현 단계

#### Phase 1: 기본 대시보드 (1-2일)
- [ ] Backend: API 엔드포인트 3개
  - `/llm-usage/summary`
  - `/llm-usage/daily-trend`
  - `/llm-usage/recent`
- [ ] Frontend: 기본 페이지
  - Summary Cards
  - Daily Cost Chart
  - Recent Calls Table

#### Phase 2: 고급 분석 (1일)
- [ ] Backend: 모델별 분석 API
- [ ] Frontend: 추가 차트
  - Pie Chart (모델 비율)
  - Histogram (응답시간 분포)
  - 필터 기능

#### Phase 3: 추가 기능 (1일)
- [ ] CSV Export
- [ ] 날짜 범위 선택
- [ ] 실시간 업데이트 (WebSocket)
- [ ] 예산 알림 설정

### 📈 데이터 집계 최적화

#### Firestore 집계 전략
```javascript
// 옵션 1: 클라이언트 집계 (소규모)
const readings = await db.collection('readings').get();
const stats = readings.docs.reduce((acc, doc) => {
  const llm_usage = doc.data().llm_usage || [];
  llm_usage.forEach(log => {
    acc.totalCost += log.estimated_cost;
    acc.totalCalls += 1;
  });
  return acc;
}, { totalCost: 0, totalCalls: 0 });

// 옵션 2: Cloud Functions 집계 (대규모 권장)
// 매일 자동 집계하여 analytics 컬렉션에 저장
```

#### PostgreSQL 집계 쿼리
```sql
-- View 생성으로 성능 향상
CREATE VIEW llm_usage_daily_stats AS
SELECT
  DATE(created_at) as date,
  provider,
  model,
  COUNT(*) as total_calls,
  SUM(estimated_cost) as total_cost,
  AVG(latency_seconds) as avg_latency,
  SUM(total_tokens) as total_tokens
FROM llm_usage_logs
GROUP BY DATE(created_at), provider, model;

-- 인덱스
CREATE INDEX idx_llm_usage_created_at_provider
ON llm_usage_logs(created_at, provider);
```

### 🔐 권한 관리

```python
# 관리자 전용 엔드포인트
@router.get("/analytics/llm-usage/*")
async def get_analytics(
    current_user=Depends(get_current_admin_user),  # 관리자만
):
    if current_user.role not in [UserRole.ADMIN, UserRole.ANALYST]:
        raise HTTPException(403, "Admin access required")
    return data
```

### ⏱️ 예상 구현 시간

| 단계 | 백엔드 | 프론트엔드 | 총계 |
|------|--------|-----------|------|
| Phase 1 (기본) | 4시간 | 6시간 | 10시간 |
| Phase 2 (고급) | 3시간 | 4시간 | 7시간 |
| Phase 3 (추가) | 2시간 | 3시간 | 5시간 |
| **총계** | **9시간** | **13시간** | **22시간** |

### 📝 다음 단계

1. **Phase 1부터 구현** - 기본 대시보드 먼저
2. **API 먼저 구현** - 백엔드부터 완성
3. **UI 먼저 구현** - 목 데이터로 화면 구성
4. **계획 검토** - 추가 요구사항 확인

### 활용 방안

#### 1. 비용 모니터링
```sql
-- PostgreSQL: 일별 비용 집계
SELECT
  DATE(created_at) as date,
  COUNT(*) as total_requests,
  SUM(estimated_cost) as daily_cost
FROM llm_usage_logs
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

#### 2. 모델 성능 분석
```sql
-- 모델별 평균 응답 시간
SELECT
  model,
  AVG(latency_seconds) as avg_latency,
  AVG(estimated_cost) as avg_cost
FROM llm_usage_logs
GROUP BY model;
```

#### 3. 실패율 추적
```python
# 재시도가 필요했던 리딩 비율
retry_count = llm_usage_logs.filter(purpose="retry").count()
total_count = llm_usage_logs.count()
retry_rate = retry_count / total_count
```

### 상태

- **LLM 추적 기능**: ✅ 구현 완료 (배포 대기)
- **대시보드**: 📋 계획 수립 완료 (구현 대기)
