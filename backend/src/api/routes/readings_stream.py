"""
SSE Streaming Endpoint for Tarot Readings

This module provides Server-Sent Events (SSE) streaming for real-time
tarot reading generation with progress updates.
"""
import asyncio
import time
import traceback
from typing import AsyncGenerator, Optional, List, Dict, Any, Set
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from jinja2 import Environment, FileSystemLoader

from src.core.logging import get_logger
from src.core.config import settings
from src.core.card_shuffle import CardShuffleService, DrawnCard
from src.database.factory import get_database_provider
from src.database.provider import DatabaseProvider
from src.schemas.reading import ReadingRequest
from src.schemas.sse_events import (
    SSEEventType,
    ReadingStage,
    create_sse_event,
    create_progress_event,
    create_card_drawn_event,
    create_section_complete_event,
    create_complete_event,
    create_error_event,
    StartedEvent,
    RAGEnrichmentEvent,
    AIGenerationEvent,
)
from src.ai import AIOrchestrator, ProviderFactory, GenerationConfig
from src.ai.prompt_engine.context_builder import ContextBuilder
from src.ai.prompt_engine.response_parser import ResponseParser
from src.ai.prompt_engine.reading_validator import ReadingValidator
from src.ai.rag.retriever import Retriever
from src.ai.rag.context_enricher import ContextEnricher
from src.ai.provider_loader import load_providers_from_settings, get_default_timeout_from_settings
from src.api.dependencies.auth import get_current_active_user

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/readings", tags=["readings-stream"])

# Jinja2 environment for prompt templates
PROMPTS_DIR = Path(__file__).parent.parent.parent.parent / "prompts"
jinja_env = Environment(loader=FileSystemLoader(str(PROMPTS_DIR)))

# Singleton holders for RAG components
_retriever: Optional[Retriever] = None
_context_enricher: Optional[ContextEnricher] = None


# Cache for AI Orchestrator instance
_orchestrator: Optional[AIOrchestrator] = None


# Track background persistence tasks to avoid premature GC
_persistence_tasks: Set[asyncio.Task] = set()


async def get_orchestrator(db_provider: DatabaseProvider) -> AIOrchestrator:
    """
    Get or create AI Orchestrator singleton with configured providers
    
    데이터베이스에서 AI Provider 설정을 로드합니다.
    DB에 설정이 없으면 환경 변수로 폴백합니다.
    """
    global _orchestrator

    if _orchestrator is not None:
        return _orchestrator

    try:
        # Load AI providers from database settings (with fallback to env vars)
        providers = await load_providers_from_settings(
            db_provider=db_provider,
            fallback_to_env=True
        )
        
        # Get default timeout from settings (with buffer for complex tarot readings)
        default_timeout = await get_default_timeout_from_settings(db_provider)
        provider_timeout = max(90, default_timeout + 60)  # At least 90s
        
        # Initialize orchestrator with loaded providers
        _orchestrator = AIOrchestrator(
            providers=providers,
            provider_timeout=provider_timeout,
            max_retries=2
        )
        logger.info(
            f"AIOrchestrator initialized with {len(providers)} provider(s) from DB, "
            f"timeout={provider_timeout}s"
        )

        return _orchestrator

    except Exception as e:
        logger.error(f"Failed to initialize AIOrchestrator: {e}")
        raise


def get_retriever() -> Retriever:
    """Get or create RAG Retriever singleton"""
    global _retriever
    if _retriever is None:
        logger.info("Initializing RAG Retriever for streaming...")
        _retriever = Retriever()
    return _retriever


def get_context_enricher() -> ContextEnricher:
    """Get or create RAG Context Enricher singleton"""
    global _context_enricher
    if _context_enricher is None:
        logger.info("Initializing RAG Context Enricher for streaming...")
        retriever = get_retriever()
        _context_enricher = ContextEnricher(retriever)
    return _context_enricher


def invalidate_orchestrator_cache() -> None:
    """
    AI Orchestrator 캐시를 무효화하여 다음 요청 시 재초기화되도록 합니다.
    
    관리자가 AI Provider 설정을 변경한 후 이 함수를 호출하면
    다음 리딩 요청부터 새로운 설정이 적용됩니다.
    """
    global _orchestrator
    if _orchestrator is not None:
        logger.info("[CacheInvalidation] Invalidating AI Orchestrator cache (streaming)")
        _orchestrator = None
    else:
        logger.info("[CacheInvalidation] AI Orchestrator cache is already empty (streaming)")


