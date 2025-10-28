"""
ResponseParser 테스트 모듈

이 모듈의 목적:
- ResponseParser 클래스의 모든 기능을 테스트
- JSON 추출 로직 검증
- Pydantic 스키마 검증 테스트
- 에러 핸들링 검증

주요 테스트:
- JSON 추출 (Markdown 코드 블록, 순수 JSON)
- 정상 응답 파싱
- 필수 필드 검증
- 길이 제약 검증
- 에러 케이스 (빈 응답, 잘못된 JSON, 스키마 불일치)

TASK-025: 응답 파서 구현 테스트
"""
import pytest
import json

from src.ai.prompt_engine.response_parser import ResponseParser
from src.ai.prompt_engine.schemas import (
    ReadingResponse,
    ParseError,
    JSONExtractionError,
    ValidationError
)


class TestResponseParserJSONExtraction:
    """JSON 추출 기능 테스트"""

    def test_extract_json_from_markdown_json_block(self):
        """Markdown ```json ... ``` 블록에서 JSON 추출"""
        text = '''
```json
{
  "cards": [],
  "card_relationships": "test",
  "overall_reading": "test reading",
  "advice": {},
  "summary": "test summary"
}
```
'''
        result = ResponseParser.extract_json(text)
        assert result.strip().startswith('{')
        assert result.strip().endswith('}')
        # JSON 파싱 가능 여부 확인
        data = json.loads(result)
        assert 'cards' in data

    def test_extract_json_from_markdown_code_block(self):
        """Markdown ``` ... ``` 블록에서 JSON 추출 (언어 지정 없음)"""
        text = '''
```
{
  "cards": [],
  "summary": "test"
}
```
'''
        result = ResponseParser.extract_json(text)
        data = json.loads(result)
        assert 'cards' in data

    def test_extract_json_from_pure_json(self):
        """순수 JSON 텍스트에서 추출"""
        text = '{"cards": [], "summary": "test"}'
        result = ResponseParser.extract_json(text)
        data = json.loads(result)
        assert 'cards' in data

    def test_extract_json_with_extra_text_before_and_after(self):
        """JSON 앞뒤에 불필요한 텍스트가 있는 경우"""
        text = '''
Here is your reading:

{"cards": [], "summary": "test"}

Thank you!
'''
        result = ResponseParser.extract_json(text)
        data = json.loads(result)
        assert 'cards' in data

    def test_extract_json_case_insensitive_json_tag(self):
        """대소문자 구분 없이 ```JSON 블록 처리"""
        text = '''
```JSON
{"cards": [], "summary": "test"}
```
'''
        result = ResponseParser.extract_json(text)
        data = json.loads(result)
        assert 'cards' in data

    def test_extract_json_fails_with_no_json(self):
        """JSON이 없는 텍스트는 실패"""
        text = "This is just plain text without any JSON"
        with pytest.raises(JSONExtractionError) as exc_info:
            ResponseParser.extract_json(text)
        assert "유효한 JSON을 찾을 수 없습니다" in str(exc_info.value)

    def test_extract_json_fails_with_incomplete_braces(self):
        """불완전한 중괄호는 실패"""
        text = "{"
        with pytest.raises(JSONExtractionError):
            ResponseParser.extract_json(text)


