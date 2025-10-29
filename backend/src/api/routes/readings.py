"""
Reading API Routes - 타로 리딩 API 엔드포인트

이 모듈의 목적:
- 타로 리딩 생성, 조회 API 엔드포인트 제공
- 원카드 및 쓰리카드 리딩 플로우 구현
- AI Provider 통합 및 응답 처리
- 리딩 결과 데이터베이스 저장 (Firestore / PostgreSQL 추상화)

주요 엔드포인트:
- POST /api/v1/readings: 새로운 리딩 생성 (원카드/쓰리카드)
- GET /api/v1/readings/{reading_id}: 리딩 상세 조회
- GET /api/v1/readings: 리딩 목록 조회 (페이지네이션)
"""
from __future__ import annotations

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from jinja2 import Environment, FileSystemLoader

from src.core.logging import get_logger
from src.core.card_shuffle import CardShuffleService, DrawnCard
from src.core.config import settings
from src.ai import AIOrchestrator, ProviderFactory, GenerationConfig
from src.ai.prompt_engine.context_builder import ContextBuilder
from src.ai.prompt_engine.response_parser import ResponseParser
from src.ai.prompt_engine.reading_validator import ReadingValidator
from src.ai.prompt_engine.schemas import ParseError, JSONExtractionError, ValidationError
from src.api.dependencies.auth import get_current_active_user
from src.database.factory import get_database_provider
from src.database.provider import (
    DatabaseProvider,
    Reading as ReadingDTO,
    Card as CardDTO,
)
from src.schemas.reading import (
    ReadingRequest,
    ReadingResponse,
    ReadingCardResponse,
    ReadingListResponse,
)
from src.schemas.card import CardResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/readings", tags=["readings"])

# Jinja2 환경 설정 (프롬프트 템플릿용)
PROMPTS_DIR = Path(__file__).parent.parent.parent.parent / "prompts"
jinja_env = Environment(loader=FileSystemLoader(str(PROMPTS_DIR)))


# AI Orchestrator 초기화 (글로벌, 싱글톤 패턴)
_orchestrator: Optional[AIOrchestrator] = None


def get_orchestrator() -> AIOrchestrator:
    """AI Orchestrator 싱글톤 인스턴스 반환"""
    global _orchestrator
    if _orchestrator is None:
        providers = []

        priority_raw = getattr(settings, "AI_PROVIDER_PRIORITY", "anthropic,openai")
        provider_order = [
            provider.strip().lower()
            for provider in priority_raw.split(",")
            if provider.strip()
        ]

        added = set()
        for provider_name in provider_order:
            if provider_name == "openai" and settings.OPENAI_API_KEY and "openai" not in added:
                openai_provider = ProviderFactory.create(
                    provider_name="openai",
                    api_key=settings.OPENAI_API_KEY,
                )
                providers.append(openai_provider)
                added.add("openai")
                logger.info("OpenAI Provider initialized")
            elif provider_name == "anthropic" and settings.ANTHROPIC_API_KEY and "anthropic" not in added:
                anthropic_provider = ProviderFactory.create(
                    provider_name="anthropic",
                    api_key=settings.ANTHROPIC_API_KEY,
                )
                providers.append(anthropic_provider)
                added.add("anthropic")
                logger.info("Anthropic Provider initialized")

        # Fallback to defaults if none added due to misconfiguration
        if not providers:
            if settings.ANTHROPIC_API_KEY:
                providers.append(
                    ProviderFactory.create(
                        provider_name="anthropic",
                        api_key=settings.ANTHROPIC_API_KEY,
                    )
                )
                logger.info("Anthropic Provider initialized (default fallback)")
            if settings.OPENAI_API_KEY:
                providers.append(
                    ProviderFactory.create(
                        provider_name="openai",
                        api_key=settings.OPENAI_API_KEY,
                    )
                )
                logger.info("OpenAI Provider initialized (default fallback)")

        if not providers:
            raise ValueError("No AI providers configured")

        _orchestrator = AIOrchestrator(providers=providers, provider_timeout=30)
        logger.info("AIOrchestrator initialized")

    return _orchestrator


def _parse_datetime(value: Optional[Any]) -> Optional[datetime]:
    """입력값을 datetime으로 변환"""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if hasattr(value, "to_datetime"):
        return value.to_datetime()
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return datetime.utcnow().replace(tzinfo=timezone.utc)


def _card_dto_to_dict(card: CardDTO) -> Dict[str, Any]:
    """Card DTO를 직렬화된 딕셔너리로 변환"""
    return card.to_dict()


