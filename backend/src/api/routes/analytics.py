"""
Analytics API Routes - LLM 사용 기록 분석 API

이 모듈의 목적:
- LLM 사용 통계 제공 (비용, 호출 수, 응답 시간)
- 일별/모델별 분석 데이터 제공
- 대시보드용 집계 데이터 API

주요 엔드포인트:
- GET /api/v1/analytics/llm-usage/summary: 요약 통계
- GET /api/v1/analytics/llm-usage/daily-trend: 일별 추세
- GET /api/v1/analytics/llm-usage/recent: 최근 호출 기록
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from collections import defaultdict

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field

from src.core.logging import get_logger
from src.api.dependencies.auth import get_current_active_user
from src.database.factory import get_database_provider
from src.database.provider import DatabaseProvider

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


# ==================== Response Models ====================

class ModelStats(BaseModel):
    """모델별 통계"""
    model: str
    provider: str
    calls: int
    total_cost: float
    avg_latency: float


class SummaryResponse(BaseModel):
    """요약 통계 응답"""
    total_cost: float = Field(..., description="총 비용 (USD)")
    total_calls: int = Field(..., description="총 호출 수")
    avg_latency_seconds: float = Field(..., description="평균 응답 시간 (초)")
    period_days: int = Field(..., description="집계 기간 (일)")
    comparison: Dict[str, float] = Field(..., description="이전 기간 대비 변화율 (%)")
    by_model: List[ModelStats] = Field(..., description="모델별 통계")


class DailyTrendData(BaseModel):
    """일별 추세 데이터"""
    date: str
    total_cost: float
    total_calls: int
    avg_latency: float
    by_model: Dict[str, Dict[str, Any]]


class DailyTrendResponse(BaseModel):
    """일별 추세 응답"""
    start_date: str
    end_date: str
    data: List[DailyTrendData]


class RecentLogEntry(BaseModel):
    """최근 호출 기록"""
    id: str
    reading_id: str
    created_at: datetime
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float
    latency_seconds: float
    purpose: str
    reading_question: Optional[str] = None


class RecentLogsResponse(BaseModel):
    """최근 호출 기록 응답"""
    total: int
    page: int
    page_size: int
    logs: List[RecentLogEntry]


# ==================== Helper Functions ====================

async def _aggregate_llm_logs(
    provider: DatabaseProvider,
    start_date: datetime,
    end_date: datetime
) -> Dict[str, Any]:
    """
    Firestore에서 LLM 로그 집계

    Args:
        provider: Database provider
        start_date: 시작 날짜
        end_date: 종료 날짜

    Returns:
        집계된 통계 데이터
    """
    # Firestore: 모든 readings에서 llm_usage 추출
    from src.database.firestore_provider import FirestoreProvider

    if not isinstance(provider, FirestoreProvider):
        raise HTTPException(500, "Currently only Firestore is supported")

    # 기간 내 readings 조회
    readings_ref = provider.readings_collection
    readings_query = readings_ref.where(
        "created_at", ">=", start_date
    ).where(
        "created_at", "<=", end_date
    )

    readings = readings_query.stream()

    # 집계 데이터 초기화
    stats = {
        "total_cost": 0.0,
        "total_calls": 0,
        "total_latency": 0.0,
        "by_model": defaultdict(lambda: {
            "calls": 0,
            "total_cost": 0.0,
            "total_latency": 0.0,
            "provider": ""
        }),
        "by_date": defaultdict(lambda: {
            "total_cost": 0.0,
            "total_calls": 0,
            "total_latency": 0.0,
            "by_model": defaultdict(lambda: {"calls": 0, "cost": 0.0})
        })
    }

    # 각 reading의 llm_usage 집계
    for reading in readings:
        reading_data = reading.to_dict()
        llm_usage = reading_data.get("llm_usage", [])

        for log in llm_usage:
            # 전체 통계
            stats["total_cost"] += log.get("estimated_cost", 0.0)
            stats["total_calls"] += 1
            stats["total_latency"] += log.get("latency_seconds", 0.0)

            # 모델별 통계
            model = log.get("model", "unknown")
            provider_name = log.get("provider", "unknown")
            stats["by_model"][model]["calls"] += 1
            stats["by_model"][model]["total_cost"] += log.get("estimated_cost", 0.0)
            stats["by_model"][model]["total_latency"] += log.get("latency_seconds", 0.0)
            stats["by_model"][model]["provider"] = provider_name

            # 날짜별 통계
            created_at = log.get("created_at")
            if created_at:
                if hasattr(created_at, "date"):
                    date_key = created_at.date().isoformat()
                else:
                    # Firestore Timestamp
                    date_key = created_at.strftime("%Y-%m-%d")

                stats["by_date"][date_key]["total_cost"] += log.get("estimated_cost", 0.0)
                stats["by_date"][date_key]["total_calls"] += 1
                stats["by_date"][date_key]["total_latency"] += log.get("latency_seconds", 0.0)
                stats["by_date"][date_key]["by_model"][model]["calls"] += 1
                stats["by_date"][date_key]["by_model"][model]["cost"] += log.get("estimated_cost", 0.0)

    return stats


# ==================== API Endpoints ====================

@router.get("/llm-usage/summary", response_model=SummaryResponse)
async def get_llm_usage_summary(
    days: int = Query(30, ge=1, le=365, description="집계 기간 (일)"),
    current_user=Depends(get_current_active_user),
    db_provider: DatabaseProvider = Depends(get_database_provider),
):
    """
    LLM 사용 요약 통계

    - 총 비용, 호출 수, 평균 응답 시간
    - 이전 기간 대비 변화율
    - 모델별 통계
    """
    logger.info(f"[Analytics] Summary requested by user {current_user.id} for {days} days")

    try:
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        # 현재 기간 통계
        current_stats = await _aggregate_llm_logs(db_provider, start_date, end_date)

        # 이전 기간 통계 (비교용)
        prev_end_date = start_date
        prev_start_date = prev_end_date - timedelta(days=days)
        prev_stats = await _aggregate_llm_logs(db_provider, prev_start_date, prev_end_date)

        # 변화율 계산
        def calc_change(current: float, previous: float) -> float:
            if previous == 0:
                return 100.0 if current > 0 else 0.0
            return ((current - previous) / previous) * 100

        comparison = {
            "cost_change_percent": calc_change(
                current_stats["total_cost"],
                prev_stats["total_cost"]
            ),
            "calls_change_percent": calc_change(
                current_stats["total_calls"],
                prev_stats["total_calls"]
            ),
            "latency_change_percent": calc_change(
                current_stats["total_latency"] / max(current_stats["total_calls"], 1),
                prev_stats["total_latency"] / max(prev_stats["total_calls"], 1)
            )
        }

        # 모델별 통계 생성
        by_model = []
        for model, model_stats in current_stats["by_model"].items():
            by_model.append(ModelStats(
                model=model,
                provider=model_stats["provider"],
                calls=model_stats["calls"],
                total_cost=round(model_stats["total_cost"], 4),
                avg_latency=round(
                    model_stats["total_latency"] / max(model_stats["calls"], 1),
                    2
                )
            ))

        # 평균 응답 시간 계산
        avg_latency = (
            current_stats["total_latency"] / max(current_stats["total_calls"], 1)
            if current_stats["total_calls"] > 0
            else 0.0
        )

        response = SummaryResponse(
            total_cost=round(current_stats["total_cost"], 4),
            total_calls=current_stats["total_calls"],
            avg_latency_seconds=round(avg_latency, 2),
            period_days=days,
            comparison=comparison,
            by_model=by_model
        )

        logger.info(
            f"[Analytics] Summary: ${response.total_cost:.4f}, "
            f"{response.total_calls} calls, "
            f"{response.avg_latency_seconds:.2f}s avg"
        )

        return response

    except Exception as e:
        logger.exception(f"[Analytics] Failed to get summary: {e}")
        raise HTTPException(500, f"Failed to retrieve analytics: {str(e)}")


@router.get("/llm-usage/daily-trend", response_model=DailyTrendResponse)
async def get_daily_trend(
    days: int = Query(30, ge=1, le=365, description="조회 기간 (일)"),
    current_user=Depends(get_current_active_user),
    db_provider: DatabaseProvider = Depends(get_database_provider),
):
    """
    일별 LLM 사용 추세

    - 기간별 일일 통계
    - 차트 렌더링용 데이터
    """
    logger.info(f"[Analytics] Daily trend requested for {days} days")

    try:
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        # 통계 집계
        stats = await _aggregate_llm_logs(db_provider, start_date, end_date)

        # 일별 데이터 생성
        daily_data = []
        for date_str in sorted(stats["by_date"].keys()):
            day_stats = stats["by_date"][date_str]

            avg_latency = (
                day_stats["total_latency"] / max(day_stats["total_calls"], 1)
                if day_stats["total_calls"] > 0
                else 0.0
            )

            daily_data.append(DailyTrendData(
                date=date_str,
                total_cost=round(day_stats["total_cost"], 4),
                total_calls=day_stats["total_calls"],
                avg_latency=round(avg_latency, 2),
                by_model=dict(day_stats["by_model"])
            ))

        return DailyTrendResponse(
            start_date=start_date.date().isoformat(),
            end_date=end_date.date().isoformat(),
            data=daily_data
        )

    except Exception as e:
        logger.exception(f"[Analytics] Failed to get daily trend: {e}")
        raise HTTPException(500, f"Failed to retrieve daily trend: {str(e)}")


@router.get("/llm-usage/recent", response_model=RecentLogsResponse)
async def get_recent_logs(
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    current_user=Depends(get_current_active_user),
    db_provider: DatabaseProvider = Depends(get_database_provider),
):
    """
    최근 LLM 호출 기록

    - 페이지네이션 지원
    - 최신순 정렬
    """
    logger.info(f"[Analytics] Recent logs requested: page={page}, size={page_size}")

    try:
        from src.database.firestore_provider import FirestoreProvider

        if not isinstance(db_provider, FirestoreProvider):
            raise HTTPException(500, "Currently only Firestore is supported")

        # 최근 readings 조회 (최대 100개)
        readings_ref = db_provider.readings_collection
        readings_query = readings_ref.order_by(
            "created_at", direction="DESCENDING"
        ).limit(100)

        readings = readings_query.stream()

        # 모든 LLM 로그 수집
        all_logs = []
        for reading in readings:
            reading_data = reading.to_dict()
            reading_id = reading_data.get("id")
            question = reading_data.get("question", "")
            llm_usage = reading_data.get("llm_usage", [])

            for log in llm_usage:
                all_logs.append(RecentLogEntry(
                    id=log.get("id", ""),
                    reading_id=log.get("reading_id", reading_id),
                    created_at=log.get("created_at", datetime.now(timezone.utc)),
                    provider=log.get("provider", ""),
                    model=log.get("model", ""),
                    prompt_tokens=log.get("prompt_tokens", 0),
                    completion_tokens=log.get("completion_tokens", 0),
                    total_tokens=log.get("total_tokens", 0),
                    estimated_cost=log.get("estimated_cost", 0.0),
                    latency_seconds=log.get("latency_seconds", 0.0),
                    purpose=log.get("purpose", "main_reading"),
                    reading_question=question[:50] + "..." if len(question) > 50 else question
                ))

        # 생성 시간순 정렬
        all_logs.sort(key=lambda x: x.created_at, reverse=True)

        # 페이지네이션
        total = len(all_logs)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_logs = all_logs[start_idx:end_idx]

        return RecentLogsResponse(
            total=total,
            page=page,
            page_size=page_size,
            logs=page_logs
        )

    except Exception as e:
        logger.exception(f"[Analytics] Failed to get recent logs: {e}")
        raise HTTPException(500, f"Failed to retrieve recent logs: {str(e)}")
