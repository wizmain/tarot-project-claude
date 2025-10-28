"""
Reading Repository - 타로 리딩 데이터 접근 계층

이 모듈의 목적:
- Reading 및 ReadingCard 모델에 대한 데이터베이스 CRUD 작업 제공
- 데이터 접근 로직을 비즈니스 로직에서 분리
- 재사용 가능한 쿼리 메서드 제공
- 트랜잭션 관리 및 에러 처리

주요 기능:
- create(): Reading 및 연관된 ReadingCard 생성
- get_by_id(): ID로 Reading 조회 (카드 정보 포함)
- get_all(): 모든 Reading 목록 조회 (페이지네이션)
- count_all(): 전체 Reading 개수 조회
- get_by_user(): 특정 사용자의 Reading 목록 조회

구현 사항:
- 정적 메서드 사용 (stateless repository 패턴)
- SQLAlchemy ORM 쿼리
- relationship을 활용한 연관 데이터 로딩
- 페이지네이션 지원 (skip, limit)

TASK 참조:
- TASK-027: 원카드 리딩 구현

사용 예시:
    from src.api.repositories import ReadingRepository
    from src.core.database import SessionLocal

    db = SessionLocal()

    # Reading 생성
    reading = ReadingRepository.create(
        db=db,
        reading_data={
            "spread_type": "one_card",
            "question": "새로운 직장으로 이직해야 할까요?",
            "overall_reading": "...",
            "advice": {...},
            "summary": "..."
        },
        cards_data=[
            {
                "card_id": 1,
                "position": "single",
                "orientation": "upright",
                "interpretation": "...",
                "key_message": "..."
            }
        ]
    )
    db.commit()

    # Reading 조회
    reading = ReadingRepository.get_by_id(db, reading.id)
    print(reading.question)
    print(reading.cards[0].card.name)
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.models import Reading, ReadingCard
from src.core.logging import get_logger

logger = get_logger(__name__)


class ReadingRepository:
    """
    Reading 데이터 접근 Repository

    Reading 및 ReadingCard 모델에 대한 데이터베이스 작업을 처리합니다.
    """

    @staticmethod
    def create(
        db: Session,
        reading_data: Dict[str, Any],
        cards_data: List[Dict[str, Any]]
    ) -> Reading:
        """
        새로운 Reading 및 연관된 ReadingCard 생성

        Args:
            db: 데이터베이스 세션
            reading_data: Reading 모델 데이터
                - spread_type: str
                - question: str
                - category: Optional[str]
                - card_relationships: Optional[str]
                - overall_reading: str
                - advice: dict (JSON)
                - summary: str
                - user_id: Optional[UUID]
            cards_data: ReadingCard 모델 데이터 리스트
                - card_id: int
                - position: str
                - orientation: str
                - interpretation: str
                - key_message: str

        Returns:
            Reading: 생성된 Reading 객체 (연관된 카드 포함)

        Raises:
            SQLAlchemyError: 데이터베이스 작업 실패 시
        """
        try:
            # Reading 생성
            reading = Reading(**reading_data)
            db.add(reading)
            db.flush()  # reading.id 생성을 위해 flush

            logger.info(f"[ReadingRepository] Reading 생성: ID={reading.id}, spread_type={reading.spread_type}")

            # ReadingCard 생성
            for card_data in cards_data:
                reading_card = ReadingCard(
                    reading_id=reading.id,
                    **card_data
                )
                db.add(reading_card)

            logger.info(f"[ReadingRepository] {len(cards_data)}개의 ReadingCard 생성 완료")

            return reading

        except Exception as e:
            logger.error(f"[ReadingRepository] Reading 생성 실패: {e}")
            raise

    @staticmethod
    def get_by_id(db: Session, reading_id: UUID) -> Optional[Reading]:
        """
        ID로 Reading 조회 (연관된 카드 정보 포함)

        Args:
            db: 데이터베이스 세션
            reading_id: Reading UUID

        Returns:
            Optional[Reading]: 조회된 Reading 객체 또는 None
        """
        try:
            reading = db.query(Reading).filter(Reading.id == reading_id).first()

            if reading:
                logger.info(
                    f"[ReadingRepository] Reading 조회 성공: "
                    f"ID={reading_id}, cards={len(reading.cards)}"
                )
            else:
                logger.warning(f"[ReadingRepository] Reading을 찾을 수 없음: ID={reading_id}")

            return reading

        except Exception as e:
            logger.error(f"[ReadingRepository] Reading 조회 실패: {e}")
            raise

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 20
    ) -> List[Reading]:
        """
        모든 Reading 목록 조회 (최신순 정렬, 페이지네이션)

        Args:
            db: 데이터베이스 세션
            skip: 건너뛸 개수
            limit: 최대 조회 개수

        Returns:
            List[Reading]: Reading 목록
        """
        try:
            readings = (
                db.query(Reading)
                .order_by(desc(Reading.created_at))
                .offset(skip)
                .limit(limit)
                .all()
            )

            logger.info(
                f"[ReadingRepository] Reading 목록 조회: "
                f"{len(readings)}개 (skip={skip}, limit={limit})"
            )

            return readings

        except Exception as e:
            logger.error(f"[ReadingRepository] Reading 목록 조회 실패: {e}")
            raise

    @staticmethod
    def count_all(db: Session) -> int:
        """
        전체 Reading 개수 조회

        Args:
            db: 데이터베이스 세션

        Returns:
            int: 전체 Reading 개수
        """
        try:
            count = db.query(Reading).count()
            logger.info(f"[ReadingRepository] 전체 Reading 개수: {count}")
            return count

        except Exception as e:
            logger.error(f"[ReadingRepository] Reading 개수 조회 실패: {e}")
            raise

    @staticmethod
    def get_by_user(
        db: Session,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20
    ) -> List[Reading]:
        """
        특정 사용자의 Reading 목록 조회

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 UUID
            skip: 건너뛸 개수
            limit: 최대 조회 개수

        Returns:
            List[Reading]: Reading 목록
        """
        try:
            readings = (
                db.query(Reading)
                .filter(Reading.user_id == user_id)
                .order_by(desc(Reading.created_at))
                .offset(skip)
                .limit(limit)
                .all()
            )

            logger.info(
                f"[ReadingRepository] 사용자 Reading 목록 조회: "
                f"user_id={user_id}, {len(readings)}개"
            )

            return readings

        except Exception as e:
            logger.error(f"[ReadingRepository] 사용자 Reading 조회 실패: {e}")
            raise

    @staticmethod
    def count_by_user(db: Session, user_id: UUID) -> int:
        """
        특정 사용자의 Reading 개수 조회

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 UUID

        Returns:
            int: 사용자의 Reading 개수
        """
        try:
            count = db.query(Reading).filter(Reading.user_id == user_id).count()
            logger.info(f"[ReadingRepository] 사용자 Reading 개수: user_id={user_id}, count={count}")
            return count

        except Exception as e:
            logger.error(f"[ReadingRepository] 사용자 Reading 개수 조회 실패: {e}")
            raise

    @staticmethod
    def get_by_spread_type(
        db: Session,
        spread_type: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[Reading]:
        """
        특정 스프레드 타입의 Reading 목록 조회

        Args:
            db: 데이터베이스 세션
            spread_type: 스프레드 타입
            skip: 건너뛸 개수
            limit: 최대 조회 개수

        Returns:
            List[Reading]: Reading 목록
        """
        try:
            readings = (
                db.query(Reading)
                .filter(Reading.spread_type == spread_type)
                .order_by(desc(Reading.created_at))
                .offset(skip)
                .limit(limit)
                .all()
            )

            logger.info(
                f"[ReadingRepository] 스프레드 타입별 Reading 조회: "
                f"spread_type={spread_type}, {len(readings)}개"
            )

            return readings

        except Exception as e:
            logger.error(f"[ReadingRepository] 스프레드 타입별 Reading 조회 실패: {e}")
            raise
