"""
리딩 응답 검증 - AI 응답의 품질과 완성도 검증

이 모듈의 목적:
- AI가 생성한 리딩 응답의 품질 검증
- 필수 필드 존재 여부 확인
- 한국어 응답 여부 확인
- 최소 길이 요구사항 충족 확인
- 카드 수와 포지션 일치 확인

주요 기능:
- validate_reading_quality(): 전체 품질 검증 (한국어, 길이, 필수 필드)
- validate_korean_content(): 한국어 응답 검증
- validate_minimum_lengths(): 최소 길이 검증
- validate_card_count(): 카드 수 검증
- 검증 실패 시 상세한 에러 메시지 제공

구현 사항:
- 한국어 감지: 유니코드 범위 검사 (AC00-D7A3)
- 최소 길이 설정 가능 (기본 100자)
- 필수 필드 체크 (cards, overall_reading, advice, summary)
- ValidationError 예외 처리

TASK 참조:
- TASK-030: 리딩 결과 검증 로직

사용 예시:
    from src.ai.prompt_engine.reading_validator import ReadingValidator
    from src.ai.prompt_engine.schemas import ReadingResponse

    # ResponseParser로 파싱된 응답
    reading = ResponseParser.parse(ai_response)

    # 품질 검증
    try:
        ReadingValidator.validate_reading_quality(reading, expected_card_count=1)
        print("검증 통과!")
    except ValidationError as e:
        logger.error(f"검증 실패: {e}")
"""
import re
import logging
from typing import Optional

from src.ai.prompt_engine.schemas import ReadingResponse, ValidationError

logger = logging.getLogger(__name__)


