"""
Admin Stats API 간단 테스트

wizmain@gmail.com (is_superuser=True)로 로그인 후 admin API 테스트
"""

import requests
import json

BASE_URL = "http://localhost:8000"

# 관리자 계정 정보 (DB에서 is_superuser=True로 설정됨)
ADMIN_EMAIL = "wizmain@gmail.com"
ADMIN_PASSWORD = "password"  # 실제 비밀번호

def print_response(title, response):
    """응답 정보 출력"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    if response.text:
        try:
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        except:
            print(response.text)

print("\n[1] 관리자 로그인 (wizmain@gmail.com)")

# 로그인 (OAuth2PasswordRequestForm 형식)
login_data = {
    "username": ADMIN_EMAIL,
    "password": ADMIN_PASSWORD
}

response = requests.post(
    f"{BASE_URL}/api/v1/auth/login",
    data=login_data
)

if response.status_code != 200:
    print(f"❌ 로그인 실패: {response.status_code}")
    print(response.text)
    print("\n새로운 관리자 계정을 생성해야 합니다...")

    # 새 관리자 계정 생성
    signup_data = {
        "email": "admin_test@example.com",
        "password": "Admin1234!",
        "username": "admin_test"
    }

    response = requests.post(f"{BASE_URL}/api/v1/auth/signup", json=signup_data)
    if response.status_code == 201:
        admin_token = response.json()["access_token"]
        print(f"\n✅ 새 계정 생성 완료: admin_test@example.com")
        print(f"   (주의: DB에서 is_superuser를 True로 설정해야 합니다)")
    else:
        print("❌ 계정 생성 실패")
        exit(1)
else:
    admin_token = response.json()["access_token"]
    print(f"✅ 로그인 성공!")
    print(f"   Access Token: {admin_token[:50]}...")

admin_headers = {"Authorization": f"Bearer {admin_token}"}

# 2. 전체 통계 조회
print("\n[2] 전체 피드백 통계 조회")
response = requests.get(f"{BASE_URL}/api/v1/admin/stats", headers=admin_headers)
print_response("GET /api/v1/admin/stats", response)

if response.status_code == 200:
    print("\n✅ 전체 통계 조회 성공")
elif response.status_code == 403:
    print("\n❌ 권한 없음 - DB에서 is_superuser=True로 설정하세요:")
    print("   psql -d tarot_db -c \"UPDATE users SET is_superuser = true WHERE email = 'wizmain@gmail.com';\"")
else:
    print(f"\n❌ 통계 조회 실패: {response.status_code}")

# 3. 기간별 통계 조회 (최근 7일)
print("\n[3] 기간별 통계 조회 (최근 7일)")
response = requests.get(
    f"{BASE_URL}/api/v1/admin/stats/period?days=7",
    headers=admin_headers
)
print_response("GET /api/v1/admin/stats/period?days=7", response)

if response.status_code == 200:
    print("\n✅ 기간별 통계 조회 성공")

# 4. 월별 통계 조회 (최근 1개월)
print("\n[4] 월별 통계 조회 (최근 1개월)")
response = requests.get(
    f"{BASE_URL}/api/v1/admin/stats/period?months=1",
    headers=admin_headers
)
print_response("GET /api/v1/admin/stats/period?months=1", response)

if response.status_code == 200:
    print("\n✅ 월별 통계 조회 성공")

# 5. Spread Type별 통계 조회
print("\n[5] Spread Type별 통계 조회")
response = requests.get(
    f"{BASE_URL}/api/v1/admin/stats/spread-types",
    headers=admin_headers
)
print_response("GET /api/v1/admin/stats/spread-types", response)

if response.status_code == 200:
    print("\n✅ Spread Type별 통계 조회 성공")

print("\n" + "="*60)
print("✅ 모든 admin API 테스트 완료!")
print("="*60)
