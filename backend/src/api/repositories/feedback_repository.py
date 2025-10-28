"""
Feedback Repository - 피드백 데이터 접근 계층

이 모듈의 목적:
- Feedback 모델에 대한 데이터베이스 CRUD 작업 제공
- 데이터 접근 로직을 비즈니스 로직에서 분리
- 재사용 가능한 쿼리 메서드 제공
- 중복 피드백 방지 로직

주요 기능:
- create(): Feedback 생성
- get_by_id(): ID로 Feedback 조회
- get_by_reading_and_user(): Reading ID와 User ID로 Feedback 조회
- get_by_reading(): Reading ID로 모든 Feedback 조회
- get_by_user(): User ID로 모든 Feedback 조회
- update(): Feedback 정보 업데이트
- delete(): Feedback 삭제
- exists(): 피드백 존재 여부 확인

구현 사항:
- 정적 메서드 사용 (stateless repository 패턴)
- SQLAlchemy ORM 쿼리
- 중복 피드백 방지 (reading_id + user_id unique constraint)
- 페이지네이션 지원

사용 예시:
    from src.api.repositories import FeedbackRepository
    from src.core.database import SessionLocal

    db = SessionLocal()

    # Feedback 생성
    feedback = FeedbackRepository.create(
        db=db,
        reading_id=uuid.UUID("..."),
        user_id=uuid.UUID("..."),
        rating=5,
        comment="훌륭한 리딩이었습니다!",
        helpful=True,
        accurate=True
    )
    db.commit()

    # Feedback 조회
    feedback = FeedbackRepository.get_by_reading_and_user(
        db, reading_id, user_id
    )

TASK 참조:
- TASK-036: 피드백 제출 API
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, Integer
from sqlalchemy.exc import IntegrityError

from src.models import Feedback
from src.core.logging import get_logger

logger = get_logger(__name__)


class FeedbackRepository:
    """
    Feedback 데이터 접근 Repository

    Feedback 모델에 대한 데이터베이스 작업을 처리합니다.
    """

    @staticmethod
    def create(
        db: Session,
        reading_id: UUID,
        user_id: UUID,
        rating: int,
        helpful: bool = True,
        accurate: bool = True,
        comment: Optional[str] = None,
    ) -> Feedback:
        """
        새로운 Feedback 생성

        Args:
            db: 데이터베이스 세션
            reading_id: 연관된 리딩 ID
            user_id: 피드백 작성자 ID
            rating: 별점 평가 (1-5)
            helpful: 리딩이 유용했는지 여부
            accurate: 리딩이 정확했는지 여부
            comment: 사용자 코멘트 (선택사항)

        Returns:
            생성된 Feedback 객체

        Raises:
            IntegrityError: 중복 피드백 시도 시 (reading_id + user_id unique constraint)

        Example:
            feedback = FeedbackRepository.create(
                db=db,
                reading_id=reading.id,
                user_id=user.id,
                rating=5,
                comment="매우 도움이 되었습니다!",
                helpful=True,
                accurate=True
            )
            db.commit()
        """
        logger.info(f"Creating feedback for reading_id={reading_id}, user_id={user_id}")

        feedback = Feedback(
            reading_id=reading_id,
            user_id=user_id,
            rating=rating,
            comment=comment,
            helpful=helpful,
            accurate=accurate
        )

        db.add(feedback)

        try:
            db.flush()
            logger.info(f"Feedback created successfully with id={feedback.id}")
            return feedback
        except IntegrityError as e:
            db.rollback()
            logger.warning(f"Duplicate feedback attempt for reading_id={reading_id}, user_id={user_id}")
            raise

    @staticmethod
    def get_by_id(db: Session, feedback_id: UUID) -> Optional[Feedback]:
        """
        ID로 Feedback 조회

        Args:
            db: 데이터베이스 세션
            feedback_id: 피드백 ID

        Returns:
            Feedback 객체 또는 None
        """
        return db.query(Feedback).filter(Feedback.id == feedback_id).first()

    @staticmethod
    def get_by_reading_and_user(
        db: Session,
        reading_id: UUID,
        user_id: UUID
    ) -> Optional[Feedback]:
        """
        Reading ID와 User ID로 Feedback 조회

        특정 사용자가 특정 리딩에 남긴 피드백을 찾습니다.
        중복 피드백 방지를 위해 사용됩니다.

        Args:
            db: 데이터베이스 세션
            reading_id: 리딩 ID
            user_id: 사용자 ID

        Returns:
            Feedback 객체 또는 None
        """
        return db.query(Feedback).filter(
            and_(
                Feedback.reading_id == reading_id,
                Feedback.user_id == user_id
            )
        ).first()

    @staticmethod
    def exists(db: Session, reading_id: UUID, user_id: UUID) -> bool:
        """
        피드백 존재 여부 확인

        Args:
            db: 데이터베이스 세션
            reading_id: 리딩 ID
            user_id: 사용자 ID

        Returns:
            피드백 존재 여부 (bool)
        """
        return db.query(Feedback).filter(
            and_(
                Feedback.reading_id == reading_id,
                Feedback.user_id == user_id
            )
        ).count() > 0

    @staticmethod
    def get_by_reading(
        db: Session,
        reading_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Feedback]:
        """
        Reading ID로 모든 Feedback 조회

        특정 리딩에 대한 모든 피드백을 최신순으로 조회합니다.

        Args:
            db: 데이터베이스 세션
            reading_id: 리딩 ID
            skip: 건너뛸 개수 (페이지네이션)
            limit: 최대 조회 개수

        Returns:
            Feedback 객체 리스트
        """
        return db.query(Feedback).filter(
            Feedback.reading_id == reading_id
        ).order_by(
            desc(Feedback.created_at)
        ).offset(skip).limit(limit).all()

    @staticmethod
    def get_by_user(
        db: Session,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Feedback]:
        """
        User ID로 모든 Feedback 조회

        특정 사용자가 작성한 모든 피드백을 최신순으로 조회합니다.

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            skip: 건너뛸 개수 (페이지네이션)
            limit: 최대 조회 개수

        Returns:
            Feedback 객체 리스트
        """
        return db.query(Feedback).filter(
            Feedback.user_id == user_id
        ).order_by(
            desc(Feedback.created_at)
        ).offset(skip).limit(limit).all()

    @staticmethod
    def update(
        db: Session,
        feedback: Feedback,
        rating: Optional[int] = None,
        comment: Optional[str] = None,
        helpful: Optional[bool] = None,
        accurate: Optional[bool] = None
    ) -> Feedback:
        """
        Feedback 정보 업데이트

        Args:
            db: 데이터베이스 세션
            feedback: 업데이트할 Feedback 객체
            rating: 새로운 별점 (선택사항)
            comment: 새로운 코멘트 (선택사항)
            helpful: 새로운 helpful 값 (선택사항)
            accurate: 새로운 accurate 값 (선택사항)

        Returns:
            업데이트된 Feedback 객체
        """
        logger.info(f"Updating feedback id={feedback.id}")

        if rating is not None:
            feedback.rating = rating
        if comment is not None:
            feedback.comment = comment
        if helpful is not None:
            feedback.helpful = helpful
        if accurate is not None:
            feedback.accurate = accurate

        db.flush()
        logger.info(f"Feedback id={feedback.id} updated successfully")
        return feedback

    @staticmethod
    def delete(db: Session, feedback: Feedback) -> None:
        """
        Feedback 삭제

        Args:
            db: 데이터베이스 세션
            feedback: 삭제할 Feedback 객체
        """
        logger.info(f"Deleting feedback id={feedback.id}")
        db.delete(feedback)
        db.flush()
        logger.info(f"Feedback id={feedback.id} deleted successfully")

    @staticmethod
    def count_by_reading(db: Session, reading_id: UUID) -> int:
        """
        특정 리딩의 피드백 개수 조회

        Args:
            db: 데이터베이스 세션
            reading_id: 리딩 ID

        Returns:
            피드백 개수
        """
        return db.query(Feedback).filter(
            Feedback.reading_id == reading_id
        ).count()

    @staticmethod
    def get_average_rating_by_reading(db: Session, reading_id: UUID) -> Optional[float]:
        """
        특정 리딩의 평균 별점 조회

        Args:
            db: 데이터베이스 세션
            reading_id: 리딩 ID

        Returns:
            평균 별점 (1-5) 또는 None (피드백이 없을 경우)
        """
        from sqlalchemy import func

        result = db.query(
            func.avg(Feedback.rating)
        ).filter(
            Feedback.reading_id == reading_id
        ).scalar()

        return float(result) if result is not None else None

    @staticmethod
    def get_global_statistics(db: Session) -> dict:
        """
        전체 피드백 통계 조회 (관리자용)

        Args:
            db: 데이터베이스 세션

        Returns:
            dict: 전체 통계 정보
                - total_feedback_count: 총 피드백 수
                - average_rating: 전체 평균 별점
                - helpful_count: helpful True 개수
                - accurate_count: accurate True 개수
                - helpful_rate: helpful 비율 (%)
                - accurate_rate: accurate 비율 (%)
        """
        from sqlalchemy import func

        # 전체 피드백 수 및 평균 별점
        stats_query = db.query(
            func.count(Feedback.id).label('total_count'),
            func.avg(Feedback.rating).label('avg_rating'),
            func.sum(func.cast(Feedback.helpful, Integer)).label('helpful_count'),
            func.sum(func.cast(Feedback.accurate, Integer)).label('accurate_count')
        ).first()

        total_count = stats_query.total_count or 0
        avg_rating = float(stats_query.avg_rating) if stats_query.avg_rating else 0.0
        helpful_count = stats_query.helpful_count or 0
        accurate_count = stats_query.accurate_count or 0

        return {
            "total_feedback_count": total_count,
            "average_rating": round(avg_rating, 2) if avg_rating else 0.0,
            "helpful_count": helpful_count,
            "accurate_count": accurate_count,
            "helpful_rate": round((helpful_count / total_count * 100), 1) if total_count > 0 else 0.0,
            "accurate_rate": round((accurate_count / total_count * 100), 1) if total_count > 0 else 0.0,
        }

    @staticmethod
    def get_statistics_by_date_range(
        db: Session,
        start_date: datetime,
        end_date: datetime
    ) -> dict:
        """
        특정 기간의 피드백 통계 조회

        Args:
            db: 데이터베이스 세션
            start_date: 시작 날짜
            end_date: 종료 날짜

        Returns:
            dict: 기간별 통계 정보
        """
        from sqlalchemy import func

        stats_query = db.query(
            func.count(Feedback.id).label('total_count'),
            func.avg(Feedback.rating).label('avg_rating'),
            func.sum(func.cast(Feedback.helpful, Integer)).label('helpful_count'),
            func.sum(func.cast(Feedback.accurate, Integer)).label('accurate_count')
        ).filter(
            and_(
                Feedback.created_at >= start_date,
                Feedback.created_at < end_date
            )
        ).first()

        total_count = stats_query.total_count or 0
        avg_rating = float(stats_query.avg_rating) if stats_query.avg_rating else 0.0
        helpful_count = stats_query.helpful_count or 0
        accurate_count = stats_query.accurate_count or 0

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_feedback_count": total_count,
            "average_rating": round(avg_rating, 2) if avg_rating else 0.0,
            "helpful_count": helpful_count,
            "accurate_count": accurate_count,
            "helpful_rate": round((helpful_count / total_count * 100), 1) if total_count > 0 else 0.0,
            "accurate_rate": round((accurate_count / total_count * 100), 1) if total_count > 0 else 0.0,
        }

    @staticmethod
    def get_statistics_by_spread_type(db: Session) -> List[dict]:
        """
        Spread Type별 피드백 통계 조회

        Args:
            db: 데이터베이스 세션

        Returns:
            List[dict]: Spread Type별 통계 리스트
        """
        from sqlalchemy import func
        from src.models import Reading

        # Reading과 Feedback을 join해서 spread_type별로 집계
        stats = db.query(
            Reading.spread_type,
            func.count(Feedback.id).label('feedback_count'),
            func.avg(Feedback.rating).label('avg_rating'),
            func.sum(func.cast(Feedback.helpful, Integer)).label('helpful_count'),
            func.sum(func.cast(Feedback.accurate, Integer)).label('accurate_count')
        ).join(
            Feedback, Reading.id == Feedback.reading_id
        ).group_by(
            Reading.spread_type
        ).all()

        result = []
        for stat in stats:
            total_count = stat.feedback_count or 0
            avg_rating = float(stat.avg_rating) if stat.avg_rating else 0.0
            helpful_count = stat.helpful_count or 0
            accurate_count = stat.accurate_count or 0

            result.append({
                "spread_type": stat.spread_type,
                "feedback_count": total_count,
                "average_rating": round(avg_rating, 2) if avg_rating else 0.0,
                "helpful_count": helpful_count,
                "accurate_count": accurate_count,
                "helpful_rate": round((helpful_count / total_count * 100), 1) if total_count > 0 else 0.0,
                "accurate_rate": round((accurate_count / total_count * 100), 1) if total_count > 0 else 0.0,
            })

        return result
