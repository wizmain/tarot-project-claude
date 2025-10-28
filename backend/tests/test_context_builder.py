"""
ContextBuilder 테스트 모듈

이 모듈의 목적:
- ContextBuilder 클래스의 모든 기능을 테스트
- Card 모델과 DrawnCard를 프롬프트용 딕셔너리로 변환하는 로직 검증
- 한국어 변환 기능 검증
- 엣지 케이스 처리 검증

주요 테스트:
- 한국어 변환 메서드 (orientation, arcana, suit)
- 단일 카드 컨텍스트 빌딩
- 여러 카드 컨텍스트 빌딩
- 방향에 따른 키워드 선택
- None 값 처리

TASK-024: 컨텍스트 빌더 구현 테스트
"""
import pytest
from typing import List, Dict, Any

from src.models import Card, ArcanaType, Suit
from src.core.card_shuffle import DrawnCard, Orientation
from src.ai.prompt_engine.context_builder import ContextBuilder


class TestContextBuilderKoreanTranslation:
    """한국어 변환 메서드 테스트"""

    def test_get_orientation_korean_upright(self):
        """정방향 한국어 변환 테스트"""
        result = ContextBuilder.get_orientation_korean("upright")
        assert result == "정방향"

    def test_get_orientation_korean_reversed(self):
        """역방향 한국어 변환 테스트"""
        result = ContextBuilder.get_orientation_korean("reversed")
        assert result == "역방향"

    def test_get_orientation_korean_unknown(self):
        """알 수 없는 방향 처리 테스트"""
        result = ContextBuilder.get_orientation_korean("unknown")
        assert result == "unknown"  # 기본값으로 입력값 반환

    def test_get_arcana_korean_major(self):
        """메이저 아르카나 한국어 변환 테스트"""
        result = ContextBuilder.get_arcana_korean(ArcanaType.MAJOR)
        assert result == "메이저 아르카나"

    def test_get_arcana_korean_minor(self):
        """마이너 아르카나 한국어 변환 테스트"""
        result = ContextBuilder.get_arcana_korean(ArcanaType.MINOR)
        assert result == "마이너 아르카나"

    def test_get_suit_korean_wands(self):
        """완드 수트 한국어 변환 테스트"""
        result = ContextBuilder.get_suit_korean(Suit.WANDS)
        assert result == "완드"

    def test_get_suit_korean_cups(self):
        """컵 수트 한국어 변환 테스트"""
        result = ContextBuilder.get_suit_korean(Suit.CUPS)
        assert result == "컵"

    def test_get_suit_korean_swords(self):
        """검 수트 한국어 변환 테스트"""
        result = ContextBuilder.get_suit_korean(Suit.SWORDS)
        assert result == "검"

    def test_get_suit_korean_pentacles(self):
        """펜타클 수트 한국어 변환 테스트"""
        result = ContextBuilder.get_suit_korean(Suit.PENTACLES)
        assert result == "펜타클"

    def test_get_suit_korean_none(self):
        """None 수트 처리 테스트 (메이저 아르카나)"""
        result = ContextBuilder.get_suit_korean(None)
        assert result is None


