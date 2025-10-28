"""
User Repository - 사용자 데이터 접근 계층

이 모듈의 목적:
- User 모델에 대한 데이터베이스 CRUD 작업 제공
- 데이터 접근 로직을 비즈니스 로직에서 분리
- 재사용 가능한 쿼리 메서드 제공
- 트랜잭션 관리 및 에러 처리

주요 기능:
- create(): User 생성
- get_by_id(): ID로 User 조회
- get_by_email(): 이메일로 User 조회
- get_by_provider(): Provider 정보로 User 조회
- update(): User 정보 업데이트
- delete(): User 삭제
- get_all(): 모든 User 목록 조회 (페이지네이션)

구현 사항:
- 정적 메서드 사용 (stateless repository 패턴)
- SQLAlchemy ORM 쿼리
- relationship을 활용한 연관 데이터 로딩
- 페이지네이션 지원 (skip, limit)

사용 예시:
    from src.api.repositories import UserRepository
    from src.core.database import SessionLocal

    db = SessionLocal()

    # User 생성
    user = UserRepository.create(
        db=db,
        email="user@example.com",
        display_name="홍길동",
        provider_id="custom_jwt",
        provider_user_id="jwt_abc123"
    )
    db.commit()

    # User 조회
    user = UserRepository.get_by_email(db, "user@example.com")
    print(user.display_name)
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_, func

from src.models import User, Reading
from src.core.logging import get_logger

logger = get_logger(__name__)


class UserRepository:
    """
    User 데이터 접근 Repository

    User 모델에 대한 데이터베이스 작업을 처리합니다.
    """

    @staticmethod
    def create(
        db: Session,
        email: str,
        provider_id: str,
        provider_user_id: str,
        display_name: Optional[str] = None,
        photo_url: Optional[str] = None,
        phone_number: Optional[str] = None,
        email_verified: bool = False,
        user_metadata: Optional[Dict[str, Any]] = None,
        password_hash: Optional[str] = None
    ) -> User:
        """
        새로운 User 생성

        Args:
            db: 데이터베이스 세션
            email: 이메일 주소
            provider_id: 인증 Provider 식별자
            provider_user_id: Provider의 사용자 ID
            display_name: 표시 이름
            photo_url: 프로필 사진 URL
            phone_number: 전화번호
            email_verified: 이메일 인증 여부
            user_metadata: 추가 메타데이터
            password_hash: 비밀번호 해시 (custom_jwt provider용)

        Returns:
            User: 생성된 User 객체

        Raises:
            SQLAlchemyError: 데이터베이스 작업 실패 시
        """
        try:
            user = User(
                email=email,
                provider_id=provider_id,
                provider_user_id=provider_user_id,
                display_name=display_name,
                photo_url=photo_url,
                phone_number=phone_number,
                email_verified=email_verified,
                user_metadata=user_metadata or {},
                password_hash=password_hash
            )
            db.add(user)
            db.flush()  # user.id 생성을 위해 flush

            logger.info(
                f"[UserRepository] User 생성: "
                f"ID={user.id}, email={email}, provider={provider_id}"
            )

            return user

        except Exception as e:
            logger.error(f"[UserRepository] User 생성 실패: {e}")
            raise

    @staticmethod
    def get_by_id(db: Session, user_id: UUID) -> Optional[User]:
        """
        ID로 User 조회

        Args:
            db: 데이터베이스 세션
            user_id: User UUID

        Returns:
            Optional[User]: 조회된 User 객체 또는 None
        """
        try:
            user = db.query(User).filter(User.id == user_id).first()

            if user:
                logger.info(f"[UserRepository] User 조회 성공: ID={user_id}")
            else:
                logger.warning(f"[UserRepository] User를 찾을 수 없음: ID={user_id}")

            return user

        except Exception as e:
            logger.error(f"[UserRepository] User 조회 실패: {e}")
            raise

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        """
        이메일로 User 조회

        Args:
            db: 데이터베이스 세션
            email: 이메일 주소

        Returns:
            Optional[User]: 조회된 User 객체 또는 None
        """
        try:
            user = db.query(User).filter(User.email == email).first()

            if user:
                logger.info(f"[UserRepository] User 조회 성공: email={email}")
            else:
                logger.debug(f"[UserRepository] User를 찾을 수 없음: email={email}")

            return user

        except Exception as e:
            logger.error(f"[UserRepository] User 조회 실패: {e}")
            raise

    @staticmethod
    def get_by_provider(
        db: Session,
        provider_id: str,
        provider_user_id: str
    ) -> Optional[User]:
        """
        Provider 정보로 User 조회

        Args:
            db: 데이터베이스 세션
            provider_id: 인증 Provider 식별자
            provider_user_id: Provider의 사용자 ID

        Returns:
            Optional[User]: 조회된 User 객체 또는 None
        """
        try:
            user = db.query(User).filter(
                and_(
                    User.provider_id == provider_id,
                    User.provider_user_id == provider_user_id
                )
            ).first()

            if user:
                logger.info(
                    f"[UserRepository] User 조회 성공: "
                    f"provider={provider_id}, provider_user_id={provider_user_id}"
                )
            else:
                logger.debug(
                    f"[UserRepository] User를 찾을 수 없음: "
                    f"provider={provider_id}, provider_user_id={provider_user_id}"
                )

            return user

        except Exception as e:
            logger.error(f"[UserRepository] User 조회 실패: {e}")
            raise

    @staticmethod
    def update(
        db: Session,
        user_id: UUID,
        **kwargs
    ) -> Optional[User]:
        """
        User 정보 업데이트

        Args:
            db: 데이터베이스 세션
            user_id: User UUID
            **kwargs: 업데이트할 필드 (display_name, photo_url, phone_number, etc.)

        Returns:
            Optional[User]: 업데이트된 User 객체 또는 None

        Raises:
            SQLAlchemyError: 데이터베이스 작업 실패 시
        """
        try:
            user = db.query(User).filter(User.id == user_id).first()

            if not user:
                logger.warning(f"[UserRepository] User를 찾을 수 없음: ID={user_id}")
                return None

            # 업데이트 가능한 필드만 업데이트
            allowed_fields = {
                'display_name', 'photo_url', 'phone_number',
                'email_verified', 'is_active', 'user_metadata', 'last_login_at'
            }

            for key, value in kwargs.items():
                if key in allowed_fields and value is not None:
                    setattr(user, key, value)

            db.flush()

            logger.info(f"[UserRepository] User 업데이트 완료: ID={user_id}")

            return user

        except Exception as e:
            logger.error(f"[UserRepository] User 업데이트 실패: {e}")
            raise

    @staticmethod
    def update_last_login(db: Session, user_id: UUID) -> Optional[User]:
        """
        마지막 로그인 시간 업데이트

        Args:
            db: 데이터베이스 세션
            user_id: User UUID

        Returns:
            Optional[User]: 업데이트된 User 객체 또는 None
        """
        try:
            user = db.query(User).filter(User.id == user_id).first()

            if not user:
                logger.warning(f"[UserRepository] User를 찾을 수 없음: ID={user_id}")
                return None

            user.last_login_at = datetime.utcnow()
            db.flush()

            logger.info(f"[UserRepository] 마지막 로그인 시간 업데이트: ID={user_id}")

            return user

        except Exception as e:
            logger.error(f"[UserRepository] 마지막 로그인 시간 업데이트 실패: {e}")
            raise

    @staticmethod
    def delete(db: Session, user_id: UUID) -> bool:
        """
        User 삭제

        Args:
            db: 데이터베이스 세션
            user_id: User UUID

        Returns:
            bool: 삭제 성공 여부

        Raises:
            SQLAlchemyError: 데이터베이스 작업 실패 시
        """
        try:
            user = db.query(User).filter(User.id == user_id).first()

            if not user:
                logger.warning(f"[UserRepository] User를 찾을 수 없음: ID={user_id}")
                return False

            db.delete(user)
            db.flush()

            logger.info(f"[UserRepository] User 삭제 완료: ID={user_id}")

            return True

        except Exception as e:
            logger.error(f"[UserRepository] User 삭제 실패: {e}")
            raise

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        is_active: Optional[bool] = None
    ) -> List[User]:
        """
        모든 User 목록 조회 (최신순 정렬, 페이지네이션)

        Args:
            db: 데이터베이스 세션
            skip: 건너뛸 개수
            limit: 최대 조회 개수
            is_active: 활성화 여부 필터 (optional)

        Returns:
            List[User]: User 목록
        """
        try:
            query = db.query(User)

            if is_active is not None:
                query = query.filter(User.is_active == is_active)

            users = (
                query
                .order_by(desc(User.created_at))
                .offset(skip)
                .limit(limit)
                .all()
            )

            logger.info(
                f"[UserRepository] User 목록 조회: "
                f"{len(users)}개 (skip={skip}, limit={limit})"
            )

            return users

        except Exception as e:
            logger.error(f"[UserRepository] User 목록 조회 실패: {e}")
            raise

    @staticmethod
    def count_all(db: Session, is_active: Optional[bool] = None) -> int:
        """
        전체 User 개수 조회

        Args:
            db: 데이터베이스 세션
            is_active: 활성화 여부 필터 (optional)

        Returns:
            int: 전체 User 개수
        """
        try:
            query = db.query(User)

            if is_active is not None:
                query = query.filter(User.is_active == is_active)

            count = query.count()
            logger.info(f"[UserRepository] 전체 User 개수: {count}")
            return count

        except Exception as e:
            logger.error(f"[UserRepository] User 개수 조회 실패: {e}")
            raise

    @staticmethod
    def get_user_with_stats(db: Session, user_id: UUID) -> Optional[Dict[str, Any]]:
        """
        사용자 정보와 통계 정보 함께 조회

        Args:
            db: 데이터베이스 세션
            user_id: User UUID

        Returns:
            Optional[Dict[str, Any]]: 사용자 정보 및 통계 (total_readings, recent_readings)
        """
        try:
            user = db.query(User).filter(User.id == user_id).first()

            if not user:
                logger.warning(f"[UserRepository] User를 찾을 수 없음: ID={user_id}")
                return None

            # 총 리딩 횟수
            total_readings = db.query(Reading).filter(Reading.user_id == user.id).count()

            # 최근 30일 리딩 횟수
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_readings = db.query(Reading).filter(
                Reading.user_id == user.id,
                Reading.created_at >= thirty_days_ago
            ).count()

            user_dict = user.to_dict()
            user_dict['total_readings'] = total_readings
            user_dict['recent_readings'] = recent_readings

            logger.info(
                f"[UserRepository] User 통계 조회: "
                f"ID={user_id}, total={total_readings}, recent={recent_readings}"
            )

            return user_dict

        except Exception as e:
            logger.error(f"[UserRepository] User 통계 조회 실패: {e}")
            raise