class ReadingValidator:
    """
    타로 리딩 응답 검증기

    AI가 생성한 리딩 응답의 품질과 완성도를 검증합니다.
    검증 항목:
    - 필수 필드 존재 여부
    - 한국어 응답 여부
    - 최소 길이 요구사항
    - 카드 수 일치 여부
    """

    # 한국어 유니코드 범위 (가-힣)
    KOREAN_PATTERN = re.compile(r'[가-힣]')

    # 최소 길이 기준 (자)
    MIN_INTERPRETATION_LENGTH = 100  # 각 카드 해석 최소 길이
    MIN_OVERALL_READING_LENGTH = 100  # 전체 리딩 최소 길이
    MIN_KEY_MESSAGE_LENGTH = 5  # 핵심 메시지 최소 길이 (Pydantic schema와 일치)
    MIN_ADVICE_FIELD_LENGTH = 30  # 조언 각 필드 최소 길이 (Pydantic schema와 일치)
    MIN_SUMMARY_LENGTH = 10  # 요약 최소 길이 (Pydantic schema와 일치)

    @staticmethod
    def validate_reading_quality(
        reading: ReadingResponse,
        expected_card_count: int,
        min_interpretation_length: Optional[int] = None,
        min_overall_length: Optional[int] = None,
        spread_type: Optional[str] = None
    ) -> None:
        """
        리딩 응답의 전체 품질 검증

        검증 항목:
        1. 필수 필드 존재 확인
        2. 카드 수 일치 확인
        3. 한국어 응답 확인 (스프레드 타입별 조정)
        4. 최소 길이 요구사항 확인 (스프레드 타입별 조정)

        Args:
            reading: 검증할 ReadingResponse 객체
            expected_card_count: 예상 카드 수 (1, 3, or 10)
            min_interpretation_length: 해석 최소 길이 (기본값 사용 시 None)
            min_overall_length: 전체 리딩 최소 길이 (기본값 사용 시 None)
            spread_type: 스프레드 타입 (one_card, three_card, celtic_cross 등)

        Raises:
            ValidationError: 검증 실패 시
        """
        logger.info(f"[ReadingValidator] 리딩 품질 검증 시작 (카드 수: {expected_card_count}, 스프레드: {spread_type})")

        # 1. 필수 필드 존재 확인 (Pydantic에서 이미 검증되지만 재확인)
        ReadingValidator._validate_required_fields(reading)

        # 2. 카드 수 확인
        ReadingValidator.validate_card_count(reading, expected_card_count)

        # 3. 한국어 응답 확인 (스프레드 타입별 조정)
        ReadingValidator.validate_korean_content(reading, spread_type=spread_type)

        # 4. 최소 길이 검증 (스프레드 타입별 조정)
        # 스프레드 타입별 기본값 조정
        if min_interpretation_length is None:
            if spread_type == "celtic_cross" or expected_card_count == 10:
                # 켈틱 크로스는 카드가 많아서 각 카드 해석이 짧을 수 있음
                min_interpretation_length = 80
            else:
                min_interpretation_length = ReadingValidator.MIN_INTERPRETATION_LENGTH
        
        if min_overall_length is None:
            if spread_type == "celtic_cross" or expected_card_count == 10:
                # 켈틱 크로스는 전체 리딩이 더 길어야 함
                min_overall_length = 300
            elif expected_card_count == 1:
                # 원카드는 전체 리딩이 짧을 수 있음
                min_overall_length = 80
            else:
                min_overall_length = ReadingValidator.MIN_OVERALL_READING_LENGTH
        
        ReadingValidator.validate_minimum_lengths(reading, min_interpretation_length, min_overall_length)

        logger.info("[ReadingValidator] 리딩 품질 검증 완료 ✅")

    @staticmethod
    def _validate_required_fields(reading: ReadingResponse) -> None:
        """
        필수 필드 존재 여부 확인

        Args:
            reading: 검증할 ReadingResponse 객체

        Raises:
            ValidationError: 필수 필드가 없거나 비어있는 경우
        """
        required_fields = {
            "cards": reading.cards,
            "overall_reading": reading.overall_reading,
            "advice": reading.advice,
            "summary": reading.summary
        }

        for field_name, field_value in required_fields.items():
            if not field_value:
                raise ValidationError(
                    f"필수 필드가 비어있습니다: {field_name}"
                )

        # cards 리스트가 비어있지 않은지 확인
        if not reading.cards or len(reading.cards) == 0:
            raise ValidationError(
                "카드 리스트가 비어있습니다"
            )

        # advice 객체의 필드 확인
        if not reading.advice.immediate_action:
            raise ValidationError(
                "조언(immediate_action)이 비어있습니다"
            )
        if not reading.advice.short_term:
            raise ValidationError(
                "조언(short_term)이 비어있습니다"
            )

    @staticmethod
    def validate_card_count(reading: ReadingResponse, expected_count: int) -> None:
        """
        카드 수가 예상과 일치하는지 확인

        Args:
            reading: 검증할 ReadingResponse 객체
            expected_count: 예상 카드 수 (1 or 3)

        Raises:
            ValidationError: 카드 수가 일치하지 않는 경우
        """
        actual_count = len(reading.cards)
        if actual_count != expected_count:
            raise ValidationError(
                f"카드 수가 일치하지 않습니다. 예상: {expected_count}, 실제: {actual_count}"
            )

        logger.debug(f"[ReadingValidator] 카드 수 검증 통과: {actual_count}장")

    @staticmethod
    def validate_korean_content(reading: ReadingResponse, spread_type: Optional[str] = None) -> None:
        """
        응답이 한국어로 작성되었는지 확인

        한글 문자(가-힣)의 비율을 확인합니다.
        스프레드 타입별로 다른 기준을 적용합니다:
        - 일반 스프레드: 최소 12% (완화됨)
        - 켈틱 크로스: 최소 10% (더 관대함)

        Args:
            reading: 검증할 ReadingResponse 객체
            spread_type: 스프레드 타입 (celtic_cross인 경우 더 관대한 기준 적용)

        Raises:
            ValidationError: 한국어 비율이 낮은 경우
        """
        # 검증할 텍스트 수집
        text_to_check = []

        # 카드 해석
        for card in reading.cards:
            text_to_check.append(card.interpretation)
            text_to_check.append(card.key_message)

        # 전체 리딩
        text_to_check.append(reading.overall_reading)

        # 조언
        text_to_check.append(reading.advice.immediate_action)
        text_to_check.append(reading.advice.short_term)
        if reading.advice.mindset:
            text_to_check.append(reading.advice.mindset)

        # 요약
        text_to_check.append(reading.summary)

        # 전체 텍스트 합치기
        full_text = " ".join(text_to_check)
        total_chars = len(full_text)

        if total_chars == 0:
            raise ValidationError(
                "응답 텍스트가 비어있습니다"
            )

        # 한글 문자 카운트
        korean_chars = len(ReadingValidator.KOREAN_PATTERN.findall(full_text))
        korean_ratio = korean_chars / total_chars

        # 스프레드 타입별 최소 비율 설정
        if spread_type == "celtic_cross":
            min_korean_ratio = 0.10  # 켈틱 크로스는 더 관대하게
        else:
            min_korean_ratio = 0.12  # 일반 스프레드는 12% (기존 20%에서 완화)

        logger.debug(
            f"[ReadingValidator] 한국어 비율: {korean_ratio:.2%} "
            f"(한글: {korean_chars}, 전체: {total_chars}, 최소 요구: {min_korean_ratio:.0%})"
        )

        # 한글 비율이 최소 기준 미만이면 실패
        if korean_ratio < min_korean_ratio:
            raise ValidationError(
                f"한국어 응답이 아닙니다. 한글 비율: {korean_ratio:.2%} "
                f"(최소 {min_korean_ratio:.0%} 필요, 스프레드: {spread_type or '일반'})"
            )

        logger.debug("[ReadingValidator] 한국어 검증 통과 ✅")

    @staticmethod
    def validate_minimum_lengths(
        reading: ReadingResponse,
        min_interpretation: int,
        min_overall: int
    ) -> None:
        """
        각 필드의 최소 길이 요구사항 확인

        Args:
            reading: 검증할 ReadingResponse 객체
            min_interpretation: 카드 해석 최소 길이
            min_overall: 전체 리딩 최소 길이

        Raises:
            ValidationError: 최소 길이 미달인 경우
        """
        # 1. 각 카드의 해석 길이 확인
        for i, card in enumerate(reading.cards, 1):
            interp_length = len(card.interpretation)
            if interp_length < min_interpretation:
                raise ValidationError(
                    f"카드 {i}의 해석이 너무 짧습니다. "
                    f"최소 {min_interpretation}자 필요, 현재 {interp_length}자"
                )

            # 핵심 메시지 길이 확인
            key_msg_length = len(card.key_message)
            if key_msg_length < ReadingValidator.MIN_KEY_MESSAGE_LENGTH:
                raise ValidationError(
                    f"카드 {i}의 핵심 메시지가 너무 짧습니다. "
                    f"최소 {ReadingValidator.MIN_KEY_MESSAGE_LENGTH}자 필요, "
                    f"현재 {key_msg_length}자"
                )

        # 2. 전체 리딩 길이 확인
        overall_length = len(reading.overall_reading)
        if overall_length < min_overall:
            raise ValidationError(
                f"전체 리딩이 너무 짧습니다. "
                f"최소 {min_overall}자 필요, 현재 {overall_length}자"
            )

        # 3. 조언 필드 길이 확인
        advice_fields = {
            "immediate_action": reading.advice.immediate_action,
            "short_term": reading.advice.short_term,
        }

        for field_name, field_value in advice_fields.items():
            field_length = len(field_value)
            if field_length < ReadingValidator.MIN_ADVICE_FIELD_LENGTH:
                raise ValidationError(
                    f"조언({field_name})이 너무 짧습니다. "
                    f"최소 {ReadingValidator.MIN_ADVICE_FIELD_LENGTH}자 필요, "
                    f"현재 {field_length}자"
                )

        # 4. 요약 길이 확인
        summary_length = len(reading.summary)
        if summary_length < ReadingValidator.MIN_SUMMARY_LENGTH:
            raise ValidationError(
                f"요약이 너무 짧습니다. "
                f"최소 {ReadingValidator.MIN_SUMMARY_LENGTH}자 필요, "
                f"현재 {summary_length}자"
            )

        logger.debug("[ReadingValidator] 최소 길이 검증 통과 ✅")
