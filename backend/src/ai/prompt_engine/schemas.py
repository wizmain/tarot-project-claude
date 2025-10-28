"""
리딩 응답 스키마 - Pydantic 모델 정의

이 모듈의 목적:
- AI Provider로부터 받은 타로 리딩 응답의 데이터 구조 정의
- JSON 응답의 자동 검증 (타입, 필수 필드, 길이 제약)
- 타입 안전성 보장 및 IDE 자동완성 지원
- 응답 데이터의 일관성 유지

주요 기능:
- CardInterpretation: 개별 카드 해석 모델 (card_id, position, interpretation, key_message)
- Advice: 조언 모델 (immediate_action, short_term, long_term, mindset, cautions)
- ReadingResponse: 전체 리딩 응답 모델 (cards, card_relationships, overall_reading, advice, summary)
- 자동 검증: 필수 필드, 최소/최대 길이, 카드 개수 등

구현 사항:
- Pydantic BaseModel을 사용한 데이터 모델 정의
- Field를 사용한 세밀한 검증 규칙 설정
- validator를 사용한 커스텀 검증 로직
- 한글 에러 메시지 제공

TASK 참조:
- TASK-025: 응답 파서 구현

사용 예시:
    from src.ai.prompt_engine.schemas import ReadingResponse

    # JSON 데이터 검증
    data = {
        "cards": [...],
        "card_relationships": "...",
        "overall_reading": "...",
        "advice": {...},
        "summary": "..."
    }

    # Pydantic이 자동으로 검증
    reading = ReadingResponse(**data)

    # 타입 안전하게 접근
    for card in reading.cards:
        print(card.interpretation)
"""
from typing import List
from pydantic import BaseModel, Field, field_validator


class CardInterpretation(BaseModel):
    """
    개별 카드 해석 모델

    AI가 생성한 각 카드에 대한 해석을 담는 모델입니다.
    선택된 카드의 위치, 의미, 핵심 메시지를 포함합니다.
    """
    card_id: str = Field(
        ...,
        description="카드 ID (예: major_0, wands_01)",
        min_length=1
    )
    position: str = Field(
        ...,
        description="카드 위치 (예: past, present, future, single, situation, action, outcome)",
        min_length=1
    )
    interpretation: str = Field(
        ...,
        description="카드 해석 내용 (200-400자 권장)",
        min_length=50,
        max_length=1000
    )
    key_message: str = Field(
        ...,
        description="핵심 메시지 한 줄 (50자 이내)",
        min_length=5,
        max_length=100
    )

    class Config:
        """Pydantic 설정"""
        # JSON 스키마 생성 시 예시 포함
        schema_extra = {
            "example": {
                "card_id": "major_0",
                "position": "present",
                "interpretation": "바보 카드는 새로운 시작과 순수한 가능성을 상징합니다.",
                "key_message": "두려움 없이 새로운 여정을 시작할 때입니다"
            }
        }


class Advice(BaseModel):
    """
    조언 모델

    타로 리딩을 바탕으로 한 구체적인 조언을 담는 모델입니다.
    단기/중기/장기 행동 계획과 마음가짐, 주의사항을 포함합니다.
    """
    immediate_action: str = Field(
        ...,
        description="즉시 실천 가능한 행동 (100-200자)",
        min_length=30,
        max_length=500
    )
    short_term: str = Field(
        ...,
        description="단기 목표 및 집중 사항 (100-200자)",
        min_length=30,
        max_length=500
    )
    long_term: str = Field(
        ...,
        description="중장기 방향성 (100-200자)",
        min_length=30,
        max_length=500
    )
    mindset: str = Field(
        ...,
        description="유지해야 할 마음가짐 (100-200자)",
        min_length=30,
        max_length=500
    )
    cautions: str = Field(
        ...,
        description="주의사항이나 피해야 할 것 (100-200자)",
        min_length=30,
        max_length=500
    )

    class Config:
        """Pydantic 설정"""
        schema_extra = {
            "example": {
                "immediate_action": "오늘 당장 시작할 수 있는 작은 일을 하나 선택해보세요.",
                "short_term": "앞으로 2주 동안은 새로운 경험에 열린 마음을 유지하세요.",
                "long_term": "향후 몇 달간은 자신만의 길을 만들어가는 과정이 될 것입니다.",
                "mindset": "초심자의 마음을 유지하세요. 배워가는 과정 자체가 가치있습니다.",
                "cautions": "지나친 무모함은 피하세요. 자유로움과 신중함 사이의 균형을 찾으세요."
            }
        }


