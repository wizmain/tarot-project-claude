"""
LLM Allocation Strategy - 모델 선택 및 할당 전략

이 모듈의 목적:
- 각 작업 유형에 맞는 최적의 LLM 모델 선택
- 비용 효율적인 모델 할당 전략
- 설정 기반 모델 관리
- 프롬프트 분석 기반 동적 할당 (선택적)

주요 기능:
- 작업 유형별 모델 선택 (카드 해석, 종합 리딩, 관계 분석, 조언)
- 모델별 토큰 제한 및 설정 관리
- 환경 변수 기반 설정 오버라이드
- 프롬프트 분석 기반 동적 할당 (SmartAllocator 통합)
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging

from src.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """모델 설정"""
    model: str
    max_tokens: int
    temperature: float
    timeout: int = 90


# 기본 LLM 할당 전략
DEFAULT_LLM_ALLOCATION: Dict[str, ModelConfig] = {
    "card_interpretation": ModelConfig(
        model="gemini-2.0-flash-lite",  # 빠르고 저렴한 모델 (최신 버전)
        max_tokens=8192,  # 켈틱 크로스 배치 해석을 위해 증가 (800 → 1500)
        temperature=0.7,
        timeout=60
    ),
    "overall_reading": ModelConfig(
        model="gemini-2.0-flash",  # 고성능 모델 (최신 버전)
        max_tokens=8192,
        temperature=0.7,
        timeout=120
    ),
    "relationships": ModelConfig(
        model="gemini-2.0-flash",  # 중간 성능 모델 (최신 버전)
        max_tokens=8192,
        temperature=0.6,
        timeout=90
    ),
    "advice": ModelConfig(
        model="gemini-2.0-flash-lite",  # 중간 성능 모델 (최신 버전)
        max_tokens=8192,
        temperature=0.7,
        timeout=90
    ),
}


class LLMAllocator:
    """
    LLM 할당 전략 관리자
    
    각 작업 유형에 맞는 최적의 모델을 선택하고 설정을 제공합니다.
    환경 변수를 통해 설정을 오버라이드할 수 있습니다.
    프롬프트 분석 기반 동적 할당도 지원합니다 (선택적).
    """
    
    def __init__(
        self,
        allocation: Optional[Dict[str, ModelConfig]] = None,
        enable_smart_allocation: bool = False
    ):
        """
        LLM 할당자 초기화
        
        Args:
            allocation: 커스텀 할당 전략 (None이면 기본값 사용)
            enable_smart_allocation: 스마트 할당 활성화 여부
        """
        self.allocation = allocation or DEFAULT_LLM_ALLOCATION.copy()
        self._apply_env_overrides()
        
        # SmartAllocator 초기화 (지연 로딩)
        self._smart_allocator = None
        self.enable_smart_allocation = enable_smart_allocation
        
        logger.info(
            f"LLMAllocator initialized with {len(self.allocation)} task types "
            f"(smart_allocation={'enabled' if enable_smart_allocation else 'disabled'})"
        )
    
    def _apply_env_overrides(self):
        """환경 변수에서 설정 오버라이드"""
        # 환경 변수 예시: CELTIC_CROSS_CARD_MODEL=claude-haiku-4-5-20251001
        # TODO: 환경 변수 지원 필요 시 구현
        
    def get_config(self, task_type: str) -> ModelConfig:
        """
        작업 유형에 맞는 모델 설정 반환
        
        Args:
            task_type: 작업 유형 ("card_interpretation", "overall_reading", 
                      "relationships", "advice")
        
        Returns:
            ModelConfig: 해당 작업에 맞는 모델 설정
        
        Raises:
            ValueError: 알 수 없는 작업 유형인 경우
        """
        if task_type not in self.allocation:
            available = ", ".join(self.allocation.keys())
            raise ValueError(
                f"Unknown task type: {task_type}. "
                f"Available types: {available}"
            )
        
        config = self.allocation[task_type]
        logger.debug(
            f"Allocated model {config.model} for task {task_type} "
            f"(max_tokens={config.max_tokens}, temp={config.temperature})"
        )
        return config
    
    def get_model(self, task_type: str) -> str:
        """작업 유형에 맞는 모델 이름 반환"""
        return self.get_config(task_type).model
    
    def get_max_tokens(self, task_type: str) -> int:
        """작업 유형에 맞는 최대 토큰 수 반환"""
        return self.get_config(task_type).max_tokens
    
    def get_temperature(self, task_type: str) -> float:
        """작업 유형에 맞는 temperature 반환"""
        return self.get_config(task_type).temperature
    
    def get_timeout(self, task_type: str) -> int:
        """작업 유형에 맞는 타임아웃 반환"""
        return self.get_config(task_type).timeout
    
    def get_config_for_prompt(
        self,
        task_type: str,
        prompt: str,
        card_count: int = 0,
        question: Optional[str] = None,
        category: Optional[str] = None,
        rag_context: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
        budget_constraint: Optional[float] = None,
        prefer_fast: bool = False
    ) -> ModelConfig:
        """
        프롬프트 분석 기반 동적 모델 할당
        
        프롬프트 내용을 분석하여 최적의 모델을 선택합니다.
        스마트 할당이 비활성화되어 있으면 기본 할당을 사용합니다.
        
        Args:
            task_type: 작업 유형
            prompt: 프롬프트 텍스트
            card_count: 카드 수
            question: 사용자 질문
            category: 카테고리
            rag_context: RAG 컨텍스트
            system_prompt: 시스템 프롬프트
            budget_constraint: 최대 예상 비용 제약 (USD)
            prefer_fast: 빠른 응답 우선 여부
        
        Returns:
            ModelConfig: 할당된 모델 설정
        """
        if not self.enable_smart_allocation:
            return self.get_config(task_type)
        
        # SmartAllocator 지연 초기화
        if self._smart_allocator is None:
            from src.ai.prompt_engine.smart_allocator import SmartAllocator
            self._smart_allocator = SmartAllocator(
                base_allocator=self
            )
        
        # 프롬프트 분석
        from src.ai.prompt_engine.prompt_analyzer import PromptAnalyzer
        analyzer = PromptAnalyzer()
        prompt_analysis = analyzer.analyze(
            prompt=prompt,
            task_type=task_type,
            card_count=card_count,
            question=question,
            category=category,
            rag_context=rag_context,
            system_prompt=system_prompt
        )
        
        # 동적 할당
        return self._smart_allocator.allocate_model(
            task_type=task_type,
            prompt_analysis=prompt_analysis,
            budget_constraint=budget_constraint,
            prefer_fast=prefer_fast
        )
    
    def update_allocation(
        self, 
        task_type: str, 
        config: ModelConfig
    ):
        """
        특정 작업 유형의 할당 전략 업데이트
        
        Args:
            task_type: 작업 유형
            config: 새로운 모델 설정
        """
        if task_type not in self.allocation:
            raise ValueError(f"Unknown task type: {task_type}")
        
        self.allocation[task_type] = config
        logger.info(
            f"Updated allocation for {task_type}: "
            f"model={config.model}, max_tokens={config.max_tokens}"
        )
    
    def get_allocation_summary(self) -> Dict[str, Any]:
        """
        현재 할당 전략 요약 반환
        
        Returns:
            할당 전략 요약 딕셔너리
        """
        return {
            task_type: {
                "model": config.model,
                "max_tokens": config.max_tokens,
                "temperature": config.temperature,
                "timeout": config.timeout
            }
            for task_type, config in self.allocation.items()
        }


# 싱글톤 인스턴스
_default_allocator: Optional[LLMAllocator] = None


def get_allocator() -> LLMAllocator:
    """
    기본 LLM 할당자 싱글톤 인스턴스 반환
    
    Returns:
        LLMAllocator: 기본 할당자 인스턴스
    """
    global _default_allocator
    if _default_allocator is None:
        _default_allocator = LLMAllocator()
    return _default_allocator


def reset_allocator():
    """할당자 싱글톤 리셋 (테스트용)"""
    global _default_allocator
    _default_allocator = None

