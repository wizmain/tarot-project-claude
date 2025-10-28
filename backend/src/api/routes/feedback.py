"""
피드백 API Routes - 타로 리딩 피드백 API 엔드포인트

이 모듈의 목적:
- 타로 리딩에 대한 사용자 피드백 제출 및 관리
- 피드백 생성, 조회, 수정, 삭제 API 제공
- 중복 피드백 방지 및 인증된 사용자만 접근 허용

주요 엔드포인트:
- POST /api/v1/readings/{reading_id}/feedback: 피드백 생성
- GET /api/v1/readings/{reading_id}/feedback: 리딩의 모든 피드백 조회
- PUT /api/v1/feedback/{feedback_id}: 피드백 수정
- DELETE /api/v1/feedback/{feedback_id}: 피드백 삭제

구현 사항:
- JWT 인증 필수 (get_current_active_user 의존성)
- 중복 피드백 방지 (409 Conflict)
- 권한 검증 (자신의 피드백만 수정/삭제 가능)
- 상세한 에러 핸들링 및 로깅

TASK 참조:
- TASK-036: 피드백 제출 API

사용 예시:
    # 피드백 생성
    POST /api/v1/readings/{reading_id}/feedback
    Headers: Authorization: Bearer <token>
    {
        "rating": 5,
        "comment": "매우 정확하고 도움이 되는 리딩이었습니다!",
        "helpful": true,
        "accurate": true
    }

    # 리딩의 모든 피드백 조회
    GET /api/v1/readings/{reading_id}/feedback?page=1&page_size=10
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.core.database import get_db
from src.core.logging import get_logger
from src.api.repositories.feedback_repository import FeedbackRepository
from src.api.repositories.reading_repository import ReadingRepository
from src.api.dependencies.auth import get_current_active_user
from src.models import User
from src.schemas.feedback import (
    FeedbackCreate,
    FeedbackUpdate,
    FeedbackResponse
)

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["feedback"])


@router.post(
    "/readings/{reading_id}/feedback",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="리딩에 대한 피드백 제출",
    description="""
    특정 타로 리딩에 대한 사용자 피드백을 제출합니다.

    - **인증 필수**: JWT 토큰이 필요합니다
    - **중복 방지**: 같은 사용자가 같은 리딩에 중복 피드백을 제출할 수 없습니다
    - **필수 필드**: rating (1-5)
    - **선택 필드**: comment, helpful, accurate

    피드백은 서비스 품질 개선과 AI 모델 튜닝에 활용됩니다.
    """
)
def create_feedback(
    reading_id: UUID,
    feedback_data: FeedbackCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    새로운 피드백 생성

    Args:
        reading_id: 피드백을 남길 리딩의 ID
        feedback_data: 피드백 데이터 (rating, comment, helpful, accurate)
        current_user: 인증된 현재 사용자
        db: 데이터베이스 세션

    Returns:
        FeedbackResponse: 생성된 피드백 정보

    Raises:
        404: 리딩을 찾을 수 없음
        409: 이미 피드백을 제출한 리딩
        500: 서버 오류
    """
    logger.info(
        f"Creating feedback for reading_id={reading_id}, "
        f"user_id={current_user.id}, rating={feedback_data.rating}"
    )

    try:
        # 1. 리딩이 존재하는지 확인
        reading = ReadingRepository.get_by_id(db, reading_id)
        if not reading:
            logger.warning(f"Reading not found: reading_id={reading_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Reading with id {reading_id} not found"
            )

        # 2. 중복 피드백 확인
        existing_feedback = FeedbackRepository.get_by_reading_and_user(
            db, reading_id, current_user.id
        )
        if existing_feedback:
            logger.warning(
                f"Duplicate feedback attempt: reading_id={reading_id}, "
                f"user_id={current_user.id}"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already submitted feedback for this reading"
            )

        # 3. 피드백 생성
        feedback = FeedbackRepository.create(
            db=db,
            reading_id=reading_id,
            user_id=current_user.id,
            rating=feedback_data.rating,
            comment=feedback_data.comment,
            helpful=feedback_data.helpful,
            accurate=feedback_data.accurate
        )

        db.commit()
        db.refresh(feedback)

        logger.info(
            f"Feedback created successfully: feedback_id={feedback.id}, "
            f"reading_id={reading_id}, user_id={current_user.id}"
        )

        return FeedbackResponse.model_validate(feedback)

    except HTTPException:
        # HTTPException은 그대로 전달
        db.rollback()
        raise
    except IntegrityError as e:
        # 데이터베이스 제약 조건 위반 (unique constraint 등)
        db.rollback()
        logger.error(f"IntegrityError while creating feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Feedback already exists for this reading"
        )
    except Exception as e:
        # 기타 예외 처리
        db.rollback()
        logger.error(f"Error creating feedback: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating feedback"
        )


