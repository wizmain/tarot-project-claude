#!/usr/bin/env python3
"""
JSON 정규화 로직 테스트 스크립트
실제 개행문자가 포함된 JSON 문자열을 파싱할 수 있는지 검증
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ai.prompt_engine.response_parser import ResponseParser
import json


def test_sanitize_json_with_newlines():
    """실제 개행문자가 포함된 JSON 테스트"""

    # 실제 LLM이 반환할 수 있는 형태의 JSON (문자열 값에 실제 개행문자 포함)
    json_with_newlines = """{
  "cards": [
    {
      "card_id": "cups_10",
      "position": "past",
      "interpretation": "과거의 Ten of Cups 카드는 가족 간의 불화와 갈등을 보여줍니다.
이상적인 가정 이미지와 현실 사이의 간극이 있었던 것으로 보입니다.
과거에 경험했던 감정적 단절과 불화가 현재의 상황에 영향을 미치고 있는 것 같습니다.",
      "key_message": "과거의 가족 갈등이 현재에 영향을 미치고 있음"
    }
  ],
  "card_relationships": "이 세 장의 카드는 질문자의 과거-현재-미래를 연결하여 보여줍니다.
과거의 가족 갈등이 현재의 상실감과 슬픔으로 이어지고 있습니다.",
  "overall_reading": "이 세 장의 타로 카드가 보여주는 전체적인 스토리는
질문자의 과거부터 현재, 그리고 미래에 이르기까지 지속되는
어려움과 고민의 여정입니다.",
  "advice": {
    "immediate_action": "지금 당장 과거의 상처를 인정하고
받아들이는 시간을 가져보세요.",
    "short_term": "상담이나 치유 활동을 통해
과거의 상처를 정화하세요.",
    "long_term": "새로운 삶의 방향을 모색해보세요.",
    "mindset": "자신에 대한 이해와 자신감을 가지세요.",
    "cautions": "다른 사람의 권위나 통제에
지나치게 의존하지 않도록 주의하세요."
  },
  "summary": "과거의 상처를 인정하고 현재에 집중하며, 자신만의 독립적인 길을 개척할 때입니다."
}"""

    print("=" * 80)
    print("테스트: 실제 개행문자가 포함된 JSON 파싱")
    print("=" * 80)

    try:
        # 1. sanitize_json 테스트
        print("\n[1단계] sanitize_json 호출...")
        sanitized = ResponseParser.sanitize_json(json_with_newlines)
        print("✓ JSON 정규화 성공")

        # 정규화된 결과 일부 출력
        print(f"\n정규화된 JSON 일부 (처음 300자):")
        print(sanitized[:300])
        print("...")

        # 2. json.loads 테스트
        print("\n[2단계] json.loads 호출...")
        data = json.loads(sanitized)
        print("✓ JSON 파싱 성공")

        # 3. 결과 검증
        print("\n[3단계] 결과 검증...")
        assert "cards" in data, "cards 필드가 없습니다"
        assert len(data["cards"]) == 1, f"cards 배열 길이가 1이 아닙니다: {len(data['cards'])}"
        assert "interpretation" in data["cards"][0], "interpretation 필드가 없습니다"

        # 파싱된 interpretation 내용 확인
        interpretation = data["cards"][0]["interpretation"]
        print(f"\n파싱된 interpretation:")
        print(interpretation)
        print(f"\n✓ 개행문자가 올바르게 포함되어 있음 (길이: {len(interpretation)}자)")

        # overall_reading 확인
        overall = data["overall_reading"]
        print(f"\n파싱된 overall_reading:")
        print(overall)
        print(f"\n✓ 개행문자가 올바르게 포함되어 있음 (길이: {len(overall)}자)")

        print("\n" + "=" * 80)
        print("모든 테스트 통과! ✓")
        print("=" * 80)
        return True

    except Exception as e:
        print(f"\n✗ 테스트 실패: {type(e).__name__}")
        print(f"에러 메시지: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_with_markdown_code_block():
    """Markdown 코드 블록으로 감싸진 JSON 테스트"""

    markdown_json = """```json
{
  "cards": [
    {
      "card_id": "major_0",
      "position": "single",
      "interpretation": "The Fool 카드는 새로운 시작을 의미합니다.
두려움 없이 앞으로 나아가세요.",
      "key_message": "새로운 시작의 순간"
    }
  ],
  "card_relationships": "단일 카드 리딩입니다.",
  "overall_reading": "당신은 지금 새로운 여정의 시작점에 있습니다.
과거의 두려움을 버리고 용기를 가지세요.",
  "advice": {
    "immediate_action": "첫 걸음을 내딛으세요.",
    "short_term": "작은 도전들을 시도해보세요.",
    "long_term": "꾸준히 전진하세요.",
    "mindset": "긍정적이고 개방적인 마음",
    "cautions": "지나친 무모함은 피하세요."
  },
  "summary": "새로운 시작을 두려워하지 마세요."
}
```"""

    print("\n" + "=" * 80)
    print("테스트: Markdown 코드 블록이 포함된 JSON 파싱")
    print("=" * 80)

    try:
        # extract_json이 markdown을 제거하고 정규화까지 수행
        print("\n[1단계] extract_json 호출...")
        extracted = ResponseParser.extract_json(markdown_json)
        print("✓ JSON 추출 및 정규화 성공")

        # json.loads 테스트
        print("\n[2단계] json.loads 호출...")
        data = json.loads(extracted)
        print("✓ JSON 파싱 성공")

        # 결과 검증
        print("\n[3단계] 결과 검증...")
        assert "cards" in data
        assert "overall_reading" in data

        print(f"\n파싱된 overall_reading:")
        print(data["overall_reading"])

        print("\n" + "=" * 80)
        print("Markdown 테스트 통과! ✓")
        print("=" * 80)
        return True

    except Exception as e:
        print(f"\n✗ 테스트 실패: {type(e).__name__}")
        print(f"에러 메시지: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_with_tabs_and_quotes():
    """탭과 따옴표가 포함된 JSON 테스트"""

    json_with_special = """{
  "cards": [
    {
      "card_id": "major_1",
      "position": "single",
      "interpretation": "The Magician은 '창조'와 '실현'을 의미합니다.\t당신의 능력을 믿으세요.",
      "key_message": "당신은 '마법사'입니다"
    }
  ],
  "card_relationships": "단일 카드",
  "overall_reading": "테스트\t문자열",
  "advice": {
    "immediate_action": "행동하세요",
    "short_term": "연습하세요",
    "long_term": "마스터하세요",
    "mindset": "긍정적",
    "cautions": "조심하세요"
  },
  "summary": "요약"
}"""

    print("\n" + "=" * 80)
    print("테스트: 탭과 따옴표가 포함된 JSON 파싱")
    print("=" * 80)

    try:
        sanitized = ResponseParser.sanitize_json(json_with_special)
        data = json.loads(sanitized)

        print("✓ 특수문자 처리 성공")
        print(f"\n파싱된 interpretation:")
        print(data["cards"][0]["interpretation"])

        print("\n" + "=" * 80)
        print("특수문자 테스트 통과! ✓")
        print("=" * 80)
        return True

    except Exception as e:
        print(f"\n✗ 테스트 실패: {type(e).__name__}")
        print(f"에러 메시지: {str(e)}")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("JSON 정규화 로직 테스트 시작")
    print("=" * 80)

    results = []

    # 테스트 실행
    results.append(("기본 개행문자 테스트", test_sanitize_json_with_newlines()))
    results.append(("Markdown 코드 블록 테스트", test_with_markdown_code_block()))
    results.append(("특수문자 테스트", test_with_tabs_and_quotes()))

    # 결과 요약
    print("\n\n" + "=" * 80)
    print("테스트 결과 요약")
    print("=" * 80)

    for name, result in results:
        status = "✓ 통과" if result else "✗ 실패"
        print(f"{name}: {status}")

    all_passed = all(result for _, result in results)

    print("\n" + "=" * 80)
    if all_passed:
        print("모든 테스트 통과! JSON 파싱 오류가 해결되었습니다.")
        print("=" * 80)
        sys.exit(0)
    else:
        print("일부 테스트 실패! 코드를 재검토해야 합니다.")
        print("=" * 80)
        sys.exit(1)
