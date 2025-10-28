"""
Reading API Routes - 타로 리딩 API 엔드포인트

이 모듈의 목적:
- 타로 리딩 생성, 조회 API 엔드포인트 제공
- 원카드 및 쓰리카드 리딩 플로우 구현
- AI Provider 통합 및 응답 처리
- 리딩 결과 데이터베이스 저장

주요 엔드포인트:
- POST /api/v1/readings: 새로운 리딩 생성 (원카드/쓰리카드)
- GET /api/v1/readings/{reading_id}: 리딩 상세 조회
- GET /api/v1/readings: 리딩 목록 조회 (페이지네이션)

리딩 생성 플로우:
1. ReadingRequest 검증 (Pydantic)
2. CardShuffleService로 카드 선택 (중복 없음, orientation 포함)
3. ContextBuilder로 프롬프트 생성 (템플릿 기반)
4. Orchestrator로 AI Provider 호출 (Fallback 지원)
5. ResponseParser로 AI 응답 파싱 및 검증
6. ReadingRepository로 DB 저장
7. ReadingResponse 반환

구현 사항:
- FastAPI의 Depends를 사용한 의존성 주입
- 상세한 에러 핸들링 및 로깅
- HTTP 상태 코드 적절히 사용 (200, 400, 404, 500)
- Swagger UI용 상세한 docstring

TASK 참조:
- TASK-027: 원카드 리딩 구현

사용 예시:
    # 원카드 리딩 생성
    POST /api/v1/readings
    {
        "question": "새로운 프로젝트를 시작해야 할까요?",
        "spread_type": "one_card",
        "category": "career"
    }

    # 리딩 조회
    GET /api/v1/readings/{reading_id}
"""
from typing import Optional
from uuid import UUID
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.logging import get_logger
from src.core.card_shuffle import CardShuffleService
from src.core.config import settings
from src.ai import AIOrchestrator, ProviderFactory, GenerationConfig
from src.ai.prompt_engine.context_builder import ContextBuilder
from src.ai.prompt_engine.response_parser import ResponseParser
from src.ai.prompt_engine.reading_validator import ReadingValidator
from src.ai.prompt_engine.schemas import ParseError, JSONExtractionError, ValidationError
from src.api.repositories.reading_repository import ReadingRepository
from src.api.dependencies.auth import get_current_active_user
from src.models import Reading, User
from src.schemas.reading import (
    ReadingRequest,
    ReadingResponse,
    ReadingCardResponse,
    ReadingListResponse
)
from src.schemas.card import CardResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/readings", tags=["readings"])

# Jinja2 환경 설정 (프롬프트 템플릿용)
PROMPTS_DIR = Path(__file__).parent.parent.parent.parent / "prompts"
jinja_env = Environment(loader=FileSystemLoader(str(PROMPTS_DIR)))

# AI Orchestrator 초기화 (글로벌, 싱글톤 패턴)
_orchestrator = None

def get_orchestrator() -> AIOrchestrator:
    """AI Orchestrator 싱글톤 인스턴스 반환"""
    global _orchestrator
    if _orchestrator is None:
        # Provider 생성 (Primary: Claude, Fallback: OpenAI)
        providers = []

        # Anthropic Provider (Primary - faster and more reliable)
        if settings.ANTHROPIC_API_KEY:
            anthropic_provider = ProviderFactory.create(
                provider_name="anthropic",
                api_key=settings.ANTHROPIC_API_KEY
            )
            providers.append(anthropic_provider)
            logger.info("Anthropic Provider initialized (Primary)")

        # OpenAI Provider (Fallback)
        if settings.OPENAI_API_KEY:
            openai_provider = ProviderFactory.create(
                provider_name="openai",
                api_key=settings.OPENAI_API_KEY
            )
            providers.append(openai_provider)
            logger.info("OpenAI Provider initialized (Fallback)")

        if not providers:
            raise ValueError("No AI providers configured")

        _orchestrator = AIOrchestrator(providers=providers, provider_timeout=30)
        logger.info(f"AIOrchestrator initialized with {len(providers)} providers")

    return _orchestrator


