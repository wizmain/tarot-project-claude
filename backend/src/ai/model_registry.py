"""
Model Registry - 중앙화된 LLM 모델 정보 관리 시스템

이 모듈의 목적:
- 모든 provider의 모델 정보를 중앙화하여 관리
- 모델 메타데이터 관리 (비용, 성능, 용도, 컨텍스트 윈도우)
- Provider별 모델 매핑 및 검색
- 동적 모델 할당을 위한 기반 제공

주요 기능:
- 모델 등록 및 조회
- Provider별 모델 정보 자동 동기화
- 조건 기반 모델 검색
- 모델 메타데이터 관리
"""
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
import logging

from src.ai.provider import AIProvider

logger = logging.getLogger(__name__)


@dataclass
class ModelMetadata:
    """모델 메타데이터"""
    model_id: str  # 고유 모델 식별자 (예: "claude-haiku-4-5-20251001")
    provider: str  # Provider 이름 (예: "anthropic")
    name: str  # 모델 표시 이름
    cost_per_1m_input: float  # 입력 100만 토큰당 비용 (USD)
    cost_per_1m_output: float  # 출력 100만 토큰당 비용 (USD)
    max_context_window: int  # 최대 컨텍스트 윈도우 (토큰 수)
    performance_tier: str  # 성능 등급: "fast", "balanced", "high"
    suitable_for: List[str] = field(default_factory=list)  # 적합한 용도: ["short", "medium", "long", "complex"]
    available: bool = True  # 사용 가능 여부
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        예상 비용 계산
        
        Args:
            input_tokens: 입력 토큰 수
            output_tokens: 출력 토큰 수
        
        Returns:
            예상 비용 (USD)
        """
        input_cost = (input_tokens / 1_000_000) * self.cost_per_1m_input
        output_cost = (output_tokens / 1_000_000) * self.cost_per_1m_output
        return input_cost + output_cost


class ModelRegistry:
    """
    중앙화된 모델 정보 레지스트리
    
    모든 provider의 모델 정보를 중앙에서 관리하고,
    동적 모델 할당을 위한 검색 및 조회 기능을 제공합니다.
    """
    
    def __init__(self):
        """모델 레지스트리 초기화"""
        self.models: Dict[str, ModelMetadata] = {}
        self.provider_models: Dict[str, List[str]] = {}  # provider -> [model_ids]
        self._initialized = False
        
        logger.info("ModelRegistry initialized")
    
    def register_model(self, metadata: ModelMetadata) -> None:
        """
        모델 등록
        
        Args:
            metadata: 모델 메타데이터
        """
        self.models[metadata.model_id] = metadata
        
        # Provider별 모델 리스트 업데이트
        if metadata.provider not in self.provider_models:
            self.provider_models[metadata.provider] = []
        
        if metadata.model_id not in self.provider_models[metadata.provider]:
            self.provider_models[metadata.provider].append(metadata.model_id)
        
        logger.debug(
            f"Registered model: {metadata.model_id} "
            f"(provider={metadata.provider}, tier={metadata.performance_tier})"
        )
    
    def get_model(self, model_id: str) -> Optional[ModelMetadata]:
        """
        모델 정보 조회
        
        Args:
            model_id: 모델 식별자
        
        Returns:
            ModelMetadata 또는 None
        """
        return self.models.get(model_id)
    
    def find_models(
        self,
        provider: Optional[str] = None,
        performance_tier: Optional[str] = None,
        max_cost_per_1m_input: Optional[float] = None,
        max_cost_per_1m_output: Optional[float] = None,
        suitable_for: Optional[str] = None,
        available_only: bool = True
    ) -> List[ModelMetadata]:
        """
        조건에 맞는 모델 검색
        
        Args:
            provider: Provider 이름 필터
            performance_tier: 성능 등급 필터 ("fast", "balanced", "high")
            max_cost_per_1m_input: 최대 입력 비용 필터
            max_cost_per_1m_output: 최대 출력 비용 필터
            suitable_for: 적합한 용도 필터 ("short", "medium", "long", "complex")
            available_only: 사용 가능한 모델만 반환
        
        Returns:
            조건에 맞는 모델 메타데이터 리스트
        """
        results = []
        
        for model_id, metadata in self.models.items():
            # 사용 가능 여부 체크
            if available_only and not metadata.available:
                continue
            
            # Provider 필터
            if provider and metadata.provider != provider:
                continue
            
            # 성능 등급 필터
            if performance_tier and metadata.performance_tier != performance_tier:
                continue
            
            # 비용 필터
            if max_cost_per_1m_input and metadata.cost_per_1m_input > max_cost_per_1m_input:
                continue
            
            if max_cost_per_1m_output and metadata.cost_per_1m_output > max_cost_per_1m_output:
                continue
            
            # 용도 필터
            if suitable_for and suitable_for not in metadata.suitable_for:
                continue
            
            results.append(metadata)
        
        return results
    
    def get_provider_models(self, provider: str) -> List[ModelMetadata]:
        """
        특정 provider의 모든 모델 반환
        
        Args:
            provider: Provider 이름
        
        Returns:
            해당 provider의 모델 메타데이터 리스트
        """
        model_ids = self.provider_models.get(provider, [])
        return [self.models[mid] for mid in model_ids if mid in self.models]
    
    def sync_from_providers(self, providers: List[AIProvider]) -> None:
        """
        Provider에서 모델 정보 자동 동기화
        
        각 provider의 MODEL_PRICING과 available_models를 읽어서
        모델 레지스트리에 등록합니다.
        
        Args:
            providers: AIProvider 인스턴스 리스트
        """
        logger.info(f"Syncing model information from {len(providers)} providers...")
        
        for provider in providers:
            provider_name = provider.provider_name
            available_models = provider.available_models
            
            # Provider의 MODEL_PRICING 가져오기
            pricing = getattr(provider, 'MODEL_PRICING', {})
            
            # 컨텍스트 윈도우 정보 가져오기 (있는 경우)
            context_windows = {}
            if hasattr(provider, 'get_model_context_window'):
                # 각 모델의 컨텍스트 윈도우 조회
                for model_id in available_models:
                    try:
                        context_windows[model_id] = provider.get_model_context_window(model_id)
                    except Exception:
                        pass
            
            # 각 모델 등록
            for model_id in available_models:
                # 가격 정보 가져오기
                pricing_info = pricing.get(model_id)
                if not pricing_info:
                    # 정확한 모델 ID가 없으면 유사한 모델 찾기
                    pricing_info = self._find_similar_pricing(model_id, pricing)
                
                if pricing_info:
                    cost_input = pricing_info.get('input', 0.0)
                    cost_output = pricing_info.get('output', 0.0)
                else:
                    # 가격 정보가 없으면 기본값 사용
                    cost_input = 0.0
                    cost_output = 0.0
                    logger.warning(
                        f"No pricing information found for model {model_id} "
                        f"(provider={provider_name})"
                    )
                
                # 컨텍스트 윈도우
                context_window = context_windows.get(model_id, 200_000)  # 기본값: 200K
                
                # 성능 등급 결정
                performance_tier = self._determine_performance_tier(
                    model_id, provider_name, cost_input, cost_output
                )
                
                # 적합한 용도 결정
                suitable_for = self._determine_suitable_for(
                    model_id, provider_name, performance_tier
                )
                
                # 모델 메타데이터 생성 및 등록
                metadata = ModelMetadata(
                    model_id=model_id,
                    provider=provider_name,
                    name=self._format_model_name(model_id),
                    cost_per_1m_input=cost_input,
                    cost_per_1m_output=cost_output,
                    max_context_window=context_window,
                    performance_tier=performance_tier,
                    suitable_for=suitable_for,
                    available=True
                )
                
                self.register_model(metadata)
        
        self._initialized = True
        logger.info(
            f"Model registry sync complete: {len(self.models)} models "
            f"from {len(self.provider_models)} providers"
        )
    
    def _find_similar_pricing(self, model_id: str, pricing: Dict) -> Optional[Dict]:
        """
        유사한 모델의 가격 정보 찾기
        
        예: "claude-haiku-4-5-20251001" -> "claude-3-haiku" 가격 사용
        """
        # 모델 이름에서 기본 이름 추출
        parts = model_id.split('-')
        if len(parts) >= 3:
            # 예: "claude-haiku-4-5-20251001" -> "claude-3-haiku"
            base_name = f"{parts[0]}-3-{parts[1]}"
            if base_name in pricing:
                return pricing[base_name]
            
            # 예: "claude-sonnet-4-5-20250929" -> "claude-3-5-sonnet"
            base_name_alt = f"{parts[0]}-3-5-{parts[1]}"
            if base_name_alt in pricing:
                return pricing[base_name_alt]
        
        return None
    
    def _determine_performance_tier(
        self,
        model_id: str,
        provider: str,
        cost_input: float,
        cost_output: float
    ) -> str:
        """
        모델의 성능 등급 결정
        
        비용과 모델 이름을 기반으로 성능 등급을 결정합니다.
        """
        model_lower = model_id.lower()
        
        # 빠른 모델 (저렴하고 빠름)
        if any(keyword in model_lower for keyword in ['haiku', 'flash', 'mini', 'nano', 'turbo']):
            return "fast"
        
        # 고성능 모델 (비싸고 강력함)
        if any(keyword in model_lower for keyword in ['opus', 'pro', 'gpt-5', 'gpt-4.1']):
            return "high"
        
        # 균형 모델 (기본값)
        return "balanced"
    
    def _determine_suitable_for(
        self,
        model_id: str,
        provider: str,
        performance_tier: str
    ) -> List[str]:
        """
        모델의 적합한 용도 결정
        """
        suitable = []
        
        if performance_tier == "fast":
            suitable.extend(["short", "medium"])
        elif performance_tier == "balanced":
            suitable.extend(["short", "medium", "long"])
        else:  # high
            suitable.extend(["medium", "long", "complex"])
        
        return suitable
    
    def _format_model_name(self, model_id: str) -> str:
        """
        모델 ID를 표시용 이름으로 변환
        
        예: "claude-haiku-4-5-20251001" -> "Claude Haiku 4.5"
        """
        parts = model_id.split('-')
        if len(parts) >= 2:
            provider_name = parts[0].capitalize()
            model_name = parts[1].capitalize()
            
            # 버전 정보 추출
            version_parts = []
            for part in parts[2:]:
                if part.isdigit() or '.' in part:
                    version_parts.append(part)
            
            if version_parts:
                version = ' '.join(version_parts[:2])  # 최대 2개만
                return f"{provider_name} {model_name} {version}"
            else:
                return f"{provider_name} {model_name}"
        
        return model_id
    
    def get_summary(self) -> Dict[str, any]:
        """
        레지스트리 요약 정보 반환
        
        Returns:
            레지스트리 통계 정보
        """
        return {
            "total_models": len(self.models),
            "providers": list(self.provider_models.keys()),
            "models_by_provider": {
                provider: len(models)
                for provider, models in self.provider_models.items()
            },
            "models_by_tier": {
                tier: len(self.find_models(performance_tier=tier))
                for tier in ["fast", "balanced", "high"]
            }
        }


# 싱글톤 인스턴스
_registry: Optional[ModelRegistry] = None


def get_registry() -> ModelRegistry:
    """
    모델 레지스트리 싱글톤 인스턴스 반환
    
    Returns:
        ModelRegistry 인스턴스
    """
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry


def reset_registry():
    """레지스트리 싱글톤 리셋 (테스트용)"""
    global _registry
    _registry = None

