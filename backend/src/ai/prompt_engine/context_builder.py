"""
Context Builder - 타로 리딩을 위한 컨텍스트 데이터 변환 모듈

이 모듈의 목적:
- Card 모델 객체를 AI 프롬프트에 사용할 수 있는 딕셔너리 형태로 변환
- 데이터베이스 모델과 프롬프트 템플릿 간의 어댑터 역할
- 영문 데이터를 한국어로 변환하여 프롬프트에 적합한 형식으로 제공
- PromptEngine과 독립적으로 테스트 가능한 컨텍스트 빌딩 로직 제공

주요 기능:
- build_card_context(): 단일 Card 객체를 프롬프트용 딕셔너리로 변환
- build_cards_context(): 여러 DrawnCard를 리스트 형태로 변환
- 한국어 변환: Orientation, ArcanaType, Suit를 한국어로 변환
- 키워드 리스트 처리 및 포맷팅

구현 사항:
- 단일 책임 원칙: 데이터 변환만 담당, 템플릿 렌더링은 PromptEngine이 담당
- 타입 안전성: 타입 힌팅을 통한 명확한 입출력 정의
- 불변성: 원본 Card 객체를 변경하지 않고 새로운 딕셔너리 반환
- 확장성: 새로운 필드 추가 시 쉽게 확장 가능한 구조

TASK 참조:
- TASK-024: 컨텍스트 빌더 구현

사용 예시:
    from src.models import Card, ArcanaType
    from src.core.card_shuffle import DrawnCard, Orientation
    from src.ai.prompt_engine.context_builder import ContextBuilder

    # Card 객체 생성
    card = Card(
        card_id="major_0",
        name="The Fool",
        arcana=ArcanaType.MAJOR,
        number=0,
        keywords=["new beginnings", "innocence"],
        upright_meaning="새로운 시작을 상징합니다.",
        reversed_meaning="무모함을 나타냅니다."
    )

    # DrawnCard로 방향 정보와 함께 사용
    drawn_card = DrawnCard(card, Orientation.UPRIGHT)

    # 컨텍스트 빌더로 변환
    builder = ContextBuilder()
    card_dict = builder.build_card_context(drawn_card)

    # 결과:
    # {
    #     "name": "The Fool",
    #     "orientation": "upright",
    #     "orientation_korean": "정방향",
    #     "arcana_korean": "메이저 아르카나",
    #     "number": 0,
    #     "keywords": ["new beginnings", "innocence"],
    #     "upright_meaning": "새로운 시작을 상징합니다.",
    #     "reversed_meaning": "무모함을 나타냅니다."
    # }
"""
from typing import Dict, Any, List, Optional, Union
from src.models import ArcanaType, Suit
from src.core.card_shuffle import DrawnCard, Orientation


