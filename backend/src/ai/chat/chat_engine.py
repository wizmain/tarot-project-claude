"""
Chat Engine - LangChain 기반 채팅 엔진

이 모듈의 목적:
- LangChain을 사용한 멀티턴 대화 처리
- 타로 마스터 페르소나 설정
- 기존 AI Orchestrator와 통합
"""
from typing import List, Dict, Any, Optional
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

from src.core.config import settings
from src.core.logging import get_logger
from src.ai.chat.memory_manager import MemoryManager
from src.ai.orchestrator import AIOrchestrator
from src.ai.provider_loader import load_providers_from_settings

logger = get_logger(__name__)


class ChatEngine:
    """
    채팅 엔진

    LangChain을 사용하여 멀티턴 대화를 처리합니다.
    """

    def __init__(self, conversation_id: str, user_id: str):
        """
        Initialize Chat Engine

        Args:
            conversation_id: 대화 ID
            user_id: 사용자 ID
        """
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.memory_manager = MemoryManager(conversation_id, user_id)

        # System prompt for tarot master
        self.system_prompt = self._load_system_prompt()

        # LLM 설정
        self.llm = self._get_llm()

        # Chat prompt template
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ])

        # LCEL Chain (LangChain Expression Language - recommended for v1.0+)
        self.chain = self.prompt_template | self.llm

    def _load_system_prompt(self) -> str:
        """타로 마스터 시스템 프롬프트 로드"""
        try:
            prompt_path = "backend/prompts/system/tarot_expert.txt"
            with open(prompt_path, "r", encoding="utf-8") as f:
                base_prompt = f.read()

            # 채팅용 추가 지시사항
            chat_instructions = """
            
## Chat Mode Instructions

You are now in a conversational chat mode. Your role is to:
1. Have natural, empathetic conversations with users about their concerns
2. Provide tarot-related guidance and insights when appropriate
3. Remember previous conversations and maintain context
4. Be warm, supportive, and encouraging

## IMPORTANT: Card Selection Rules
- You MUST NEVER draw or select tarot cards yourself
- You MUST NEVER describe specific cards or their meanings unless the user has already selected cards
- When a user asks for a tarot reading, fortune, or card interpretation, you should:
  1. Ask them to select their cards first
  2. Say something like: "좋아요! 카드를 선택해주시면 해석해 드릴게요. 아래에서 카드를 골라주세요."
  3. Wait for them to select cards before providing any interpretation

## Response Guidelines
- When user mentions: 운세, 타로, 리딩, 카드, fortune, reading, cards
- DO NOT start a reading or describe cards
- Instead, guide them to select cards with the card selector below
- Example responses:
  - "물론이죠! 카드를 선택해주시면 바로 해석해 드릴게요. 🌟"
  - "네, 타로 리딩을 해드릴게요. 먼저 아래에서 카드를 선택해주세요!"
  - "좋아요! 어떤 카드가 나올지 기대되네요. 카드를 골라주세요."

Keep responses conversational and natural, not overly formal.
"""
            return base_prompt + chat_instructions
        except Exception as e:
            logger.warning(f"Failed to load system prompt: {e}, using default")
            return "You are a professional tarot reader with 20 years of experience. Be empathetic, warm, and supportive."

    def _get_llm(self):
        """LLM 인스턴스 생성"""
        provider = settings.DEFAULT_AI_PROVIDER.lower()

        if provider == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is not set. Please set it in your .env file or environment variables.")
            return ChatOpenAI(
                model=settings.OPENAI_MODEL,
                temperature=0.7,
                api_key=settings.OPENAI_API_KEY,
            )
        elif provider == "anthropic":
            if not settings.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY is not set. Please set it in your .env file or environment variables.")
            return ChatAnthropic(
                model=settings.ANTHROPIC_MODEL,
                temperature=0.7,
                api_key=settings.ANTHROPIC_API_KEY,
            )
        elif provider == "gemini":
            if not settings.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY is not set. Please set it in your .env file or environment variables.")
            return ChatGoogleGenerativeAI(
                model=settings.GEMINI_MODEL,
                temperature=0.7,
                google_api_key=settings.GEMINI_API_KEY,
            )
        else:
            # Default to OpenAI
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is not set. Please set it in your .env file or environment variables.")
            return ChatOpenAI(
                model=settings.OPENAI_MODEL,
                temperature=0.7,
                api_key=settings.OPENAI_API_KEY,
            )

    async def initialize(self):
        """채팅 엔진 초기화 (메모리 로드)"""
        await self.memory_manager.load_memory()

    async def chat(self, user_input: str) -> str:
        """
        사용자 입력에 대한 응답 생성

        Args:
            user_input: 사용자 메시지

        Returns:
            AI 응답
        """
        try:
            # 메모리 변수 가져오기
            memory_vars = self.memory_manager.get_memory_variables()
            chat_history = memory_vars.get("chat_history", [])

            # LCEL Chain 실행
            response = await self.chain.ainvoke({
                "input": user_input,
                "chat_history": chat_history,
            })

            # LCEL returns AIMessage directly, extract content
            from langchain_core.messages import AIMessage
            if isinstance(response, AIMessage):
                ai_response = response.content
                # 메모리에 추가 (이미 AIMessage 객체이므로 직접 사용)
                self.memory_manager.short_term_memory.chat_memory.add_message(response)
            else:
                # Fallback for unexpected response types
                ai_response = str(response)
                self.memory_manager.short_term_memory.chat_memory.add_message(
                    AIMessage(content=ai_response)
                )

            return ai_response

        except Exception as e:
            logger.error(f"[ChatEngine] Failed to generate response: {e}")
            raise

    async def suggest_tarot_reading(self, context: str) -> bool:
        """
        맥락을 분석하여 타로 리딩 제안 여부 결정

        Args:
            context: 현재 대화 맥락

        Returns:
            타로 리딩 제안 여부
        """
        # 타로/운세 직접 요청 키워드 (높은 우선순위)
        tarot_request_keywords = [
            "운세", "타로", "리딩", "카드", "점", "fortune", "reading", "card",
            "뽑아", "봐줘", "봐주세요", "해줘", "해주세요", "알려줘"
        ]
        
        context_lower = context.lower()
        
        # 타로 관련 직접 요청인 경우 바로 True
        for keyword in tarot_request_keywords:
            if keyword in context_lower:
                return True

        return False

    async def generate_conversation_title(self, first_message: str) -> str:
        """
        첫 메시지를 기반으로 대화 제목 자동 생성

        Args:
            first_message: 사용자의 첫 메시지

        Returns:
            생성된 대화 제목 (최대 40자)
        """
        try:
            # 간단한 프롬프트로 제목 생성
            title_prompt = f"""Based on this user message, generate a short, concise conversation title (max 40 characters).
The title should capture the main topic or concern.
Respond with ONLY the title, nothing else.
Use Korean if the message is in Korean, English if the message is in English.

User message: {first_message}

Title:"""

            response = await self.llm.ainvoke(title_prompt)
            
            # Extract content from response
            from langchain_core.messages import AIMessage
            if isinstance(response, AIMessage):
                title = response.content.strip()
            else:
                title = str(response).strip()

            # 최대 길이 제한
            if len(title) > 40:
                title = title[:37] + "..."

            # 따옴표 제거
            title = title.strip('"\'')

            logger.info(f"[ChatEngine] Generated title: {title}")
            return title

        except Exception as e:
            logger.error(f"[ChatEngine] Failed to generate title: {e}")
            # 실패 시 첫 메시지의 앞부분 사용
            if len(first_message) > 30:
                return first_message[:27] + "..."
            return first_message

