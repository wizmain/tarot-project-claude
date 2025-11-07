# Tarot AI 배포 가이드

## 환경 변수 설정

### 1. Backend URL 변경 시 업데이트 필요 파일

#### **프론트엔드 - Production URL 설정**

**파일: `frontend/src/config/env.ts`**
```typescript
const environmentConfigs: Record<Environment, Partial<EnvironmentConfig>> = {
  development: {
    apiUrl: 'http://localhost:8000',
  },
  production: {
    apiUrl: 'https://tarot-backend-iesbsif62q-du.a.run.app',  // ← 여기 수정
  },
  test: {
    apiUrl: 'http://localhost:8000',
  },
};
```

**파일: `frontend/.env.production`**
```bash
NEXT_PUBLIC_API_URL=https://tarot-backend-iesbsif62q-du.a.run.app  # ← 여기 수정
```

#### **프론트엔드 - Local Development URL 설정**

**파일: `frontend/.env.local`** (주의: 이 파일은 .env.production을 override 합니다)
```bash
# API Configuration
# 주의: NEXT_PUBLIC_API_URL을 여기에 설정하면 프로덕션 빌드에도 영향을 줍니다
# 로컬 개발은 config/env.ts의 development 설정을 사용하므로 이 라인은 주석 처리하세요

# NEXT_PUBLIC_API_URL=http://localhost:8000  # ← 반드시 주석 처리!

# Authentication Provider Selection
NEXT_PUBLIC_AUTH_PROVIDER=firebase
```

## 2. 배포 프로세스

### Backend URL이 변경되었을 때

1. **Backend 배포 후 새 URL 확인**
   ```bash
   gcloud run services describe tarot-backend \
     --region=asia-northeast3 \
     --project=tarot-aacbf \
     --format="value(status.url)"
   ```

2. **Frontend 환경 설정 파일 업데이트**
   - `frontend/src/config/env.ts` → production.apiUrl 수정
   - `frontend/.env.production` → NEXT_PUBLIC_API_URL 수정
   - `frontend/.env.local` → NEXT_PUBLIC_API_URL이 있다면 **반드시 제거 또는 주석 처리**

3. **Frontend 빌드 및 배포**
   ```bash
   cd frontend

   # 캐시 완전 삭제
   rm -rf .next out node_modules/.cache

   # 프로덕션 빌드
   npm run build

   # 빌드된 파일에 올바른 URL이 포함되었는지 확인
   grep -r "tarot-backend" out/_next/static/chunks/app/cards/ | head -1

   # Firebase 배포
   cd ..
   firebase deploy --only hosting --project tarot-aacbf
   ```

## 3. 현재 설정 (2025-10-31 기준)

### Backend
- **URL**: https://tarot-backend-iesbsif62q-du.a.run.app
- **Region**: asia-northeast3
- **Memory**: 2Gi
- **Project**: tarot-aacbf

### Frontend
- **URL**: https://tarot-aacbf.web.app
- **Project**: tarot-aacbf

### AI Settings
- **Primary Model**: gpt-4.1-nano
- **Provider Priority**: openai,claude
- **Language**: Prompt=EN, Response=KO

## 4. 트러블슈팅

### 문제: 프로덕션에서 localhost:8000에 연결하려고 함

**원인**: `.env.local` 파일에 `NEXT_PUBLIC_API_URL=http://localhost:8000`이 설정되어 있음

**해결**:
```bash
# frontend/.env.local 파일 수정
# NEXT_PUBLIC_API_URL 라인 제거 또는 주석 처리

# 캐시 삭제 및 재빌드
cd frontend
rm -rf .next out
npm run build
```

### 문제: 빌드 후에도 이전 URL을 참조

**원인**: Next.js 빌드 캐시

**해결**:
```bash
# 완전한 클린 빌드
rm -rf frontend/.next frontend/out frontend/node_modules/.cache
cd frontend && npm run build
```

### 문제: ERR_SSL_PROTOCOL_ERROR

**원인**:
1. HTTP URL을 HTTPS로 접근
2. 잘못된 백엔드 URL
3. 브라우저 캐시

**해결**:
1. env.ts와 .env.production의 URL이 `https://`로 시작하는지 확인
2. 브라우저 캐시 완전 삭제 (Cmd+Shift+Delete)
3. 시크릿 모드에서 테스트

## 5. 환경 변수 우선순위

Next.js 환경 변수 로딩 순서 (높은 우선순위부터):
1. `.env.local` (모든 환경에서 로드, git에 커밋하지 않음)
2. `.env.production` (production 빌드 시)
3. `.env.development` (development 시)
4. `.env` (기본값)

**중요**: `.env.local`은 `.env.production`을 override하므로, 프로덕션 빌드 시에도 주의 필요!

## 6. 배포 체크리스트

- [ ] Backend 새 URL 확인
- [ ] `frontend/src/config/env.ts` production.apiUrl 업데이트
- [ ] `frontend/.env.production` NEXT_PUBLIC_API_URL 업데이트
- [ ] `frontend/.env.local`에 NEXT_PUBLIC_API_URL이 없는지 확인
- [ ] 이전 빌드 캐시 삭제 (`rm -rf .next out`)
- [ ] 프로덕션 빌드 (`npm run build`)
- [ ] 빌드 파일에서 올바른 URL 확인
- [ ] Firebase 배포
- [ ] 프로덕션 환경에서 동작 확인

## 7. Quick Reference

### 현재 백엔드 URL 확인
```bash
gcloud run services describe tarot-backend \
  --region=asia-northeast3 \
  --project=tarot-aacbf \
  --format="value(status.url)"
```

### 환경 변수가 올바르게 설정되었는지 빌드 파일에서 확인
```bash
# localhost가 있는지 확인 (없어야 함)
grep -r "localhost:8000" frontend/out/_next/static/chunks/app/ | wc -l

# 프로덕션 URL이 있는지 확인 (있어야 함)
grep -r "tarot-backend-iesbsif62q" frontend/out/_next/static/chunks/app/ | wc -l
```

### Cloud Run 메모리 설정 확인/변경
```bash
# 현재 설정 확인
gcloud run services describe tarot-backend \
  --region=asia-northeast3 \
  --project=tarot-aacbf \
  --format="value(spec.template.spec.containers[0].resources.limits.memory)"

# 메모리 변경 (예: 2Gi)
gcloud run services update tarot-backend \
  --region=asia-northeast3 \
  --memory=2Gi \
  --project=tarot-aacbf
```
