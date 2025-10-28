"""
Prompt Engine - Jinja2 기반 타로 리딩 프롬프트 생성 엔진

이 모듈의 목적:
- Jinja2 템플릿을 사용한 동적 프롬프트 생성
- 시스템 프롬프트, 리딩 프롬프트, 출력 포맷 관리
- 카드 데이터를 템플릿에 주입하여 완성된 프롬프트 생성
- 다양한 스프레드 타입 지원 (원카드, 쓰리카드 등)

주요 컴포넌트:
- PromptType: 사용 가능한 템플릿 타입 열거형
- PromptEngine: 템플릿 로딩 및 렌더링 메인 클래스

제공하는 템플릿:
- system/tarot_expert.txt: 타로 전문가 페르소나
- reading/one_card.txt: 원카드 리딩
- reading/three_card_past_present_future.txt: 과거-현재-미래
- reading/three_card_situation_action_outcome.txt: 상황-행동-결과
- output/structured_response.txt: JSON 응답 형식

TASK-021: 프롬프트 템플릿 시스템 설계 구현
TASK-022: 타로 전문가 시스템 프롬프트 작성
TASK-023: 스프레드별 리딩 프롬프트 작성

사용 예시:
    engine = PromptEngine()
    prompts = engine.build_full_prompt(
        question="새로운 직장으로 이직해야 할까요?",
        cards=[card1],
        spread_type="one_card"
    )
    # prompts = {"system_prompt": "...", "user_prompt": "..."}
"""
import os
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound

logger = logging.getLogger(__name__)


class PromptType(Enum):
    """
    사용 가능한 프롬프트 템플릿 타입

    각 타입은 prompts/ 디렉토리 내의 템플릿 파일 경로를 나타냅니다.
    """
    SYSTEM = "system/tarot_expert"
    ONE_CARD = "reading/one_card"
    THREE_CARD_PAST_PRESENT_FUTURE = "reading/three_card_past_present_future"
    THREE_CARD_SITUATION_ACTION_OUTCOME = "reading/three_card_situation_action_outcome"
    OUTPUT_FORMAT = "output/structured_response"


