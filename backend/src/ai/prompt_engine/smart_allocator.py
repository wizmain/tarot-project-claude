"""
Smart Allocator - 프롬프트 분석 기반 동적 모델 할당

이 모듈의 목적:
- 프롬프트 분석 결과를 기반으로 최적의 모델 선택
- 비용/성능 최적화 자동화
- 작업 유형과 프롬프트 특성을 조합한 지능적 할당

주요 기능:
- 프롬프트 분석 기반 모델 선택
- 비용 최적화 (예상 비용 계산)
- 성능 최적화 (응답 시간 고려)
- Fallback 전략
"""
from typing import Optional, List, Dict, Any
import logging

from src.ai.prompt_engine.llm_allocation import LLMAllocator, ModelConfig, DEFAULT_LLM_ALLOCATION
from src.ai.prompt_engine.prompt_analyzer import PromptAnalysis
from src.ai.model_registry import ModelRegistry, get_registry

logger = logging.getLogger(__name__)


class SmartAllocator:
    """
    지능형 모델 할당자
    
    프롬프트 분석 결과를 기반으로 최적의 모델을 동적으로 선택합니다.
    비용과 성능을 고려하여 균형잡힌 할당을 수행합니다.
    """
    
    def __init__(
        self,
        base_allocator: Optional[LLMAllocator] = None,
        registry: Optional[ModelRegistry] = None
    ):
        """
        SmartAllocator 초기화
        
        Args:
            base_allocator: 기본 LLMAllocator (None이면 새로 생성)
            registry: ModelRegistry 인스턴스 (None이면 싱글톤 사용)
        
        Note:
            enable_smart_allocation은 LLMAllocator에서 제어됩니다.
            SmartAllocator는 항상 활성화된 상태로 동작하며,
            LLMAllocator.get_config_for_prompt()에서 이미 체크됩니다.
        """
        self.base_allocator = base_allocator or LLMAllocator()
        self.registry = registry or get_registry()
        
        logger.info("SmartAllocator initialized")
    
    def allocate_model(
        self,
        task_type: str,
        prompt_analysis: PromptAnalysis,
        budget_constraint: Optional[float] = None,
        prefer_fast: bool = False
    ) -> ModelConfig:
        """
        프롬프트 분석 기반 모델 할당
        
        Args:
            task_type: 작업 유형 ("card_interpretation", "overall_reading" 등)
            prompt_analysis: 프롬프트 분석 결과
            budget_constraint: 최대 예상 비용 제약 (USD, 선택적)
            prefer_fast: 빠른 응답 우선 여부
        
        Returns:
            ModelConfig: 할당된 모델 설정
        
        Note:
            이 메서드는 LLMAllocator.get_config_for_prompt()에서만 호출되며,
            LLMAllocator에서 이미 enable_smart_allocation을 체크했으므로
            여기서는 항상 스마트 할당을 수행합니다.
        """
        # 기본 모델 가져오기
        base_config = self.base_allocator.get_config(task_type)
        base_model_id = base_config.model
        
        # 기본 모델이 레지스트리에 있는지 확인
        base_metadata = self.registry.get_model(base_model_id)
        
        # 프롬프트 분석 결과 기반 조정
        selected_model = self._select_optimal_model(
            task_type=task_type,
            prompt_analysis=prompt_analysis,
            base_model_id=base_model_id,
            budget_constraint=budget_constraint,
            prefer_fast=prefer_fast
        )
        
        # 선택된 모델의 메타데이터 가져오기
        selected_metadata = self.registry.get_model(selected_model)
        
        if selected_metadata:
            # 선택된 모델의 설정 생성
            config = ModelConfig(
                model=selected_model,
                max_tokens=self._calculate_max_tokens(
                    prompt_analysis.estimated_output_tokens,
                    base_config.max_tokens
                ),
                temperature=base_config.temperature,
                timeout=self._calculate_timeout(
                    prompt_analysis.complexity_score,
                    base_config.timeout
                )
            )
            
            logger.info(
                f"Smart allocation: {task_type} -> {selected_model} "
                f"(base={base_model_id}, complexity={prompt_analysis.complexity_score:.2f})"
            )
            
            return config
        else:
            # 레지스트리에 없으면 기본 모델 사용
            logger.warning(
                f"Model {selected_model} not found in registry, "
                f"using base model {base_model_id}"
            )
            return base_config
    
    def _select_optimal_model(
        self,
        task_type: str,
        prompt_analysis: PromptAnalysis,
        base_model_id: str,
        budget_constraint: Optional[float] = None,
        prefer_fast: bool = False
    ) -> str:
        """
        최적 모델 선택
        
        Args:
            task_type: 작업 유형
            prompt_analysis: 프롬프트 분석 결과
            base_model_id: 기본 모델 ID
            budget_constraint: 비용 제약
            prefer_fast: 빠른 응답 우선
        
        Returns:
            선택된 모델 ID
        """
        # 적합한 성능 등급의 모델 검색
        suitable_models = self.registry.find_models(
            performance_tier=None if not prompt_analysis.suitable_tiers 
            else prompt_analysis.suitable_tiers[0],  # 첫 번째 등급 사용
            available_only=True
        )
        
        # 적합한 등급이 없으면 모든 등급에서 검색
        if not suitable_models:
            suitable_models = self.registry.find_models(available_only=True)
        
        if not suitable_models:
            logger.warning("No suitable models found, using base model")
            return base_model_id
        
        # 비용 제약이 있으면 필터링
        if budget_constraint:
            suitable_models = [
                m for m in suitable_models
                if m.estimate_cost(
                    prompt_analysis.estimated_input_tokens,
                    prompt_analysis.estimated_output_tokens
                ) <= budget_constraint
            ]
        
        if not suitable_models:
            logger.warning(
                f"No models within budget constraint {budget_constraint}, "
                f"using base model"
            )
            return base_model_id
        
        # 모델 선택 전략
        if prefer_fast or prompt_analysis.urgency == "high":
            # 빠른 응답 우선: 가장 빠른 모델 선택
            selected = min(
                suitable_models,
                key=lambda m: (
                    m.performance_tier != "fast",  # fast 우선
                    m.cost_per_1m_input + m.cost_per_1m_output  # 비용 낮은 순
                )
            )
        elif prompt_analysis.requires_high_quality:
            # 고품질 우선: 고성능 모델 선택
            high_quality = [m for m in suitable_models if m.performance_tier == "high"]
            if high_quality:
                # 비용이 가장 낮은 고성능 모델
                selected = min(
                    high_quality,
                    key=lambda m: m.cost_per_1m_input + m.cost_per_1m_output
                )
            else:
                # 고성능이 없으면 balanced 중 최고
                balanced = [m for m in suitable_models if m.performance_tier == "balanced"]
                selected = balanced[0] if balanced else suitable_models[0]
        else:
            # 비용 최적화: 예상 비용이 가장 낮은 모델 선택
            selected = min(
                suitable_models,
                key=lambda m: m.estimate_cost(
                    prompt_analysis.estimated_input_tokens,
                    prompt_analysis.estimated_output_tokens
                )
            )
        
        return selected.model_id
    
    def _calculate_max_tokens(
        self,
        estimated_output_tokens: int,
        base_max_tokens: int
    ) -> int:
        """
        최대 토큰 수 계산
        
        예상 출력 토큰 수를 고려하여 적절한 max_tokens 설정
        
        Args:
            estimated_output_tokens: 예상 출력 토큰 수
            base_max_tokens: 기본 max_tokens
        
        Returns:
            계산된 max_tokens
        """
        # 예상 출력의 1.5배 + 여유분
        calculated = int(estimated_output_tokens * 1.5) + 200
        
        # 기본값과 계산값 중 큰 값 사용
        max_tokens = max(calculated, base_max_tokens)
        
        # API 제한 (4096) 준수
        return min(max_tokens, 4096)
    
    def _calculate_timeout(
        self,
        complexity_score: float,
        base_timeout: int
    ) -> int:
        """
        타임아웃 계산
        
        복잡도에 따라 타임아웃 조정
        
        Args:
            complexity_score: 복잡도 점수
            base_timeout: 기본 타임아웃
        
        Returns:
            계산된 타임아웃
        """
        # 복잡도가 높으면 타임아웃 증가
        if complexity_score > 0.7:
            return int(base_timeout * 1.5)
        elif complexity_score > 0.4:
            return int(base_timeout * 1.2)
        
        return base_timeout