class TestResponseParserParsing:
    """응답 파싱 기능 테스트"""

    @pytest.fixture
    def valid_reading_json(self):
        """유효한 리딩 응답 JSON"""
        return {
            "cards": [
                {
                    "card_id": "major_0",
                    "position": "present",
                    "interpretation": "바보 카드는 새로운 시작을 상징합니다. " * 5,  # 충분한 길이
                    "key_message": "새로운 시작의 시간입니다"
                }
            ],
            "card_relationships": "단일 카드 리딩으로 집중된 에너지를 나타냅니다. " * 2,
            "overall_reading": "타로는 당신에게 새로운 시작의 시기임을 알려주고 있습니다. " * 5,
            "advice": {
                "immediate_action": "오늘 당장 시작할 수 있는 작은 일을 하나 선택해보세요. " * 2,
                "short_term": "앞으로 2주 동안은 새로운 경험에 열린 마음을 유지하세요. " * 2,
                "long_term": "향후 몇 달간은 자신만의 길을 만들어가는 과정이 될 것입니다. " * 2,
                "mindset": "초심자의 마음을 유지하세요. 배움 자체가 가치있습니다. " * 2,
                "cautions": "지나친 무모함은 피하세요. 균형을 찾으세요. " * 2
            },
            "summary": "새로운 시작을 받아들이고 순수한 마음으로 성장하세요"
        }

    def test_parse_valid_json_response(self, valid_reading_json):
        """유효한 JSON 응답 파싱 성공"""
        text = json.dumps(valid_reading_json, ensure_ascii=False)
        reading = ResponseParser.parse(text)

        assert isinstance(reading, ReadingResponse)
        assert len(reading.cards) == 1
        assert reading.cards[0].card_id == "major_0"
        assert reading.summary == "새로운 시작을 받아들이고 순수한 마음으로 성장하세요"

    def test_parse_json_with_markdown_block(self, valid_reading_json):
        """Markdown 코드 블록으로 감싸진 JSON 파싱"""
        json_str = json.dumps(valid_reading_json, ensure_ascii=False, indent=2)
        text = f"```json\n{json_str}\n```"

        reading = ResponseParser.parse(text)
        assert isinstance(reading, ReadingResponse)
        assert len(reading.cards) == 1

    def test_parse_three_card_reading(self):
        """3장 카드 리딩 파싱"""
        three_card_json = {
            "cards": [
                {
                    "card_id": "major_0",
                    "position": "past",
                    "interpretation": "과거에는 순수한 시작의 에너지가 있었습니다. " * 5,
                    "key_message": "순수한 시작점"
                },
                {
                    "card_id": "major_1",
                    "position": "present",
                    "interpretation": "현재는 능력을 발휘할 시기입니다. " * 5,
                    "key_message": "능력 발휘의 시간"
                },
                {
                    "card_id": "wands_01",
                    "position": "future",
                    "interpretation": "미래에는 새로운 창조적 에너지가 시작됩니다. " * 5,
                    "key_message": "창조적 시작"
                }
            ],
            "card_relationships": "과거의 순수한 시작이 현재의 능력으로 이어지고 미래의 창조로 발전합니다. " * 3,
            "overall_reading": "전체적으로 성장과 발전의 여정을 보여주고 있습니다. " * 8,
            "advice": {
                "immediate_action": "오늘 당장 실천할 수 있는 것을 시작하세요. " * 3,
                "short_term": "2주간 새로운 경험에 집중하세요. " * 3,
                "long_term": "장기적으로 자신만의 길을 만들어가세요. " * 3,
                "mindset": "성장 마인드셋을 유지하세요. " * 3,
                "cautions": "조급함은 피하세요. " * 3
            },
            "summary": "과거의 시작이 현재의 능력으로, 미래의 창조로 이어집니다"
        }

        text = json.dumps(three_card_json, ensure_ascii=False)
        reading = ResponseParser.parse(text)

        assert len(reading.cards) == 3
        assert reading.cards[0].position == "past"
        assert reading.cards[1].position == "present"
        assert reading.cards[2].position == "future"

    def test_parse_empty_response_fails(self):
        """빈 응답은 실패"""
        with pytest.raises(ParseError) as exc_info:
            ResponseParser.parse("")
        assert "비어있습니다" in str(exc_info.value)

    def test_parse_whitespace_only_response_fails(self):
        """공백만 있는 응답은 실패"""
        with pytest.raises(ParseError):
            ResponseParser.parse("   \n\n  \t  ")

    def test_parse_invalid_json_fails(self):
        """잘못된 JSON 형식은 실패"""
        text = '{"cards": [}, "invalid": json}'
        with pytest.raises(JSONExtractionError) as exc_info:
            ResponseParser.parse(text)
        assert "유효하지 않은 JSON" in str(exc_info.value)


