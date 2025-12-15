"""
Chat API Routes - 채팅 API 엔드포인트

이 모듈의 목적:
- 채팅 대화 생성, 메시지 전송 API 엔드포인트 제공
- LangChain 기반 채팅 엔진 통합
- 타로 리딩 통합

주요 엔드포인트:
- POST /api/v1/chat/conversations: 새 대화 시작
- POST /api/v1/chat/conversations/{conversation_id}/messages: 메시지 전송
- GET /api/v1/chat/conversations: 대화 목록 조회
- GET /api/v1/chat/conversations/{conversation_id}: 대화 상세 조회
- POST /api/v1/chat/conversations/{conversation_id}/reading: 대화 중 타로 리딩 요청
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.core.logging import get_logger
from src.core.database import get_db_optional
from src.api.dependencies.auth import get_current_active_user
from src.database.factory import get_database_provider
from src.database.provider import DatabaseProvider
from src.ai.chat.chat_engine import ChatEngine
from src.schemas.chat import (
    ConversationCreateRequest,
    ConversationResponse,
    ConversationListResponse,
    MessageCreateRequest,
    MessageResponse,
    MessageListResponse,
    ChatResponse,
    TarotReadingRequest,
)
from src.models import User

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

# ChatEngine 캐시 (conversation_id -> ChatEngine)
_chat_engines: dict[str, ChatEngine] = {}


def get_chat_engine(conversation_id: str, user_id: str) -> ChatEngine:
    """ChatEngine 인스턴스 가져오기 (캐시 사용)"""
    cache_key = f"{conversation_id}_{user_id}"
    if cache_key not in _chat_engines:
        _chat_engines[cache_key] = ChatEngine(conversation_id, user_id)
    return _chat_engines[cache_key]


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    request: ConversationCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Optional[Session] = Depends(get_db_optional),
):
    """새 대화 시작"""
    try:
        db_provider = get_database_provider()
        user_id = str(current_user.id)

        # 대화 제목 생성 (첫 메시지 기반 또는 기본값)
        title = request.title or "새 대화"

        conversation = await db_provider.create_conversation({
            "user_id": user_id,
            "title": title,
        })

        logger.info(f"[Chat] Created conversation {conversation.id} for user {user_id}")

        return ConversationResponse(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )

    except Exception as e:
        logger.error(f"[Chat] Failed to create conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations", response_model=ConversationListResponse)
async def get_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Optional[Session] = Depends(get_db_optional),
):
    """대화 목록 조회"""
    try:
        db_provider = get_database_provider()
        user_id = str(current_user.id)

        conversations = await db_provider.get_conversations_by_user(
            user_id=user_id,
            skip=skip,
            limit=limit,
        )

        return ConversationListResponse(
            conversations=[
                ConversationResponse(
                    id=conv.id,
                    user_id=conv.user_id,
                    title=conv.title,
                    created_at=conv.created_at,
                    updated_at=conv.updated_at,
                )
                for conv in conversations
            ],
            total=len(conversations),  # TODO: 실제 total count 구현
        )

    except Exception as e:
        logger.error(f"[Chat] Failed to get conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Optional[Session] = Depends(get_db_optional),
):
    """대화 상세 조회"""
    try:
        db_provider = get_database_provider()
        conversation = await db_provider.get_conversation_by_id(conversation_id)

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # 권한 확인
        if str(conversation.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")

        return ConversationResponse(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Chat] Failed to get conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversations/{conversation_id}/messages", response_model=ChatResponse)
async def send_message(
    conversation_id: str,
    request: MessageCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Optional[Session] = Depends(get_db_optional),
):
    """메시지 전송"""
    try:
        db_provider = get_database_provider()
        user_id = str(current_user.id)

        # 대화 존재 확인
        conversation = await db_provider.get_conversation_by_id(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # 권한 확인
        if str(conversation.user_id) != user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # ChatEngine 가져오기 및 초기화
        chat_engine = get_chat_engine(conversation_id, user_id)
        await chat_engine.initialize()

        # 첫 메시지인지 확인 (제목이 "새 대화"인 경우)
        is_first_message = conversation.title == "새 대화"
        
        # 사용자 메시지 저장
        user_message = await db_provider.create_message({
            "conversation_id": conversation_id,
            "role": "user",
            "content": request.content,
            "metadata": request.metadata,
        })

        # 첫 메시지인 경우 제목 자동 생성
        if is_first_message:
            try:
                new_title = await chat_engine.generate_conversation_title(request.content)
                await db_provider.update_conversation(conversation_id, {"title": new_title})
                conversation.title = new_title  # 현재 객체도 업데이트
                logger.info(f"[Chat] Updated conversation title to: {new_title}")
            except Exception as e:
                logger.warning(f"[Chat] Failed to generate conversation title: {e}")
                # 제목 생성 실패해도 대화는 계속 진행

        # ★ 타로 리딩 요청인지 먼저 확인 (AI 응답 생성 전)
        suggest_tarot = await chat_engine.suggest_tarot_reading(request.content)
        
        if suggest_tarot:
            # 타로 리딩 요청인 경우: AI가 직접 리딩하지 않고 카드 선택 안내만 제공
            ai_response_text = "좋아요! 🌟 타로 카드를 선택해주시면 해석해 드릴게요. 아래에서 카드를 골라주세요!"
            logger.info(f"[Chat] Tarot reading requested - prompting card selection")
        else:
            # 일반 대화: AI 응답 생성
            ai_response_text = await chat_engine.chat(request.content)

        # AI 메시지 저장
        ai_message = await db_provider.create_message({
            "conversation_id": conversation_id,
            "role": "assistant",
            "content": ai_response_text,
        })

        # Message 객체를 MessageResponse로 변환
        if hasattr(ai_message, 'to_dict'):
            message_dict = ai_message.to_dict()
            # to_dict()는 created_at을 isoformat()으로 변환하므로 다시 datetime으로 변환 필요
            from datetime import datetime
            if isinstance(message_dict.get('created_at'), str):
                message_dict['created_at'] = datetime.fromisoformat(message_dict['created_at'].replace('Z', '+00:00'))
        else:
            message_dict = {
                "id": str(ai_message.id),
                "conversation_id": str(ai_message.conversation_id),
                "role": ai_message.role,
                "content": ai_message.content,
                "metadata": getattr(ai_message, 'message_metadata', None) or getattr(ai_message, 'metadata', None) or {},
                "created_at": ai_message.created_at,
            }

        return ChatResponse(
            message=MessageResponse(**message_dict),
            suggest_tarot=suggest_tarot,
            conversation_title=conversation.title if is_first_message else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Chat] Failed to send message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}/messages", response_model=MessageListResponse)
async def get_messages(
    conversation_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Optional[Session] = Depends(get_db_optional),
):
    """대화별 메시지 목록 조회"""
    try:
        db_provider = get_database_provider()
        user_id = str(current_user.id)

        # 대화 존재 및 권한 확인
        conversation = await db_provider.get_conversation_by_id(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        if str(conversation.user_id) != user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        messages = await db_provider.get_messages_by_conversation(
            conversation_id=conversation_id,
            skip=skip,
            limit=limit,
        )

        # Message 객체를 딕셔너리로 변환
        from datetime import datetime
        message_list = []
        for msg in messages:
            if hasattr(msg, 'to_dict'):
                message_dict = msg.to_dict()
                # to_dict()는 created_at을 isoformat()으로 변환하므로 다시 datetime으로 변환 필요
                if isinstance(message_dict.get('created_at'), str):
                    message_dict['created_at'] = datetime.fromisoformat(message_dict['created_at'].replace('Z', '+00:00'))
            else:
                message_dict = {
                    "id": str(msg.id),
                    "conversation_id": str(msg.conversation_id),
                    "role": msg.role,
                    "content": msg.content,
                    "metadata": getattr(msg, 'message_metadata', None) or getattr(msg, 'metadata', None) or {},
                    "created_at": msg.created_at,
                }
            message_list.append(MessageResponse(**message_dict))

        return MessageListResponse(
            messages=message_list,
            total=len(messages),  # TODO: 실제 total count 구현
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Chat] Failed to get messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversations/{conversation_id}/tarot-reading", response_model=MessageResponse)
async def add_tarot_reading_message(
    conversation_id: str,
    request: TarotReadingRequest,
    current_user: User = Depends(get_current_active_user),
    db: Optional[Session] = Depends(get_db_optional),
):
    """타로 리딩 결과를 AI 메시지로 추가"""
    try:
        db_provider = get_database_provider()
        user_id = str(current_user.id)

        # 대화 존재 확인
        conversation = await db_provider.get_conversation_by_id(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # 권한 확인
        if str(conversation.user_id) != user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # ChatEngine 가져오기 및 초기화
        chat_engine = get_chat_engine(conversation_id, user_id)
        await chat_engine.initialize()

        # 타로 리딩 생성을 위한 정보 수집
        cards_info = request.cards_info or []
        question = request.question
        
        logger.info(f"[Chat] Tarot reading request - cards: {len(cards_info)}, question: {question[:50]}...")

        # ChatEngine에게 타로 리딩 응답 생성 요청
        card_descriptions = []
        for i, card_info in enumerate(cards_info):
            position = ""
            if len(cards_info) == 3:
                positions = ["과거", "현재", "미래"]
                position = f"[{positions[i]}] "
            elif len(cards_info) == 1:
                position = "[오늘의 운세] "
            
            # Pydantic 모델은 속성으로 접근
            card_name = card_info.name if hasattr(card_info, 'name') else card_info.get('name', '알 수 없는 카드')
            is_reversed = card_info.is_reversed if hasattr(card_info, 'is_reversed') else card_info.get('is_reversed', False)
            reversed_text = "(역방향)" if is_reversed else ""
            card_descriptions.append(f"{position}{card_name} {reversed_text}")
        
        cards_text = ", ".join(card_descriptions)
        
        # AI에게 타로 리딩 해석 요청
        reading_prompt = f"""사용자가 타로 카드를 뽑았습니다. 타로 마스터로서 이 카드들을 해석해주세요.