@router.get(
    "/readings/{reading_id}/feedback",
    response_model=List[FeedbackResponse],
    summary="리딩의 모든 피드백 조회",
    description="""
    특정 타로 리딩에 대한 모든 피드백을 조회합니다.

    - **인증 불필요**: 공개 엔드포인트
    - **페이지네이션**: page와 page_size 파라미터로 제어
    - **정렬**: 최신순 (created_at DESC)

    관리자 또는 통계 목적으로 사용됩니다.
    """
)
def get_reading_feedback(
    reading_id: UUID,
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    page_size: int = Query(10, ge=1, le=100, description="페이지당 항목 수"),
    db: Session = Depends(get_db)
):
    """
    특정 리딩의 모든 피드백 조회

    Args:
        reading_id: 리딩 ID
        page: 페이지 번호 (1부터 시작)
        page_size: 페이지당 항목 수 (1-100)
        db: 데이터베이스 세션

    Returns:
        List[FeedbackResponse]: 피드백 리스트

    Raises:
        404: 리딩을 찾을 수 없음
    """
    logger.info(
        f"Fetching feedback for reading_id={reading_id}, "
        f"page={page}, page_size={page_size}"
    )

    # 리딩이 존재하는지 확인
    reading = ReadingRepository.get_by_id(db, reading_id)
    if not reading:
        logger.warning(f"Reading not found: reading_id={reading_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reading with id {reading_id} not found"
        )

    # 피드백 조회
    skip = (page - 1) * page_size
    feedbacks = FeedbackRepository.get_by_reading(
        db, reading_id, skip=skip, limit=page_size
    )

    logger.info(
        f"Found {len(feedbacks)} feedbacks for reading_id={reading_id}"
    )

    return [FeedbackResponse.model_validate(f) for f in feedbacks]