def _card_dict_to_response(card_dict: Dict[str, Any]) -> CardResponse:
    """카드 딕셔너리를 CardResponse로 변환"""
    if not card_dict:
        raise ValueError("Card data is missing")

    name = card_dict.get("name") or card_dict.get("name_en")
    if name is None:
        raise ValueError("Card name is missing")

    created_at = _parse_datetime(card_dict.get("created_at")) or datetime.utcnow()
    updated_at = _parse_datetime(card_dict.get("updated_at")) or created_at

    return CardResponse(
        id=card_dict.get("id"),
        name=name,
        name_ko=card_dict.get("name_ko") or card_dict.get("nameKo") or name,
        number=card_dict.get("number"),
        arcana_type=card_dict.get("arcana_type") or card_dict.get("arcanaType"),
        suit=card_dict.get("suit"),
        keywords_upright=card_dict.get("keywords_upright", []),
        keywords_reversed=card_dict.get("keywords_reversed", []),
        meaning_upright=card_dict.get("meaning_upright", ""),
        meaning_reversed=card_dict.get("meaning_reversed", ""),
        description=card_dict.get("description"),
        symbolism=card_dict.get("symbolism"),
        image_url=card_dict.get("image_url"),
        created_at=created_at,
        updated_at=updated_at,
    )


async def _hydrate_card_entry(
    card_entry: Dict[str, Any],
    reading_id: str,
    index: int,
    provider: DatabaseProvider,
) -> ReadingCardResponse:
    """Firestore 카드 엔트리를 API 응답 형태로 변환"""
    card_data = card_entry.get("card")

    if not card_data and card_entry.get("card_id") is not None:
        card_dto = await provider.get_card_by_id(int(card_entry["card_id"]))
        if card_dto:
            card_data = _card_dto_to_dict(card_dto)

    if not card_data:
        raise ValueError("Card details are unavailable for reading card entry")

    card_response = _card_dict_to_response(card_data)

    return ReadingCardResponse(
        id=card_entry.get("id") or f"{reading_id}_card_{index}",
        reading_id=reading_id,
        card_id=card_response.id,
        position=card_entry.get("position"),
        orientation=card_entry.get("orientation"),
        interpretation=card_entry.get("interpretation"),
        key_message=card_entry.get("key_message"),
        card=card_response,
    )


async def _build_reading_response(
    reading: ReadingDTO,
    provider: DatabaseProvider,
) -> ReadingResponse:
    """Reading DTO를 API 응답으로 변환"""
    cards: List[ReadingCardResponse] = []
    for index, card_entry in enumerate(reading.cards or []):
        cards.append(await _hydrate_card_entry(card_entry, reading.id, index, provider))

    created_at = _parse_datetime(reading.created_at) or datetime.utcnow()
    updated_at = _parse_datetime(reading.updated_at) or created_at

    return ReadingResponse(
        id=reading.id,
        user_id=reading.user_id,
        spread_type=reading.spread_type,
        question=reading.question,
        category=reading.category,
        cards=cards,
        card_relationships=reading.card_relationships,
        overall_reading=reading.overall_reading,
        advice=reading.advice,
        summary=reading.summary,
        created_at=created_at,
        updated_at=updated_at,
    )


def _build_cards_payload(
    drawn_cards: List[DrawnCard],
    parsed_cards: List[Any],
) -> List[Dict[str, Any]]:
    """Firestore 저장을 위한 카드 payload 생성"""
    payload: List[Dict[str, Any]] = []
    for index, card_interp in enumerate(parsed_cards):
        drawn_card = drawn_cards[index]
        payload.append(
            {
                "card_id": drawn_card.card.id,
                "position": card_interp.position,
                "orientation": drawn_card.orientation.value,
                "interpretation": card_interp.interpretation,
                "key_message": card_interp.key_message,
                "card": drawn_card.card.to_dict(),
            }
        )
    return payload


