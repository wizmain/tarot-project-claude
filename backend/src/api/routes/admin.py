"""
Admin API Routes - 관리자 전용 피드백 통계 엔드포인트

DatabaseProvider 추상화를 사용하여 Firestore / PostgreSQL 양쪽을 지원합니다.
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query

from src.core.logging import get_logger
from src.api.dependencies.auth import get_current_superuser
from src.database.factory import get_database_provider
from src.database.provider import DatabaseProvider

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get(
    "/stats",
    summary="전체 피드백 통계 조회 (관리자 전용)",
    description="전체 피드백 통계를 조회합니다.",
)
async def get_global_statistics(
    current_user=Depends(get_current_superuser),
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
    current_user=Depends(get_current_superuser),
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
    current_user=Depends(get_current_superuser),
    db_provider: DatabaseProvider = Depends(get_database_provider),
):
    logger.info(
        "Spread type stats requested by user_id=%s",
        getattr(current_user, "id", None),
    )

    stats = await db_provider.get_feedback_statistics_by_spread_type()
    return stats
