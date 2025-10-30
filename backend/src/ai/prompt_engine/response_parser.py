"""
응답 파서 - AI 응답 텍스트를 구조화된 JSON으로 변환

이 모듈의 목적:
- AI Provider로부터 받은 텍스트 응답을 파싱하여 구조화된 데이터로 변환
- JSON 추출 및 검증 (Markdown 코드 블록 제거, 유효성 검사)
- Pydantic 스키마를 사용한 자동 검증
- 파싱 실패 시 명확한 에러 메시지 제공

주요 기능:
- parse(): AI 응답 텍스트를 ReadingResponse 객체로 변환
- extract_json(): 응답 텍스트에서 JSON 추출 (코드 블록 제거)
- validate_response(): Pydantic을 사용한 응답 검증
- 상세한 에러 핸들링 및 로깅

구현 사항:
- 정규표현식을 사용한 JSON 추출 (```json ... ``` 패턴 처리)
- json.loads()를 사용한 JSON 파싱
- Pydantic ValidationError 처리 및 사용자 친화적 에러 메시지 변환
- 로깅을 통한 파싱 과정 추적

TASK 참조:
- TASK-025: 응답 파서 구현

사용 예시:
    from src.ai.prompt_engine.response_parser import ResponseParser
    from src.ai.prompt_engine.schemas import ReadingResponse

    # AI로부터 받은 텍스트 응답
    ai_response = '''
    ```json
    {
      "cards": [...],
      "overall_reading": "..."
    }
    ```
    '''

    # 파싱 및 검증
    try:
        reading = ResponseParser.parse(ai_response)
        print(reading.summary)
    except ParseError as e:
        logger.error(f"파싱 실패: {e}")
"""
import json
import re
import logging
from typing import Dict, Any

from pydantic import ValidationError as PydanticValidationError

from src.ai.prompt_engine.schemas import (
    ReadingResponse,
    ParseError,
    JSONExtractionError,
    ValidationError
)

logger = logging.getLogger(__name__)