def invalidate_rag_cache() -> None:
    """
    RAG 관련 캐시를 무효화합니다 (Retriever, ContextEnricher).
    """
    global _retriever, _context_enricher
    
    if _retriever is not None or _context_enricher is not None:
        logger.info("[CacheInvalidation] Invalidating RAG cache (streaming)")
        _retriever = None
        _context_enricher = None
    else:
        logger.info("[CacheInvalidation] RAG cache is already empty (streaming)")


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


async def generate_reading_stream(
    request: ReadingRequest,
    user_id: str,
    db_provider: DatabaseProvider
) -> AsyncGenerator[str, None]:
    """
    Generate tarot reading with SSE progress updates

    Args:
        request: Reading creation request
        user_id: Authenticated user ID
        db_provider: Database provider instance

    Yields:
        SSE formatted event strings
    """
    start_time = time.time()
    reading_id = None

    try:
        # ===== Stage 1: Initialize =====
        yield create_progress_event(
            ReadingStage.INITIALIZING,
            0,
            "리딩 준비 중..."
        ).to_sse_format()

        yield create_sse_event(
            SSEEventType.STARTED,
            StartedEvent()
        ).to_sse_format()

        await asyncio.sleep(0.1)

        # ===== Stage 2: Draw Cards =====
        card_count_map = {
            "one_card": 1,
            "three_card_past_present_future": 3,
            "three_card_situation_action_outcome": 3,
        }
        card_count = card_count_map.get(request.spread_type, 1)

        # Two modes: User Selection vs Random
        if request.selected_card_ids:
            # User Selection Mode: Use selected cards
            yield create_progress_event(
                ReadingStage.DRAWING_CARDS,
                10,
                "선택한 카드를 준비하는 중..."
            ).to_sse_format()
            
            logger.info(f"[SSE] User Selection Mode: {request.selected_card_ids}")
            
            # Validate card count
            if len(request.selected_card_ids) != card_count:
                raise ValueError(
                    f"선택한 카드 수({len(request.selected_card_ids)})가 "
                    f"필요한 카드 수({card_count})와 일치하지 않습니다."
                )
            
            # Fetch selected cards from database
            from src.core.card_shuffle import DrawnCard, Orientation, CardData, CardShuffleService
            
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
        else:
            # Random Mode: Draw random cards
            yield create_progress_event(
                ReadingStage.DRAWING_CARDS,
                10,
                "카드를 뽑는 중..."
            ).to_sse_format()
            
            logger.info(f"[SSE] Random Mode: drawing {card_count} cards")
            
            drawn_cards = await CardShuffleService.draw_cards(
                count=card_count,
                provider=db_provider,
            )

        # Send card drawn events
        position_names = {
            "one_card": ["현재"],
            "three_card_past_present_future": ["과거", "현재", "미래"],
            "three_card_situation_action_outcome": ["상황", "행동", "결과"],
        }
        positions = position_names.get(request.spread_type, [])

        for idx, drawn_card in enumerate(drawn_cards):
            progress = 10 + int((idx + 1) / len(drawn_cards) * 20)  # 10-30%
            position = positions[idx] if idx < len(positions) else f"Position {idx+1}"

            yield create_card_drawn_event(
                card_id=drawn_card.card.id,
                card_name=drawn_card.card.name,
                card_name_ko=drawn_card.card.name_ko,
                position=position,
                is_reversed=(drawn_card.orientation.value == "reversed"),
                progress=progress
            ).to_sse_format()

            await asyncio.sleep(0.2)

        logger.info(
            "[SSE] 카드 선택 완료: %s",
            [f"{dc.card.name}({dc.orientation.value})" for dc in drawn_cards],
        )

        # ===== Stage 3: RAG Context Enrichment =====
        yield create_progress_event(
            ReadingStage.ENRICHING_CONTEXT,
            35,
            "카드 의미 검색 중...",
            "타로 지식 데이터베이스에서 카드 정보를 가져오고 있습니다"
        ).to_sse_format()

        context_enricher = get_context_enricher()
        card_data = [
            {"id": dc.card.id, "is_reversed": dc.orientation.value == "reversed"}
            for dc in drawn_cards
        ]

        # Phase 2 Optimization: Use async version for parallel RAG queries
        rag_context = await context_enricher.enrich_prompt_context_async(
            cards=card_data,
            spread_type=request.spread_type,
            question=request.question,
            category=request.category or "general",
            language="ko",
        )

        yield create_sse_event(
            SSEEventType.RAG_ENRICHMENT,
            RAGEnrichmentEvent(
                cards_enriched=len(rag_context.get("card_contexts", [])),
                spread_context_loaded=bool(rag_context.get("spread_context")),
                category_context_loaded=bool(rag_context.get("category_guidance"))
            )
        ).to_sse_format()

        yield create_progress_event(
            ReadingStage.ENRICHING_CONTEXT,
            50,
            "컨텍스트 준비 완료"
        ).to_sse_format()

        logger.info("[SSE] RAG 컨텍스트 강화 완료")
        await asyncio.sleep(0.1)

        # ===== Stage 4: AI Generation =====
        yield create_progress_event(
            ReadingStage.GENERATING_AI,
            60,
            "AI 리딩 생성 중...",
            "Claude AI가 타로 리딩을 해석하고 있습니다"
        ).to_sse_format()

        # Build context for AI generation
        cards_context = [ContextBuilder.build_card_context(dc) for dc in drawn_cards]

        if request.spread_type == "one_card":
            prompt_context = {
                "question": request.question,
                "category": request.category,
                "card": cards_context[0],
                "rag_context": rag_context,
            }
        else:
            prompt_context = {
                "question": request.question,
                "category": request.category,
                "cards": cards_context,
                "rag_context": rag_context,
            }

        # Build prompts using Jinja2 templates
        # Select template based on prompt language setting
        prompt_lang = settings.PROMPT_LANGUAGE
        lang_suffix = f"_{prompt_lang}" if prompt_lang == "en" else ""

        template_map = {
            "one_card": f"reading/one_card{lang_suffix}.txt",
            "three_card_past_present_future": f"reading/three_card_past_present_future{lang_suffix}.txt",
            "three_card_situation_action_outcome": f"reading/three_card_situation_action_outcome{lang_suffix}.txt",
        }
        template_path = template_map.get(request.spread_type, f"reading/one_card{lang_suffix}.txt")

        logger.info(f"[SSE] Using prompt template: {template_path} (language: {prompt_lang})")

        system_template = jinja_env.get_template("system/tarot_expert.txt")
        system_prompt = system_template.render()

        reading_template = jinja_env.get_template(template_path)
        reading_prompt = reading_template.render(**prompt_context)

        output_template = jinja_env.get_template("output/structured_response.txt")
        output_format = output_template.render()

        full_prompt = f"{reading_prompt}\n\n{output_format}"

        orchestrator = await get_orchestrator(db_provider)
        card_count = len(drawn_cards)

        # Phase 1 Optimization: Increased max_tokens to prevent truncation and reduce retries
        # English prompts are more token-efficient, but Korean responses still need sufficient tokens
        MAX_TOKENS_CONFIG = {
            "one_card": {"en": 2000, "ko": 2000},  # Increased from 1500
            "three_card": {"en": 3500, "ko": 3500},  # Increased from 2500
        }
        spread_category = "three_card" if card_count > 1 else "one_card"
        max_tokens = MAX_TOKENS_CONFIG[spread_category].get(prompt_lang, 2500)

        yield create_sse_event(
            SSEEventType.AI_GENERATION,
            AIGenerationEvent(
                provider="anthropic",
                model="claude-sonnet-4",
                message="AI 리딩 생성 시작"
            )
        ).to_sse_format()

        # Retry logic for parsing failures
        MAX_PARSE_RETRIES = 2
        parsed_response = None
        last_parse_error = None
        all_llm_results = []

        for parse_attempt in range(MAX_PARSE_RETRIES + 1):
            try:
                # Generate response (재시도 시 max_tokens 증가)
                if parse_attempt > 0:
                    logger.warning(
                        "[SSE] 파싱 재시도 %d/%d: 이전 오류=%s",
                        parse_attempt,
                        MAX_PARSE_RETRIES,
                        str(last_parse_error)[:100]
                    )
                    max_tokens = int(max_tokens * 1.3)

                    yield create_progress_event(
                        ReadingStage.GENERATING_AI,
                        60 + parse_attempt * 5,
                        f"AI 리딩 재생성 중... (시도 {parse_attempt + 1}/{MAX_PARSE_RETRIES + 1})"
                    ).to_sse_format()

                llm_result = await orchestrator.generate(
                    prompt=full_prompt,
                    system_prompt=system_prompt,
                    config=GenerationConfig(
                        max_tokens=max_tokens,
                        temperature=0.7,
                        timeout=90,
                    ),
                )

                all_llm_results.append(llm_result)

                # Check if response was truncated
                if llm_result.response.finish_reason in ("max_tokens", "length"):
                    logger.warning(
                        "[SSE] 응답이 잘렸을 수 있음: finish_reason=%s, tokens=%d/%d",
                        llm_result.response.finish_reason,
                        llm_result.response.completion_tokens,
                        max_tokens
                    )

                # Parse the response
                parser = ResponseParser()
                parsed_response = parser.parse(llm_result.response.content)

                # Parsing succeeded!
                if parse_attempt > 0:
                    logger.info("[SSE] 파싱 성공! (재시도 %d회 후)", parse_attempt)

                break  # Exit retry loop

            except Exception as e:
                last_parse_error = e

                if parse_attempt >= MAX_PARSE_RETRIES:
                    logger.error("[SSE] 모든 파싱 재시도 실패 (%d회)", parse_attempt + 1)
                    raise

                logger.warning(
                    "[SSE] 파싱 실패, 재시도 예정: %s",
                    str(e)[:200]
                )
                continue

        if parsed_response is None:
            from src.ai.prompt_engine.schemas import ParseError
            raise ParseError("파싱 재시도 후에도 응답을 처리할 수 없습니다")

        yield create_progress_event(
            ReadingStage.GENERATING_AI,
            80,
            "AI 리딩 생성 완료"
        ).to_sse_format()

        logger.info("[SSE] AI 리딩 생성 완료: %d 토큰 사용", llm_result.response.total_tokens)

        # ===== Stage 5: Validate =====
        yield create_progress_event(
            ReadingStage.FINALIZING,
            82,
            "리딩 분석 중..."
        ).to_sse_format()

        validator = ReadingValidator()
        card_count = len(drawn_cards)
        validator.validate_reading_quality(
            reading=parsed_response,
            expected_card_count=card_count
        )
        # Note: validate_reading_quality raises ValidationError on failure, no return value

        # ===== Send section-complete events as data becomes available =====

        # 1. Summary section
        yield create_section_complete_event(
            section="summary",
            data={"summary": parsed_response.summary},
            progress=84
        ).to_sse_format()
        await asyncio.sleep(0.1)

        # 2. Cards section
        cards_payload = _build_cards_payload(drawn_cards, parsed_response.cards)
        yield create_section_complete_event(
            section="cards",
            data={"cards": cards_payload},
            progress=86
        ).to_sse_format()
        await asyncio.sleep(0.1)

        # 3. Overall reading section
        yield create_section_complete_event(
            section="overall_reading",
            data={"overall_reading": parsed_response.overall_reading},
            progress=88
        ).to_sse_format()
        await asyncio.sleep(0.1)

        # 4. Advice section
        yield create_section_complete_event(
            section="advice",
            data={"advice": parsed_response.advice.model_dump()},
            progress=90
        ).to_sse_format()
        await asyncio.sleep(0.1)

        # ===== Stage 6: Save to Database =====
        yield create_progress_event(
            ReadingStage.FINALIZING,
            92,
            "리딩 저장 예약 중..."
        ).to_sse_format()

        # Build LLM usage logs for all attempts (including retries)
        llm_usage_logs = []
        logger.info(f"[SSE] Building LLM usage logs: {len(all_llm_results)} parse attempts")
        for result_idx, result in enumerate(all_llm_results):
            # Each orchestrator result may have multiple provider attempts
            logger.info(f"[SSE]   Parse attempt {result_idx + 1}: {len(result.all_attempts)} provider attempts")
            for attempt_idx, attempt in enumerate(result.all_attempts):
                # Determine purpose
                if result_idx == len(all_llm_results) - 1:
                    # Last parsing attempt
                    if attempt_idx == len(result.all_attempts) - 1:
                        purpose = "main_reading"  # Final success
                    else:
                        purpose = "retry"  # Provider retry within same parse attempt
                else:
                    # Previous parsing attempts
                    purpose = "parse_retry"  # Parse failure retry

                log_entry = {
                    "provider": attempt.provider,
                    "model": attempt.model,
                    "prompt_tokens": attempt.prompt_tokens or 0,
                    "completion_tokens": attempt.completion_tokens or 0,
                    "total_tokens": attempt.total_tokens or 0,
                    "estimated_cost": attempt.estimated_cost or 0.0,
                    "latency_seconds": (attempt.latency_ms or 0) / 1000.0,  # 🐛 Fix: Convert ms to seconds
                    "purpose": purpose,
                    "created_at": datetime.now(timezone.utc),
                }
                llm_usage_logs.append(log_entry)
                logger.info(
                    f"[SSE]     - {purpose}: {attempt.provider}/{attempt.model}, "
                    f"{attempt.total_tokens} tokens, {log_entry['latency_seconds']:.2f}s"
                )

        logger.info(f"[SSE] Total LLM usage logs: {len(llm_usage_logs)}")

        reading_id = str(uuid4())

        reading_data = {
            "id": reading_id,
            "user_id": user_id,
            "spread_type": request.spread_type,
            "question": request.question,
            "category": request.category or "general",
            "cards": cards_payload,
            "card_relationships": parsed_response.card_relationships,
            "overall_reading": parsed_response.overall_reading,
            "advice": parsed_response.advice.model_dump(),
            "summary": parsed_response.summary,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "llm_usage": llm_usage_logs,
        }

        async def _persist_reading() -> None:
            try:
                await db_provider.create_reading(reading_data)
                logger.info("[SSE] Background reading persistence complete: reading_id=%s", reading_id)
            except Exception as persistence_error:
                logger.error(
                    "[SSE] Background reading persistence failed: id=%s error=%s",
                    reading_id,
                    persistence_error
                )
                logger.error(traceback.format_exc())

        persistence_task = asyncio.create_task(_persist_reading())
        _persistence_tasks.add(persistence_task)

        def _cleanup_task(task: asyncio.Task) -> None:
            _persistence_tasks.discard(task)
            if task.cancelled():
                logger.warning("[SSE] Background persistence task cancelled: reading_id=%s", reading_id)
            elif task.exception():
                logger.error(
                    "[SSE] Background persistence task raised: reading_id=%s error=%s",
                    reading_id,
                    task.exception()
                )

        persistence_task.add_done_callback(_cleanup_task)

        yield create_progress_event(
            ReadingStage.FINALIZING,
            95,
            "저장 백그라운드 처리 중"
        ).to_sse_format()

        # ===== Stage 7: Complete =====
        total_time = time.time() - start_time

        yield create_progress_event(
            ReadingStage.COMPLETED,
            100,
            "리딩 완료!"
        ).to_sse_format()

        reading_summary = {
            "reading_id": reading_id,
            "question": request.question,
            "spread_type": request.spread_type,
            "card_count": len(drawn_cards),
            "category": request.category,
            "status": "pending",
        }

        yield create_complete_event(
            reading_id=reading_id,
            total_time=round(total_time, 2),
            reading_summary=reading_summary
        ).to_sse_format()
        logger.info(f"[SSE] Reading {reading_id} generated (persistence scheduled) in {total_time:.2f}s")

    except Exception as e:
        logger.error(f"[SSE] Error generating reading: {e}")
        logger.error(traceback.format_exc())

        yield create_error_event(
            error_type=type(e).__name__,
            message=str(e),
            details=traceback.format_exc()[:500],  # Truncate for safety
            stage=ReadingStage.GENERATING_AI
        ).to_sse_format()


