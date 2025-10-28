"""
Admin Stats API 테스트 스크립트

이 스크립트는 다음을 테스트합니다:
1. 일반 사용자 회원가입 및 피드백 생성
2. 관리자 사용자 생성 (is_superuser=True)
3. 관리자 API 접근 권한 검증
4. 전체 피드백 통계 조회
5. 기간별 통계 조회
6. Spread Type별 통계 조회
"""

import requests
import json
from uuid import uuid4
from sqlalchemy.orm import Session
from src.core.database import SessionLocal
from src.api.repositories.user_repository import UserRepository

BASE_URL = "http://localhost:8000"

def print_response(title, response):
    """응답 정보 출력"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    try:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except:
        print(response.text)

def create_admin_user(db: Session, email: str, password: str) -> str:
    """
    관리자 사용자를 직접 DB에 생성

    Returns:
        str: 생성된 사용자의 ID
    """
    from src.auth.models import PasswordHasher

    # 비밀번호 해시화
    hashed_password = PasswordHasher.hash_password(password)

    # 관리자 사용자 생성
    user = UserRepository.create(
        db=db,
        email=email,
        provider_id="custom_jwt",
        is_superuser=True,  # 관리자 플래그
        hashed_password=hashed_password
    )

    db.commit()
    db.refresh(user)

    return str(user.id)

def main():
    db = SessionLocal()

    try:
        # 1. 일반 사용자 회원가입 및 피드백 생성 (기존 피드백이 있을 수 있음)
        print("\n[1] 테스트용 피드백 데이터 준비")
        print("(이전 테스트에서 생성된 피드백 사용)")

        # 2. 관리자 사용자 생성
        print("\n[2] 관리자 사용자 생성")

        admin_email = f"admin_{uuid4().hex[:8]}@example.com"
        admin_password = "Admin1234!"

        try:
            admin_user_id = create_admin_user(db, admin_email, admin_password)
            print(f"✅ 관리자 사용자 생성 완료: {admin_email}")
            print(f"   User ID: {admin_user_id}")
            print(f"   is_superuser: True")
        except Exception as e:
            print(f"❌ 관리자 사용자 생성 실패: {e}")
            return

        # 3. 관리자 로그인 (JWT 토큰 획득)
        print("\n[3] 관리자 로그인")

        # 먼저 회원가입 API로 토큰 획득 (이미 DB에 생성되어 있으므로 로그인 endpoint 사용)
        # 하지만 비밀번호 해시 때문에 로그인이 안 될 수 있으므로, 다시 회원가입 API로 생성
        # 이미 DB에 있는 사용자는 회원가입이 안 되므로, 직접 JWT 토큰 생성

        from src.auth import AuthOrchestrator, AuthProviderFactory
        from src.core.config import settings

        # JWT Provider로 토큰 생성
        jwt_provider = AuthProviderFactory.create(
            provider_name="custom_jwt",
            secret_key=settings.SECRET_KEY,
            algorithm='HS256',
            access_token_expire_minutes=60,
            refresh_token_expire_days=7
        )

        # 관리자 토큰 생성
        token_result = await jwt_provider.create_token(
            user_id=admin_user_id,
            email=admin_email
        )

        admin_token = token_result.access_token
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        print(f"✅ 관리자 JWT 토큰 생성: {admin_token[:50]}...")

        # 4. 일반 사용자로 admin API 접근 시도 (403 예상)
        print("\n[4] 일반 사용자로 admin API 접근 시도 (403 예상)")

        # 일반 사용자 생성 및 토큰 획득
        normal_email = f"normal_{uuid4().hex[:8]}@example.com"
        normal_password = "Normal1234!"

        signup_data = {
            "email": normal_email,
            "password": normal_password,
            "username": f"normal_{uuid4().hex[:6]}"
        }

        response = requests.post(f"{BASE_URL}/api/v1/auth/signup", json=signup_data)
        if response.status_code == 201:
            normal_token = response.json()["access_token"]
            normal_headers = {"Authorization": f"Bearer {normal_token}"}

            # admin API 접근 시도
            response = requests.get(f"{BASE_URL}/api/v1/admin/stats", headers=normal_headers)
            print_response("일반 사용자로 admin API 접근", response)

            if response.status_code == 403:
                print("\n✅ 권한 검증 정상 작동 (403 Forbidden)")
            else:
                print("\n❌ 권한 검증 실패 - 일반 사용자가 admin API 접근 가능!")

        # 5. 관리자로 전체 통계 조회
        print("\n[5] 관리자로 전체 피드백 통계 조회")

        response = requests.get(f"{BASE_URL}/api/v1/admin/stats", headers=admin_headers)
        print_response("전체 피드백 통계", response)

        if response.status_code == 200:
            print("\n✅ 전체 통계 조회 성공")
        else:
            print("\n❌ 전체 통계 조회 실패")

        # 6. 기간별 통계 조회 (최근 7일)
        print("\n[6] 기간별 통계 조회 (최근 7일)")

        response = requests.get(
            f"{BASE_URL}/api/v1/admin/stats/period?days=7",
            headers=admin_headers
        )
        print_response("기간별 통계 (최근 7일)", response)

        if response.status_code == 200:
            print("\n✅ 기간별 통계 조회 성공")

        # 7. Spread Type별 통계 조회
        print("\n[7] Spread Type별 통계 조회")

        response = requests.get(
            f"{BASE_URL}/api/v1/admin/stats/spread-types",
            headers=admin_headers
        )
        print_response("Spread Type별 통계", response)

        if response.status_code == 200:
            print("\n✅ Spread Type별 통계 조회 성공")

        print("\n" + "="*60)
        print("✅ 모든 테스트 완료!")
        print("="*60)

    finally:
        db.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