class TestContextBuilderSingleCard:
    """단일 카드 컨텍스트 빌딩 테스트"""

    @pytest.fixture
    def major_card(self) -> Card:
        """메이저 아르카나 카드 픽스처 (The Fool)"""
        card = Card(
            id=1,
            name="The Fool",
            name_ko="바보",
            number=0,
            arcana_type=ArcanaType.MAJOR,
            suit=None,
            keywords_upright=["새로운 시작", "순수", "자유"],
            keywords_reversed=["무모함", "경솔함", "위험"],
            meaning_upright="새로운 시작을 상징하는 카드입니다. 순수한 마음으로 모험을 떠나세요.",
            meaning_reversed="무모한 결정을 경고합니다. 신중하게 생각하세요.",
            description="여행을 시작하는 젊은이",
            symbolism="무한한 가능성과 새로운 시작",
            image_url="/images/major_00.jpg"
        )
        return card

    @pytest.fixture
    def minor_card(self) -> Card:
        """마이너 아르카나 카드 픽스처 (Ace of Wands)"""
        card = Card(
            id=23,
            name="Ace of Wands",
            name_ko="완드 에이스",
            number=1,
            arcana_type=ArcanaType.MINOR,
            suit=Suit.WANDS,
            keywords_upright=["창조", "영감", "성장"],
            keywords_reversed=["좌절", "지연", "장애물"],
            meaning_upright="새로운 창조적 에너지가 시작됩니다. 열정을 따르세요.",
            meaning_reversed="프로젝트 시작에 어려움이 있을 수 있습니다.",
            description="손에서 뻗어나오는 완드",
            symbolism="창조적 에너지의 시작",
            image_url="/images/wands_01.jpg"
        )
        return card

    def test_build_card_context_major_upright(self, major_card):
        """메이저 아르카나 정방향 컨텍스트 빌딩"""
        drawn_card = DrawnCard(major_card, Orientation.UPRIGHT)
        context = ContextBuilder.build_card_context(drawn_card)

        assert context["name"] == "The Fool"
        assert context["orientation"] == "upright"
        assert context["orientation_korean"] == "정방향"
        assert context["arcana_korean"] == "메이저 아르카나"
        assert context["suit_korean"] is None
        assert context["number"] == 0
        assert context["keywords"] == ["새로운 시작", "순수", "자유"]
        assert "새로운 시작을 상징" in context["upright_meaning"]
        assert "무모한 결정을 경고" in context["reversed_meaning"]

    def test_build_card_context_major_reversed(self, major_card):
        """메이저 아르카나 역방향 컨텍스트 빌딩"""
        drawn_card = DrawnCard(major_card, Orientation.REVERSED)
        context = ContextBuilder.build_card_context(drawn_card)

        assert context["orientation"] == "reversed"
        assert context["orientation_korean"] == "역방향"
        # 역방향일 때는 reversed 키워드를 사용
        assert context["keywords"] == ["무모함", "경솔함", "위험"]

    def test_build_card_context_minor_upright(self, minor_card):
        """마이너 아르카나 정방향 컨텍스트 빌딩"""
        drawn_card = DrawnCard(minor_card, Orientation.UPRIGHT)
        context = ContextBuilder.build_card_context(drawn_card)

        assert context["name"] == "Ace of Wands"
        assert context["orientation"] == "upright"
        assert context["arcana_korean"] == "마이너 아르카나"
        assert context["suit_korean"] == "완드"
        assert context["number"] == 1
        assert context["keywords"] == ["창조", "영감", "성장"]

    def test_build_card_context_minor_reversed(self, minor_card):
        """마이너 아르카나 역방향 컨텍스트 빌딩"""
        drawn_card = DrawnCard(minor_card, Orientation.REVERSED)
        context = ContextBuilder.build_card_context(drawn_card)

        assert context["orientation"] == "reversed"
        assert context["keywords"] == ["좌절", "지연", "장애물"]

    def test_build_card_context_with_all_suits(self):
        """모든 수트 카드의 한국어 변환 테스트"""
        suits = [
            (Suit.WANDS, "완드"),
            (Suit.CUPS, "컵"),
            (Suit.SWORDS, "검"),
            (Suit.PENTACLES, "펜타클"),
        ]

        for suit, expected_korean in suits:
            card = Card(
                id=1,
                name=f"Test Card",
                name_ko="테스트 카드",
                number=1,
                arcana_type=ArcanaType.MINOR,
                suit=suit,
                keywords_upright=["test"],
                keywords_reversed=["test"],
                meaning_upright="Test upright",
                meaning_reversed="Test reversed"
            )
            drawn_card = DrawnCard(card, Orientation.UPRIGHT)
            context = ContextBuilder.build_card_context(drawn_card)

            assert context["suit_korean"] == expected_korean

    def test_build_card_context_empty_keywords(self):
        """빈 키워드 리스트 처리 테스트"""
        card = Card(
            id=1,
            name="Test Card",
            name_ko="테스트 카드",
            number=1,
            arcana_type=ArcanaType.MAJOR,
            suit=None,
            keywords_upright=[],
            keywords_reversed=[],
            meaning_upright="Test",
            meaning_reversed="Test"
        )
        drawn_card = DrawnCard(card, Orientation.UPRIGHT)
        context = ContextBuilder.build_card_context(drawn_card)

        assert context["keywords"] == []

    def test_build_card_context_none_keywords(self):
        """None 키워드 처리 테스트"""
        card = Card(
            id=1,
            name="Test Card",
            name_ko="테스트 카드",
            number=1,
            arcana_type=ArcanaType.MAJOR,
            suit=None,
            keywords_upright=None,
            keywords_reversed=None,
            meaning_upright="Test",
            meaning_reversed="Test"
        )
        drawn_card = DrawnCard(card, Orientation.UPRIGHT)
        context = ContextBuilder.build_card_context(drawn_card)

        assert context["keywords"] == []


