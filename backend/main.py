"""
타로 AI 리딩 서비스 - 메인 애플리케이션

이 모듈의 목적:
- FastAPI 애플리케이션 생성 및 설정
- CORS 미들웨어 설정 (프론트엔드 연동)
- API 라우터 등록 (카드, 리딩 등)
- 전역 로깅 설정
- Health check 엔드포인트 제공

주요 엔드포인트:
- GET /: 루트 엔드포인트, 서비스 상태 확인
- GET /health: 헬스 체크, 데이터베이스 연결 확인
- GET /docs: Swagger UI (API 문서)
- GET /api/v1/cards: 타로 카드 API

애플리케이션 구조:
1. 로깅 설정 초기화
2. FastAPI 앱 생성
3. CORS 미들웨어 추가
4. API 라우터 등록
5. 헬스 체크 엔드포인트 정의

실행 방법:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

TASK-003: 백엔드 프로젝트 초기화 구현
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import settings
from src.core.logging import setup_logging, get_logger
from src.core.firebase_admin import initialize_firebase_admin
from src.api.routes import cards_router, readings_router, auth_router, feedback_router, admin_router

# 로깅 시스템 초기화
# 애플리케이션 시작 시 로그 설정을 먼저 수행하여
# 이후 모든 로그가 올바르게 기록되도록 합니다
setup_logging()
logger = get_logger(__name__)

# Firebase Admin SDK 초기화 (Firestore 사용을 위해)
try:
    initialize_firebase_admin()
except Exception as e:
    logger.warning(f"Firebase initialization failed (non-critical): {e}")

# FastAPI 애플리케이션 인스턴스 생성
# Swagger UI와 ReDoc 자동 문서화 활성화
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered Tarot card reading service with multi-provider support",
    docs_url="/docs",
    redoc_url="/redoc",
)

logger.info(f"FastAPI application created: {settings.APP_NAME} v{settings.APP_VERSION}")

# CORS(Cross-Origin Resource Sharing) 설정
# 프론트엔드(Next.js)에서 백엔드 API 호출을 허용하기 위함
# 개발 환경에서는 localhost:3000, 프로덕션에서는 실제 도메인 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # 허용할 오리진 목록
    allow_credentials=True,                   # 쿠키 전송 허용
    allow_methods=["*"],                      # 모든 HTTP 메서드 허용
    allow_headers=["*"],                      # 모든 HTTP 헤더 허용
)

# API 라우터 등록
# /api/v1/cards 경로로 카드 관련 API 엔드포인트 추가
app.include_router(cards_router)
logger.info("Card routes registered")

# /api/v1/readings 경로로 리딩 관련 API 엔드포인트 추가
app.include_router(readings_router)
logger.info("Reading routes registered")

# /api/v1/auth 경로로 인증 관련 API 엔드포인트 추가
app.include_router(auth_router)
logger.info("Auth routes registered")

# /api/v1/feedback 경로로 피드백 관련 API 엔드포인트 추가
app.include_router(feedback_router)
logger.info("Feedback routes registered")

# /api/v1/admin 경로로 관리자 관련 API 엔드포인트 추가
app.include_router(admin_router)
logger.info("Admin routes registered")


@app.get("/")
async def root():
    """
    루트 엔드포인트

    서비스가 정상 작동 중인지 확인하는 간단한 헬스 체크.
    프론트엔드나 모니터링 도구에서 서비스 가용성 확인에 사용.

    Returns:
        dict: 서비스 이름, 버전, 상태 정보
    """
    return {
        "message": "Welcome to Tarot AI Reading Service",
        "version": settings.APP_VERSION,
        "status": "healthy",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/api/v1/status")
async def api_status():
    """API status endpoint"""
    return {
        "api_version": "v1",
        "status": "operational",
        "features": {
            "cards": "available",
            "readings": "available",  # TASK-027: 원카드 리딩 구현 완료
            "auth": "available",  # 인증 및 회원가입 기능
            "feedback": "available",  # TASK-036: 피드백 제출 API 구현 완료
            "ai_providers": ["openai", "claude"],
            "auth_providers": ["custom_jwt", "firebase", "auth0"],
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