class TestResponseParserValidation:
    """Pydantic 검증 기능 테스트"""

    def test_validate_missing_required_field(self):
        """필수 필드 누락 시 실패"""
        incomplete_data = {
            "cards": [
                {
                    "card_id": "major_0",
                    "position": "present",
                    "interpretation": "test interpretation " * 10,
                    "key_message": "test message"
                }
            ],
            # overall_reading 필드 누락
            "card_relationships": "test relationships " * 5,
            "advice": {
                "immediate_action": "test action " * 5,
                "short_term": "test short " * 5,
                "long_term": "test long " * 5,
                "mindset": "test mindset " * 5,
                "cautions": "test cautions " * 5
            },
            "summary": "test summary"
        }

        text = json.dumps(incomplete_data)
        with pytest.raises(ValidationError) as exc_info:
            ResponseParser.parse(text)
        assert "필수 필드 누락" in str(exc_info.value) or "overall_reading" in str(exc_info.value)

    def test_validate_interpretation_too_short(self):
        """해석이 너무 짧으면 실패 (최소 50자)"""
        data = {
            "cards": [
                {
                    "card_id": "major_0",
                    "position": "present",
                    "interpretation": "short",  # 너무 짧음
                    "key_message": "test message"
                }
            ],
            "card_relationships": "test relationships " * 5,
            "overall_reading": "test overall " * 15,
            "advice": {
                "immediate_action": "test action " * 5,
                "short_term": "test short " * 5,
                "long_term": "test long " * 5,
                "mindset": "test mindset " * 5,
                "cautions": "test cautions " * 5
            },
            "summary": "test summary"
        }

        text = json.dumps(data)
        with pytest.raises(ValidationError) as exc_info:
            ResponseParser.parse(text)
        # Pydantic V2는 영문 메시지를 반환하므로 "at least" 또는 한글화된 메시지 확인
        error_msg = str(exc_info.value).lower()
        assert "at least" in error_msg or "interpretation" in error_msg

    def test_validate_summary_too_long(self):
        """요약이 너무 길면 실패 (최대 150자)"""
        data = {
            "cards": [
                {
                    "card_id": "major_0",
                    "position": "present",
                    "interpretation": "test interpretation " * 10,
                    "key_message": "test message"
                }
            ],
            "card_relationships": "test relationships " * 5,
            "overall_reading": "test overall " * 15,
            "advice": {
                "immediate_action": "test action " * 5,
                "short_term": "test short " * 5,
                "long_term": "test long " * 5,
                "mindset": "test mindset " * 5,
                "cautions": "test cautions " * 5
            },
            "summary": "x" * 200  # 너무 김
        }

        text = json.dumps(data)
        with pytest.raises(ValidationError) as exc_info:
            ResponseParser.parse(text)
        error_msg = str(exc_info.value).lower()
        assert "at most" in error_msg or "summary" in error_msg

    def test_validate_empty_cards_array(self):
        """빈 카드 배열은 실패"""
        data = {
            "cards": [],  # 비어있음
            "card_relationships": "test relationships " * 5,
            "overall_reading": "test overall " * 15,
            "advice": {
                "immediate_action": "test action " * 5,
                "short_term": "test short " * 5,
                "long_term": "test long " * 5,
                "mindset": "test mindset " * 5,
                "cautions": "test cautions " * 5
            },
            "summary": "test summary"
        }

        text = json.dumps(data)
        with pytest.raises(ValidationError) as exc_info:
            ResponseParser.parse(text)
        error_msg = str(exc_info.value).lower()
        assert "at least" in error_msg or "cards" in error_msg or "최소 1개" in str(exc_info.value)

    def test_validate_duplicate_positions(self):
        """중복된 position은 실패"""
        data = {
            "cards": [
                {
                    "card_id": "major_0",
                    "position": "present",
                    "interpretation": "test interpretation 1 " * 10,
                    "key_message": "test message 1"
                },
                {
                    "card_id": "major_1",
                    "position": "present",  # 중복!
                    "interpretation": "test interpretation 2 " * 10,
                    "key_message": "test message 2"
                }
            ],
            "card_relationships": "test relationships " * 5,
            "overall_reading": "test overall " * 15,
            "advice": {
                "immediate_action": "test action " * 5,
                "short_term": "test short " * 5,
                "long_term": "test long " * 5,
                "mindset": "test mindset " * 5,
                "cautions": "test cautions " * 5
            },
            "summary": "test summary"
        }

        text = json.dumps(data)
        with pytest.raises(ValidationError) as exc_info:
            ResponseParser.parse(text)
        assert "중복" in str(exc_info.value)

    def test_validate_wrong_type_for_cards(self):
        """cards가 배열이 아니면 실패"""
        data = {
            "cards": "not an array",  # 잘못된 타입
            "card_relationships": "test",
            "overall_reading": "test overall " * 15,
            "advice": {
                "immediate_action": "test action " * 5,
                "short_term": "test short " * 5,
                "long_term": "test long " * 5,
                "mindset": "test mindset " * 5,
                "cautions": "test cautions " * 5
            },
            "summary": "test summary"
        }

        text = json.dumps(data)
        with pytest.raises(ValidationError) as exc_info:
            ResponseParser.parse(text)
        error_msg = str(exc_info.value).lower()
        assert "list" in error_msg or "cards" in error_msg or "타입" in str(exc_info.value)


class TestResponseParserUtilityMethods:
    """유틸리티 메서드 테스트"""

    @pytest.fixture
    def sample_reading(self):
        """샘플 ReadingResponse 객체"""
        from src.ai.prompt_engine.schemas import ReadingResponse, CardInterpretation, Advice

        return ReadingResponse(
            cards=[
                CardInterpretation(
                    card_id="major_0",
                    position="present",
                    interpretation="바보 카드는 새로운 시작을 상징합니다. " * 5,
                    key_message="새로운 시작"
                )
            ],
            card_relationships="단일 카드 에너지 " * 5,
            overall_reading="새로운 시작의 시기입니다. " * 10,
            advice=Advice(
                immediate_action="오늘 시작하세요. " * 5,
                short_term="2주간 집중하세요. " * 5,
                long_term="장기적으로 성장하세요. " * 5,
                mindset="긍정적으로 생각하세요. " * 5,
                cautions="조급함을 피하세요. " * 5
            ),
            summary="새로운 시작을 받아들이세요"
        )

    def test_to_dict(self, sample_reading):
        """ReadingResponse를 딕셔너리로 변환"""
        result = ResponseParser.to_dict(sample_reading)

        assert isinstance(result, dict)
        assert 'cards' in result
        assert 'summary' in result
        assert result['cards'][0]['card_id'] == 'major_0'

    def test_to_json(self, sample_reading):
        """ReadingResponse를 JSON 문자열로 변환"""
        result = ResponseParser.to_json(sample_reading)

        assert isinstance(result, str)
        # JSON 파싱 가능 여부 확인
        data = json.loads(result)
        assert 'cards' in data
        assert data['summary'] == "새로운 시작을 받아들이세요"

    def test_to_json_with_custom_indent(self, sample_reading):
        """커스텀 들여쓰기로 JSON 생성"""
        result = ResponseParser.to_json(sample_reading, indent=4)

        assert isinstance(result, str)
        assert '    ' in result  # 4칸 들여쓰기 확인
