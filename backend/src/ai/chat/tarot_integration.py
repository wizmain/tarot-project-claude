"""
Tarot Integration - 대화 중 타로 리딩 통합 모듈

이 모듈의 목적:
- 대화 중 타로 리딩 요청 처리
- AI 자동 제안 로직
- 기존 리딩 API와 통합
"""
from typing import Dict, Any, Optional, List
from src.core.logging import get_logger
from src.ai.chat.chat_engine import ChatEngine

logger = get_logger(__name__)


class TarotIntegration:
    """
    타로 통합 모듈

    대화 중 타로 리딩을 통합합니다.
    """

    def __init__(self, chat_engine: ChatEngine):
        """
        Initialize Tarot Integration

        Args:
            chat_engine: ChatEngine 인스턴스
        """
        self.chat_engine = chat_engine

    async def analyze_context_for_tarot_suggestion(self, conversation_history: List[Dict[str, str]]) -> bool:
        """
        대화 맥락을 분석하여 타로 리딩 제안 여부 결정

        Args:
            conversation_history: 대화 히스토리

        Returns:
            타로 리딩 제안 여부
        """
        # 최근 대화 내용 분석
        recent_context = " ".join([
            msg.get("content", "") for msg in conversation_history[-5:]
        ])

        return await self.chat_engine.suggest_tarot_reading(recent_context)

    def format_reading_response(self, reading_data: Dict[str, Any]) -> str:
        """
        리딩 결과를 대화 메시지 형식으로 포맷

        Args:
            reading_data: 리딩 데이터

        Returns:
            포맷된 메시지
        """
        cards_info = "\n".join([
            f"- {card.get('name_ko', card.get('name', ''))}: {card.get('key_message', '')}"
            for card in reading_data.get("cards", [])
        ])

        message = f"""타로 리딩 결과를 알려드리겠습니다.

**뽑은 카드:**
{cards_info}

**종합 해석:**
{reading_data.get('overall_reading', '')}

**조언:**
{reading_data.get('advice', {}).get('immediate_action', '')}

이 리딩이 도움이 되셨나요? 더 궁금한 점이 있으시면 언제든 말씀해 주세요."""

        return message

