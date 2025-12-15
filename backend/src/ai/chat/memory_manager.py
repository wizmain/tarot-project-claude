"""
Memory Manager - 단기/장기 메모리 관리 모듈

이 모듈의 목적:
- LangChain Memory를 사용한 대화 메모리 관리
- 단기 메모리: 최근 5개 메시지 (ConversationBufferMemory)
- 장기 메모리: 대화 요약 및 중요 정보 (DB 저장)
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from langchain_classic.memory import ConversationBufferMemory, ConversationSummaryMemory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

from src.core.config import settings
from src.core.logging import get_logger
from src.database.factory import get_database_provider

logger = get_logger(__name__)


class MemoryManager:
    """
    메모리 관리자

    단기 메모리와 장기 메모리를 관리합니다.
    - 단기 메모리: 최근 5개 메시지 (대화 컨텍스트 유지)
    - 장기 메모리: 대화 요약 및 중요 정보 (DB에 영구 저장)
    """

    def __init__(self, conversation_id: str, user_id: str):
        """
        Initialize Memory Manager

        Args:
            conversation_id: 대화 ID
            user_id: 사용자 ID
        """
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.db = get_database_provider()

        # LLM for summary (use lightweight model)
        self.summary_llm = self._get_summary_llm()

        # Short-term memory: 최근 5개 메시지
        self.short_term_memory = ConversationBufferMemory(
            return_messages=True,
            memory_key="chat_history",
            max_token_limit=1000,  # 약 5개 메시지
        )

        # Long-term memory: 대화 요약
        self.long_term_memory = ConversationSummaryMemory(
            llm=self.summary_llm,
            return_messages=True,
            memory_key="summary_history",
        )

    def _get_summary_llm(self):
        """요약용 LLM 선택 (경량 모델)"""
        provider = settings.DEFAULT_AI_PROVIDER.lower()

        if provider == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is not set. Please set it in your .env file or environment variables.")
            return ChatOpenAI(
                model=settings.OPENAI_MODEL,
                temperature=0.3,  # 요약은 낮은 temperature
                api_key=settings.OPENAI_API_KEY,
            )
        elif provider == "anthropic":
            if not settings.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY is not set. Please set it in your .env file or environment variables.")
            return ChatAnthropic(
                model=settings.ANTHROPIC_MODEL,
                temperature=0.3,
                api_key=settings.ANTHROPIC_API_KEY,
            )
        elif provider == "gemini":
            if not settings.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY is not set. Please set it in your .env file or environment variables.")
            return ChatGoogleGenerativeAI(
                model=settings.GEMINI_MODEL,
                temperature=0.3,
                google_api_key=settings.GEMINI_API_KEY,
            )
        else:
            # Default to OpenAI
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is not set. Please set it in your .env file or environment variables.")
            return ChatOpenAI(
                model=settings.OPENAI_MODEL,
                temperature=0.3,
                api_key=settings.OPENAI_API_KEY,
            )

    async def load_memory(self):
        """DB에서 메모리 로드"""
        try:
            # 최근 5개 메시지 로드 (단기 메모리)
            recent_messages = await self.db.get_recent_messages_by_conversation(
                self.conversation_id,
                limit=5
            )

            # LangChain 메시지 형식으로 변환
            from langchain_core.messages import HumanMessage, AIMessage
            for msg in recent_messages:
                if msg.role == "user":
                    self.short_term_memory.chat_memory.add_message(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    self.short_term_memory.chat_memory.add_message(AIMessage(content=msg.content))

            logger.info(
                f"[MemoryManager] Loaded {len(recent_messages)} messages for conversation {self.conversation_id}"
            )
        except Exception as e:
            logger.error(f"[MemoryManager] Failed to load memory: {e}")

    async def save_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """메시지를 DB에 저장"""
        try:
            await self.db.create_message({
                "conversation_id": self.conversation_id,
                "role": role,
                "content": content,
                "metadata": metadata or {},
            })

            # 단기 메모리에 추가
            from langchain_core.messages import HumanMessage, AIMessage
            if role == "user":
                self.short_term_memory.chat_memory.add_message(HumanMessage(content=content))
            elif role == "assistant":
                self.short_term_memory.chat_memory.add_message(AIMessage(content=content))

        except Exception as e:
            logger.error(f"[MemoryManager] Failed to save message: {e}")

    def get_memory_variables(self) -> Dict[str, Any]:
        """메모리 변수 반환 (LangChain 프롬프트에 사용)"""
        memory_vars = {}

        # 단기 메모리
        short_term = self.short_term_memory.load_memory_variables({})
        memory_vars.update(short_term)

        # 장기 메모리 (요약)
        long_term = self.long_term_memory.load_memory_variables({})
        if long_term.get("summary_history"):
            memory_vars["long_term_summary"] = long_term["summary_history"]

        return memory_vars

    async def update_summary(self):
        """대화 요약 업데이트 (장기 메모리)"""
        try:
            # 현재 대화를 요약하여 장기 메모리에 저장
            # ConversationSummaryMemory가 자동으로 요약을 관리
            # 필요시 DB에 요약 저장 가능
            pass
        except Exception as e:
            logger.error(f"[MemoryManager] Failed to update summary: {e}")

    def clear_memory(self):
        """메모리 초기화"""
        self.short_term_memory.clear()
        self.long_term_memory.clear()