@router.post("/", response_model=ReadingResponse, status_code=201)
async def create_reading(
    request: ReadingRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    새로운 타로 리딩 생성 (인증 필요)

    현재 지원하는 스프레드:
    - **one_card**: 원카드 리딩 (1장)
    - **three_card_past_present_future**: 쓰리카드 리딩 - 과거/현재/미래 (3장)
    - **three_card_situation_action_outcome**: 쓰리카드 리딩 - 상황/행동/결과 (3장)

    플로우:
    1. 사용자 인증 확인 (Bearer Token)
    2. 요청 검증 (spread_type, question)
    3. 카드 선택 (CardShuffleService - 중복 없음, orientation 랜덤)
    4. 프롬프트 생성 (ContextBuilder - 템플릿 기반)
    5. AI 호출 (Orchestrator - Fallback 지원)
    6. 응답 파싱 (ResponseParser - JSON 검증)
    7. DB 저장 (Reading + ReadingCard, user_id 포함)
    8. 응답 반환

    Args:
        request: 리딩 요청 데이터
            - question: 사용자의 질문 (5-500자)
            - spread_type: 스프레드 타입
            - category: 리딩 카테고리 (optional)
            - user_context: 추가 컨텍스트 (optional)
        current_user: 인증된 사용자 (자동 주입)
        db: 데이터베이스 세션

    Returns:
        ReadingResponse: 생성된 리딩 결과

    Raises:
        HTTPException 401: 인증 실패
        HTTPException 403: 비활성화된 사용자
        HTTPException 400: 잘못된 요청 (카드 선택 실패, AI 응답 파싱 실패)
        HTTPException 500: 서버 에러 (AI 호출 실패, DB 저장 실패)
    """
    logger.info(
        f"[CreateReading] 리딩 생성 요청: "
        f"spread_type={request.spread_type}, "
        f"question={request.question[:50]}..."
    )

    try:
        # 1. 카드 선택
        # spread_type에 따라 선택할 카드 수 결정
        card_count_map = {
            "one_card": 1,
            "three_card_past_present_future": 3,
            "three_card_situation_action_outcome": 3,
        }
        card_count = card_count_map.get(request.spread_type, 1)

        logger.info(f"[CreateReading] 카드 선택 시작: {card_count}장")
        drawn_cards = CardShuffleService.draw_cards(db, count=card_count)
        logger.info(
            f"[CreateReading] 카드 선택 완료: "
            f"{[f'{dc.card.name}({dc.orientation})' for dc in drawn_cards]}"
        )

        # 2. 프롬프트 생성
        logger.info("[CreateReading] 프롬프트 생성 시작")

        # 카드 컨텍스트 빌드
        cards_context = [
            ContextBuilder.build_card_context(dc) for dc in drawn_cards
        ]

        # 스프레드 타입에 따른 템플릿 선택
        template_map = {
            "one_card": "reading/one_card.txt",
            "three_card_past_present_future": "reading/three_card_past_present_future.txt",
            "three_card_situation_action_outcome": "reading/three_card_situation_action_outcome.txt",
        }

        template_path = template_map.get(request.spread_type, "reading/one_card.txt")

        # System 프롬프트 로드
        system_template = jinja_env.get_template("system/tarot_expert.txt")
        system_prompt = system_template.render()

        # Reading 프롬프트 로드 및 렌더링
        reading_template = jinja_env.get_template(template_path)

        # 원카드의 경우 단일 카드, 쓰리카드의 경우 리스트
        if request.spread_type == "one_card":
            prompt_context = {
                "question": request.question,
                "category": request.category,
                "user_context": request.user_context,
                "card": cards_context[0]
            }
        else:
            prompt_context = {
                "question": request.question,
                "category": request.category,
                "user_context": request.user_context,
                "cards": cards_context
            }

        reading_prompt = reading_template.render(**prompt_context)

        # Output 포맷 프롬프트 로드
        output_template = jinja_env.get_template("output/structured_response.txt")
        output_format = output_template.render()

        # 전체 프롬프트 조합
        full_prompt = f"{reading_prompt}\n\n{output_format}"

        logger.info(f"[CreateReading] 프롬프트 생성 완료: {len(full_prompt)}자")

        # 3. AI 호출
        logger.info("[CreateReading] AI Provider 호출 시작")
        orchestrator = get_orchestrator()

        ai_response = await orchestrator.generate(
            prompt=full_prompt,
            system_prompt=system_prompt,
            config=GenerationConfig(
                max_tokens=2000,
                temperature=0.7
            )
        )

        raw_response = ai_response.content
        logger.info(f"[CreateReading] AI 응답 수신 완료: {len(raw_response)}자")

        # 4. 응답 파싱
        logger.info("[CreateReading] AI 응답 파싱 시작")
        parsed_response = ResponseParser.parse(raw_response)
        logger.info(
            f"[CreateReading] 파싱 완료: "
            f"{len(parsed_response.cards)}개 카드, "
            f"summary={parsed_response.summary[:30]}..."
        )

        # 4-1. 응답 품질 검증
        logger.info("[CreateReading] 응답 품질 검증 시작")
        ReadingValidator.validate_reading_quality(
            reading=parsed_response,
            expected_card_count=card_count
        )
        logger.info("[CreateReading] 응답 품질 검증 완료 ✅")

        # 5. DB 저장
        logger.info("[CreateReading] DB 저장 시작")

        # Reading 데이터 준비
        reading_data = {
            "spread_type": request.spread_type,
            "question": request.question,
            "category": request.category,
            "card_relationships": parsed_response.card_relationships,
            "overall_reading": parsed_response.overall_reading,
            "advice": parsed_response.advice.model_dump(),  # Pydantic V2
            "summary": parsed_response.summary,
            "user_id": current_user.id,  # 인증된 사용자 ID 저장
        }

        # ReadingCard 데이터 준비
        # parsed_response의 cards와 실제 drawn_cards를 매핑
        cards_data = []
        for i, card_interp in enumerate(parsed_response.cards):
            # drawn_cards에서 해당 카드 찾기
            drawn_card = drawn_cards[i]

            # card_id는 card_interp.card_id가 아니라 실제 drawn_card.card.id 사용
            # (AI가 반환한 card_id는 position 정보일 수 있음)
            cards_data.append({
                "card_id": drawn_card.card.id,
                "position": card_interp.position,
                "orientation": drawn_card.orientation,
                "interpretation": card_interp.interpretation,
                "key_message": card_interp.key_message,
            })

        # Repository를 통해 저장
        reading = ReadingRepository.create(
            db=db,
            reading_data=reading_data,
            cards_data=cards_data
        )
        db.commit()
        db.refresh(reading)  # relationship 데이터 로딩

        logger.info(
            f"[CreateReading] DB 저장 완료: "
            f"reading_id={reading.id}, "
            f"{len(reading.cards)}개 카드"
        )

        # 6. 응답 생성
        response_data = reading.to_dict()
        logger.info(f"[CreateReading] 리딩 생성 성공: {reading.id}")

        return ReadingResponse(**response_data)

    except ValueError as e:
        # CardShuffleService 에러 (카드 부족 등)
        logger.error(f"[CreateReading] 카드 선택 실패: {e}")
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"카드 선택 실패: {str(e)}"
        )

    except (ParseError, JSONExtractionError, ValidationError) as e:
        # ResponseParser 에러 (파싱 실패, 검증 실패)
        logger.error(f"[CreateReading] AI 응답 파싱 실패: {e}")
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"AI 응답 처리 실패: {str(e)}"
        )

    except Exception as e:
        # 기타 에러 (AI 호출 실패, DB 저장 실패 등)
        logger.error(f"[CreateReading] 리딩 생성 실패: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="리딩 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        )


@router.get("/{reading_id}", response_model=ReadingResponse)
async def get_reading(
    reading_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    리딩 상세 조회 (인증 필요)

    특정 리딩의 전체 정보를 조회합니다.
    연관된 카드 정보도 함께 반환됩니다.
    자신의 리딩만 조회할 수 있습니다.

    Args:
        reading_id: Reading UUID
        current_user: 인증된 사용자 (자동 주입)
        db: 데이터베이스 세션

    Returns:
        ReadingResponse: 리딩 상세 정보

    Raises:
        HTTPException 401: 인증 실패
        HTTPException 403: 권한 없음 (다른 사용자의 리딩)
        HTTPException 404: 리딩을 찾을 수 없음
        HTTPException 500: 서버 에러
    """
    try:
        reading = ReadingRepository.get_by_id(db, reading_id)

        if not reading:
            logger.warning(f"[GetReading] 리딩을 찾을 수 없음: {reading_id}")
            raise HTTPException(
                status_code=404,
                detail="리딩을 찾을 수 없습니다"
            )

        # 권한 검증: 자신의 리딩만 조회 가능
        if reading.user_id != current_user.id:
            logger.warning(
                f"[GetReading] 권한 없음: user_id={current_user.id}, "
                f"reading.user_id={reading.user_id}"
            )
            raise HTTPException(
                status_code=403,
                detail="이 리딩에 접근할 권한이 없습니다"
            )

        logger.info(f"[GetReading] 리딩 조회 성공: {reading_id}")

        response_data = reading.to_dict()
        return ReadingResponse(**response_data)

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"[GetReading] 리딩 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail="리딩 조회 중 오류가 발생했습니다"
        )


