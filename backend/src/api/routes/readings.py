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
from src.ai.models import (
    AIProviderError,
    AIRateLimitError,
    AITimeoutError,
    AIServiceUnavailableError,
    AIAuthenticationError,
)
from src.ai.rag.retriever import Retriever
from src.ai.rag.context_enricher import ContextEnricher
from src.ai.provider_loader import load_providers_from_settings, get_default_timeout_from_settings
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
_retriever: Optional[Retriever] = None
_context_enricher: Optional[ContextEnricher] = None


async def get_orchestrator(db_provider: DatabaseProvider) -> AIOrchestrator:
    """
    AI Orchestrator 싱글톤 인스턴스 반환
    
    데이터베이스에서 AI Provider 설정을 로드합니다.
    DB에 설정이 없으면 환경 변수로 폴백합니다.
    """
    global _orchestrator
    
    if _orchestrator is None:
        # Load providers from database settings
        providers = await load_providers_from_settings(
            db_provider=db_provider,
            fallback_to_env=True
        )
        
        # Get timeout from settings
        timeout = await get_default_timeout_from_settings(db_provider)
        
        _orchestrator = AIOrchestrator(
            providers=providers,
            provider_timeout=timeout,
        )
        logger.info(
            f"AIOrchestrator initialized with {len(providers)} provider(s) from DB, "
            f"timeout={timeout}s"
        )

    return _orchestrator


def get_retriever() -> Retriever:
    """RAG Retriever 싱글톤 인스턴스 반환"""
    global _retriever
    if _retriever is None:
        logger.info("Initializing RAG Retriever...")
        _retriever = Retriever()
        logger.info("RAG Retriever initialized successfully")
    return _retriever


def get_context_enricher() -> ContextEnricher:
    """RAG Context Enricher 싱글톤 인스턴스 반환"""
    global _context_enricher
    if _context_enricher is None:
        logger.info("Initializing RAG Context Enricher...")
        retriever = get_retriever()
        _context_enricher = ContextEnricher(retriever)
        logger.info("RAG Context Enricher initialized successfully")
    return _context_enricher


def invalidate_orchestrator_cache() -> None:
    """
    AI Orchestrator 캐시를 무효화하여 다음 요청 시 재초기화되도록 합니다.
    
    관리자가 AI Provider 설정을 변경한 후 이 함수를 호출하면
    다음 리딩 요청부터 새로운 설정이 적용됩니다.
    """
    global _orchestrator
    if _orchestrator is not None:
        logger.info("[CacheInvalidation] Invalidating AI Orchestrator cache")
        _orchestrator = None
    else:
        logger.info("[CacheInvalidation] AI Orchestrator cache is already empty")