class ReadingResponse(BaseModel):
    """
    전체 타로 리딩 응답 모델

    AI Provider가 생성한 완전한 타로 리딩 응답을 담는 최상위 모델입니다.
    개별 카드 해석, 카드 간 관계, 종합 리딩, 조언, 요약을 포함합니다.
    """
    cards: List[CardInterpretation] = Field(
        ...,
        description="선택된 카드들의 해석 리스트",
        min_length=1,
        max_length=10
    )
    card_relationships: str = Field(
        ...,
        description="카드들 간의 관계와 연결성 설명 (150-300자)",
        min_length=20,
        max_length=800
    )
    overall_reading: str = Field(
        ...,
        description="종합 리딩 - 전체적인 메시지와 통찰 (300-500자)",
        min_length=100,
        max_length=1500
    )
    advice: Advice = Field(
        ...,
        description="구체적인 조언 객체"
    )
    summary: str = Field(
        ...,
        description="한 줄 요약 메시지 (80자 이내)",
        min_length=10,
        max_length=150
    )

    @field_validator('cards')
    @classmethod
    def validate_cards_count(cls, v):
        """
        카드 개수 검증

        Args:
            v: cards 리스트

        Returns:
            검증된 cards 리스트

        Raises:
            ValueError: 카드가 1개 미만인 경우
        """
        if len(v) < 1:
            raise ValueError("최소 1개의 카드 해석이 필요합니다")
        if len(v) > 10:
            raise ValueError("최대 10개의 카드만 지원됩니다")
        return v

    @field_validator('cards')
    @classmethod
    def validate_unique_positions(cls, v):
        """
        카드 위치 중복 검증

        같은 스프레드 내에서 동일한 position을 가진 카드가 있는지 확인합니다.

        Args:
            v: cards 리스트

        Returns:
            검증된 cards 리스트

        Raises:
            ValueError: 동일한 position이 중복된 경우
        """
        positions = [card.position for card in v]
        if len(positions) != len(set(positions)):
            raise ValueError("카드 위치(position)가 중복되었습니다")
        return v

    class Config:
        """Pydantic 설정"""
        schema_extra = {
            "example": {
                "cards": [
                    {
                        "card_id": "major_0",
                        "position": "past",
                        "interpretation": "과거에는 새로운 시작의 에너지가 있었습니다.",
                        "key_message": "순수한 시작점에서 출발했습니다"
                    }
                ],
                "card_relationships": "과거의 순수한 시작이 현재의 상황으로 이어지고 있습니다.",
                "overall_reading": "전체적으로 새로운 시작과 성장의 여정을 보여주고 있습니다.",
                "advice": {
                    "immediate_action": "오늘 작은 첫걸음을 내딛으세요.",
                    "short_term": "2주간 새로운 경험에 열린 마음을 유지하세요.",
                    "long_term": "자신만의 길을 만들어가세요.",
                    "mindset": "초심자의 마음을 유지하세요.",
                    "cautions": "지나친 무모함은 피하세요."
                },
                "summary": "새로운 시작을 받아들이고 성장하세요"
            }
        }


class ParseError(Exception):
    """
    응답 파싱 에러

    AI 응답을 파싱하는 과정에서 발생하는 모든 에러의 기본 클래스입니다.
    """
    pass


class JSONExtractionError(ParseError):
    """
    JSON 추출 에러

    응답 텍스트에서 유효한 JSON을 찾을 수 없을 때 발생합니다.
    """
    pass


class ValidationError(ParseError):
    """
    검증 에러

    파싱된 JSON이 ReadingResponse 스키마를 만족하지 못할 때 발생합니다.
    """
    pass
