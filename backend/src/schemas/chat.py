"""
채팅 Request/Response 스키마 정의

이 모듈의 목적:
- 채팅 API의 요청/응답 데이터 구조 정의
- Pydantic V2를 사용한 자동 검증 및 직렬화
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ConversationCreateRequest(BaseModel):
    """대화 생성 요청"""
    title: Optional[str] = Field(None, max_length=255, description="대화 제목")


class ConversationResponse(BaseModel):
    """대화 응답"""
    id: str = Field(..., description="대화 ID")
    user_id: str = Field(..., description="사용자 ID")
    title: str = Field(..., description="대화 제목")
    created_at: datetime = Field(..., description="생성 시간")
    updated_at: datetime = Field(..., description="업데이트 시간")


class ConversationListResponse(BaseModel):
    """대화 목록 응답"""
    conversations: List[ConversationResponse] = Field(..., description="대화 목록")
    total: int = Field(..., description="전체 대화 수")


class MessageCreateRequest(BaseModel):
    """메시지 생성 요청"""
    content: str = Field(..., min_length=1, max_length=5000, description="메시지 내용")
    metadata: Optional[Dict[str, Any]] = Field(None, description="메타데이터")


class MessageResponse(BaseModel):
    """메시지 응답"""
    id: str = Field(..., description="메시지 ID")
    conversation_id: str = Field(..., description="대화 ID")
    role: str = Field(..., description="메시지 역할 (user, assistant, system)")
    content: str = Field(..., description="메시지 내용")
    metadata: Optional[Dict[str, Any]] = Field(None, description="메타데이터")
    created_at: datetime = Field(..., description="생성 시간")


class MessageListResponse(BaseModel):
    """메시지 목록 응답"""
    messages: List[MessageResponse] = Field(..., description="메시지 목록")
    total: int = Field(..., description="전체 메시지 수")


class ChatResponse(BaseModel):
    """채팅 응답"""
    message: MessageResponse = Field(..., description="AI 응답 메시지")
    suggest_tarot: bool = Field(False, description="타로 리딩 제안 여부")
    conversation_title: Optional[str] = Field(None, description="업데이트된 대화 제목 (첫 메시지 시)")


class CardInfo(BaseModel):
    """카드 정보"""
    id: int = Field(..., description="카드 ID")
    name: str = Field(..., description="카드 이름")
    is_reversed: bool = Field(False, description="역방향 여부")


class TarotReadingRequest(BaseModel):
    """대화 중 타로 리딩 요청"""
    question: str = Field(..., min_length=1, max_length=500, description="질문")
    spread_type: Optional[str] = Field(None, description="스프레드 타입")
    selected_card_ids: Optional[List[int]] = Field(None, description="선택한 카드 ID 목록")
    reversed_states: Optional[List[bool]] = Field(None, description="카드 역방향 상태")
    cards_info: Optional[List[CardInfo]] = Field(None, description="카드 상세 정보 목록")

