"""
Admin API Routes - 관리자 전용 API 엔드포인트

이 모듈의 목적:
- 관리자 전용 통계 및 관리 기능 제공
- 전체 시스템 모니터링 및 분석 데이터 제공
- is_superuser 권한 검증 필수

주요 엔드포인트:
- GET /api/v1/admin/stats: 전체 피드백 통계
- GET /api/v1/admin/stats/period: 기간별 피드백 통계
- GET /api/v1/admin/stats/spread-types: Spread Type별 통계

구현 사항:
- get_current_superuser dependency 사용 (관리자 권한 필수)
- 전체 통계 및 분석 데이터 제공
- 일별/주별/월별 통계 지원

TASK 참조:
- TASK-037: 피드백 통계 API

사용 예시:
    # 전체 통계 조회
    GET /api/v1/admin/stats
    Headers: Authorization: Bearer <admin_token>

    # 최근 7일간 통계
    GET /api/v1/admin/stats/period?days=7

    # Spread Type별 통계
    GET /api/v1/admin/stats/spread-types
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.logging import get_logger
from src.api.repositories.feedback_repository import FeedbackRepository
from src.api.dependencies.auth import get_current_superuser
from src.models import User

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get(
    "/stats",
    summary="전체 피드백 통계 조회 (관리자 전용)",
    description="""
    전체 시스템의 피드백 통계를 조회합니다.

    - **관리자 권한 필수**: is_superuser=True인 사용자만 접근 가능
    - **전체 통계**: 전체 평균 별점, 총 피드백 수, helpful/accurate 비율
    - **실시간 데이터**: 데이터베이스에서 실시간 집계

    시스템 품질 모니터링 및 개선 지표 분석에 활용됩니다.
    """
)
def get_global_statistics(
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    전체 피드백 통계 조회

    Args:
        current_user: 관리자 사용자 (get_current_superuser)
        db: 데이터베이스 세션

    Returns:
        dict: 전체 통계 정보
            - total_feedback_count: 총 피드백 수
            - average_rating: 전체 평균 별점
            - helpful_count: helpful True 개수
            - accurate_count: accurate True 개수
            - helpful_rate: helpful 비율 (%)
            - accurate_rate: accurate 비율 (%)

    Raises:
        403: 관리자 권한 없음
    """
    logger.info(f"Admin stats requested by user_id={current_user.id}")

    stats = FeedbackRepository.get_global_statistics(db)

    logger.info(f"Global stats: {stats}")

    return stats


@router.get(
    "/stats/period",
    summary="기간별 피드백 통계 조회 (관리자 전용)",
    description="""
    특정 기간의 피드백 통계를 조회합니다.

    - **관리자 권한 필수**: is_superuser=True인 사용자만 접근 가능
    - **기간 필터링**: days, weeks, months 파라미터로 조회 기간 설정
    - **일별/주별/월별**: 유연한 기간 설정 지원

    트렌드 분석 및 성과 측정에 활용됩니다.
    """
)
def get_period_statistics(
    days: Optional[int] = Query(None, ge=1, le=365, description="최근 N일 (1-365)"),
    weeks: Optional[int] = Query(None, ge=1, le=52, description="최근 N주 (1-52)"),
    months: Optional[int] = Query(None, ge=1, le=12, description="최근 N개월 (1-12)"),
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    기간별 피드백 통계 조회

    Args:
        days: 최근 N일
        weeks: 최근 N주
        months: 최근 N개월
        current_user: 관리자 사용자
        db: 데이터베이스 세션

    Returns:
        dict: 기간별 통계 정보

    Raises:
        403: 관리자 권한 없음
    """
    logger.info(
        f"Period stats requested by user_id={current_user.id}, "
        f"days={days}, weeks={weeks}, months={months}"
    )

    # 현재 시각
    end_date = datetime.utcnow()

    # 시작 날짜 계산 (우선순위: days > weeks > months, 기본값: 7일)
    if days:
        start_date = end_date - timedelta(days=days)
        period_label = f"최근 {days}일"
    elif weeks:
        start_date = end_date - timedelta(weeks=weeks)
        period_label = f"최근 {weeks}주"
    elif months:
        start_date = end_date - timedelta(days=months * 30)  # 대략적 계산
        period_label = f"최근 {months}개월"
    else:
        # 기본값: 최근 7일
        start_date = end_date - timedelta(days=7)
        period_label = "최근 7일"

    stats = FeedbackRepository.get_statistics_by_date_range(
        db, start_date, end_date
    )

    stats["period_label"] = period_label

    logger.info(f"Period stats ({period_label}): {stats}")

    return stats


@router.get(
    "/stats/spread-types",
    summary="Spread Type별 피드백 통계 조회 (관리자 전용)",
    description="""
    각 Spread Type (원카드, 쓰리카드 등)별 피드백 통계를 조회합니다.

    - **관리자 권한 필수**: is_superuser=True인 사용자만 접근 가능
    - **Spread Type별 집계**: one_card, three_card 등 각 타입별 통계
    - **상세 메트릭**: 평균 별점, helpful/accurate 비율

    각 Spread Type의 성능 비교 및 개선 방향 결정에 활용됩니다.
    """
)
def get_spread_type_statistics(
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    Spread Type별 피드백 통계 조회

    Args:
        current_user: 관리자 사용자
        db: 데이터베이스 세션

    Returns:
        List[dict]: Spread Type별 통계 리스트
            - spread_type: Spread Type 이름
            - feedback_count: 피드백 수
            - average_rating: 평균 별점
            - helpful_count: helpful True 개수
            - accurate_count: accurate True 개수
            - helpful_rate: helpful 비율 (%)
            - accurate_rate: accurate 비율 (%)

    Raises:
        403: 관리자 권한 없음
    """
    logger.info(f"Spread type stats requested by user_id={current_user.id}")

    stats = FeedbackRepository.get_statistics_by_spread_type(db)

    logger.info(f"Spread type stats: {len(stats)} types found")

    return {
        "spread_types": stats,
        "total_types": len(stats)
    }
