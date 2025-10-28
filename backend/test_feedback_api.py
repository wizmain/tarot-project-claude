"""
Feedback API 테스트 스크립트

이 스크립트는 다음을 테스트합니다:
1. 사용자 회원가입/로그인 (JWT 토큰 획득)
2. 리딩 생성 (피드백을 남길 대상)
3. 피드백 제출 (POST /api/v1/readings/{reading_id}/feedback)
4. 중복 피드백 시도 (409 Conflict 확인)
5. 피드백 조회 (GET /api/v1/readings/{reading_id}/feedback)
6. 피드백 통계 조회 (GET /api/v1/readings/{reading_id}/feedback/stats)
"""

import requests
import json
from uuid import uuid4

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

def main():
    # 1. 회원가입/로그인
    print("\n[1] 사용자 회원가입/로그인")

    # 테스트용 사용자 정보
    test_email = f"feedback_test_{uuid4().hex[:8]}@example.com"
    test_password = "Test1234!"

    # 회원가입
    signup_data = {
        "email": test_email,
        "password": test_password,
        "username": f"feedback_tester_{uuid4().hex[:6]}"
    }

    response = requests.post(f"{BASE_URL}/api/v1/auth/signup", json=signup_data)
    print_response("회원가입", response)

    if response.status_code != 201:
        print("❌ 회원가입 실패")
        return

    # 회원가입 시 반환된 토큰 사용
    token_data = response.json()
    access_token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    print(f"\n✅ JWT 토큰 획득 (회원가입): {access_token[:50]}...")

    # 2. 리딩 생성
    print("\n[2] 리딩 생성")

    reading_data = {
        "question": "피드백 테스트를 위한 리딩입니다.",
        "spread_type": "one_card",
        "category": "career"
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/readings",
        json=reading_data,
        headers=headers
    )
    print_response("리딩 생성", response)

    if response.status_code != 201:
        print("❌ 리딩 생성 실패")
        return

    reading = response.json()
    reading_id = reading["id"]

    print(f"\n✅ 리딩 생성 완료: reading_id={reading_id}")

    # 3. 피드백 제출
    print("\n[3] 피드백 제출")

    feedback_data = {
        "rating": 5,
        "comment": "정말 정확하고 도움이 되는 리딩이었습니다! 감사합니다.",
        "helpful": True,
        "accurate": True
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/readings/{reading_id}/feedback",
        json=feedback_data,
        headers=headers
    )
    print_response("피드백 제출", response)

    if response.status_code != 201:
        print("❌ 피드백 제출 실패")
        return

    feedback = response.json()
    feedback_id = feedback["id"]

    print(f"\n✅ 피드백 제출 완료: feedback_id={feedback_id}")

    # 4. 중복 피드백 시도 (409 Conflict 확인)
    print("\n[4] 중복 피드백 시도 (409 Conflict 예상)")

    response = requests.post(
        f"{BASE_URL}/api/v1/readings/{reading_id}/feedback",
        json=feedback_data,
        headers=headers
    )
    print_response("중복 피드백 시도", response)

    if response.status_code == 409:
        print("\n✅ 중복 피드백 방지 정상 작동 (409 Conflict)")
    else:
        print("\n❌ 중복 피드백 방지 실패")

    # 5. 리딩의 모든 피드백 조회
    print("\n[5] 리딩의 모든 피드백 조회")

    response = requests.get(
        f"{BASE_URL}/api/v1/readings/{reading_id}/feedback"
    )
    print_response("피드백 조회", response)

    if response.status_code == 200:
        feedbacks = response.json()
        print(f"\n✅ 피드백 {len(feedbacks)}개 조회 완료")
    else:
        print("\n❌ 피드백 조회 실패")

    # 6. 피드백 통계 조회
    print("\n[6] 피드백 통계 조회")

    response = requests.get(
        f"{BASE_URL}/api/v1/readings/{reading_id}/feedback/stats"
    )
    print_response("피드백 통계", response)

    if response.status_code == 200:
        print("\n✅ 피드백 통계 조회 완료")
    else:
        print("\n❌ 피드백 통계 조회 실패")

    # 7. 피드백 수정
    print("\n[7] 피드백 수정")

    update_data = {
        "rating": 4,
        "comment": "수정된 피드백입니다. 전반적으로 좋았지만 약간의 개선 여지가 있습니다."
    }

    response = requests.put(
        f"{BASE_URL}/api/v1/feedback/{feedback_id}",
        json=update_data,
        headers=headers
    )
    print_response("피드백 수정", response)

    if response.status_code == 200:
        print("\n✅ 피드백 수정 완료")
    else:
        print("\n❌ 피드백 수정 실패")

    # 8. 피드백 삭제
    print("\n[8] 피드백 삭제")

    response = requests.delete(
        f"{BASE_URL}/api/v1/feedback/{feedback_id}",
        headers=headers
    )

    print(f"\n{'='*60}")
    print("피드백 삭제")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")

    if response.status_code == 204:
        print("\n✅ 피드백 삭제 완료 (204 No Content)")
    else:
        print("\n❌ 피드백 삭제 실패")
        print(f"Response: {response.text}")

    print("\n" + "="*60)
    print("✅ 모든 테스트 완료!")
    print("="*60)

if __name__ == "__main__":
    main()