질문: {question}
뽑은 카드: {cards_text}

친절하고 공감적인 타로 마스터로서 카드를 해석하고, 사용자에게 의미 있는 조언을 해주세요.
각 카드의 의미와 전체적인 메시지를 설명해주세요."""

        ai_response = await chat_engine.chat(reading_prompt)

        # AI 메시지 저장 (카드 정보를 딕셔너리로 변환)
        cards_dict = [
            {
                "id": c.id if hasattr(c, 'id') else c.get('id'),
                "name": c.name if hasattr(c, 'name') else c.get('name'),
                "is_reversed": c.is_reversed if hasattr(c, 'is_reversed') else c.get('is_reversed', False)
            }
            for c in cards_info
        ]
        ai_message = await db_provider.create_message({
            "conversation_id": conversation_id,
            "role": "assistant",
            "content": ai_response,
            "metadata": {
                "type": "tarot_reading",
                "cards": cards_dict,
                "question": question,
            },
        })

        logger.info(f"[Chat] Added tarot reading message to conversation {conversation_id}")

        # Message 객체를 MessageResponse로 변환
        from datetime import datetime as dt
        if hasattr(ai_message, 'to_dict'):
            message_dict = ai_message.to_dict()
            if isinstance(message_dict.get('created_at'), str):
                message_dict['created_at'] = dt.fromisoformat(message_dict['created_at'].replace('Z', '+00:00'))
        else:
            message_dict = {
                "id": str(ai_message.id),
                "conversation_id": str(ai_message.conversation_id),
                "role": ai_message.role,
                "content": ai_message.content,
                "metadata": getattr(ai_message, 'message_metadata', None) or getattr(ai_message, 'metadata', None) or {},
                "created_at": ai_message.created_at,
            }

        return MessageResponse(**message_dict)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Chat] Failed to add tarot reading message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Optional[Session] = Depends(get_db_optional),
):
    """대화 삭제"""
    try:
        db_provider = get_database_provider()
        user_id = str(current_user.id)

        # 대화 존재 및 권한 확인
        conversation = await db_provider.get_conversation_by_id(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        if str(conversation.user_id) != user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # 대화 삭제 (cascade로 메시지도 함께 삭제됨)
        success = await db_provider.delete_conversation(conversation_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete conversation")

        logger.info(f"[Chat] Deleted conversation {conversation_id} for user {user_id}")

        # ChatEngine 캐시에서 제거
        cache_key = f"{conversation_id}_{user_id}"
        if cache_key in _chat_engines:
            del _chat_engines[cache_key]

        return None  # 204 No Content

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Chat] Failed to delete conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversations/{conversation_id}/reading")
async def create_reading_from_chat(
    conversation_id: str,
    request: TarotReadingRequest,
    current_user: User = Depends(get_current_active_user),
    db: Optional[Session] = Depends(get_db_optional),
):
    """대화 중 타로 리딩 요청"""
    # 기존 리딩 API와 통합
    # TODO: readings.py의 로직 재사용
    raise HTTPException(status_code=501, detail="Not implemented yet")

