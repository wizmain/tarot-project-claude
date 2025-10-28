"""
Unit tests for Prompt Engine (TASK-021)

Tests verify:
- Template loading and rendering
- System prompt generation
- One-card reading prompts
- Three-card reading prompts (both types)
- Output format prompts
- Full prompt building
- Error handling
"""
import pytest
from pathlib import Path

from src.ai.prompt_engine import PromptEngine, PromptType


@pytest.fixture
def engine():
    """Create PromptEngine instance for testing"""
    return PromptEngine()


@pytest.fixture
def sample_card():
    """Sample card data for testing"""
    return {
        "name": "The Fool",
        "orientation": "upright",
        "orientation_korean": "정방향",
        "arcana_korean": "메이저 아르카나",
        "number": 0,
        "keywords": ["new beginnings", "innocence", "adventure", "freedom"],
        "upright_meaning": "바보 카드는 새로운 시작과 순수한 가능성을 상징합니다.",
        "reversed_meaning": "역방향의 바보는 무모함이나 준비 부족을 나타낼 수 있습니다."
    }


@pytest.fixture
def sample_three_cards():
    """Sample three cards data for testing"""
    return [
        {
            "name": "The Fool",
            "orientation": "upright",
            "orientation_korean": "정방향",
            "arcana_korean": "메이저 아르카나",
            "number": 0,
            "keywords": ["new beginnings", "innocence"],
            "upright_meaning": "새로운 시작을 상징합니다.",
            "reversed_meaning": "무모함을 나타냅니다."
        },
        {
            "name": "The Lovers",
            "orientation": "reversed",
            "orientation_korean": "역방향",
            "arcana_korean": "메이저 아르카나",
            "suit_korean": None,
            "number": 6,
            "keywords": ["choice", "relationship", "values"],
            "upright_meaning": "사랑과 조화를 상징합니다.",
            "reversed_meaning": "갈등이나 불균형을 나타냅니다."
        },
        {
            "name": "The Tower",
            "orientation": "upright",
            "orientation_korean": "정방향",
            "arcana_korean": "메이저 아르카나",
            "number": 16,
            "keywords": ["sudden change", "upheaval", "revelation"],
            "upright_meaning": "급격한 변화를 상징합니다.",
            "reversed_meaning": "변화에 대한 저항을 나타냅니다."
        }
    ]


class TestPromptEngineInitialization:
    """Test suite for PromptEngine initialization"""

    def test_engine_initialization(self, engine):
        """Test engine initializes successfully"""
        assert engine is not None
        assert engine.prompts_dir.exists()
        assert engine.env is not None

    def test_prompts_directory_exists(self, engine):
        """Test prompts directory structure"""
        assert (engine.prompts_dir / "system").exists()
        assert (engine.prompts_dir / "reading").exists()
        assert (engine.prompts_dir / "output").exists()

    def test_custom_prompts_directory(self):
        """Test engine with custom prompts directory"""
        current_file = Path(__file__)
        backend_dir = current_file.parent.parent
        prompts_dir = backend_dir / "prompts"

        engine = PromptEngine(prompts_dir=str(prompts_dir))
        assert engine.prompts_dir == prompts_dir

    def test_invalid_prompts_directory(self):
        """Test engine fails with invalid directory"""
        with pytest.raises(FileNotFoundError):
            PromptEngine(prompts_dir="/nonexistent/directory")


class TestTemplateLoading:
    """Test suite for template loading"""

    def test_load_system_template(self, engine):
        """Test loading system prompt template"""
        template = engine.load_template(PromptType.SYSTEM)
        assert template is not None

    def test_load_one_card_template(self, engine):
        """Test loading one-card reading template"""
        template = engine.load_template(PromptType.ONE_CARD)
        assert template is not None

    def test_load_three_card_past_present_future_template(self, engine):
        """Test loading three-card past-present-future template"""
        template = engine.load_template(PromptType.THREE_CARD_PAST_PRESENT_FUTURE)
        assert template is not None

    def test_load_three_card_situation_action_outcome_template(self, engine):
        """Test loading three-card situation-action-outcome template"""
        template = engine.load_template(PromptType.THREE_CARD_SITUATION_ACTION_OUTCOME)
        assert template is not None

    def test_load_output_format_template(self, engine):
        """Test loading output format template"""
        template = engine.load_template(PromptType.OUTPUT_FORMAT)
        assert template is not None

    def test_get_available_templates(self, engine):
        """Test getting list of available templates"""
        templates = engine.get_available_templates()

        assert "SYSTEM" in templates
        assert "ONE_CARD" in templates
        assert "THREE_CARD_PAST_PRESENT_FUTURE" in templates
        assert "THREE_CARD_SITUATION_ACTION_OUTCOME" in templates
        assert "OUTPUT_FORMAT" in templates


