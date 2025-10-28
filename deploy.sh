#!/bin/bash
set -e

echo "🚀 타로 프로젝트 Firebase 배포 시작..."

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 프로젝트 설정
PROJECT_ID="${FIREBASE_PROJECT_ID:-your-project-id}"
REGION="${CLOUD_RUN_REGION:-asia-northeast3}"
BACKEND_SERVICE="${BACKEND_SERVICE_NAME:-tarot-backend}"

echo -e "${YELLOW}📋 배포 설정:${NC}"
echo "  - Firebase Project: $PROJECT_ID"
echo "  - Cloud Run Region: $REGION"
echo "  - Backend Service: $BACKEND_SERVICE"
echo ""

# 1. 환경 변수 확인
echo -e "${YELLOW}🔍 환경 변수 확인 중...${NC}"
if [ -z "$FIREBASE_PROJECT_ID" ]; then
    echo -e "${RED}❌ FIREBASE_PROJECT_ID 환경 변수가 설정되지 않았습니다.${NC}"
    echo "  다음 명령어로 설정하세요:"
    echo "  export FIREBASE_PROJECT_ID=your-project-id"
    exit 1
fi

# 2. Backend를 Cloud Run에 배포
echo -e "${YELLOW}📦 Backend를 Cloud Run에 배포 중...${NC}"
cd backend

# gcloud가 설치되어 있는지 확인
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI가 설치되지 않았습니다.${NC}"
    echo "  https://cloud.google.com/sdk/docs/install 에서 설치하세요."
    exit 1
fi

# Cloud Run에 배포
gcloud run deploy $BACKEND_SERVICE \
  --source . \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --project $PROJECT_ID \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --timeout 300

# Backend URL 가져오기
BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE \
  --region $REGION \
  --project $PROJECT_ID \
  --format 'value(status.url)')

if [ -z "$BACKEND_URL" ]; then
    echo -e "${RED}❌ Backend URL을 가져올 수 없습니다.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Backend 배포 완료: $BACKEND_URL${NC}"
cd ..

# 3. Frontend 빌드
echo -e "${YELLOW}🏗️  Frontend 빌드 중...${NC}"
cd frontend

# Node.js가 설치되어 있는지 확인
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm이 설치되지 않았습니다.${NC}"
    echo "  https://nodejs.org 에서 Node.js를 설치하세요."
    exit 1
fi

# 환경 변수 설정
export NEXT_PUBLIC_API_URL=$BACKEND_URL

# 의존성 설치 (필요한 경우)
if [ ! -d "node_modules" ]; then
    echo "  📥 의존성 설치 중..."
    npm install
fi

# 프로덕션 빌드
npm run build

if [ ! -d "out" ]; then
    echo -e "${RED}❌ 빌드 결과물(out 디렉토리)을 찾을 수 없습니다.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Frontend 빌드 완료${NC}"
cd ..

# 4. Firebase Hosting에 배포
echo -e "${YELLOW}🌐 Firebase Hosting에 배포 중...${NC}"

# Firebase CLI가 설치되어 있는지 확인
if ! command -v firebase &> /dev/null; then
    echo -e "${RED}❌ Firebase CLI가 설치되지 않았습니다.${NC}"
    echo "  다음 명령어로 설치하세요:"
    echo "  npm install -g firebase-tools"
    exit 1
fi

# Firebase에 배포
firebase deploy --only hosting --project $PROJECT_ID

FRONTEND_URL="https://$PROJECT_ID.web.app"

echo ""
echo -e "${GREEN}✅ 배포 완료!${NC}"
echo ""
echo -e "${YELLOW}📍 배포된 URL:${NC}"
echo "  Frontend: $FRONTEND_URL"
echo "  Backend:  $BACKEND_URL"
echo ""
echo -e "${YELLOW}🔧 다음 단계:${NC}"
echo "  1. Frontend에서 Backend URL이 올바르게 연결되는지 확인"
echo "  2. 데이터베이스 마이그레이션 실행 (필요시)"
echo "  3. 환경 변수 설정 확인"
echo ""