class ResponseParser:
    """
    AI 응답 파서

    AI Provider가 생성한 텍스트 응답을 파싱하여 구조화된
    ReadingResponse 객체로 변환합니다.

    주요 기능:
    - JSON 추출: Markdown 코드 블록이나 불필요한 텍스트 제거
    - JSON 파싱: 문자열을 Python 딕셔너리로 변환
    - 검증: Pydantic 스키마를 사용한 자동 검증
    """

    @staticmethod
    def parse(response_text: str) -> ReadingResponse:
        """
        AI 응답 텍스트를 파싱하여 ReadingResponse 객체 반환

        처리 과정:
        1. 빈 응답 체크
        2. JSON 추출 (코드 블록 제거)
        3. JSON 파싱
        4. Pydantic 검증
        5. ReadingResponse 객체 반환

        Args:
            response_text: AI Provider가 생성한 원본 텍스트 응답

        Returns:
            ReadingResponse: 검증된 타로 리딩 응답 객체

        Raises:
            ParseError: 빈 응답인 경우
            JSONExtractionError: JSON을 추출할 수 없는 경우
            ValidationError: 스키마 검증에 실패한 경우
        """
        if not response_text or not response_text.strip():
            logger.error("[ResponseParser] 빈 응답을 받았습니다")
            raise ParseError("AI 응답이 비어있습니다")

        logger.info(f"[ResponseParser] 응답 파싱 시작 (길이: {len(response_text)}자)")
        logger.debug("[ResponseParser] 원본 응답:\n%s", response_text)

        # 1. JSON 추출
        try:
            json_text = ResponseParser.extract_json(response_text)
            logger.debug(f"[ResponseParser] JSON 추출 성공 (길이: {len(json_text)}자)")
        except JSONExtractionError as e:
            logger.error(f"[ResponseParser] JSON 추출 실패: {e}")
            raise

        # 2. JSON 파싱
        try:
            data = json.loads(json_text)
            logger.debug("[ResponseParser] JSON 파싱 성공")
        except json.JSONDecodeError as e:
            logger.error(f"[ResponseParser] JSON 파싱 실패: {e}")
            raise JSONExtractionError(
                f"유효하지 않은 JSON 형식입니다: {e.msg} (line {e.lineno}, col {e.colno})"
            )

        # 3. Pydantic 검증
        try:
            reading = ResponseParser.validate_response(data)
            logger.info("[ResponseParser] 응답 검증 성공")
            return reading
        except ValidationError as e:
            logger.error(f"[ResponseParser] 검증 실패: {e}")
            raise

    @staticmethod
    def extract_json(text: str) -> str:
        """
        응답 텍스트에서 JSON 추출

        다음 형식들을 처리합니다:
        - ```json ... ``` (Markdown 코드 블록)
        - ``` ... ``` (일반 코드 블록)
        - 순수 JSON 텍스트

        Args:
            text: AI 응답 원본 텍스트

        Returns:
            str: 추출된 JSON 문자열

        Raises:
            JSONExtractionError: JSON을 찾을 수 없는 경우
        """
        text = text.strip()

        # 패턴 1: ```json ... ``` 형식
        json_block_pattern = r'```json\s*\n(.*?)\n```'
        match = re.search(json_block_pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            logger.debug("[ResponseParser] Markdown json 코드 블록 발견")
            return match.group(1).strip()

        # 패턴 2: ``` ... ``` 형식 (언어 지정 없음)
        code_block_pattern = r'```\s*\n(.*?)\n```'
        match = re.search(code_block_pattern, text, re.DOTALL)
        if match:
            logger.debug("[ResponseParser] Markdown 코드 블록 발견")
            return match.group(1).strip()

        # 패턴 3: { ... } 형식 (순수 JSON)
        # 첫 번째 { 부터 마지막 } 까지 추출
        first_brace = text.find('{')
        last_brace = text.rfind('}')

        if first_brace != -1 and last_brace != -1 and first_brace < last_brace:
            logger.debug("[ResponseParser] 순수 JSON 객체 발견")
            return text[first_brace:last_brace + 1]

        # JSON을 찾을 수 없음
        logger.error(f"[ResponseParser] JSON을 찾을 수 없습니다. 응답 일부: {text[:200]}...")
        raise JSONExtractionError(
            "응답에서 유효한 JSON을 찾을 수 없습니다. "
            "AI가 올바른 형식으로 응답하지 않았을 수 있습니다."
        )

    @staticmethod
    def validate_response(data: Dict[str, Any]) -> ReadingResponse:
        """
        파싱된 JSON 데이터를 Pydantic 스키마로 검증

        Args:
            data: JSON 파싱 결과 (Python dict)

        Returns:
            ReadingResponse: 검증된 리딩 응답 객체

        Raises:
            ValidationError: 스키마 검증 실패 시
        """
        try:
            # Pydantic이 자동으로 검증
            reading = ReadingResponse(**data)
            logger.debug(
                f"[ResponseParser] 검증 성공: "
                f"{len(reading.cards)}개 카드, "
                f"요약={reading.summary[:30]}..."
            )
            return reading

        except PydanticValidationError as e:
            # Pydantic 에러를 사용자 친화적 메시지로 변환
            errors = e.errors()
            error_messages = []

            for error in errors:
                field = ' -> '.join(str(loc) for loc in error['loc'])
                msg = error['msg']
                error_type = error['type']

                if error_type == 'value_error.missing':
                    error_messages.append(f"필수 필드 누락: {field}")
                elif error_type == 'value_error.any_str.min_length':
                    error_messages.append(f"필드가 너무 짧습니다: {field} ({msg})")
                elif error_type == 'value_error.any_str.max_length':
                    error_messages.append(f"필드가 너무 깁니다: {field} ({msg})")
                elif error_type == 'value_error.list.min_items':
                    error_messages.append(f"항목이 부족합니다: {field} ({msg})")
                elif error_type == 'value_error.list.max_items':
                    error_messages.append(f"항목이 너무 많습니다: {field} ({msg})")
                elif 'type_error' in error_type:
                    error_messages.append(f"잘못된 타입: {field} ({msg})")
                else:
                    error_messages.append(f"{field}: {msg}")

            error_summary = '\n'.join(f"  - {msg}" for msg in error_messages)
            logger.error(f"[ResponseParser] Pydantic 검증 실패:\n{error_summary}")

            raise ValidationError(
                f"응답이 올바른 형식을 따르지 않습니다:\n{error_summary}"
            )

    @staticmethod
    def to_dict(reading: ReadingResponse) -> Dict[str, Any]:
        """
        ReadingResponse 객체를 딕셔너리로 변환

        데이터베이스 저장이나 API 응답을 위해 사용합니다.

        Args:
            reading: ReadingResponse 객체

        Returns:
            Dict[str, Any]: JSON 직렬화 가능한 딕셔너리
        """
        return reading.model_dump()

    @staticmethod
    def to_json(reading: ReadingResponse, indent: int = 2) -> str:
        """
        ReadingResponse 객체를 JSON 문자열로 변환

        Args:
            reading: ReadingResponse 객체
            indent: JSON 들여쓰기 (기본값: 2)

        Returns:
            str: JSON 문자열
        """
        import json
        # model_dump_json은 ensure_ascii 옵션이 없으므로 model_dump 후 json.dumps 사용
        return json.dumps(reading.model_dump(), indent=indent, ensure_ascii=False)