class TestContextBuilderMultipleCards:
    """여러 카드 컨텍스트 빌딩 테스트"""

    @pytest.fixture
    def three_cards(self) -> List[Card]:
        """쓰리카드 리딩용 카드 3장 픽스처"""
        cards = [
            Card(
                id=1,
                name="The Fool",
                name_ko="바보",
                number=0,
                arcana_type=ArcanaType.MAJOR,
                suit=None,
                keywords_upright=["새로운 시작"],
                keywords_reversed=["무모함"],
                meaning_upright="과거: 순수한 시작",
                meaning_reversed="과거: 경솔한 결정"
            ),
            Card(
                id=2,
                name="The Magician",
                name_ko="마법사",
                number=1,
                arcana_type=ArcanaType.MAJOR,
                suit=None,
                keywords_upright=["창조", "능력"],
                keywords_reversed=["조작", "속임수"],
                meaning_upright="현재: 능력 발휘",
                meaning_reversed="현재: 기만"
            ),
            Card(
                id=23,
                name="Ace of Wands",
                name_ko="완드 에이스",
                number=1,
                arcana_type=ArcanaType.MINOR,
                suit=Suit.WANDS,
                keywords_upright=["창조", "영감"],
                keywords_reversed=["좌절"],
                meaning_upright="미래: 새로운 시작",
                meaning_reversed="미래: 지연"
            ),
        ]
        return cards

    def test_build_cards_context_three_cards_upright(self, three_cards):
        """3장의 카드를 정방향으로 빌딩"""
        drawn_cards = [
            DrawnCard(three_cards[0], Orientation.UPRIGHT),
            DrawnCard(three_cards[1], Orientation.UPRIGHT),
            DrawnCard(three_cards[2], Orientation.UPRIGHT),
        ]

        contexts = ContextBuilder.build_cards_context(drawn_cards)

        assert len(contexts) == 3
        assert contexts[0]["name"] == "The Fool"
        assert contexts[1]["name"] == "The Magician"
        assert contexts[2]["name"] == "Ace of Wands"

        # 모두 정방향
        for ctx in contexts:
            assert ctx["orientation"] == "upright"
            assert ctx["orientation_korean"] == "정방향"

    def test_build_cards_context_mixed_orientations(self, three_cards):
        """정방향/역방향 혼합 카드 빌딩"""
        drawn_cards = [
            DrawnCard(three_cards[0], Orientation.UPRIGHT),
            DrawnCard(three_cards[1], Orientation.REVERSED),
            DrawnCard(three_cards[2], Orientation.UPRIGHT),
        ]

        contexts = ContextBuilder.build_cards_context(drawn_cards)

        assert contexts[0]["orientation"] == "upright"
        assert contexts[1]["orientation"] == "reversed"
        assert contexts[2]["orientation"] == "upright"

        # 키워드도 방향에 따라 올바르게 선택되어야 함
        assert contexts[0]["keywords"] == ["새로운 시작"]
        assert contexts[1]["keywords"] == ["조작", "속임수"]
        assert contexts[2]["keywords"] == ["창조", "영감"]

    def test_build_cards_context_major_and_minor(self, three_cards):
        """메이저/마이너 혼합 카드의 한국어 변환"""
        drawn_cards = [
            DrawnCard(three_cards[0], Orientation.UPRIGHT),
            DrawnCard(three_cards[1], Orientation.UPRIGHT),
            DrawnCard(three_cards[2], Orientation.UPRIGHT),
        ]

        contexts = ContextBuilder.build_cards_context(drawn_cards)

        # 메이저 아르카나 (첫 두 장)
        assert contexts[0]["arcana_korean"] == "메이저 아르카나"
        assert contexts[0]["suit_korean"] is None
        assert contexts[1]["arcana_korean"] == "메이저 아르카나"
        assert contexts[1]["suit_korean"] is None

        # 마이너 아르카나 (세 번째 장)
        assert contexts[2]["arcana_korean"] == "마이너 아르카나"
        assert contexts[2]["suit_korean"] == "완드"

    def test_build_cards_context_empty_list(self):
        """빈 리스트 처리 테스트"""
        contexts = ContextBuilder.build_cards_context([])
        assert contexts == []

    def test_build_cards_context_single_card(self):
        """단일 카드 리스트 처리 테스트 (원카드 리딩)"""
        card = Card(
            id=1,
            name="The Fool",
            name_ko="바보",
            number=0,
            arcana_type=ArcanaType.MAJOR,
            suit=None,
            keywords_upright=["새로운 시작"],
            keywords_reversed=["무모함"],
            meaning_upright="Test",
            meaning_reversed="Test"
        )
        drawn_cards = [DrawnCard(card, Orientation.UPRIGHT)]

        contexts = ContextBuilder.build_cards_context(drawn_cards)

        assert len(contexts) == 1
        assert contexts[0]["name"] == "The Fool"


