# 🚀 타로 프로젝트 Firebase 배포 가이드

이 문서는 타로 프로젝트를 Firebase Hosting과 Google Cloud Run에 배포하는 전체 과정을 설명합니다.

## 📋 목차
1. [사전 준비](#사전-준비)
2. [환경 변수 설정](#환경-변수-설정)
3. [데이터베이스 설정](#데이터베이스-설정)
4. [배포 실행](#배포-실행)
5. [배포 후 확인](#배포-후-확인)
6. [문제 해결](#문제-해결)

---

## 사전 준비

### 1. 필수 도구 설치

```bash
# Firebase CLI 설치
npm install -g firebase-tools

# Google Cloud SDK 설치 (gcloud)
# https://cloud.google.com/sdk/docs/install 참조

# Docker 설치 (선택사항, 로컬 테스트용)
# https://www.docker.com/get-started 참조
```

### 2. Google Cloud / Firebase 프로젝트 생성

1. [Firebase Console](https://console.firebase.google.com/)에서 프로젝트 생성
2. [Google Cloud Console](https://console.cloud.google.com/)에서 결제 활성화
3. 필요한 API 활성화:
   ```bash
   gcloud services enable run.googleapis.com
   gcloud services enable cloudbuild.googleapis.com
   gcloud services enable sqladmin.googleapis.com
   ```

### 3. Firebase 인증 설정

Firebase Console에서:
1. Authentication → Sign-in method 활성화
   - Email/Password 활성화
   - Google 로그인 활성화
2. Firebase Admin SDK 서비스 계정 키 다운로드
   - Project Settings → Service accounts → Generate new private key

---

## 환경 변수 설정

### Backend (Cloud Run)

Cloud Run에 설정할 환경 변수:

```bash
# 데이터베이스 (Cloud SQL)
DATABASE_URL=postgresql://USER:PASSWORD@/DB_NAME?host=/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME

# JWT 인증
SECRET_KEY=your-very-secret-key-here-minimum-32-characters

# AI API Keys
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Firebase (선택사항, Firebase Auth 사용 시)
FIREBASE_CREDENTIALS_PATH=/app/firebase-credentials.json

# Auth Provider 설정
AUTH_PRIMARY_PROVIDER=custom_jwt
# 또는 firebase 사용 시: AUTH_PRIMARY_PROVIDER=firebase
```

#### Cloud Run 환경 변수 설정 방법

```bash
# 방법 1: gcloud 명령어로 직접 설정
gcloud run services update tarot-backend \
  --region=asia-northeast3 \
  --set-env-vars="SECRET_KEY=your-secret-key,DATABASE_URL=postgresql://..."

# 방법 2: Secret Manager 사용 (권장)
# Secret 생성
echo -n "sk-ant-..." | gcloud secrets create anthropic-api-key --data-file=-

# Cloud Run에서 Secret 사용
gcloud run services update tarot-backend \
  --region=asia-northeast3 \
  --set-secrets="ANTHROPIC_API_KEY=anthropic-api-key:latest"
```

### Frontend (Firebase Hosting)

Frontend 빌드 시 필요한 환경 변수:

```bash
# frontend/.env.production 파일 생성
NEXT_PUBLIC_API_URL=https://tarot-backend-xxx.run.app
NEXT_PUBLIC_FIREBASE_API_KEY=your-api-key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=123456789
NEXT_PUBLIC_FIREBASE_APP_ID=1:123:web:abc
```

---

## 데이터베이스 설정

### Cloud SQL (PostgreSQL) 생성

```bash
# 1. Cloud SQL 인스턴스 생성
gcloud sql instances create tarot-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=asia-northeast3 \
  --storage-type=SSD \
  --storage-size=10GB

# 2. 데이터베이스 생성
gcloud sql databases create tarot_db --instance=tarot-db

# 3. 사용자 생성
gcloud sql users create tarot_user \
  --instance=tarot-db \
  --password=STRONG_PASSWORD_HERE

# 4. Cloud Run에서 Cloud SQL 연결 설정
gcloud run services update tarot-backend \
  --region=asia-northeast3 \
  --add-cloudsql-instances=PROJECT_ID:REGION:tarot-db
```

### 데이터베이스 마이그레이션

```bash
# Cloud Run 컨테이너 내에서 실행
# 또는 Cloud SQL Proxy를 통해 로컬에서 실행

# 1. Cloud SQL Proxy 다운로드 및 실행
./cloud-sql-proxy PROJECT_ID:REGION:tarot-db

# 2. 마이그레이션 실행
cd backend
source venv/bin/activate
alembic upgrade head

# 3. 초기 데이터 시딩
python scripts/seed_cards.py
```

---

## 배포 실행

### 자동 배포 (권장)

```bash
# 프로젝트 루트에서 실행
export FIREBASE_PROJECT_ID=your-project-id
./deploy.sh
```

### 수동 배포

#### 1. Backend 배포

```bash
cd backend

# Cloud Run에 배포
gcloud run deploy tarot-backend \
  --source . \
  --platform managed \
  --region asia-northeast3 \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --timeout 300 \
  --set-env-vars="SECRET_KEY=...,DATABASE_URL=..."

# Backend URL 확인
gcloud run services describe tarot-backend \
  --region asia-northeast3 \
  --format 'value(status.url)'
```

#### 2. Frontend 배포

```bash
cd frontend

# 환경 변수 설정
export NEXT_PUBLIC_API_URL=https://tarot-backend-xxx.run.app

# 빌드
npm install
npm run build

# Firebase에 배포
cd ..
firebase deploy --only hosting
```

---

## 배포 후 확인

### 1. Frontend 확인

```bash
# 브라우저에서 열기
open https://your-project-id.web.app

# 또는 curl로 확인
curl https://your-project-id.web.app
```

### 2. Backend API 확인

```bash
# 헬스 체크
curl https://tarot-backend-xxx.run.app/health

# API 테스트
curl https://tarot-backend-xxx.run.app/api/v1/cards?page_size=5
```

### 3. 로그 확인

```bash
# Backend 로그
gcloud run services logs read tarot-backend \
  --region asia-northeast3 \
  --limit 50

# Frontend 로그 (Firebase Hosting)
firebase hosting:channel:list
```

---

## 문제 해결

### Backend가 시작되지 않는 경우

1. **로그 확인**
   ```bash
   gcloud run services logs read tarot-backend --region asia-northeast3 --limit 100
   ```

2. **환경 변수 확인**
   ```bash
   gcloud run services describe tarot-backend --region asia-northeast3 --format="value(spec.template.spec.containers[0].env)"
   ```

3. **Cloud SQL 연결 확인**
   ```bash
   gcloud run services describe tarot-backend --region asia-northeast3 --format="value(spec.template.metadata.annotations)"
   ```

### Frontend에서 Backend API 호출 실패

1. **CORS 설정 확인** (backend/main.py)
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://your-project-id.web.app"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

2. **API URL 확인**
   - Frontend 빌드 시 `NEXT_PUBLIC_API_URL`이 올바르게 설정되었는지 확인
   - 브라우저 개발자 도구에서 Network 탭 확인

### 데이터베이스 연결 오류

1. **Cloud SQL 인스턴스 상태 확인**
   ```bash
   gcloud sql instances describe tarot-db
   ```

2. **Cloud Run과 Cloud SQL 연결 확인**
   ```bash
   gcloud run services describe tarot-backend --region asia-northeast3
   ```

3. **DATABASE_URL 형식 확인**
   ```
   # Unix Socket (Cloud Run 권장)
   postgresql://USER:PASSWORD@/DB_NAME?host=/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME

   # TCP (로컬 테스트)
   postgresql://USER:PASSWORD@HOST:5432/DB_NAME
   ```

---

## 비용 최적화

### Cloud Run
- 최소 인스턴스 0으로 설정 (Cold Start 허용)
- CPU 할당: "Request 처리 시에만" 선택
- Memory: 512Mi로 시작 (필요시 증가)

### Cloud SQL
- 개발 환경: db-f1-micro (공유 CPU)
- 프로덕션: db-g1-small 이상
- 자동 백업 활성화
- 불필요한 복제본 비활성화

### Firebase Hosting
- 무료 티어 (10GB 스토리지, 360MB/일 전송)
- CDN 자동 캐싱

---

## 추가 리소스

- [Firebase Hosting 문서](https://firebase.google.com/docs/hosting)
- [Cloud Run 문서](https://cloud.google.com/run/docs)
- [Cloud SQL 문서](https://cloud.google.com/sql/docs)
- [Next.js Static Export](https://nextjs.org/docs/app/building-your-application/deploying/static-exports)

---

## 문의

배포 과정에서 문제가 발생하면 다음을 확인하세요:
1. 로그 확인
2. 환경 변수 확인
3. API 권한 확인
4. 결제 활성화 확인
