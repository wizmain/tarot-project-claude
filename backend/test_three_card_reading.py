"""
쓰리카드 리딩 API 테스트
"""
import requests
import json

# 테스트 데이터
test_data = {
    "question": "새로운 프로젝트를 시작하는 것에 대해 조언을 구합니다",
    "spread_type": "three_card_past_present_future",
    "category": "career"
}

print("=" * 80)
print("쓰리카드 리딩 테스트 시작")
print("=" * 80)
print(f"\n질문: {test_data['question']}")
print(f"스프레드 타입: {test_data['spread_type']}")
print(f"카테고리: {test_data['category']}")
print("\nAPI 호출 중...")

# POST 요청
response = requests.post(
    "http://localhost:8000/api/v1/readings/",
    json=test_data,
    headers={"Content-Type": "application/json"}
)

print(f"\n상태 코드: {response.status_code}")

if response.status_code == 201:
    result = response.json()
    print("\n✅ 리딩 생성 성공!")
    print("=" * 80)
    print(f"\nReading ID: {result['id']}")
    print(f"Spread Type: {result['spread_type']}")
    print(f"Question: {result['question']}")
    print(f"\n선택된 카드 ({len(result['cards'])}장):")

    for i, card_data in enumerate(result['cards'], 1):
        card = card_data['card']
        print(f"\n{i}. 위치: {card_data['position']}")
        print(f"   카드: {card['name']} ({card_data['orientation']})")
        print(f"   해석: {card_data['interpretation'][:100]}...")
        print(f"   핵심 메시지: {card_data['key_message']}")

    if result.get('card_relationships'):
        print(f"\n카드 관계성:\n{result['card_relationships'][:200]}...")

    print(f"\n전체 리딩:\n{result['overall_reading'][:200]}...")

    print(f"\n조언:")
    advice = result['advice']
    for key, value in advice.items():
        print(f"  - {key}: {value[:100]}...")

    print(f"\n요약: {result['summary']}")

else:
    print(f"\n❌ 실패: {response.status_code}")
    print(f"응답: {response.text}")

print("\n" + "=" * 80)
