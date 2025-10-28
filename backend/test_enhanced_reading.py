"""
개선된 프롬프트 테스트 스크립트

카드와 질문의 연관성이 강화된 해석을 테스트합니다.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

# 1. 회원가입 (새 사용자 생성)
print("[1] 회원가입...")
from uuid import uuid4

signup_data = {
    "email": f"test_{uuid4().hex[:8]}@example.com",
    "password": "Test1234!",
    "username": f"test_user_{uuid4().hex[:6]}"
}

response = requests.post(f"{BASE_URL}/api/v1/auth/signup", json=signup_data)
if response.status_code == 201:
    access_token = response.json()["access_token"]
    print(f"✅ 회원가입 성공!")
    print(f"Email: {signup_data['email']}")
else:
    print(f"❌ 회원가입 실패: {response.status_code}")
    print(response.text)
    exit(1)

headers = {"Authorization": f"Bearer {access_token}"}

# 2. 원카드 리딩 테스트 (진로 고민)
print("\n" + "="*60)
print("[2] 원카드 리딩 테스트 - 진로 고민")
print("="*60)

reading_request = {
    "question": "지금 회사를 그만두고 새로운 일을 시작하는 것이 맞는 선택일까요? 불안하지만 더 이상 현재 일에서 의미를 찾기 어렵습니다.",
    "spread_type": "one_card",
    "category": "career"
}

response = requests.post(
    f"{BASE_URL}/api/v1/readings",
    headers=headers,
    json=reading_request
)

if response.status_code == 201:
    reading = response.json()
    print(f"\n✅ 리딩 성공!")
    print(f"\nReading ID: {reading['id']}")
    print(f"질문: {reading['question']}")
    print(f"\n{'='*60}")
    print("뽑힌 카드:")
    print(f"{'='*60}")
    for card in reading['cards']:
        print(f"- {card['name']} ({card['orientation_korean']})")

    print(f"\n{'='*60}")
    print("AI 해석:")
    print(f"{'='*60}")
    print(reading['interpretation'])

else:
    print(f"\n❌ 리딩 실패: {response.status_code}")
    print(response.text)

# 3. 쓰리카드 리딩 테스트 (관계 고민)
print("\n" + "="*60)
print("[3] 쓰리카드 리딩 테스트 - 관계 고민")
print("="*60)

reading_request = {
    "question": "오랜 친구와의 관계가 최근 멀어지고 있습니다. 이 관계를 회복할 수 있을까요?",
    "spread_type": "three_card_past_present_future",
    "category": "relationship"
}

response = requests.post(
    f"{BASE_URL}/api/v1/readings",
    headers=headers,
    json=reading_request
)

if response.status_code == 201:
    reading = response.json()
    print(f"\n✅ 리딩 성공!")
    print(f"\nReading ID: {reading['id']}")
    print(f"질문: {reading['question']}")
    print(f"\n{'='*60}")
    print("뽑힌 카드:")
    print(f"{'='*60}")
    for i, card in enumerate(reading['cards'], 1):
        position_names = ["과거", "현재", "미래"]
        print(f"{position_names[i-1]}: {card['name']} ({card['orientation_korean']})")

    print(f"\n{'='*60}")
    print("AI 해석:")
    print(f"{'='*60}")
    print(reading['interpretation'])

else:
    print(f"\n❌ 리딩 실패: {response.status_code}")
    print(response.text)

print("\n" + "="*60)
print("✅ 테스트 완료!")
print("="*60)
print("\n개선 사항 확인:")
print("1. AI가 질문을 깊이 분석했는가?")
print("2. 카드와 질문의 연관성을 명확히 설명했는가?")
print("3. '우연이 아닌 필연'으로 해석했는가?")
print("4. 사용자 상황에 맞는 구체적인 조언을 제공했는가?")
