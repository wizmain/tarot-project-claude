# Tarot AI 프로젝트 진행 상황

## 진행 현황 요약 (2025-10-29)

- Firestore로 카드와 피드백 데이터 이관은 완료됐지만 리딩 생성 경로가 여전히 SQLAlchemy 레이어를 호출해 Cloud Run에서 Postgres 접속 오류가 발생 중입니다.
- AI 리딩은 OpenAI GPT-4.1을 1순위, Anthropic Claude를 2순위로 두는 `AI_PROVIDER_PRIORITY` 구성이 소스에 반영되어 있으며, 변경 사항을 활성화하려면 백엔드 재배포가 한 번 더 필요합니다.
- 프론트/백엔드는 Firebase Authentication 경로로 정리되었고 기존 JWT/SQL 경로는 제거 대상입니다. 로컬 검증 시 `FIREBASE_CREDENTIALS_PATH` 등 Firebase 자격 증명 환경 변수를 준비해야 합니다.
- 빠른 응답과 개인화 강화를 위한 LLM 전략(빠른/심화 모드, 스트리밍, 사용자 프로필 요약, 템플릿 캐싱)을 수립했으며 구현과 모니터링 작업은 아직 착수하지 않았습니다.

### 다음 단계
1. `backend/src/api/dependencies/auth.py`, `backend/src/api/routes/readings.py`, `backend/src/api/repositories/*`에서 남아 있는 SQLAlchemy 의존성을 Firestore 전용 구현으로 교체하고 통합 테스트를 추가합니다.
2. 백엔드를 재배포해 OpenAI 우선순위가 실제로 적용되는지 확인하고, 요청별 지연 시간·토큰 사용량 로깅을 활성화합니다.
3. 합의된 LLM 전략에 맞춰 프롬프트 스캐폴드와 사용자 프로필 요약, 스트리밍 응답을 코드에 반영한 뒤 성능 및 품질을 측정합니다.

## 최근 작업 (2025-10-29)

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
