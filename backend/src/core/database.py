"""
데이터베이스 연결 및 세션 관리 모듈

이 모듈의 목적:
- PostgreSQL 데이터베이스 연결 풀 관리
- SQLAlchemy 엔진 및 세션 설정
- FastAPI 의존성 주입용 세션 제공
- 모든 ORM 모델의 베이스 클래스 제공

주요 컴포넌트:
- engine: 데이터베이스 연결 엔진 (connection pool 포함)
- SessionLocal: 데이터베이스 세션 팩토리
- Base: 모든 모델의 부모 클래스
- get_db(): FastAPI 엔드포인트에서 사용하는 세션 제공 함수
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from src.core.config import settings

# SQLAlchemy 엔진 생성
# pool_pre_ping: 연결 풀에서 가져온 연결이 유효한지 사전 확인
# pool_size: 연결 풀의 기본 크기
# max_overflow: 풀이 가득 찰 때 추가로 생성 가능한 연결 수
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# 데이터베이스 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 모든 ORM 모델의 베이스 클래스
Base = declarative_base()


def get_db():
    """
    데이터베이스 세션 제공 의존성 함수

    FastAPI 엔드포인트에서 Depends()와 함께 사용하여
    데이터베이스 세션을 자동으로 주입받습니다.
    요청이 완료되면 세션을 자동으로 닫습니다.

    Usage in FastAPI:
        @app.get("/items/")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