class TestSystemPromptRendering:
    """Test suite for system prompt rendering"""

    def test_render_system_prompt(self, engine):
        """Test rendering system prompt"""
        prompt = engine.render_system_prompt()

        assert prompt is not None
        assert len(prompt) > 0
        assert "타로" in prompt
        assert "전문" in prompt or "리더" in prompt

    def test_system_prompt_contains_guidelines(self, engine):
        """Test system prompt contains key guidelines"""
        prompt = engine.render_system_prompt()

        # Check for key sections
        assert "역할" in prompt or "전문성" in prompt
        assert "해석" in prompt
        assert "톤앤매너" in prompt or "응답" in prompt


class TestOneCardPromptRendering:
    """Test suite for one-card prompt rendering"""

    def test_render_one_card_prompt_basic(self, engine, sample_card):
        """Test rendering basic one-card prompt"""
        prompt = engine.render_one_card_prompt(
            question="새로운 직장으로 이직해야 할까요?",
            card=sample_card
        )

        assert prompt is not None
        assert "새로운 직장으로 이직해야 할까요?" in prompt
        assert "The Fool" in prompt
        assert "정방향" in prompt

    def test_one_card_prompt_with_category(self, engine, sample_card):
        """Test one-card prompt with category"""
        prompt = engine.render_one_card_prompt(
            question="Test question",
            card=sample_card,
            category="career"
        )

        assert "career" in prompt

    def test_one_card_prompt_with_context(self, engine, sample_card):
        """Test one-card prompt with user context"""
        prompt = engine.render_one_card_prompt(
            question="Test question",
            card=sample_card,
            user_context="현재 5년차 직장인입니다"
        )

        assert "현재 5년차 직장인입니다" in prompt

    def test_one_card_prompt_includes_keywords(self, engine, sample_card):
        """Test that prompt includes card keywords"""
        prompt = engine.render_one_card_prompt(
            question="Test question",
            card=sample_card
        )

        # Check at least one keyword is present
        assert any(keyword in prompt for keyword in sample_card["keywords"])


class TestThreeCardPromptRendering:
    """Test suite for three-card prompt rendering"""

    def test_render_three_card_past_present_future(self, engine, sample_three_cards):
        """Test rendering three-card past-present-future prompt"""
        prompt = engine.render_three_card_prompt(
            question="내 연애운은 어떻게 될까요?",
            cards=sample_three_cards,
            spread_type="past_present_future"
        )

        assert prompt is not None
        assert "내 연애운은 어떻게 될까요?" in prompt
        assert "과거" in prompt
        assert "현재" in prompt
        assert "미래" in prompt
        assert "The Fool" in prompt
        assert "The Lovers" in prompt
        assert "The Tower" in prompt

    def test_render_three_card_situation_action_outcome(self, engine, sample_three_cards):
        """Test rendering three-card situation-action-outcome prompt"""
        prompt = engine.render_three_card_prompt(
            question="이 프로젝트를 어떻게 진행해야 할까요?",
            cards=sample_three_cards,
            spread_type="situation_action_outcome"
        )

        assert prompt is not None
        assert "이 프로젝트를 어떻게 진행해야 할까요?" in prompt
        assert "상황" in prompt
        assert "행동" in prompt
        assert "결과" in prompt

    def test_three_card_prompt_invalid_card_count(self, engine, sample_card):
        """Test that three-card prompt rejects invalid card count"""
        with pytest.raises(ValueError, match="exactly 3 cards"):
            engine.render_three_card_prompt(
                question="Test",
                cards=[sample_card],  # Only 1 card
                spread_type="past_present_future"
            )

    def test_three_card_prompt_invalid_spread_type(self, engine, sample_three_cards):
        """Test that invalid spread type raises error"""
        with pytest.raises(ValueError, match="Unknown spread type"):
            engine.render_three_card_prompt(
                question="Test",
                cards=sample_three_cards,
                spread_type="invalid_type"
            )