@router.get("/", response_model=ReadingListResponse)
async def list_readings(
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    spread_type: Optional[str] = Query(None, description="스프레드 타입 필터"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    리딩 목록 조회 (인증 필요)

    인증된 사용자의 리딩 목록을 최신순으로 조회합니다.
    페이지네이션 및 필터링을 지원합니다.

    Args:
        page: 페이지 번호 (1부터 시작)
        page_size: 페이지당 항목 수 (최대 100)
        spread_type: 스프레드 타입 필터 (optional)
        current_user: 인증된 사용자 (자동 주입)
        db: 데이터베이스 세션

    Returns:
        ReadingListResponse: 사용자의 리딩 목록 및 페이지네이션 정보

    Raises:
        HTTPException 401: 인증 실패
        HTTPException 403: 비활성화된 사용자
        HTTPException 500: 서버 에러
    """
    try:
        skip = (page - 1) * page_size

        # 인증된 사용자의 리딩만 조회
        if spread_type:
            # spread_type 필터링이 있는 경우
            readings = (
                db.query(Reading)
                .filter(Reading.user_id == current_user.id)
                .filter(Reading.spread_type == spread_type)
                .order_by(desc(Reading.created_at))
                .offset(skip)
                .limit(page_size)
                .all()
            )
            total = (
                db.query(Reading)
                .filter(Reading.user_id == current_user.id)
                .filter(Reading.spread_type == spread_type)
                .count()
            )
        else:
            # 모든 리딩 조회
            readings = ReadingRepository.get_by_user(
                db, current_user.id, skip, page_size
            )
            total = ReadingRepository.count_by_user(db, current_user.id)

        logger.info(
            f"[ListReadings] 사용자 리딩 목록 조회: "
            f"user_id={current_user.id}, {len(readings)}개 (page={page}, total={total})"
        )

        # Reading 모델을 ReadingResponse로 변환
        reading_responses = [
            ReadingResponse(**reading.to_dict())
            for reading in readings
        ]

        return ReadingListResponse(
            total=total,
            page=page,
            page_size=page_size,
            readings=reading_responses
        )

    except Exception as e:
        logger.error(f"[ListReadings] 리딩 목록 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail="리딩 목록 조회 중 오류가 발생했습니다"
        )