@router.put(
    "/feedback/{feedback_id}",
    response_model=FeedbackResponse,
    summary="피드백 수정",
    description="""
    자신이 작성한 피드백을 수정합니다.

    - **인증 필수**: JWT 토큰이 필요합니다
    - **권한 검증**: 자신의 피드백만 수정 가능
    - **부분 업데이트**: 수정하고 싶은 필드만 포함

    모든 필드는 선택사항이며, 제공된 필드만 업데이트됩니다.
    """
)
def update_feedback(
    feedback_id: UUID,
    feedback_data: FeedbackUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    기존 피드백 수정

    Args:
        feedback_id: 수정할 피드백 ID
        feedback_data: 수정할 데이터 (모든 필드 선택사항)
        current_user: 인증된 현재 사용자
        db: 데이터베이스 세션

    Returns:
        FeedbackResponse: 수정된 피드백 정보

    Raises:
        404: 피드백을 찾을 수 없음
        403: 권한 없음 (다른 사용자의 피드백)
        500: 서버 오류
    """
    logger.info(
        f"Updating feedback: feedback_id={feedback_id}, "
        f"user_id={current_user.id}"
    )

    try:
        # 1. 피드백 조회
        feedback = FeedbackRepository.get_by_id(db, feedback_id)
        if not feedback:
            logger.warning(f"Feedback not found: feedback_id={feedback_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feedback with id {feedback_id} not found"
            )

        # 2. 권한 확인 (자신의 피드백만 수정 가능)
        if feedback.user_id != current_user.id:
            logger.warning(
                f"Unauthorized feedback update attempt: "
                f"feedback_id={feedback_id}, "
                f"feedback_owner={feedback.user_id}, "
                f"requester={current_user.id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own feedback"
            )

        # 3. 피드백 업데이트
        updated_feedback = FeedbackRepository.update(
            db=db,
            feedback=feedback,
            rating=feedback_data.rating,
            comment=feedback_data.comment,
            helpful=feedback_data.helpful,
            accurate=feedback_data.accurate
        )

        db.commit()
        db.refresh(updated_feedback)

        logger.info(
            f"Feedback updated successfully: feedback_id={feedback_id}"
        )

        return FeedbackResponse.model_validate(updated_feedback)

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating feedback: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating feedback"
        )


@router.delete(
    "/feedback/{feedback_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="피드백 삭제",
    description="""
    자신이 작성한 피드백을 삭제합니다.

    - **인증 필수**: JWT 토큰이 필요합니다
    - **권한 검증**: 자신의 피드백만 삭제 가능
    - **완전 삭제**: 복구 불가능

    삭제 성공 시 204 No Content를 반환합니다.
    """
)
def delete_feedback(
    feedback_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    기존 피드백 삭제

    Args:
        feedback_id: 삭제할 피드백 ID
        current_user: 인증된 현재 사용자
        db: 데이터베이스 세션

    Returns:
        None (204 No Content)

    Raises:
        404: 피드백을 찾을 수 없음
        403: 권한 없음 (다른 사용자의 피드백)
        500: 서버 오류
    """
    logger.info(
        f"Deleting feedback: feedback_id={feedback_id}, "
        f"user_id={current_user.id}"
    )

    try:
        # 1. 피드백 조회
        feedback = FeedbackRepository.get_by_id(db, feedback_id)
        if not feedback:
            logger.warning(f"Feedback not found: feedback_id={feedback_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feedback with id {feedback_id} not found"
            )

        # 2. 권한 확인 (자신의 피드백만 삭제 가능)
        if feedback.user_id != current_user.id:
            logger.warning(
                f"Unauthorized feedback delete attempt: "
                f"feedback_id={feedback_id}, "
                f"feedback_owner={feedback.user_id}, "
                f"requester={current_user.id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own feedback"
            )

        # 3. 피드백 삭제
        FeedbackRepository.delete(db, feedback)
        db.commit()

        logger.info(
            f"Feedback deleted successfully: feedback_id={feedback_id}"
        )

        return None

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting feedback: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting feedback"
        )


@router.get(
    "/readings/{reading_id}/feedback/stats",
    summary="리딩 피드백 통계",
    description="""
    특정 리딩의 피드백 통계를 조회합니다.

    - **인증 불필요**: 공개 엔드포인트
    - **통계 정보**: 평균 별점, 총 피드백 수, helpful/accurate 비율

    리딩 품질 평가 및 AI 모델 개선에 활용됩니다.
    """
)
def get_feedback_stats(
    reading_id: UUID,
    db: Session = Depends(get_db)
):
    """
    특정 리딩의 피드백 통계 조회

    Args:
        reading_id: 리딩 ID
        db: 데이터베이스 세션

    Returns:
        dict: 피드백 통계 (평균 별점, 총 개수 등)

    Raises:
        404: 리딩을 찾을 수 없음
    """
    logger.info(f"Fetching feedback stats for reading_id={reading_id}")

    # 리딩이 존재하는지 확인
    reading = ReadingRepository.get_by_id(db, reading_id)
    if not reading:
        logger.warning(f"Reading not found: reading_id={reading_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reading with id {reading_id} not found"
        )

    # 통계 계산
    total_count = FeedbackRepository.count_by_reading(db, reading_id)
    avg_rating = FeedbackRepository.get_average_rating_by_reading(db, reading_id)

    # 모든 피드백 가져오기 (helpful/accurate 비율 계산용)
    feedbacks = FeedbackRepository.get_by_reading(
        db, reading_id, skip=0, limit=1000  # 충분히 큰 limit
    )

    helpful_count = sum(1 for f in feedbacks if f.helpful)
    accurate_count = sum(1 for f in feedbacks if f.accurate)

    stats = {
        "reading_id": str(reading_id),
        "total_feedback_count": total_count,
        "average_rating": round(avg_rating, 2) if avg_rating else None,
        "helpful_count": helpful_count,
        "accurate_count": accurate_count,
        "helpful_rate": round(helpful_count / total_count * 100, 1) if total_count > 0 else 0,
        "accurate_rate": round(accurate_count / total_count * 100, 1) if total_count > 0 else 0
    }

    logger.info(f"Feedback stats for reading_id={reading_id}: {stats}")

    return stats