class TestOutputFormatRendering:
    """Test suite for output format rendering"""

    def test_render_output_format(self, engine):
        """Test rendering output format instructions"""
        prompt = engine.render_output_format_prompt()

        assert prompt is not None
        assert len(prompt) > 0
        assert "JSON" in prompt
        assert "cards" in prompt
        assert "overall_reading" in prompt
        assert "advice" in prompt


class TestFullPromptBuilding:
    """Test suite for full prompt building"""

    def test_build_one_card_full_prompt(self, engine, sample_card):
        """Test building complete one-card prompt"""
        result = engine.build_full_prompt(
            question="Test question",
            cards=[sample_card],
            spread_type="one_card"
        )

        assert "system_prompt" in result
        assert "user_prompt" in result
        assert len(result["system_prompt"]) > 0
        assert len(result["user_prompt"]) > 0
        assert "Test question" in result["user_prompt"]

    def test_build_three_card_full_prompt(self, engine, sample_three_cards):
        """Test building complete three-card prompt"""
        result = engine.build_full_prompt(
            question="Test question",
            cards=sample_three_cards,
            spread_type="past_present_future"
        )

        assert "system_prompt" in result
        assert "user_prompt" in result
        assert "과거" in result["user_prompt"]
        assert "현재" in result["user_prompt"]
        assert "미래" in result["user_prompt"]

    def test_build_prompt_without_system(self, engine, sample_card):
        """Test building prompt without system prompt"""
        result = engine.build_full_prompt(
            question="Test",
            cards=[sample_card],
            include_system_prompt=False
        )

        assert result["system_prompt"] == ""
        assert len(result["user_prompt"]) > 0

    def test_build_prompt_without_output_format(self, engine, sample_card):
        """Test building prompt without output format"""
        result = engine.build_full_prompt(
            question="Test",
            cards=[sample_card],
            include_output_format=False
        )

        # Should not contain JSON format instructions
        assert "JSON" not in result["user_prompt"]

    def test_build_prompt_validates_card_count(self, engine, sample_card):
        """Test that build_full_prompt validates card count"""
        with pytest.raises(ValueError, match="exactly 1 card"):
            engine.build_full_prompt(
                question="Test",
                cards=[sample_card, sample_card],  # 2 cards for one-card reading
                spread_type="one_card"
            )

    def test_build_prompt_with_all_options(self, engine, sample_three_cards):
        """Test building prompt with all optional parameters"""
        result = engine.build_full_prompt(
            question="Test question",
            cards=sample_three_cards,
            spread_type="situation_action_outcome",
            category="career",
            user_context="I'm a software engineer",
            include_system_prompt=True,
            include_output_format=True
        )

        assert "Test question" in result["user_prompt"]
        assert "career" in result["user_prompt"]
        assert "I'm a software engineer" in result["user_prompt"]
        assert len(result["system_prompt"]) > 0


class TestErrorHandling:
    """Test suite for error handling"""

    def test_missing_template_file(self, engine):
        """Test handling of missing template file"""
        # This would require modifying PromptType enum or mocking,
        # so we'll test the actual behavior with invalid path
        with pytest.raises(Exception):  # TemplateNotFound or similar
            # Try to load a template that doesn't exist
            engine.env.get_template("nonexistent/template.txt")

    def test_invalid_card_data_structure(self, engine):
        """Test handling of incomplete card data"""
        incomplete_card = {
            "name": "Test Card",
            # Missing required fields
        }

        # Should handle gracefully (Jinja2 will render undefined as empty)
        prompt = engine.render_one_card_prompt(
            question="Test",
            card=incomplete_card
        )
        assert prompt is not None