@router.post("/stream/test", response_class=StreamingResponse)
async def create_reading_stream_test(
    request: ReadingRequest,
    db_provider: DatabaseProvider = Depends(get_database_provider),
):
    """
    Test endpoint for SSE streaming without authentication

    **WARNING: This is for testing only. Remove in production!**
    """
    # Use a test user ID
    test_user_id = "test-user-sse"
    logger.info(f"[SSE Test] Starting streamed reading for test user: {request.spread_type}")

    return StreamingResponse(
        generate_reading_stream(request, test_user_id, db_provider),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


@router.post("/stream", response_class=StreamingResponse)
async def create_reading_stream(
    request: ReadingRequest,
    current_user=Depends(get_current_active_user),
    db_provider: DatabaseProvider = Depends(get_database_provider),
):
    """
    Create a new tarot reading with SSE streaming

    This endpoint streams Server-Sent Events with real-time progress updates
    during the reading generation process.

    **Authentication Required**

    **Event Types:**
    - `started`: Reading generation begins
    - `progress`: Progress update with percentage and message
    - `card_drawn`: A card has been drawn
    - `rag_enrichment`: RAG context enrichment completed
    - `ai_generation`: AI generation started
    - `complete`: Reading generation completed successfully
    - `error`: An error occurred during generation

    **Response:** text/event-stream (SSE format)
    """
    # Extract user_id - both FirebaseUser and SQLAlchemy User models use 'id' attribute
    user_id = current_user.id
    logger.info(f"[SSE] Starting streamed reading for user {user_id}: {request.spread_type}")

    return StreamingResponse(
        generate_reading_stream(request, user_id, db_provider),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )
