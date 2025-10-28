"""
리딩 검증 로직 테스트

TASK-030: 리딩 결과 검증 로직
"""
import pytest
from src.ai.prompt_engine.reading_validator import ReadingValidator
from src.ai.prompt_engine.schemas import (
    ReadingResponse,
    CardInterpretation,
    Advice,
    ValidationError
)


class TestReadingValidator:
    """ReadingValidator 테스트 클래스"""

    @pytest.fixture
    def valid_one_card_reading(self):
        """유효한 원카드 리딩 응답"""
        return ReadingResponse(
            cards=[
                CardInterpretation(
                    card_id="fool",
                    position="present",
                    interpretation="이 카드는 새로운 시작과 모험을 상징합니다. " * 10,  # 100자 이상
                    key_message="새로운 시작을 두려워하지 마세요"
                )
            ],
            card_relationships=None,
            overall_reading="전체적으로 새로운 시작의 에너지가 강하게 나타나고 있습니다. " * 5,  # 150자 이상
            advice=Advice(
                immediate_action="오늘부터 새로운 계획을 시작하세요. 작은 단계부터 시작하는 것이 좋습니다.",
                short_term="한 달 동안 매일 조금씩 새로운 것을 시도해보세요. 실패를 두려워하지 마세요.",
                long_term="3개월 후에는 큰 변화를 경험할 것입니다. 지속적으로 노력하면 성공할 수 있습니다.",
                mindset="열린 마음으로 새로운 경험을 받아들이세요. 유연한 사고방식을 유지하세요.",
                cautions="너무 서두르지 마세요. 충분한 준비 없이 시작하면 실패할 수 있습니다."
            ),
            summary="새로운 시작의 시기입니다. 용기를 내어 도전하세요."
        )

    @pytest.fixture
    def valid_three_card_reading(self):
        """유효한 쓰리카드 리딩 응답"""
        return ReadingResponse(
            cards=[
                CardInterpretation(
                    card_id="past",
                    position="과거",
                    interpretation="과거에는 많은 노력을 기울였지만 성과가 보이지 않았습니다. " * 5,
                    key_message="인내심을 가지고 기다렸습니다"
                ),
                CardInterpretation(
                    card_id="present",
                    position="현재",
                    interpretation="현재는 전환점에 서있습니다. 새로운 기회가 다가오고 있습니다. " * 5,
                    key_message="변화의 시작을 맞이하고 있습니다"
                ),
                CardInterpretation(
                    card_id="future",
                    position="미래",
                    interpretation="미래에는 긍정적인 결과를 얻을 것입니다. 노력이 결실을 맺습니다. " * 5,
                    key_message="성공과 성취가 기다리고 있습니다"
                )
            ],
            card_relationships="세 카드는 성장과 발전의 여정을 보여줍니다. 과거의 인내가 현재의 기회로 이어지고 미래의 성공으로 완성됩니다.",
            overall_reading="전체적으로 긍정적인 흐름입니다. 과거의 노력이 헛되지 않았으며, 지금이 변화를 받아들일 시기입니다. " * 3,
            advice=Advice(
                immediate_action="다가오는 기회를 놓치지 마세요. 지금 행동을 시작하는 것이 중요합니다.",
                short_term="2주 안에 구체적인 계획을 세우고 실행하세요. 작은 성공을 쌓아가세요.",
                long_term="3개월 후에는 큰 변화를 경험할 것입니다. 지속적인 노력이 결실을 맺습니다.",
                mindset="긍정적인 태도를 유지하세요. 열린 마음으로 받아들이세요.",
                cautions="너무 조급해하지 마세요. 충분한 준비를 하고 진행하세요."
            ),
            summary="과거의 인내가 현재의 기회로, 미래의 성공으로 이어집니다."
        )

    def test_validate_card_count_success(self, valid_one_card_reading):
        """카드 수 검증 성공 테스트"""
        # 정상 케이스: 1장 기대, 1장 제공
        ReadingValidator.validate_card_count(valid_one_card_reading, expected_count=1)
        # 예외 발생하지 않으면 통과

    def test_validate_card_count_failure(self, valid_one_card_reading):
        """카드 수 검증 실패 테스트"""
        # 실패 케이스: 3장 기대, 1장 제공
        with pytest.raises(ValidationError) as exc_info:
            ReadingValidator.validate_card_count(valid_one_card_reading, expected_count=3)

        assert "카드 수가 일치하지 않습니다" in str(exc_info.value)

    def test_validate_korean_content_success(self, valid_one_card_reading):
        """한국어 응답 검증 성공 테스트"""
        ReadingValidator.validate_korean_content(valid_one_card_reading)
        # 예외 발생하지 않으면 통과

    def test_validate_korean_content_failure(self):
        """한국어 응답 검증 실패 테스트 (영어 응답)"""
        english_reading = ReadingResponse(
            cards=[
                CardInterpretation(
                    card_id="fool",
                    position="present",
                    interpretation="This card represents new beginnings and adventures. " * 10,
                    key_message="Don't be afraid of new starts"
                )
            ],
            overall_reading="Overall, the energy of new beginnings is strong. " * 5,
            advice=Advice(
                immediate_action="Start your new plan today. Begin with small steps.",
                short_term="Try something new every day for a month. Don't be afraid.",
                long_term="You will experience big changes in three months.",
                mindset="Keep an open mind to new experiences.",
                cautions="Don't rush too much. Prepare well before starting."
            ),
            summary="It's time for a new beginning. Have courage to challenge."
        )

        with pytest.raises(ValidationError) as exc_info:
            ReadingValidator.validate_korean_content(english_reading)

        assert "한국어 응답이 아닙니다" in str(exc_info.value)

    def test_validate_minimum_lengths_success(self, valid_one_card_reading):
        """최소 길이 검증 성공 테스트"""
        ReadingValidator.validate_minimum_lengths(
            valid_one_card_reading,
            min_interpretation=100,
            min_overall=150
        )
        # 예외 발생하지 않으면 통과

    def test_validate_minimum_lengths_short_interpretation(self):
        """해석 길이 부족 테스트"""
        short_reading = ReadingResponse(
            cards=[
                CardInterpretation(
                    card_id="fool",
                    position="present",
                    interpretation="짧은 해석",  # 100자 미만
                    key_message="메시지"
                )
            ],
            overall_reading="전체 리딩입니다. " * 20,
            advice=Advice(
                immediate_action="행동하세요. " * 10,
                short_term="목표를 세우세요. " * 10,
                long_term="장기적인 계획을 세우세요. " * 8,
                mindset="긍정적인 마음을 유지하세요. " * 8,
                cautions="주의하세요. " * 15
            ),
            summary="요약입니다. " * 10
        )

        with pytest.raises(ValidationError) as exc_info:
            ReadingValidator.validate_minimum_lengths(
                short_reading,
                min_interpretation=100,
                min_overall=150
            )

        assert "해석이 너무 짧습니다" in str(exc_info.value)

    def test_validate_minimum_lengths_short_overall(self):
        """전체 리딩 길이 부족 테스트"""
        short_overall_reading = ReadingResponse(
            cards=[
                CardInterpretation(
                    card_id="fool",
                    position="present",
                    interpretation="이 카드는 새로운 시작을 나타냅니다. " * 10,
                    key_message="새로운 시작의 메시지입니다"
                )
            ],
            overall_reading="짧은 전체 리딩",  # 150자 미만
            advice=Advice(
                immediate_action="행동하세요. " * 10,
                short_term="목표를 세우세요. " * 10,
                long_term="장기적인 계획을 세우세요. " * 8,
                mindset="긍정적인 마음을 유지하세요. " * 8,
                cautions="주의하세요. " * 15
            ),
            summary="요약입니다. " * 10
        )

        with pytest.raises(ValidationError) as exc_info:
            ReadingValidator.validate_minimum_lengths(
                short_overall_reading,
                min_interpretation=100,
                min_overall=150
            )

        assert "전체 리딩이 너무 짧습니다" in str(exc_info.value)

    def test_validate_reading_quality_success(self, valid_one_card_reading):
        """전체 품질 검증 성공 테스트"""
        ReadingValidator.validate_reading_quality(
            valid_one_card_reading,
            expected_card_count=1
        )
        # 예외 발생하지 않으면 통과

    def test_validate_reading_quality_three_card(self, valid_three_card_reading):
        """쓰리카드 품질 검증 성공 테스트"""
        ReadingValidator.validate_reading_quality(
            valid_three_card_reading,
            expected_card_count=3
        )
        # 예외 발생하지 않으면 통과

    def test_validate_required_fields_empty_cards(self):
        """필수 필드 검증: 빈 카드 리스트"""
        empty_cards_reading = ReadingResponse(
            cards=[],  # 빈 리스트
            overall_reading="전체 리딩입니다. " * 20,
            advice=Advice(
                immediate_action="행동하세요. " * 10,
                short_term="목표를 세우세요. " * 10,
                long_term="장기적인 계획을 세우세요. " * 8,
                mindset="긍정적인 마음을 유지하세요. " * 8,
                cautions="주의하세요. " * 15
            ),
            summary="요약입니다. " * 10
        )

        with pytest.raises(ValidationError) as exc_info:
            ReadingValidator._validate_required_fields(empty_cards_reading)

        assert "카드 리스트가 비어있습니다" in str(exc_info.value)

    def test_validate_required_fields_empty_advice(self):
        """필수 필드 검증: 빈 조언 필드"""
        empty_advice_reading = ReadingResponse(
            cards=[
                CardInterpretation(
                    card_id="fool",
                    position="present",
                    interpretation="해석입니다. " * 20,
                    key_message="핵심 메시지입니다"
                )
            ],
            overall_reading="전체 리딩입니다. " * 20,
            advice=Advice(
                immediate_action="",  # 빈 문자열
                short_term="목표를 세우세요. " * 10,
                long_term="장기적인 계획을 세우세요. " * 8,
                mindset="긍정적인 마음을 유지하세요. " * 8,
                cautions="주의하세요. " * 15
            ),
            summary="요약입니다. " * 10
        )

        with pytest.raises(ValidationError) as exc_info:
            ReadingValidator._validate_required_fields(empty_advice_reading)

        assert "immediate_action" in str(exc_info.value)

    def test_custom_min_lengths(self, valid_one_card_reading):
        """커스텀 최소 길이 설정 테스트"""
        # 더 짧은 최소 길이로 검증
        ReadingValidator.validate_reading_quality(
            valid_one_card_reading,
            expected_card_count=1,
            min_interpretation_length=50,
            min_overall_length=100
        )
        # 예외 발생하지 않으면 통과