class TestContextBuilderEdgeCases:
    """엣지 케이스 및 예외 상황 테스트"""

    def test_context_immutability(self):
        """원본 Card 객체가 변경되지 않는지 확인"""
        card = Card(
            id=1,
            name="The Fool",
            name_ko="바보",
            number=0,
            arcana_type=ArcanaType.MAJOR,
            suit=None,
            keywords_upright=["test"],
            keywords_reversed=["test"],
            meaning_upright="Original upright",
            meaning_reversed="Original reversed"
        )
        original_name = card.name
        original_meaning = card.meaning_upright

        drawn_card = DrawnCard(card, Orientation.UPRIGHT)
        context = ContextBuilder.build_card_context(drawn_card)

        # 컨텍스트 수정
        context["name"] = "Modified Name"
        context["upright_meaning"] = "Modified Meaning"

        # 원본 Card는 변경되지 않아야 함
        assert card.name == original_name
        assert card.meaning_upright == original_meaning

    def test_context_contains_all_required_fields(self):
        """생성된 컨텍스트가 모든 필수 필드를 포함하는지 확인"""
        card = Card(
            id=1,
            name="Test",
            name_ko="테스트",
            number=0,
            arcana_type=ArcanaType.MAJOR,
            suit=None,
            keywords_upright=["test"],
            keywords_reversed=["test"],
            meaning_upright="Test",
            meaning_reversed="Test"
        )
        drawn_card = DrawnCard(card, Orientation.UPRIGHT)
        context = ContextBuilder.build_card_context(drawn_card)

        required_fields = [
            "name",
            "orientation",
            "orientation_korean",
            "arcana_korean",
            "suit_korean",
            "number",
            "keywords",
            "upright_meaning",
            "reversed_meaning",
        ]

        for field in required_fields:
            assert field in context, f"Required field '{field}' is missing"

    def test_context_field_types(self):
        """컨텍스트 필드의 타입이 올바른지 확인"""
        card = Card(
            id=1,
            name="Test",
            name_ko="테스트",
            number=5,
            arcana_type=ArcanaType.MINOR,
            suit=Suit.CUPS,
            keywords_upright=["love", "emotion"],
            keywords_reversed=["loss"],
            meaning_upright="Test",
            meaning_reversed="Test"
        )
        drawn_card = DrawnCard(card, Orientation.UPRIGHT)
        context = ContextBuilder.build_card_context(drawn_card)

        assert isinstance(context["name"], str)
        assert isinstance(context["orientation"], str)
        assert isinstance(context["orientation_korean"], str)
        assert isinstance(context["arcana_korean"], str)
        assert isinstance(context["suit_korean"], str) or context["suit_korean"] is None
        assert isinstance(context["number"], int) or context["number"] is None
        assert isinstance(context["keywords"], list)
        assert isinstance(context["upright_meaning"], str)
        assert isinstance(context["reversed_meaning"], str)
