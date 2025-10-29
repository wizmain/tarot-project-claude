"""
타로 리딩 Request/Response 스키마 정의

이 모듈의 목적:
- 리딩 API의 요청/응답 데이터 구조 정의
- Pydantic V2를 사용한 자동 검증 및 직렬화
- FastAPI와 데이터베이스 모델 간의 데이터 변환
- API 문서 자동 생성을 위한 스키마 제공

주요 스키마:
- ReadingRequest: 리딩 생성 요청
- ReadingCardResponse: 리딩에 사용된 카드 정보 응답
- ReadingResponse: 리딩 결과 응답
- ReadingListResponse: 리딩 목록 응답 (페이지네이션)

구현 사항:
- Pydantic V2 BaseModel 사용
- Field 검증 (min_length, max_length, 정규식 등)
- Optional 필드 처리
- datetime 자동 직렬화
- nested 모델 지원 (CardResponse 포함)

TASK 참조:
- TASK-027: 원카드 리딩 구현

사용 예시:
    from src.schemas.reading import ReadingRequest, ReadingResponse

    # 요청 검증
    request = ReadingRequest(
        question="새로운 직장으로 이직해야 할까요?",
        spread_type="one_card",
        category="career"
    )

    # 응답 생성
    response = ReadingResponse(
        id=reading.id,
        question=reading.question,
        cards=[...],
        overall_reading="...",
        advice={...},
        summary="..."
    )
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from src.schemas.card import CardResponse


class ReadingRequest(BaseModel):
    """
    타로 리딩 생성 요청 스키마

    클라이언트로부터 받는 리딩 요청 데이터를 검증합니다.
    """
    question: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="사용자의 질문 (5-500자)",
        examples=["새로운 직장으로 이직해야 할까요?"]
    )
    spread_type: str = Field(
        default="one_card",
        pattern="^(one_card|three_card_past_present_future|three_card_situation_action_outcome)$",
        description="스프레드 타입 (one_card, three_card_past_present_future, three_card_situation_action_outcome)",
        examples=["one_card"]
    )
    category: Optional[str] = Field(
        default=None,
        pattern="^(love|career|finance|health|personal_growth|spirituality)?$",
        description="리딩 카테고리 (love, career, finance, health, personal_growth, spirituality)",
        examples=["career"]
    )
    user_context: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="추가 컨텍스트 정보 (최대 1000자)",
        examples=["현재 3년차 개발자이며, 더 큰 회사로 이직을 고민 중입니다."]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "question": "새로운 프로젝트를 시작해야 할까요?",
                "spread_type": "one_card",
                "category": "career",
                "user_context": "현재 안정적인 직장에 다니고 있지만 새로운 도전을 하고 싶습니다."
            }
        }


class ReadingCardResponse(BaseModel):
    """
    리딩에 사용된 카드 정보 응답 스키마

    리딩 결과에 포함되는 개별 카드의 정보와 해석을 담습니다.
    """
    id: str = Field(..., description="ReadingCard identifier")
    reading_id: str = Field(..., description="Reading ID (UUID or document ID)")
    card_id: int = Field(..., description="Card ID")
    position: str = Field(..., description="카드 위치 (single, past, present, future, situation, action, outcome)")
    orientation: str = Field(..., description="카드 방향 (upright, reversed)")
    interpretation: str = Field(..., description="AI가 생성한 카드 해석")
    key_message: str = Field(..., description="핵심 메시지 한 줄")
    card: CardResponse = Field(..., description="카드 상세 정보")


class ReadingResponse(BaseModel):
    """
    타로 리딩 결과 응답 스키마

    완성된 리딩 결과를 클라이언트에게 반환합니다.
    """
    id: str = Field(..., description="Reading ID (UUID)")
    user_id: Optional[str] = Field(None, description="사용자 ID (Firebase UID)")
    spread_type: str = Field(..., description="스프레드 타입")
    question: str = Field(..., description="사용자의 질문")
    category: Optional[str] = Field(None, description="리딩 카테고리")
    cards: List[ReadingCardResponse] = Field(..., description="리딩에 사용된 카드들")
    card_relationships: Optional[str] = Field(None, description="카드 간 관계 설명 (쓰리카드 이상)")
    overall_reading: str = Field(..., description="AI가 생성한 종합 리딩")
    advice: Dict[str, str] = Field(..., description="조언 객체")
    summary: str = Field(..., description="한 줄 요약")
    created_at: Optional[datetime] = Field(None, description="생성 시각")
    updated_at: Optional[datetime] = Field(None, description="수정 시각")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "reading_123",
                "user_id": "firebase_uid_abc",
                "spread_type": "one_card",
                "question": "새로운 프로젝트를 시작해야 할까요?",
                "category": "career",
                "cards": [
                    {
                        "id": "reading_123_card_1",
                        "reading_id": "reading_123",
                        "card_id": 1,
                        "position": "single",
                        "orientation": "upright",
                        "interpretation": "바보 카드는 새로운 시작과 모험을 상징합니다...",
                        "key_message": "두려움 없이 새로운 여정을 시작하세요",
                        "card": {
                            "id": 1,
                            "name": "The Fool",
                            "name_ko": "바보",
                            "arcana_type": "major",
                            "number": 0,
                            "suit": None,
                            "keywords_upright": ["새로운 시작", "순수함"],
                            "keywords_reversed": ["무모함", "방향성 상실"],
                            "meaning_upright": "새로운 시작과 가능성...",
                            "meaning_reversed": "무모한 결정에 대한 경고...",
                            "description": "젊은이가 절벽 끝에 서 있습니다...",
                            "symbolism": "흰 장미는 순수함을 상징합니다...",
                            "image_url": "/images/cards/00-the-fool.jpg",
                            "created_at": "2025-10-19T10:30:00Z",
                            "updated_at": "2025-10-19T10:30:00Z"
                        }
                    }
                ],
                "card_relationships": None,
                "overall_reading": "바보 카드는 당신이 새로운 프로젝트를 시작하기에 완벽한 시기임을 알려줍니다...",
                "advice": {
                    "immediate_action": "우선 프로젝트의 기본 계획을 세워보세요.",
                    "short_term": "다음 2-3주 동안은 리서치와 준비에 집중하세요.",
                    "long_term": "장기적으로 이 프로젝트는 당신의 성장에 큰 도움이 될 것입니다.",
                    "mindset": "실패를 두려워하지 말고 배움의 기회로 받아들이세요.",
                    "cautions": "너무 성급하게 진행하지 말고 계획을 충분히 세우세요."
                },
                "summary": "새로운 시작에 완벽한 시기, 두려움 없이 도전하세요",
                "created_at": "2025-10-19T10:30:00Z",
                "updated_at": "2025-10-19T10:30:00Z"
            }
        }


class ReadingListResponse(BaseModel):
    """
    리딩 목록 응답 스키마 (페이지네이션 포함)

    여러 리딩 결과를 페이지네이션과 함께 반환합니다.
    """
    total: int = Field(..., description="전체 리딩 개수")
    page: int = Field(..., description="현재 페이지 번호")
    page_size: int = Field(..., description="페이지당 항목 수")
    readings: List[ReadingResponse] = Field(..., description="리딩 목록")

    class Config:
        json_schema_extra = {
            "example": {
                "total": 10,
                "page": 1,
                "page_size": 5,
                "readings": []
            }
        }