class ContextBuilder:
    """
    타로 카드 컨텍스트 빌더

    Card 모델과 DrawnCard 객체를 프롬프트 템플릿에서 사용할 수 있는
    딕셔너리 형태로 변환합니다. 영문 enum 값을 한국어로 변환하여
    한국어 프롬프트에 적합한 형식으로 제공합니다.
    """

    # 방향 한국어 변환 매핑
    ORIENTATION_KOREAN = {
        "upright": "정방향",
        "reversed": "역방향",
    }

    # 아르카나 타입 한국어 변환 매핑
    ARCANA_KOREAN = {
        ArcanaType.MAJOR: "메이저 아르카나",
        ArcanaType.MINOR: "마이너 아르카나",
    }

    # 수트 한국어 변환 매핑
    SUIT_KOREAN = {
        Suit.WANDS: "완드",
        Suit.CUPS: "컵",
        Suit.SWORDS: "검",
        Suit.PENTACLES: "펜타클",
    }

    @staticmethod
    def get_orientation_korean(orientation: str) -> str:
        """
        카드 방향을 한국어로 변환

        Args:
            orientation: "upright" 또는 "reversed"

        Returns:
            한국어 방향 ("정방향" 또는 "역방향")
        """
        return ContextBuilder.ORIENTATION_KOREAN.get(orientation, orientation)

    @staticmethod
    def get_arcana_korean(arcana: Union[ArcanaType, str]) -> str:
        """
        아르카나 타입을 한국어로 변환

        Args:
            arcana: ArcanaType enum 값

        Returns:
            한국어 아르카나 타입 ("메이저 아르카나" 또는 "마이너 아르카나")
        """
        if isinstance(arcana, str):
            try:
                arcana_enum = ArcanaType(arcana)
            except ValueError:
                return arcana
        else:
            arcana_enum = arcana
        return ContextBuilder.ARCANA_KOREAN.get(arcana_enum, str(arcana_enum))

    @staticmethod
    def get_suit_korean(suit: Optional[Union[Suit, str]]) -> Optional[str]:
        """
        수트를 한국어로 변환

        Args:
            suit: Suit enum 값 (메이저 아르카나의 경우 None)

        Returns:
            한국어 수트 이름 또는 None
        """
        if suit is None:
            return None
        if isinstance(suit, str):
            try:
                suit_enum = Suit(suit)
            except ValueError:
                return suit
        else:
            suit_enum = suit
        return ContextBuilder.SUIT_KOREAN.get(suit_enum, str(suit_enum))

    @staticmethod
    def build_card_context(drawn_card: DrawnCard) -> Dict[str, Any]:
        """
        DrawnCard 객체를 프롬프트용 딕셔너리로 변환

        Card 객체와 방향 정보를 결합하여 Jinja2 템플릿에서 사용할 수 있는
        딕셔너리 형태로 변환합니다. 모든 enum 값은 한국어로 변환됩니다.

        Args:
            drawn_card: 선택된 카드 (Card + Orientation)

        Returns:
            프롬프트 템플릿용 딕셔너리:
            - name: 카드 이름
            - orientation: 방향 (영문)
            - orientation_korean: 방향 (한국어)
            - arcana_korean: 아르카나 타입 (한국어)
            - suit_korean: 수트 (한국어, 마이너 아르카나만)
            - number: 카드 번호
            - keywords: 키워드 리스트 (방향에 따라 upright/reversed)
            - upright_meaning: 정방향 의미
            - reversed_meaning: 역방향 의미
        """
        card = drawn_card.card
        orientation = drawn_card.orientation.value

        # 방향에 따라 적절한 키워드 선택
        if orientation == "upright":
            keywords = card.keywords_upright if getattr(card, "keywords_upright", None) else []
        else:
            keywords = card.keywords_reversed if getattr(card, "keywords_reversed", None) else []

        context = {
            "name": card.name,
            "orientation": orientation,
            "orientation_korean": ContextBuilder.get_orientation_korean(orientation),
            "arcana_korean": ContextBuilder.get_arcana_korean(getattr(card, "arcana_type", None)),
            "number": getattr(card, "number", None),
            "keywords": keywords,
            "upright_meaning": getattr(card, "meaning_upright", ""),
            "reversed_meaning": getattr(card, "meaning_reversed", ""),
        }

        # 수트 정보 추가 (마이너 아르카나만 해당)
        suit_value = getattr(card, "suit", None)
        if suit_value:
            context["suit_korean"] = ContextBuilder.get_suit_korean(suit_value)
        else:
            context["suit_korean"] = None

        return context

    @staticmethod
    def build_cards_context(drawn_cards: List[DrawnCard]) -> List[Dict[str, Any]]:
        """
        여러 DrawnCard를 프롬프트용 리스트로 변환

        Args:
            drawn_cards: 선택된 카드들의 리스트

        Returns:
            각 카드의 컨텍스트 딕셔너리를 담은 리스트
        """
        return [
            ContextBuilder.build_card_context(drawn_card)
            for drawn_card in drawn_cards
        ]
