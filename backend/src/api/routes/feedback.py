"""
피드백 API Routes - 타로 리딩 피드백 API 엔드포인트

Firestore 및 PostgreSQL 제공자에 호환되도록 DatabaseProvider 추상화를 사용합니다.
"""
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.core.logging import get_logger
from src.api.dependencies.auth import get_current_active_user, get_current_superuser
from src.database.factory import get_database_provider
from src.database.provider import DatabaseProvider, Feedback as FeedbackDTO
from src.schemas.feedback import (
    FeedbackCreate,
    FeedbackUpdate,
    FeedbackResponse,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["feedback"])


def _feedback_to_response(feedback: FeedbackDTO) -> FeedbackResponse:
    """Convert provider Feedback DTO to API response schema"""
    return FeedbackResponse(
        id=str(feedback.id),
        reading_id=str(feedback.reading_id),
        user_id=str(feedback.user_id),
        rating=feedback.rating,
        comment=feedback.comment,
        helpful=feedback.helpful,
        accurate=feedback.accurate,
        created_at=feedback.created_at,
        updated_at=feedback.updated_at,
    )


@router.post(
    "/readings/{reading_id}/feedback",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="리딩에 대한 피드백 제출",
)
async def create_feedback(
    reading_id: str,
    feedback_data: FeedbackCreate,
    current_user=Depends(get_current_active_user),
    db_provider: DatabaseProvider = Depends(get_database_provider),
):
    """
    특정 리딩에 대한 피드백 생성
    """
    logger.info(
        "Creating feedback for reading_id=%s, user_id=%s, rating=%s",
        reading_id,
        getattr(current_user, "id", None),
        feedback_data.rating,
    )

    reading = await db_provider.get_reading_by_id(reading_id)
    if not reading:
        logger.warning("Reading not found: %s", reading_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reading with id {reading_id} not found",
        )

    user_id = str(getattr(current_user, "id", None))

    existing_feedback = await db_provider.get_feedback_by_reading_and_user(
        reading_id=reading_id,
        user_id=user_id,
    )
    if existing_feedback:
        logger.warning(
            "Duplicate feedback attempt: reading_id=%s user_id=%s",
            reading_id,
            user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already submitted feedback for this reading",
        )

    feedback = await db_provider.create_feedback(
        {
            "reading_id": reading_id,
            "user_id": user_id,
            "rating": feedback_data.rating,
            "comment": feedback_data.comment,
            "helpful": feedback_data.helpful,
            "accurate": feedback_data.accurate,
            "spread_type": reading.spread_type,
        }
    )

    return _feedback_to_response(feedback)


@router.get(
    "/readings/{reading_id}/feedback",
    response_model=List[FeedbackResponse],
    summary="리딩의 모든 피드백 조회",
)
async def get_reading_feedback(
    reading_id: str,
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    page_size: int = Query(10, ge=1, le=100, description="페이지당 항목 수"),
    db_provider: DatabaseProvider = Depends(get_database_provider),
):
    """
    특정 리딩의 모든 피드백 조회
    """
    logger.info(
        "Fetching feedback for reading_id=%s page=%s page_size=%s",
        reading_id,
        page,
        page_size,
    )

    reading = await db_provider.get_reading_by_id(reading_id)
    if not reading:
        logger.warning("Reading not found: %s", reading_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reading with id {reading_id} not found",
        )

    skip = (page - 1) * page_size
    feedback_list = await db_provider.get_feedback_by_reading(
        reading_id=reading_id,
        skip=skip,
        limit=page_size,
    )

    logger.info(
        "Found %s feedbacks for reading_id=%s",
        len(feedback_list),
        reading_id,
    )

    return [_feedback_to_response(feedback) for feedback in feedback_list]


@router.put(
    "/feedback/{feedback_id}",
    response_model=FeedbackResponse,
    summary="피드백 수정",
)
async def update_feedback(
    feedback_id: str,
    feedback_data: FeedbackUpdate,
    current_user=Depends(get_current_active_user),
    db_provider: DatabaseProvider = Depends(get_database_provider),
):
    """
    피드백 업데이트
    """
    logger.info(
        "Updating feedback feedback_id=%s user_id=%s",
        feedback_id,
        getattr(current_user, "id", None),
    )

    feedback = await db_provider.get_feedback_by_id(feedback_id)
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feedback with id {feedback_id} not found",
        )

    if str(feedback.user_id) != str(getattr(current_user, "id", None)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own feedback",
        )

    updated_feedback = await db_provider.update_feedback(
        feedback_id=feedback_id,
        feedback_data=feedback_data.model_dump(exclude_none=True),
    )
    if not updated_feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feedback with id {feedback_id} not found",
        )

    return _feedback_to_response(updated_feedback)


@router.delete(
    "/feedback/{feedback_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="피드백 삭제",
)
async def delete_feedback(
    feedback_id: str,
    current_user=Depends(get_current_active_user),
    db_provider: DatabaseProvider = Depends(get_database_provider),
):
    """
    피드백 삭제
    """
    logger.info(
        "Deleting feedback feedback_id=%s user_id=%s",
        feedback_id,
        getattr(current_user, "id", None),
    )

    feedback = await db_provider.get_feedback_by_id(feedback_id)
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feedback with id {feedback_id} not found",
        )

    if str(feedback.user_id) != str(getattr(current_user, "id", None)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own feedback",
        )

    deleted = await db_provider.delete_feedback(feedback_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feedback with id {feedback_id} not found",
        )

    return None