class PromptEngine:
    """
    Template-based prompt generation engine

    Features:
    - Jinja2 template rendering
    - Multiple reading types support
    - Context building for cards
    - System prompt management
    """

    def __init__(self, prompts_dir: Optional[str] = None):
        """
        Initialize Prompt Engine

        Args:
            prompts_dir: Path to prompts directory (defaults to backend/prompts)
        """
        if prompts_dir is None:
            # Default to backend/prompts directory
            current_file = Path(__file__)
            backend_dir = current_file.parent.parent.parent.parent
            prompts_dir = backend_dir / "prompts"

        self.prompts_dir = Path(prompts_dir)

        if not self.prompts_dir.exists():
            raise FileNotFoundError(
                f"Prompts directory not found: {self.prompts_dir}"
            )

        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.prompts_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            autoescape=False  # We're generating prompts, not HTML
        )

        logger.info(f"[PromptEngine] Initialized with prompts_dir: {self.prompts_dir}")

    def load_template(self, prompt_type: PromptType) -> Template:
        """
        Load a template by type

        Args:
            prompt_type: Type of prompt to load

        Returns:
            Jinja2 Template object

        Raises:
            TemplateNotFound: If template file doesn't exist
        """
        template_path = f"{prompt_type.value}.txt"

        try:
            template = self.env.get_template(template_path)
            logger.debug(f"[PromptEngine] Loaded template: {template_path}")
            return template
        except TemplateNotFound:
            logger.error(f"[PromptEngine] Template not found: {template_path}")
            raise

    def render_system_prompt(self) -> str:
        """
        Render system prompt (tarot expert persona)

        Returns:
            Rendered system prompt text
        """
        template = self.load_template(PromptType.SYSTEM)
        return template.render()

    def render_one_card_prompt(
        self,
        question: str,
        card: Dict[str, Any],
        category: Optional[str] = None,
        user_context: Optional[str] = None
    ) -> str:
        """
        Render one-card reading prompt

        Args:
            question: User's question
            card: Card data dictionary with fields:
                - name: Card name
                - orientation: "upright" or "reversed"
                - orientation_korean: "정방향" or "역방향"
                - arcana_korean: "메이저 아르카나" or "마이너 아르카나"
                - suit_korean: Suit in Korean (optional)
                - number: Card number (optional)
                - keywords: List of keywords
                - upright_meaning: Upright meaning text
                - reversed_meaning: Reversed meaning text
            category: Optional reading category
            user_context: Optional additional context

        Returns:
            Rendered prompt text
        """
        template = self.load_template(PromptType.ONE_CARD)

        context = {
            "question": question,
            "card": card,
            "category": category,
            "user_context": user_context
        }

        return template.render(**context)

    def render_three_card_prompt(
        self,
        question: str,
        cards: List[Dict[str, Any]],
        spread_type: str = "past_present_future",
        category: Optional[str] = None,
        user_context: Optional[str] = None
    ) -> str:
        """
        Render three-card reading prompt

        Args:
            question: User's question
            cards: List of 3 card data dictionaries (same structure as one_card)
            spread_type: "past_present_future" or "situation_action_outcome"
            category: Optional reading category
            user_context: Optional additional context

        Returns:
            Rendered prompt text

        Raises:
            ValueError: If cards list doesn't have exactly 3 cards
        """
        if len(cards) != 3:
            raise ValueError(f"Three-card reading requires exactly 3 cards, got {len(cards)}")

        # Select template based on spread type
        if spread_type == "past_present_future":
            template = self.load_template(PromptType.THREE_CARD_PAST_PRESENT_FUTURE)
        elif spread_type == "situation_action_outcome":
            template = self.load_template(PromptType.THREE_CARD_SITUATION_ACTION_OUTCOME)
        else:
            raise ValueError(f"Unknown spread type: {spread_type}")

        context = {
            "question": question,
            "cards": cards,
            "category": category,
            "user_context": user_context
        }

        return template.render(**context)

    def render_output_format_prompt(self) -> str:
        """
        Render output format specification prompt

        Returns:
            Rendered output format instructions
        """
        template = self.load_template(PromptType.OUTPUT_FORMAT)
        return template.render()

    def build_full_prompt(
        self,
        question: str,
        cards: List[Dict[str, Any]],
        spread_type: str = "one_card",
        category: Optional[str] = None,
        user_context: Optional[str] = None,
        include_system_prompt: bool = True,
        include_output_format: bool = True
    ) -> Dict[str, str]:
        """
        Build complete prompt with system prompt, reading prompt, and output format

        Args:
            question: User's question
            cards: List of card data dictionaries (1 or 3 cards)
            spread_type: "one_card", "past_present_future", or "situation_action_outcome"
            category: Optional reading category
            user_context: Optional additional context
            include_system_prompt: Whether to include system prompt
            include_output_format: Whether to include output format instructions

        Returns:
            Dictionary with:
                - system_prompt: System prompt (or empty string if not included)
                - user_prompt: User prompt (reading request)

        Raises:
            ValueError: If card count doesn't match spread type
        """
        # Validate cards count
        if spread_type == "one_card" and len(cards) != 1:
            raise ValueError(f"One-card reading requires exactly 1 card, got {len(cards)}")
        elif spread_type in ["past_present_future", "situation_action_outcome"] and len(cards) != 3:
            raise ValueError(f"Three-card reading requires exactly 3 cards, got {len(cards)}")

        # Build system prompt
        system_prompt = ""
        if include_system_prompt:
            system_prompt = self.render_system_prompt()

        # Build reading prompt
        if spread_type == "one_card":
            reading_prompt = self.render_one_card_prompt(
                question=question,
                card=cards[0],
                category=category,
                user_context=user_context
            )
        else:
            reading_prompt = self.render_three_card_prompt(
                question=question,
                cards=cards,
                spread_type=spread_type,
                category=category,
                user_context=user_context
            )

        # Add output format if requested
        user_prompt = reading_prompt
        if include_output_format:
            output_format = self.render_output_format_prompt()
            user_prompt = f"{reading_prompt}\n\n{output_format}"

        logger.info(
            f"[PromptEngine] Built {spread_type} prompt "
            f"(system={include_system_prompt}, format={include_output_format})"
        )

        return {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt
        }

    def get_available_templates(self) -> Dict[str, Path]:
        """
        Get list of available template files

        Returns:
            Dictionary mapping template type to file path
        """
        templates = {}

        for prompt_type in PromptType:
            template_path = self.prompts_dir / f"{prompt_type.value}.txt"
            if template_path.exists():
                templates[prompt_type.name] = template_path

        return templates