def invalidate_rag_cache() -> None:
    """
    RAG 관련 캐시를 무효화합니다 (Retriever, ContextEnricher).
    """
    global _retriever, _context_enricher
    
    if _retriever is not None or _context_enricher is not None:
        logger.info("[CacheInvalidation] Invalidating RAG cache (Retriever, ContextEnricher)")
        _retriever = None
        _context_enricher = None
    else:
        logger.info("[CacheInvalidation] RAG cache is already empty")


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
    from src.schemas.reading import LLMUsageResponse

    cards: List[ReadingCardResponse] = []
    for index, card_entry in enumerate(reading.cards or []):
        cards.append(await _hydrate_card_entry(card_entry, reading.id, index, provider))

    created_at = _parse_datetime(reading.created_at) or datetime.utcnow()
    updated_at = _parse_datetime(reading.updated_at) or created_at

    # Build LLM usage response objects
    llm_usage_responses = []
    for log_entry in reading.llm_usage:
        llm_usage_responses.append(LLMUsageResponse(
            id=log_entry.get("id", ""),
            reading_id=log_entry.get("reading_id", reading.id),
            provider=log_entry.get("provider", ""),
            model=log_entry.get("model", ""),
            prompt_tokens=log_entry.get("prompt_tokens", 0),
            completion_tokens=log_entry.get("completion_tokens", 0),
            total_tokens=log_entry.get("total_tokens", 0),
            estimated_cost=log_entry.get("estimated_cost", 0.0),
            latency_seconds=log_entry.get("latency_seconds", 0.0),
            purpose=log_entry.get("purpose", "main_reading"),
            created_at=_parse_datetime(log_entry.get("created_at")),
        ))

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
        llm_usage=llm_usage_responses,
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
        # Import card shuffle components (needed for both user selection and random modes)
        from src.core.card_shuffle import DrawnCard, Orientation, CardData, CardShuffleService
        
        card_count_map = {
            "one_card": 1,
            "three_card_past_present_future": 3,
            "three_card_situation_action_outcome": 3,
            "celtic_cross": 10,
        }
        card_count = card_count_map.get(request.spread_type, 1)

        # Two modes: User Selection vs Random
        if request.selected_card_ids:
            # User Selection Mode: Use selected cards
            logger.info(
                "[CreateReading] User Selection Mode: %s",
                request.selected_card_ids
            )
            
            # Validate card count
            if len(request.selected_card_ids) != card_count:
                raise ValueError(
                    f"선택한 카드 수({len(request.selected_card_ids)})가 "
                    f"필요한 카드 수({card_count})와 일치하지 않습니다."
                )
            
            # Validate reversed_states if provided
            if request.reversed_states is not None:
                if len(request.reversed_states) != len(request.selected_card_ids):
                    raise ValueError(
                        f"reversed_states 길이({len(request.reversed_states)})가 "
                        f"selected_card_ids 길이({len(request.selected_card_ids)})와 일치하지 않습니다."
                    )
            
            drawn_cards = []
            for idx, card_id in enumerate(request.selected_card_ids):
                card_dto = await db_provider.get_card_by_id(card_id)
                if not card_dto:
                    raise ValueError(f"카드 ID {card_id}를 찾을 수 없습니다.")
                
                # Convert to CardData
                card_data = CardData(
                    id=card_dto.id,
                    name=card_dto.name_en,
                    name_ko=card_dto.name_ko,
                    arcana_type=card_dto.arcana_type,
                    number=card_dto.number,
                    suit=card_dto.suit,
                    keywords_upright=card_dto.keywords_upright,
                    keywords_reversed=card_dto.keywords_reversed,
                    meaning_upright=card_dto.meaning_upright,
                    meaning_reversed=card_dto.meaning_reversed,
                    description=card_dto.description,
                    symbolism=card_dto.symbolism,
                    image_url=card_dto.image_url,
                )
                
                # Use provided reversed_states if available, otherwise randomly determine (30% chance for reversed)
                if request.reversed_states is not None and idx < len(request.reversed_states):
                    orientation = Orientation.REVERSED if request.reversed_states[idx] else Orientation.UPRIGHT
                else:
                    orientation = CardShuffleService._random_orientation()
                
                drawn_cards.append(DrawnCard(card_data, orientation))
            
            logger.info(
                "[CreateReading] 사용자 선택 카드: %s",
                [f"{dc.card.name}({dc.orientation.value})" for dc in drawn_cards],
            )
        else:
            # Random Mode: Draw random cards
            logger.info("[CreateReading] Random Mode: drawing %d cards", card_count)
            
            drawn_cards = await CardShuffleService.draw_cards(
                count=card_count,
                provider=db_provider,
            )
            logger.info(
                "[CreateReading] 랜덤 카드 선택 완료: %s",
                [f"{dc.card.name}({dc.orientation.value})" for dc in drawn_cards],
            )

        # RAG context enrichment
        context_enricher = get_context_enricher()
        card_data = [
            {"id": dc.card.id, "is_reversed": dc.orientation.value == "reversed"}
            for dc in drawn_cards
        ]
        rag_context = context_enricher.enrich_prompt_context(
            cards=card_data,
            spread_type=request.spread_type,
            question=request.question,
            category=request.category or "general",
            language="ko",
        )
        logger.info("[CreateReading] RAG 컨텍스트 강화 완료")

        cards_context = [ContextBuilder.build_card_context(dc) for dc in drawn_cards]

        # Build prompts using Jinja2 templates
        # Select template based on prompt language setting
        prompt_lang = settings.PROMPT_LANGUAGE
        lang_suffix = f"_{prompt_lang}" if prompt_lang == "en" else ""

        template_map = {
            "one_card": f"reading/one_card{lang_suffix}.txt",
            "three_card_past_present_future": f"reading/three_card_past_present_future{lang_suffix}.txt",
            "three_card_situation_action_outcome": f"reading/three_card_situation_action_outcome{lang_suffix}.txt",
            "celtic_cross": f"reading/celtic_cross{lang_suffix}.txt",
        }
        template_path = template_map.get(request.spread_type, f"reading/one_card{lang_suffix}.txt")

        logger.info(f"[CreateReading] Using prompt template: {template_path} (language: {prompt_lang})")

        system_template = jinja_env.get_template("system/tarot_expert.txt")
        system_prompt = system_template.render()

        # Try to load template with language suffix, fallback to default (Korean) if not found
        try:
            reading_template = jinja_env.get_template(template_path)
            logger.debug(f"[CreateReading] Template loaded successfully: {template_path}")
        except Exception as e:
            # If language-specific template doesn't exist, fallback to default (Korean) version
            if lang_suffix:
                logger.warning(
                    f"[CreateReading] Template {template_path} not found (error: {e}), "
                    f"falling back to default (Korean) version"
                )
                # Remove language suffix to use default template
                base_template_map = {
                    "one_card": "reading/one_card.txt",
                    "three_card_past_present_future": "reading/three_card_past_present_future.txt",
                    "three_card_situation_action_outcome": "reading/three_card_situation_action_outcome.txt",
                    "celtic_cross": "reading/celtic_cross.txt",
                }
                fallback_template_path = base_template_map.get(
                    request.spread_type, "reading/one_card.txt"
                )
                try:
                    reading_template = jinja_env.get_template(fallback_template_path)
                    logger.info(f"[CreateReading] Using fallback template: {fallback_template_path}")
                except Exception as fallback_error:
                    logger.error(
                        f"[CreateReading] Failed to load both primary ({template_path}) and "
                        f"fallback ({fallback_template_path}) templates: {fallback_error}"
                    )
                    raise HTTPException(
                        status_code=500,
                        detail=f"템플릿 파일을 로드할 수 없습니다: {fallback_template_path}",
                    )
            else:
                # If already using default template, re-raise the error
                logger.error(f"[CreateReading] Failed to load template {template_path}: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"템플릿 파일을 로드할 수 없습니다: {template_path}",
                )

        if request.spread_type == "one_card":
            prompt_context = {
                "question": request.question,
                "category": request.category,
                "user_context": request.user_context,
                "card": cards_context[0],
                "rag_context": rag_context,
            }
        else:
            prompt_context = {
                "question": request.question,
                "category": request.category,
                "user_context": request.user_context,
                "cards": cards_context,
                "rag_context": rag_context,
            }

        reading_prompt = reading_template.render(**prompt_context)
        output_template = jinja_env.get_template("output/structured_response.txt")
        output_format = output_template.render()

        full_prompt = f"{reading_prompt}\n\n{output_format}"

        orchestrator = await get_orchestrator(db_provider)
        # Optimized max_tokens configuration by spread type
        # Note: API limit is 4096 tokens, so we cap at that value
        # - One card: 2000 tokens (sufficient for single card interpretation)
        # - Three card: 3500 tokens (balanced for three cards)
        # - Celtic Cross: 4096 tokens (10 cards require extensive interpretation, capped at API limit)
        MAX_TOKENS_CONFIG = {
            1: 2000,   # one_card
            3: 3500,   # three_card spreads
            10: 4096,  # celtic_cross (capped at API limit)
        }
        max_tokens = MAX_TOKENS_CONFIG.get(card_count, 3500)  # Default fallback
        # Ensure max_tokens doesn't exceed API limit
        max_tokens = min(max_tokens, 4096)

        # Retry logic for parsing failures
        MAX_PARSE_RETRIES = 2  # 최대 2번 재시도 (총 3번 시도)
        parsed_response = None
        last_parse_error = None
        all_orchestrator_responses = []  # 모든 시도의 응답 저장 (LLM 로그용)

        for parse_attempt in range(MAX_PARSE_RETRIES + 1):
            try:
                # Generate response (재시도 시에는 새로운 응답 생성)
                if parse_attempt > 0:
                    logger.warning(
                        "[CreateReading] 파싱 재시도 %d/%d: 이전 오류=%s",
                        parse_attempt,
                        MAX_PARSE_RETRIES,
                        str(last_parse_error)[:100]
                    )
                    # 재시도 시 max_tokens를 증가시켜 응답이 잘리지 않도록 함 (API 제한 고려)
                    previous_max_tokens = max_tokens
                    max_tokens = min(int(max_tokens * 1.3), 4096)  # Cap at API limit
                    logger.info(
                        "[CreateReading] max_tokens 증가: %d → %d (API 제한: 4096)",
                        previous_max_tokens,
                        max_tokens
                    )

                orchestrator_response = await orchestrator.generate(
                    prompt=full_prompt,
                    system_prompt=system_prompt,
                    config=GenerationConfig(
                        max_tokens=max_tokens,
                        temperature=0.7,
                    ),
                )

                # 모든 시도 저장 (LLM 로그용)
                all_orchestrator_responses.append(orchestrator_response)

                # Extract successful response
                ai_response = orchestrator_response.response
                raw_response = ai_response.content

                # Check if response was truncated due to max_tokens limit
                if ai_response.finish_reason == "max_tokens" or ai_response.finish_reason == "length":
                    logger.warning(
                        "[CreateReading] 응답이 max_tokens 제한으로 잘렸을 수 있습니다. "
                        "finish_reason=%s, tokens=%d/%d, attempt=%d",
                        ai_response.finish_reason,
                        ai_response.completion_tokens,
                        max_tokens,
                        parse_attempt + 1
                    )

                # Try to parse the response
                parsed_response = ResponseParser.parse(raw_response)

                # Parsing succeeded!
                if parse_attempt > 0:
                    logger.info(
                        "[CreateReading] 파싱 성공! (재시도 %d회 후)",
                        parse_attempt
                    )
                break  # Exit retry loop on success

            except (ParseError, JSONExtractionError, ValidationError) as e:
                last_parse_error = e
                
                # Enhanced error logging with context
                error_type = type(e).__name__
                error_summary = str(e)[:300]  # Truncate for logging
                
                # Check if response was truncated
                was_truncated = (
                    ai_response.finish_reason in ("max_tokens", "length") 
                    if 'ai_response' in locals() else False
                )
                
                logger.warning(
                    "[CreateReading] 파싱 실패 (시도 %d/%d): %s - %s%s",
                    parse_attempt + 1,
                    MAX_PARSE_RETRIES + 1,
                    error_type,
                    error_summary,
                    " (응답이 잘림)" if was_truncated else ""
                )

                # 마지막 시도였다면 예외를 다시 던짐
                if parse_attempt >= MAX_PARSE_RETRIES:
                    logger.error(
                        "[CreateReading] 모든 파싱 재시도 실패 (%d회 시도). "
                        "마지막 오류: %s - %s",
                        parse_attempt + 1,
                        error_type,
                        error_summary
                    )
                    raise

                # 아직 재시도 가능하면 계속 진행
                continue

        # 파싱이 성공하지 못했다면 (이론적으로 도달 불가능)
        if parsed_response is None:
            raise ParseError("파싱 재시도 후에도 응답을 처리할 수 없습니다")

        ReadingValidator.validate_reading_quality(
            reading=parsed_response,
            expected_card_count=card_count,
            spread_type=request.spread_type,
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

        # Phase 3 Optimization: Build LLM usage logs for batch creation
        llm_logs_batch = []
        total_llm_attempts = 0
        total_llm_cost = 0.0

        for orch_resp_idx, orch_resp in enumerate(all_orchestrator_responses):
            # 각 파싱 시도마다 orchestrator가 여러 provider를 시도할 수 있음
            for attempt_idx, attempt in enumerate(orch_resp.all_attempts):
                # purpose 결정
                if orch_resp_idx == len(all_orchestrator_responses) - 1:
                    # 마지막 파싱 시도
                    if attempt_idx == len(orch_resp.all_attempts) - 1:
                        purpose = "main_reading"  # 최종 성공
                    else:
                        purpose = "retry"  # 같은 파싱 시도 내 재시도
                else:
                    # 이전 파싱 시도들
                    purpose = "parse_retry"  # 파싱 실패 후 재시도

                llm_logs_batch.append({
                    "provider": attempt.provider,
                    "model": attempt.model,
                    "prompt_tokens": attempt.prompt_tokens or 0,
                    "completion_tokens": attempt.completion_tokens or 0,
                    "total_tokens": attempt.total_tokens or 0,
                    "estimated_cost": attempt.estimated_cost or 0.0,
                    "latency_seconds": (attempt.latency_ms or 0) / 1000.0,
                    "purpose": purpose,
                })

                total_llm_attempts += 1
                total_llm_cost += attempt.estimated_cost or 0.0
        
        # Phase 3: Create all LLM logs in one batch operation
        if llm_logs_batch:
            await db_provider.create_llm_usage_logs_batch(
                reading_dto.id,
                llm_logs_batch
            )
            
            # Log latency statistics
            total_latency = sum(log['latency_seconds'] for log in llm_logs_batch)
            avg_latency = total_latency / len(llm_logs_batch) if llm_logs_batch else 0
            logger.info(
                "[CreateReading] LLM 로그 저장 완료: %d개, 평균 응답시간: %.2fs",
                len(llm_logs_batch),
                avg_latency
            )

        reading_response = await _build_reading_response(reading_dto, db_provider)

        logger.info(
            "[CreateReading] 리딩 생성 성공: %s (LLM attempts: %d, Parsing retries: %d, Total cost: $%.4f, Avg latency: %.2fs)",
            reading_response.id,
            total_llm_attempts,
            len(all_orchestrator_responses) - 1,  # 첫 시도는 제외
            total_llm_cost,
            avg_latency if llm_logs_batch else 0
        )
        return reading_response

    except (ParseError, JSONExtractionError, ValidationError) as e:
        logger.error("[CreateReading] AI 응답 처리 실패: %s", e)
        # Provide user-friendly error messages based on error type
        if isinstance(e, JSONExtractionError):
            error_detail = "AI 응답 형식 오류가 발생했습니다. 응답이 잘렸을 수 있습니다."
        elif isinstance(e, ValidationError):
            error_detail = "AI 응답 검증 실패: " + str(e)
        else:
            error_detail = "AI 응답 파싱 실패: " + str(e)
        raise HTTPException(
            status_code=400,
            detail=error_detail,
        )
    except ValueError as e:
        logger.error("[CreateReading] 카드 선택 실패: %s", e)
        raise HTTPException(
            status_code=400,
            detail=f"카드 선택 실패: {str(e)}",
        )
    except (AIRateLimitError, AIServiceUnavailableError) as e:
        logger.error("[CreateReading] AI 서비스 일시적 오류: %s", e)
        raise HTTPException(
            status_code=503,
            detail="AI 서비스가 일시적으로 사용할 수 없습니다. 잠시 후 다시 시도해주세요.",
        )
    except AITimeoutError as e:
        logger.error("[CreateReading] AI 요청 타임아웃: %s", e)
        raise HTTPException(
            status_code=504,
            detail="AI 응답 생성 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.",
        )
    except AIAuthenticationError as e:
        logger.error("[CreateReading] AI 인증 오류: %s", e)
        raise HTTPException(
            status_code=500,
            detail="AI 서비스 인증 오류가 발생했습니다. 관리자에게 문의해주세요.",
        )
    except AIProviderError as e:
        logger.error("[CreateReading] AI Provider 오류: %s", e)
        raise HTTPException(
            status_code=500,
            detail="AI 서비스 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[CreateReading] 리딩 생성 실패: %s", e)
        # Log the actual error type for debugging
        error_type = type(e).__name__
        logger.error(f"[CreateReading] 예상치 못한 오류 타입: {error_type}")
        raise HTTPException(
            status_code=500,
            detail="리딩 생성 중 예상치 못한 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
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
