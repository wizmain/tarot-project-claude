"""
사용자 비밀번호 설정 스크립트

특정 사용자의 비밀번호를 설정합니다.
"""
import sys
import os
import bcrypt
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import settings
from src.core.database import SessionLocal
from src.models import User


def hash_password(password: str) -> str:
    """
    bcrypt로 비밀번호 해싱

    Args:
        password: 평문 비밀번호

    Returns:
        해싱된 비밀번호
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def set_password(email: str, password: str):
    """
    사용자 비밀번호 설정

    Args:
        email: 사용자 이메일
        password: 새 비밀번호
    """
    db = SessionLocal()

    try:
        # 사용자 조회
        user = db.query(User).filter(User.email == email).first()

        if not user:
            print(f"❌ 사용자를 찾을 수 없습니다: {email}")
            return False

        # 비밀번호 해싱
        print(f"🔒 비밀번호 해싱 중...")
        password_hash = hash_password(password)

        # 비밀번호 업데이트
        user.password_hash = password_hash
        db.commit()

        print(f"✅ 비밀번호가 성공적으로 설정되었습니다!")
        print(f"📧 이메일: {email}")
        print(f"🔑 비밀번호: {password}")
        print(f"🔐 해시: {password_hash[:50]}...")

        return True

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        db.rollback()
        return False

    finally:
        db.close()


def main():
    """메인 실행 함수"""
    import argparse

    parser = argparse.ArgumentParser(description='사용자 비밀번호 설정')
    parser.add_argument('--email', type=str, required=True, help='사용자 이메일')
    parser.add_argument('--password', type=str, required=True, help='새 비밀번호')

    args = parser.parse_args()

    print(f"🔧 사용자 비밀번호 설정 스크립트")
    print(f"="*60)
    print(f"📧 이메일: {args.email}")
    print(f"🔑 비밀번호: {args.password}")
    print(f"="*60)

    # 비밀번호 설정
    success = set_password(args.email, args.password)

    if success:
        print(f"\n✅ 작업 완료!")
        print(f"\n로그인 정보:")
        print(f"  이메일: {args.email}")
        print(f"  비밀번호: {args.password}")
    else:
        print(f"\n❌ 작업 실패!")
        sys.exit(1)


if __name__ == "__main__":
    main()
