"""
Parallel Reading Engine - 병렬 LLM 처리 엔진

이 모듈의 목적:
- 켈틱 크로스 리딩을 병렬 LLM 호출로 처리
- 프롬프트 세분화 및 배치 생성
- 결과 통합 및 검증
- 카드 인용 시스템 통합

주요 기능:
- 카드 배치 생성 및 병렬 해석
- 종합 리딩, 관계 분석, 조언 병렬 생성
- 결과 통합 및 ReadingResponse 생성
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from src.ai.orchestrator import AIOrchestrator
from src.ai.models import GenerationConfig, OrchestratorResponse
from src.ai.prompt_engine.context_builder import ContextBuilder
from src.ai.prompt_engine.response_parser import ResponseParser
import json
from src.ai.prompt_engine.schemas import ReadingResponse, CardInterpretation, Advice, JSONExtractionError
from src.ai.prompt_engine.llm_allocation import LLMAllocator, get_allocator
from src.ai.prompt_engine.citation_formatter import CitationFormatter
from src.core.card_shuffle import DrawnCard
from src.core.config import settings
from src.ai.prompt_engine.spread_config import get_spread_config

logger = logging.getLogger(__name__)


class ParallelReadingEngine:
    """
    병렬 리딩 엔진
    
    병렬 처리를 지원하는 스프레드 타입의 리딩을 병렬 LLM 호출로 처리하여 성능과 품질을 향상시킵니다.
    스프레드 설정은 spread_config.py에서 관리되며, 새로운 스프레드 타입 추가 시 설정만 추가하면 됩니다.
    """
    
    def __init__(
        self,
        orchestrator: AIOrchestrator,
        allocator: Optional[LLMAllocator] = None,
        spread_type: str = "celtic_cross"
    ):
        """
        병렬 리딩 엔진 초기화
        
        Args:
            orchestrator: AI 오케스트레이터 인스턴스
            allocator: LLM 할당자 (None이면 기본값 사용)
            spread_type: 스프레드 타입 (기본값: celtic_cross)
        """
        self.orchestrator = orchestrator
        self.allocator = allocator or get_allocator()
        self.spread_type = spread_type
        
        # 스프레드 설정 로드
        self.spread_config = get_spread_config(spread_type)
        if not self.spread_config:
            raise ValueError(f"Unknown spread type: {spread_type}")
        
        if not self.spread_config.supports_parallel:
            raise ValueError(f"Spread type {spread_type} does not support parallel processing")
        
        self.batch_size = self.spread_config.batch_size
        
        # 동시 호출 수 제한 설정 (Rate limiting)
        max_concurrent = self.spread_config.max_concurrent_calls
        if max_concurrent is None:
            # 기본값: 배치 수 + Phase 2 작업 수 (종합, 관계, 조언)
            # 켈틱 크로스의 경우: 4개 배치 + 3개 Phase 2 = 7개
            # 안전을 위해 5개로 제한
            max_concurrent = 5
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        # Jinja2 환경 설정
        prompts_dir = Path(__file__).parent.parent.parent.parent / "prompts"
        self.jinja_env = Environment(loader=FileSystemLoader(str(prompts_dir)))
        
        # 시스템 프롬프트 로드
        try:
            system_template = self.jinja_env.get_template("system/tarot_expert.txt")
            self.system_prompt = system_template.render()
        except Exception as e:
            logger.warning(f"Failed to load system prompt: {e}")
            self.system_prompt = "You are a professional tarot reader."
        
        logger.info(
            f"ParallelReadingEngine initialized for {spread_type} "
            f"with batch_size={self.batch_size}, max_concurrent={max_concurrent}"
        )
    
    def _create_card_batches(
        self,
        drawn_cards: List[DrawnCard],
        cards_context: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        """
        카드를 배치로 분할
        
        Args:
            drawn_cards: 선택된 카드 리스트
            cards_context: 카드 컨텍스트 리스트
        
        Returns:
            배치 리스트 (각 배치는 카드 정보 딕셔너리 리스트)
        """
        batches = []
        positions = self.spread_config.positions
        
        for i in range(0, len(drawn_cards), self.batch_size):
            batch = []
            for j in range(i, min(i + self.batch_size, len(drawn_cards))):
                pos_info = positions[j] if j < len(positions) else None
                card_info = {
                    "card": cards_context[j],
                    "drawn_card": drawn_cards[j],
                    "position_info": {
                        "index": pos_info.index if pos_info else j,
                        "position": pos_info.position if pos_info else f"position_{j}",
                        "name": pos_info.name if pos_info else f"포지션 {j+1}",
                        "meaning": pos_info.meaning if pos_info else "",
                    } if pos_info else {
                        "index": j,
                        "position": f"position_{j}",
                        "name": f"포지션 {j+1}",
                        "meaning": "",
                    }
                }
                batch.append(card_info)
            batches.append(batch)
        
        logger.info(
            f"Created {len(batches)} batches from {len(drawn_cards)} cards "
            f"(batch_size={self.batch_size})"
        )
        return batches
    
    async def _generate_card_batch_interpretation(
        self,
        batch: List[Dict[str, Any]],
        question: str,
        category: Optional[str],
        rag_context: Optional[Dict[str, Any]]
    ) -> List[CardInterpretation]:
        """
        카드 배치 해석 생성
        
        Args:
            batch: 카드 배치
            question: 질문
            category: 카테고리
            rag_context: RAG 컨텍스트
        
        Returns:
            카드 해석 리스트
        """
    async def _generate_card_batch_interpretation(
        self,
        batch: List[Dict[str, Any]],
        question: str,
        category: Optional[str],
        rag_context: Optional[Dict[str, Any]]
    ) -> List[CardInterpretation]:
        """
        카드 배치 해석 생성
        
        Args:
            batch: 카드 배치
            question: 질문
            category: 카테고리
            rag_context: RAG 컨텍스트
        
        Returns:
            카드 해석 리스트
        """
        # 프롬프트 언어 설정 확인 (기본: 영어)
        prompt_lang = settings.PROMPT_LANGUAGE
        lang_suffix = f"_{prompt_lang}" if prompt_lang == "en" else "_en"  # Default to English
        
        # 스프레드 설정에서 템플릿 경로 가져오기
        template_base = self.spread_config.parallel_templates.get("card") if self.spread_config.parallel_templates else None
        if not template_base:
            raise ValueError(f"No card template configured for spread type: {self.spread_type}")
        
        template_name = template_base.replace(".txt", f"{lang_suffix}.txt")
        
        # 프롬프트 템플릿 로드
        try:
            template = self.jinja_env.get_template(template_name)
        except Exception as e:
            logger.warning(f"Template {template_name} not found, falling back to English: {e}")
            template = self.jinja_env.get_template(template_base.replace(".txt", "_en.txt"))
        
        # 배치용 카드 정보 준비
        cards_data = []
        for card_info in batch:
            card_ctx = card_info["card"]
            pos_info = card_info["position_info"]
            cards_data.append({
                "id": str(card_ctx["id"]),  # Ensure card_id is string
                "name": card_ctx["name"],
                "orientation": card_ctx["orientation"],
                "orientation_korean": card_ctx["orientation_korean"],
                "arcana_korean": card_ctx["arcana_korean"],
                "suit_korean": card_ctx.get("suit_korean"),
                "keywords": card_ctx["keywords"],
                "upright_meaning": card_ctx["upright_meaning"],
                "reversed_meaning": card_ctx["reversed_meaning"],
                "position": pos_info["position"],
                "position_index": pos_info["index"],
                "position_name": pos_info["name"],
                "position_meaning": pos_info["meaning"],
            })
        
        # 프롬프트 렌더링
        prompt_context = {
            "question": question,
            "category": category,
            "cards": cards_data,
            "response_language": settings.RESPONSE_LANGUAGE,  # Add response language to context
        }
        prompt = template.render(**prompt_context)
        
        # 출력 형식 추가
        output_template = self.jinja_env.get_template("output/structured_response.txt")
        output_format = output_template.render()
        full_prompt = f"{prompt}\n\n{output_format}"
        
        # LLM 설정 가져오기 (프롬프트 분석 기반 동적 할당)
        config = self.allocator.get_config_for_prompt(
            task_type="card_interpretation",
            prompt=full_prompt,
            card_count=len(batch),
            question=question,
            category=category,
            rag_context=rag_context,
            system_prompt=self.system_prompt
        )
        model = config.model
        max_tokens = config.max_tokens
        
        # 재시도 로직: 응답이 잘렸을 경우 max_tokens 증가하여 재시도
        MAX_RETRIES = 2
        last_error = None
        all_responses: List[OrchestratorResponse] = []
        
        for attempt in range(MAX_RETRIES + 1):
            try:
                # LLM 호출 (동시 호출 수 제한 적용)
                async with self.semaphore:
                    response = await self.orchestrator.generate(
                        prompt=full_prompt,
                        system_prompt=self.system_prompt,
                        config=GenerationConfig(
                            max_tokens=max_tokens,
                            temperature=config.temperature
                        ),
                        model=model
                    )
                
                # 모든 시도 결과 수집
                all_responses.append(response)
                
                # 응답이 잘렸는지 확인
                if response.response.finish_reason in ("max_tokens", "length"):
                    logger.warning(
                        f"[ParallelEngine] 응답이 잘렸을 수 있음 (시도 {attempt + 1}/{MAX_RETRIES + 1}): "
                        f"finish_reason={response.response.finish_reason}, "
                        f"tokens={response.response.completion_tokens}/{max_tokens}"
                    )
                
                # 응답 파싱
                parser = ResponseParser()
                parsed = parser.parse(response.response.content)
                
                return parsed.cards, all_responses
                
            except JSONExtractionError as e:
                last_error = e
                error_msg = str(e)
                
                # 잘림 감지: max_tokens 증가하여 재시도
                if "불완전" in error_msg or "잘렸" in error_msg or "max_tokens" in error_msg:
                    if attempt < MAX_RETRIES:
                        # max_tokens 증가 (최대 max_tokens 제한)
                        previous_max_tokens = max_tokens
                        max_tokens = min(int(max_tokens * 1.5), max_tokens)
                        logger.warning(
                            f"[ParallelEngine] JSON 잘림 감지, max_tokens 증가하여 재시도 "
                            f"({previous_max_tokens} → {max_tokens}, 시도 {attempt + 2}/{MAX_RETRIES + 1})"
                        )
                        continue
                    else:
                        logger.error(
                            f"[ParallelEngine] 모든 재시도 실패 ({MAX_RETRIES + 1}회 시도). "
                            f"마지막 오류: {error_msg[:200]}"
                        )
                        raise
                else:
                    # 잘림이 아닌 다른 JSON 오류는 즉시 실패
                    raise
            except Exception as e:
                # 다른 예외는 즉시 실패
                logger.error(f"[ParallelEngine] 예상치 못한 오류: {e}")
                raise
        
        # 이론적으로 도달 불가능
        if last_error:
            raise last_error
        raise RuntimeError("재시도 로직 오류")
    
    async def generate_reading(
        self,
        drawn_cards: List[DrawnCard],
        question: str,
        category: Optional[str] = None,
        rag_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[ReadingResponse, List[OrchestratorResponse]]:
        """
        병렬 리딩 생성
        
        Args:
            drawn_cards: 선택된 카드 리스트
            question: 질문
            category: 카테고리
            rag_context: RAG 컨텍스트
        
        Returns:
            ReadingResponse: 완성된 리딩 응답
        """
        expected_count = self.spread_config.card_count
        if len(drawn_cards) != expected_count:
            raise ValueError(
                f"{self.spread_type} requires exactly {expected_count} cards, "
                f"got {len(drawn_cards)}"
            )
        
        logger.info(f"Starting parallel reading generation for {len(drawn_cards)} cards")
        
        # 카드 컨텍스트 빌드
        cards_context = [ContextBuilder.build_card_context(dc) for dc in drawn_cards]
        
        # Phase 1: 카드 배치 생성 및 병렬 해석
        batches = self._create_card_batches(drawn_cards, cards_context)
        
        logger.info(f"Phase 1: Generating card interpretations in {len(batches)} parallel batches")
        batch_tasks = [
            self._generate_card_batch_interpretation(
                batch=batch,
                question=question,
                category=category,
                rag_context=rag_context
            )
            for batch in batches
        ]
        
        batch_results = await asyncio.gather(*batch_tasks)
        
        # 모든 카드 해석 통합 및 LLM 호출 결과 수집
        all_card_interpretations = []
        all_llm_responses: List[OrchestratorResponse] = []
        for batch_result in batch_results:
            cards, responses = batch_result
            all_card_interpretations.extend(cards)
            all_llm_responses.extend(responses)
        
        # 카드 ID 순서로 정렬 (포지션 순서 유지)
        card_id_to_index = {dc.card.id: idx for idx, dc in enumerate(drawn_cards)}
        all_card_interpretations.sort(
            key=lambda c: card_id_to_index.get(c.card_id, 999)
        )
        
        logger.info(f"Phase 1 complete: Generated {len(all_card_interpretations)} card interpretations")
        
        # Phase 2: 종합 리딩, 관계 분석, 조언 병렬 생성
        logger.info("Phase 2: Generating overall reading, relationships, and advice in parallel")
        
        # 카드 요약 생성 (종합 리딩용)
        positions = self.spread_config.positions
        card_summaries = [
            {
                "card_id": str(ci.card_id),  # Ensure string type
                "name": next(
                    (cc["name"] for cc in cards_context if str(cc["id"]) == str(ci.card_id)),
                    str(ci.card_id)
                ),
                "position": ci.position,
                "position_index": next(
                    (i for i, pos in enumerate(positions) 
                     if pos.position == ci.position),
                    -1
                ),
                "position_name": next(
                    (pos.name for pos in positions 
                     if pos.position == ci.position),
                    ci.position
                ),
                "orientation_korean": next(
                    (cc["orientation_korean"] for cc in cards_context 
                     if str(cc["id"]) == str(ci.card_id)),
                    "정방향"
                ),
                "interpretation": ci.interpretation,
                "key_message": ci.key_message,
            }
            for ci in all_card_interpretations
        ]
        
        # 병렬 작업 생성
        overall_task = self._generate_overall_reading(
            question=question,
            category=category,
            card_summaries=card_summaries,
            rag_context=rag_context
        )
        
        relationships_task = self._generate_relationships(
            question=question,
            category=category,
            card_summaries=card_summaries
        )
        
        # Phase 2 실행 (종합 리딩과 관계 분석 병렬)
        overall_result_tuple, relationships_result_tuple = await asyncio.gather(
            overall_task,
            relationships_task
        )
        
        overall_result, overall_response = overall_result_tuple
        relationships_result, relationships_response = relationships_result_tuple
        
        # LLM 호출 결과 수집
        if overall_response:
            all_llm_responses.append(overall_response)
        if relationships_response:
            all_llm_responses.append(relationships_response)
        
        # 조언 생성 (종합 리딩 결과 필요)
        advice_result_tuple = await self._generate_advice(
            question=question,
            category=category,
            card_summaries=card_summaries,
            overall_reading_summary=overall_result["overall_reading"][:500]  # 요약
        )
        
        advice_result, advice_response = advice_result_tuple
        if advice_response:
            all_llm_responses.append(advice_response)
        
        logger.info("Phase 2 complete: Generated overall reading, relationships, and advice")
        
        # 카드 인용 추가
        positions = self.spread_config.positions
        citation_formatter = CitationFormatter.create_card_mapping(
            cards=[
                {
                    "card_id": str(ci.card_id),  # Ensure string type
                    "name": next(
                        (cc["name"] for cc in cards_context if str(cc["id"]) == str(ci.card_id)),
                        str(ci.card_id)
                    ),
                    "position": ci.position,
                }
                for ci in all_card_interpretations
            ],
            position_names=[pos.name for pos in positions]
        )
        
        formatter = CitationFormatter(citation_formatter)
        overall_reading_with_citations = formatter.add_citations(
            overall_result["overall_reading"]
        )
        
        # 최종 ReadingResponse 생성
        reading_response = ReadingResponse(
            cards=all_card_interpretations,
            card_relationships=relationships_result["card_relationships"],
            overall_reading=overall_reading_with_citations,
            advice=advice_result["advice"],
            summary=overall_result["summary"]
        )
        
        logger.info("Parallel reading generation complete")
        return reading_response, all_llm_responses
    
    async def _generate_overall_reading(
        self,
        question: str,
        category: Optional[str],
        card_summaries: List[Dict[str, Any]],
        rag_context: Optional[Dict[str, Any]]
    ) -> Tuple[Dict[str, str], OrchestratorResponse]:
        """종합 리딩 생성"""
        # 프롬프트 언어 설정 확인 (기본: 영어)
        prompt_lang = settings.PROMPT_LANGUAGE
        lang_suffix = f"_{prompt_lang}" if prompt_lang == "en" else "_en"  # Default to English
        
        # 스프레드 설정에서 템플릿 경로 가져오기
        template_base = self.spread_config.parallel_templates.get("overall") if self.spread_config.parallel_templates else None
        if not template_base:
            raise ValueError(f"No overall template configured for spread type: {self.spread_type}")
        
        template_name = template_base.replace(".txt", f"{lang_suffix}.txt")
        
        try:
            template = self.jinja_env.get_template(template_name)
        except Exception as e:
            logger.warning(f"Template {template_name} not found, falling back to English: {e}")
            template = self.jinja_env.get_template(template_base.replace(".txt", "_en.txt"))
        
        prompt_context = {
            "question": question,
            "category": category,
            "card_summaries": card_summaries,
            "rag_context": rag_context,
            "response_language": settings.RESPONSE_LANGUAGE,  # Add response language to context
        }
        prompt = template.render(**prompt_context)
        
        output_template = self.jinja_env.get_template("output/structured_response.txt")
        output_format = output_template.render()
        full_prompt = f"{prompt}\n\n{output_format}"
        
        # LLM 설정 가져오기 (프롬프트 분석 기반 동적 할당)
        config = self.allocator.get_config_for_prompt(
            task_type="overall_reading",
            prompt=full_prompt,
            card_count=len(card_summaries),
            question=question,
            category=category,
            rag_context=rag_context,
            system_prompt=self.system_prompt
        )
        
        # 동시 호출 수 제한 적용
        async with self.semaphore:
            response = await self.orchestrator.generate(
                prompt=full_prompt,
                system_prompt=self.system_prompt,
                config=GenerationConfig(
                    max_tokens=config.max_tokens,
                    temperature=config.temperature
                ),
                model=config.model
            )
        
        parser = ResponseParser()
        parsed_data = parser.extract_json(response.response.content)
        data = json.loads(parsed_data)
        
        return {
            "overall_reading": data.get("overall_reading", ""),
            "summary": data.get("summary", "")
        }, response
    
    async def _generate_relationships(
        self,
        question: str,
        category: Optional[str],
        card_summaries: List[Dict[str, Any]]
    ) -> Tuple[Dict[str, str], Optional[OrchestratorResponse]]:
        """카드 관계 분석 생성"""
        # 프롬프트 언어 설정 확인 (기본: 영어)
        prompt_lang = settings.PROMPT_LANGUAGE
        lang_suffix = f"_{prompt_lang}" if prompt_lang == "en" else "_en"  # Default to English
        
        # 스프레드 설정에서 템플릿 경로 가져오기
        template_base = self.spread_config.parallel_templates.get("relationships") if self.spread_config.parallel_templates else None
        if not template_base:
            # 관계 분석이 선택적일 수 있음 (일부 스프레드는 관계 분석이 없을 수 있음)
            return {"card_relationships": ""}, None
        
        template_name = template_base.replace(".txt", f"{lang_suffix}.txt")
        
        try:
            template = self.jinja_env.get_template(template_name)
        except Exception as e:
            logger.warning(f"Template {template_name} not found, falling back to English: {e}")
            template = self.jinja_env.get_template(template_base.replace(".txt", "_en.txt"))
        
        prompt_context = {
            "question": question,
            "category": category,
            "card_summaries": card_summaries,
            "response_language": settings.RESPONSE_LANGUAGE,  # Add response language to context
        }
        prompt = template.render(**prompt_context)
        
        output_template = self.jinja_env.get_template("output/structured_response.txt")
        output_format = output_template.render()
        full_prompt = f"{prompt}\n\n{output_format}"
        
        # LLM 설정 가져오기 (프롬프트 분석 기반 동적 할당)
        config = self.allocator.get_config_for_prompt(
            task_type="relationships",
            prompt=full_prompt,
            card_count=len(card_summaries),
            question=question,
            category=category,
            system_prompt=self.system_prompt
        )
        
        # 동시 호출 수 제한 적용
        async with self.semaphore:
            response = await self.orchestrator.generate(
                prompt=full_prompt,
                system_prompt=self.system_prompt,
                config=GenerationConfig(
                    max_tokens=config.max_tokens,
                    temperature=config.temperature
                ),
                model=config.model
            )
        
        parser = ResponseParser()
        parsed_data = parser.extract_json(response.response.content)
        data = json.loads(parsed_data)
        
        return {
            "card_relationships": data.get("card_relationships", "")
        }, response
    
    async def _generate_advice(
        self,
        question: str,
        category: Optional[str],
        card_summaries: List[Dict[str, Any]],
        overall_reading_summary: str
    ) -> Tuple[Dict[str, Advice], Optional[OrchestratorResponse]]:
        """조언 생성"""
        # 프롬프트 언어 설정 확인 (기본: 영어)
        prompt_lang = settings.PROMPT_LANGUAGE
        lang_suffix = f"_{prompt_lang}" if prompt_lang == "en" else "_en"  # Default to English
        
        # 스프레드 설정에서 템플릿 경로 가져오기
        template_base = self.spread_config.parallel_templates.get("advice") if self.spread_config.parallel_templates else None
        if not template_base:
            # 조언이 선택적일 수 있음 (기본 조언 생성)
            return {
                "advice": Advice(
                    immediate_action="현재 상황을 고려하여 즉시 실천 가능한 작은 행동을 시작하세요.",
                    short_term="앞으로 2-3주 동안 집중할 목표를 설정하세요.",
                    long_term="장기적인 방향성을 고려하여 계획을 세우세요.",
                    mindset="긍정적이면서도 현실적인 마음가짐을 유지하세요.",
                    cautions="성급한 결정을 피하고 신중하게 접근하세요."
                )
            }, None
        
        template_name = template_base.replace(".txt", f"{lang_suffix}.txt")
        
        try:
            template = self.jinja_env.get_template(template_name)
        except Exception as e:
            logger.warning(f"Template {template_name} not found, falling back to English: {e}")
            template = self.jinja_env.get_template(template_base.replace(".txt", "_en.txt"))
        
        prompt_context = {
            "question": question,
            "category": category,
            "card_summaries": card_summaries,
            "overall_reading_summary": overall_reading_summary,
            "response_language": settings.RESPONSE_LANGUAGE,  # Add response language to context
        }
        prompt = template.render(**prompt_context)
        
        output_template = self.jinja_env.get_template("output/structured_response.txt")
        output_format = output_template.render()
        full_prompt = f"{prompt}\n\n{output_format}"
        
        # LLM 설정 가져오기 (프롬프트 분석 기반 동적 할당)
        config = self.allocator.get_config_for_prompt(
            task_type="advice",
            prompt=full_prompt,
            card_count=len(card_summaries),
            question=question,
            category=category,
            system_prompt=self.system_prompt
        )
        
        # 동시 호출 수 제한 적용
        async with self.semaphore:
            response = await self.orchestrator.generate(
                prompt=full_prompt,
                system_prompt=self.system_prompt,
                config=GenerationConfig(
                    max_tokens=config.max_tokens,
                    temperature=config.temperature
                ),
                model=config.model
            )
        
        parser = ResponseParser()
        parsed_data = parser.extract_json(response.response.content)
        data = json.loads(parsed_data)
        
        # Advice 객체 생성
        advice_data = data.get("advice", {})
        advice = Advice(**advice_data)
        
        return {
            "advice": advice
        }, response

