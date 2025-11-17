"""
Spread Configuration - 스프레드 타입별 설정 관리

이 모듈의 목적:
- 각 스프레드 타입의 설정을 중앙화하여 관리
- 새로운 스프레드 타입 추가 시 설정만 추가하면 되도록 추상화
- 중복 코드 제거 및 확장성 향상

주요 기능:
- 스프레드 타입별 카드 수, 포지션 정보, 프롬프트 템플릿 경로 관리
- 병렬 처리 지원 여부 및 배치 크기 설정
- 스프레드별 특화 설정 관리
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class PositionInfo:
    """포지션 정보"""
    index: int
    position: str  # 영어 포지션명 (예: "present", "past")
    name: str  # 한글 포지션명 (예: "현재", "과거")
    meaning: str  # 포지션 의미 설명


@dataclass
class SpreadConfig:
    """스프레드 설정"""
    spread_type: str
    card_count: int
    positions: List[PositionInfo]
    supports_parallel: bool = False  # 병렬 처리 지원 여부
    batch_size: int = 3  # 병렬 처리 시 배치 크기
    prompt_templates: Optional[Dict[str, str]] = None  # 프롬프트 템플릿 경로
    # 병렬 처리용 템플릿 (None이면 단일 프롬프트 사용)
    parallel_templates: Optional[Dict[str, str]] = None
    max_tokens: Optional[int] = None  # 최대 토큰 수 (None이면 자동 계산)
    # 병렬 처리 시 동시 호출 수 제한 (None이면 제한 없음)
    max_concurrent_calls: Optional[int] = None


# 스프레드 설정 레지스트리
SPREAD_CONFIGS: Dict[str, SpreadConfig] = {
    "one_card": SpreadConfig(
        spread_type="one_card",
        card_count=1,
        positions=[
            PositionInfo(
                index=0,
                position="single",
                name="현재",
                meaning="현재 상황이나 질문. 지금 일어나고 있는 일을 나타냅니다."
            )
        ],
        supports_parallel=False,
        prompt_templates={
            "main": "reading/one_card.txt"
        },
        max_tokens=2000
    ),
    "three_card_past_present_future": SpreadConfig(
        spread_type="three_card_past_present_future",
        card_count=3,
        positions=[
            PositionInfo(index=0, position="past", name="과거", meaning="과거의 영향과 기반"),
            PositionInfo(index=1, position="present", name="현재", meaning="현재 상황과 도전"),
            PositionInfo(index=2, position="future", name="미래", meaning="가까운 미래의 가능성"),
        ],
        supports_parallel=False,
        prompt_templates={
            "main": "reading/three_card_past_present_future.txt"
        },
        max_tokens=3500
    ),
    "three_card_situation_action_outcome": SpreadConfig(
        spread_type="three_card_situation_action_outcome",
        card_count=3,
        positions=[
            PositionInfo(index=0, position="situation", name="상황", meaning="현재 상황"),
            PositionInfo(index=1, position="action", name="행동", meaning="취해야 할 행동"),
            PositionInfo(index=2, position="outcome", name="결과", meaning="예상되는 결과"),
        ],
        supports_parallel=False,
        prompt_templates={
            "main": "reading/three_card_situation_action_outcome.txt"
        },
        max_tokens=3500
    ),
    "celtic_cross": SpreadConfig(
        spread_type="celtic_cross",
        card_count=10,
        positions=[
            PositionInfo(index=0, position="present", name="현재", meaning="현재 상황이나 질문. 지금 일어나고 있는 일을 나타냅니다."),
            PositionInfo(index=1, position="challenge", name="도전", meaning="현재 상황을 가로지르는 즉각적인 도전이나 장애물."),
            PositionInfo(index=2, position="past", name="과거", meaning="현재 상황으로 이끈 먼 과거의 기반. 근본 원인이나 배경."),
            PositionInfo(index=3, position="future", name="미래", meaning="가까운 미래의 가능성이나 곧 다가올 것."),
            PositionInfo(index=4, position="above", name="의식적 목표", meaning="의식적 목표, 열망, 또는 질문자가 달성하고자 하는 것."),
            PositionInfo(index=5, position="below", name="무의식적 영향", meaning="무의식적 영향, 숨겨진 동기, 또는 근본적인 기반."),
            PositionInfo(index=6, position="advice", name="조언", meaning="상황에 접근하는 방법에 대한 조언이나 안내."),
            PositionInfo(index=7, position="external", name="외부 영향", meaning="외부 영향, 다른 사람들, 또는 상황에 영향을 미치는 환경적 요인."),
            PositionInfo(index=8, position="hopes_fears", name="희망과 두려움", meaning="상황을 둘러싼 희망과 두려움. 질문자의 감정 상태."),
            PositionInfo(index=9, position="outcome", name="최종 결과", meaning="현재 경로가 계속되면 최종 결과나 해결책."),
        ],
        supports_parallel=True,
        batch_size=3,
        parallel_templates={
            "card": "reading/celtic_cross_card.txt",
            "overall": "reading/celtic_cross_overall.txt",
            "relationships": "reading/celtic_cross_relationships.txt",
            "advice": "reading/celtic_cross_advice.txt",
        },
        max_tokens=4096,
        max_concurrent_calls=5  # 동시에 최대 5개의 LLM 호출 허용
    ),
    # 향후 추가될 스프레드 타입 예시
    # "horoscope": SpreadConfig(
    #     spread_type="horoscope",
    #     card_count=12,  # 12개 별자리
    #     positions=[...],
    #     supports_parallel=True,
    #     batch_size=4,
    #     parallel_templates={
    #         "card": "reading/horoscope_card.txt",
    #         "overall": "reading/horoscope_overall.txt",
    #     }
    # ),
}


def get_spread_config(spread_type: str) -> Optional[SpreadConfig]:
    """
    스프레드 타입에 맞는 설정 반환
    
    Args:
        spread_type: 스프레드 타입 문자열
    
    Returns:
        SpreadConfig 또는 None (존재하지 않는 타입인 경우)
    """
    return SPREAD_CONFIGS.get(spread_type)


def get_card_count(spread_type: str) -> int:
    """
    스프레드 타입에 맞는 카드 수 반환
    
    Args:
        spread_type: 스프레드 타입 문자열
    
    Returns:
        카드 수 (기본값: 1)
    """
    config = get_spread_config(spread_type)
    return config.card_count if config else 1


def get_position_names(spread_type: str) -> List[str]:
    """
    스프레드 타입에 맞는 포지션 이름 리스트 반환
    
    Args:
        spread_type: 스프레드 타입 문자열
    
    Returns:
        포지션 이름 리스트 (한글)
    """
    config = get_spread_config(spread_type)
    if config:
        return [pos.name for pos in config.positions]
    return []


def supports_parallel_processing(spread_type: str) -> bool:
    """
    스프레드 타입이 병렬 처리를 지원하는지 확인
    
    Args:
        spread_type: 스프레드 타입 문자열
    
    Returns:
        병렬 처리 지원 여부
    """
    config = get_spread_config(spread_type)
    return config.supports_parallel if config else False


def get_prompt_template_path(
    spread_type: str,
    template_key: str = "main",
    language: str = "en"
) -> Optional[str]:
    """
    스프레드 타입에 맞는 프롬프트 템플릿 경로 반환
    
    Args:
        spread_type: 스프레드 타입 문자열
        template_key: 템플릿 키 ("main", "card", "overall" 등)
        language: 언어 ("en" 또는 "ko")
    
    Returns:
        템플릿 경로 또는 None
    """
    config = get_spread_config(spread_type)
    if not config:
        return None
    
    # 병렬 처리용 템플릿 확인
    if config.parallel_templates and template_key in config.parallel_templates:
        base_path = config.parallel_templates[template_key]
    # 일반 템플릿 확인
    elif config.prompt_templates and template_key in config.prompt_templates:
        base_path = config.prompt_templates[template_key]
    else:
        return None
    
    # 언어 접미사 추가
    if language == "en":
        # 영어 프롬프트가 있으면 _en 접미사 추가
        if base_path.endswith(".txt"):
            return base_path.replace(".txt", "_en.txt")
        return f"{base_path}_en.txt"
    else:
        # 한국어는 기본 경로 사용
        return base_path


def register_spread_config(config: SpreadConfig):
    """
    새로운 스프레드 설정 등록
    
    Args:
        config: SpreadConfig 인스턴스
    """
    SPREAD_CONFIGS[config.spread_type] = config
    logger.info(f"Registered new spread config: {config.spread_type}")


def get_max_tokens(spread_type: str, language: str = "ko") -> int:
    """
    스프레드 타입에 맞는 최대 토큰 수 반환
    
    Args:
        spread_type: 스프레드 타입 문자열
        language: 언어 ("en" 또는 "ko")
    
    Returns:
        최대 토큰 수 (기본값: 2500)
    """
    config = get_spread_config(spread_type)
    if config and config.max_tokens:
        return config.max_tokens
    
    # 기본값: 카드 수에 따라 결정
    card_count = get_card_count(spread_type)
    if card_count == 1:
        return 2000
    elif card_count == 3:
        return 3500
    elif card_count >= 10:
        return 4096  # API limit
    else:
        return 2500