@router.post("", response_model=ReadingResponse, status_code=201)
async def create_reading(
    request: ReadingRequest,
    current_user=Depends(get_current_active_user),
    db_provider: DatabaseProvider = Depends(get_database_provider),
):
    """
    새로운 타로 리딩 생성 (인증 필요)
    """
    logger.info(
        "[CreateReading] 요청 접수: spread_type=%s question=%s...",
        request.spread_type,
        request.question[:50],
    )

    try:
        card_count_map = {
            "one_card": 1,
            "three_card_past_present_future": 3,
            "three_card_situation_action_outcome": 3,
        }
        card_count = card_count_map.get(request.spread_type, 1)

        drawn_cards = await CardShuffleService.draw_cards(
            count=card_count,
            provider=db_provider,
        )
        logger.info(
            "[CreateReading] 카드 선택 완료: %s",
            [f"{dc.card.name}({dc.orientation.value})" for dc in drawn_cards],
        )

        cards_context = [ContextBuilder.build_card_context(dc) for dc in drawn_cards]

        template_map = {
            "one_card": "reading/one_card.txt",
            "three_card_past_present_future": "reading/three_card_past_present_future.txt",
            "three_card_situation_action_outcome": "reading/three_card_situation_action_outcome.txt",
        }
        template_path = template_map.get(request.spread_type, "reading/one_card.txt")

        system_template = jinja_env.get_template("system/tarot_expert.txt")
        system_prompt = system_template.render()

        reading_template = jinja_env.get_template(template_path)

        if request.spread_type == "one_card":
            prompt_context = {
                "question": request.question,
                "category": request.category,
                "user_context": request.user_context,
                "card": cards_context[0],
            }
        else:
            prompt_context = {
                "question": request.question,
                "category": request.category,
                "user_context": request.user_context,
                "cards": cards_context,
            }

        reading_prompt = reading_template.render(**prompt_context)
        output_template = jinja_env.get_template("output/structured_response.txt")
        output_format = output_template.render()

        full_prompt = f"{reading_prompt}\n\n{output_format}"

        orchestrator = get_orchestrator()
        # 다중 카드 스프레드에서는 응답이 길어져 타임아웃이 발생하기 쉬우므로
        # 카드 수에 맞춰 토큰 한도를 조정해 응답 시간을 단축한다.
        max_tokens = 900 if card_count == 1 else 1300

        ai_response = await orchestrator.generate(
            prompt=full_prompt,
            system_prompt=system_prompt,
            config=GenerationConfig(
                max_tokens=max_tokens,
                temperature=0.7,
            ),
        )

        raw_response = ai_response.content
        parsed_response = ResponseParser.parse(raw_response)

        ReadingValidator.validate_reading_quality(
            reading=parsed_response,
            expected_card_count=card_count,
        )

        reading_data = {
            "spread_type": request.spread_type,
            "question": request.question,
            "category": request.category,
            "card_relationships": parsed_response.card_relationships,
            "overall_reading": parsed_response.overall_reading,
            "advice": parsed_response.advice.model_dump(),
            "summary": parsed_response.summary,
            "user_id": getattr(current_user, "id", None),
            "cards": _build_cards_payload(drawn_cards, parsed_response.cards),
        }

        reading_dto = await db_provider.create_reading(reading_data)
        reading_response = await _build_reading_response(reading_dto, db_provider)

        logger.info("[CreateReading] 리딩 생성 성공: %s", reading_response.id)
        return reading_response

    except (ParseError, JSONExtractionError, ValidationError) as e:
        logger.error("[CreateReading] AI 응답 처리 실패: %s", e)
        raise HTTPException(
            status_code=400,
            detail=f"AI 응답 처리 실패: {str(e)}",
        )
    except ValueError as e:
        logger.error("[CreateReading] 카드 선택 실패: %s", e)
        raise HTTPException(
            status_code=400,
            detail=f"카드 선택 실패: {str(e)}",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[CreateReading] 리딩 생성 실패: %s", e)
        raise HTTPException(
            status_code=500,
            detail="리딩 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
        )


@router.get("/{reading_id}", response_model=ReadingResponse)
async def get_reading(
    reading_id: str,
    current_user=Depends(get_current_active_user),
    db_provider: DatabaseProvider = Depends(get_database_provider),
):
    """
    리딩 상세 조회 (인증 필요)
    """
    try:
        reading = await db_provider.get_reading_by_id(reading_id)
        if not reading:
            logger.warning("[GetReading] 리딩을 찾을 수 없음: %s", reading_id)
            raise HTTPException(status_code=404, detail="리딩을 찾을 수 없습니다")

        if reading.user_id and getattr(current_user, "id", None):
            if reading.user_id != str(current_user.id):
                logger.warning(
                    "[GetReading] 권한 없음: requester=%s owner=%s",
                    current_user.id,
                    reading.user_id,
                )
                raise HTTPException(
                    status_code=403,
                    detail="이 리딩에 접근할 권한이 없습니다",
                )

        return await _build_reading_response(reading, db_provider)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[GetReading] 리딩 조회 실패: %s", e)
        raise HTTPException(
            status_code=500,
            detail="리딩 조회 중 오류가 발생했습니다",
        )


@router.get("/", response_model=ReadingListResponse)
async def list_readings(
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    spread_type: Optional[str] = Query(None, description="스프레드 타입 필터"),
    current_user=Depends(get_current_active_user),
    db_provider: DatabaseProvider = Depends(get_database_provider),
):
    """
    리딩 목록 조회 (인증 필요)
    """
    try:
        skip = (page - 1) * page_size

        readings = await db_provider.get_readings_by_user(
            user_id=str(current_user.id),
            skip=skip,
            limit=page_size,
            spread_type=spread_type,
        )

        total = await db_provider.get_total_readings_count(
            user_id=str(current_user.id),
            spread_type=spread_type,
        )

        reading_responses: List[ReadingResponse] = []
        for reading in readings:
            reading_responses.append(await _build_reading_response(reading, db_provider))

        return ReadingListResponse(
            total=total,
            page=page,
            page_size=page_size,
            readings=reading_responses,
        )

    except Exception as e:
        logger.exception("[ListReadings] 리딩 목록 조회 실패: %s", e)
        raise HTTPException(
            status_code=500,
            detail="리딩 목록 조회 중 오류가 발생했습니다",
        )
