"""
Admin API Routes - 관리자 전용 엔드포인트

이 모듈의 목적:
- 관리자 대시보드 데이터 제공
- 피드백 통계 조회
- LLM 사용 통계 조회
- 시스템 설정 조회
- 캐시 무효화 (AI Provider 설정 변경 시)

DatabaseProvider 추상화를 사용하여 Firestore / PostgreSQL 양쪽을 지원합니다.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, Query

from src.core.logging import get_logger
from src.api.dependencies.auth import get_current_admin_user
from src.database.factory import get_database_provider
from src.database.provider import DatabaseProvider

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


class DashboardStats(BaseModel):
    """관리자 대시보드 통계"""
    total_users: int = Field(..., description="총 사용자 수")
    total_readings: int = Field(..., description="총 리딩 수")
    total_feedback: int = Field(..., description="총 피드백 수")
    avg_rating: float = Field(..., description="평균 평점")
    total_cost: float = Field(..., description="총 LLM 비용 (USD)")
    readings_today: int = Field(..., description="오늘 생성된 리딩 수")
    readings_this_week: int = Field(..., description="이번 주 생성된 리딩 수")
    readings_this_month: int = Field(..., description="이번 달 생성된 리딩 수")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_users": 150,
                "total_readings": 1250,
                "total_feedback": 320,
                "avg_rating": 4.5,
                "total_cost": 12.45,
                "readings_today": 25,
                "readings_this_week": 180,
                "readings_this_month": 650
            }
        }


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    current_admin=Depends(get_current_admin_user),
    db_provider: DatabaseProvider = Depends(get_database_provider),
):
    """
    관리자 대시보드 통계 조회 (관리자 전용)
    
    Returns:
        DashboardStats: 대시보드 통계 데이터
    """
    try:
        logger.info(
            "[Admin] Dashboard stats requested by %s",
            getattr(current_admin, 'email', 'unknown')
        )
        
        # Gather all statistics
        feedback_stats = await db_provider.get_feedback_statistics()
        
        # Get total users count
        total_users = await db_provider.get_total_users_count()
        
        # Get total readings count (all readings, not just with feedback)
        total_readings = await db_provider.get_total_readings_count_all()
        
        # Calculate time-based metrics
        now = datetime.utcnow()
        today_start = datetime(now.year, now.month, now.day)
        week_start = today_start - timedelta(days=now.weekday())
        month_start = datetime(now.year, now.month, 1)
        
        readings_today = await db_provider.get_readings_count_by_date_range(
            start_date=today_start,
            end_date=now
        )
        
        readings_this_week = await db_provider.get_readings_count_by_date_range(
            start_date=week_start,
            end_date=now
        )
        
        readings_this_month = await db_provider.get_readings_count_by_date_range(
            start_date=month_start,
            end_date=now
        )
        
        # Get total LLM cost
        total_cost = await db_provider.get_total_llm_cost()
        
        return DashboardStats(
            total_users=total_users,
            total_readings=total_readings,
            total_feedback=feedback_stats.get("total_feedback_count", 0),
            avg_rating=feedback_stats.get("average_rating", 0.0),
            total_cost=total_cost,
            readings_today=readings_today,
            readings_this_week=readings_this_week,
            readings_this_month=readings_this_month
        )
        
    except Exception as e:
        logger.error(f"[Admin] 대시보드 통계 조회 실패: {e}")
        from fastapi import HTTPException
        raise HTTPException(
            status_code=500,
            detail="대시보드 통계 조회 중 오류가 발생했습니다"
        )


@router.get(
    "/stats",
    summary="전체 피드백 통계 조회 (관리자 전용)",
    description="전체 피드백 통계를 조회합니다.",
)
async def get_global_statistics(
    current_user=Depends(get_current_admin_user),
    db_provider: DatabaseProvider = Depends(get_database_provider),
):
    logger.info("Admin stats requested by user_id=%s", getattr(current_user, "id", None))
    stats = await db_provider.get_feedback_statistics()
    logger.info("Global stats: %s", stats)
    return stats


@router.get(
    "/stats/period",
    summary="기간별 피드백 통계 조회 (관리자 전용)",
    description="특정 기간의 피드백 통계를 조회합니다.",
)
async def get_period_statistics(
    days: Optional[int] = Query(None, ge=1, le=365, description="최근 N일"),
    weeks: Optional[int] = Query(None, ge=1, le=52, description="최근 N주"),
    months: Optional[int] = Query(None, ge=1, le=12, description="최근 N개월"),
    current_user=Depends(get_current_admin_user),
    db_provider: DatabaseProvider = Depends(get_database_provider),
):
    logger.info(
        "Period stats requested by user_id=%s days=%s weeks=%s months=%s",
        getattr(current_user, "id", None),
        days,
        weeks,
        months,
    )

    end_date = datetime.utcnow()
    if days:
        start_date = end_date - timedelta(days=days)
    elif weeks:
        start_date = end_date - timedelta(weeks=weeks)
    elif months:
        start_date = end_date - timedelta(days=months * 30)
    else:
        start_date = end_date - timedelta(days=7)

    stats = await db_provider.get_feedback_statistics_by_date_range(
        start_date=start_date,
        end_date=end_date,
    )
    return stats


@router.get(
    "/stats/spread-types",
    summary="Spread Type별 피드백 통계 조회 (관리자 전용)",
    description="스프레드 타입별 피드백 통계를 조회합니다.",
)
async def get_spread_type_statistics(
    current_user=Depends(get_current_admin_user),
    db_provider: DatabaseProvider = Depends(get_database_provider),
):
    logger.info(
        "Spread type stats requested by user_id=%s",
        getattr(current_user, "id", None),
    )

    stats = await db_provider.get_feedback_statistics_by_spread_type()
    return stats


class CacheInvalidationRequest(BaseModel):
    """캐시 무효화 요청"""
    cache_types: List[str] = Field(
        default=["orchestrator"],
        description="Cache types to invalidate: orchestrator, rag, cards, all"
    )


class CacheInvalidationResponse(BaseModel):
    """캐시 무효화 응답"""
    success: bool
    invalidated: List[str]
    message: str


@router.post(
    "/cache/invalidate",
    response_model=CacheInvalidationResponse,
    summary="캐시 무효화 (관리자 전용)",
    description="AI Provider 설정 변경 시 캐시를 무효화하여 새 설정이 즉시 적용되도록 합니다."
)
async def invalidate_cache(
    request: CacheInvalidationRequest,
    current_user=Depends(get_current_admin_user),
    db_provider: DatabaseProvider = Depends(get_database_provider),
):
    """
    캐시를 무효화합니다. (관리자 전용)
    
    Args:
        request: 무효화할 캐시 타입 목록
            - orchestrator: AI Orchestrator 캐시 (Provider 설정 변경 시)
            - rag: RAG 캐시 (Retriever, ContextEnricher)
            - cards: 카드 데이터 캐시
            - all: 모든 캐시
    
    Returns:
        CacheInvalidationResponse: 무효화된 캐시 목록
    """
    logger.info(
        "[Admin] Cache invalidation requested by %s, types=%s",
        getattr(current_user, 'email', 'unknown'),
        request.cache_types
    )
    
    invalidated = []
    
    try:
        # Orchestrator 캐시 무효화
        if "orchestrator" in request.cache_types or "all" in request.cache_types:
            from src.api.routes.readings import invalidate_orchestrator_cache as inv_readings
            from src.api.routes.readings_stream import invalidate_orchestrator_cache as inv_stream
            
            inv_readings()
            inv_stream()
            invalidated.append("orchestrator")
            logger.info("[Admin] ✓ AI Orchestrator cache invalidated")
        
        # RAG 캐시 무효화
        if "rag" in request.cache_types or "all" in request.cache_types:
            from src.api.routes.readings import invalidate_rag_cache as inv_rag_readings
            from src.api.routes.readings_stream import invalidate_rag_cache as inv_rag_stream
            
            inv_rag_readings()
            inv_rag_stream()
            invalidated.append("rag")
            logger.info("[Admin] ✓ RAG cache invalidated")
        
        # Cards 캐시 무효화
        if "cards" in request.cache_types or "all" in request.cache_types:
            db_provider.invalidate_cards_cache()  # Synchronous method
            invalidated.append("cards")
            logger.info("[Admin] ✓ Cards cache invalidated")
        
        return CacheInvalidationResponse(
            success=True,
            invalidated=invalidated,
            message=f"Successfully invalidated: {', '.join(invalidated)}"
        )
        
    except Exception as e:
        logger.error(f"[Admin] Cache invalidation failed: {e}", exc_info=True)
        from fastapi import HTTPException
        raise HTTPException(
            status_code=500,
            detail=f"캐시 무효화 중 오류가 발생했습니다: {str(e)}"
        )
