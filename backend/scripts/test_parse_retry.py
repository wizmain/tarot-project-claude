#!/usr/bin/env python3
"""
JSON 파싱 재시도 로직 테스트

이 스크립트는 파싱이 실패할 가능성이 있는 상황을 시뮬레이션하여
재시도 로직이 제대로 작동하는지 확인합니다.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ai.prompt_engine.response_parser import ResponseParser
from src.ai.prompt_engine.schemas import JSONExtractionError


def test_parse_retry_logic():
    """재시도가 필요한 케이스들 테스트"""

    print("=" * 80)
    print("JSON 파싱 재시도 로직 테스트")
    print("=" * 80)

    # Test 1: 잘린 JSON (max_tokens 부족)
    print("\n[Test 1] 잘린 JSON - 파싱 실패 예상")
    truncated_json = """{
  "cards": [
    {
      "card_id": "major_01",
      "position": "single",
      "interpretation": "이 카드가 선택된 것은 우연이 아닙니다. The Magician은 당신이 지금 현재 가진 능력과 잠재력을 상징합니다.",
      "key_message": "당신의 능력과 의지를 발휘할 때입니다"
    }
  ],
  "card_relationships": "단일 카드 리딩입니다.",
  "overall_reading": "The Magician 카드는...",
  "advice": {
    "immediate_action": "오늘 당장 실행하세요",
    "short_term": "2-3주 내에 집중하세요",
    "long_term": "장기적으로 준비하세요",
    "mindset": "자신감을 가지"""  # 여기서 잘림!

    try:
        ResponseParser.parse(truncated_json)
        print("❌ 예상과 달리 파싱 성공 (버그일 수 있음)")
    except JSONExtractionError as e:
        print(f"✓ 예상대로 파싱 실패: {str(e)[:100]}...")
        if "불완전" in str(e) or "잘린" in str(e):
            print("✓ 잘린 응답 감지 로직 작동")

    # Test 2: 개행문자가 포함된 JSON (sanitize로 해결 가능)
    print("\n[Test 2] 개행문자 포함 JSON - sanitize 후 파싱 성공 예상")
    json_with_newlines = """{
  "cards": [
    {
      "card_id": "major_01",
      "position": "single",
      "interpretation": "이것은 테스트입니다.
새로운 줄입니다.",
      "key_message": "테스트"
    }
  ],
  "card_relationships": "테스트",
  "overall_reading": "테스트",
  "advice": {
    "immediate_action": "테스트",
    "short_term": "테스트",
    "long_term": "테스트",
    "mindset": "테스트",
    "cautions": "테스트"
  },
  "summary": "테스트"
}"""

    try:
        result = ResponseParser.parse(json_with_newlines)
        print(f"✓ 파싱 성공!")
        has_newline = '\n' in result.cards[0].interpretation
        print(f"  interpretation에 개행문자 포함: {has_newline}")
    except Exception as e:
        print(f"❌ 파싱 실패 (sanitize가 작동하지 않음): {e}")

    # Test 3: 완전한 JSON
    print("\n[Test 3] 완전한 JSON - 즉시 파싱 성공 예상")
    complete_json = """{
  "cards": [
    {
      "card_id": "major_01",
      "position": "single",
      "interpretation": "완전한 해석입니다.",
      "key_message": "핵심 메시지"
    }
  ],
  "card_relationships": "관계 설명",
  "overall_reading": "전체 리딩",
  "advice": {
    "immediate_action": "즉시 행동",
    "short_term": "단기 조언",
    "long_term": "장기 조언",
    "mindset": "마음가짐",
    "cautions": "주의사항"
  },
  "summary": "요약"
}"""

    try:
        result = ResponseParser.parse(complete_json)
        print(f"✓ 파싱 성공!")
        print(f"  summary: {result.summary}")
    except Exception as e:
        print(f"❌ 파싱 실패: {e}")

    print("\n" + "=" * 80)
    print("재시도 로직 동작 방식:")
    print("=" * 80)
    print("""
1. 첫 번째 시도: max_tokens=1500 (원카드) 또는 2500 (쓰리카드)
2. 파싱 실패 시:
   - 경고 로그 출력
   - max_tokens를 30% 증가 (1500 → 1950, 2500 → 3250)
   - 새로운 LLM 호출로 재시도
3. 최대 2번 재시도 (총 3번 시도)
4. 모든 시도의 LLM 로그 저장 (purpose: "parse_retry")

이 로직은 실제 API 호출에서 작동하며, 단위 테스트로는 검증하기 어렵습니다.
실제 리딩 생성 시 로그를 확인하여 재시도가 발생했는지 확인할 수 있습니다.
    """)

    print("\n💡 실제 재시도 확인 방법:")
    print("1. 백엔드 로그에서 '[CreateReading] 파싱 재시도' 메시지 찾기")
    print("2. LLM usage 로그에서 'parse_retry' purpose 확인")
    print("3. 총 LLM attempts 수가 1보다 큰지 확인")


if __name__ == "__main__":
    test_parse_retry_logic()
