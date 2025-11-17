"""
Prompt Analyzer - 프롬프트 내용 분석 및 특성 추출

이 모듈의 목적:
- 프롬프트의 길이, 복잡도, 예상 출력 길이 등을 분석
- 동적 모델 할당을 위한 프롬프트 특성 추출
- 토큰 수 추정 및 복잡도 점수 계산

주요 기능:
- 프롬프트 토큰 수 추정
- 복잡도 분석 (카드 수, 질문 길이, 구조적 복잡도)
- 예상 출력 길이 추정
- 작업 유형별 특성 분석
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging
import re

logger = logging.getLogger(__name__)


@dataclass
class PromptAnalysis:
    """프롬프트 분석 결과"""
    estimated_input_tokens: int  # 예상 입력 토큰 수
    estimated_output_tokens: int  # 예상 출력 토큰 수
    complexity_score: float  # 복잡도 점수 (0.0 ~ 1.0)
    urgency: str  # 긴급도: "low", "medium", "high"
    requires_high_quality: bool  # 고품질 응답 필요 여부
    suitable_tiers: List[str]  # 적합한 성능 등급: ["fast", "balanced", "high"]
    
    # 추가 메타데이터
    prompt_length: int  # 프롬프트 문자 수
    card_count: int  # 카드 수
    question_length: int  # 질문 길이
    has_rag_context: bool  # RAG 컨텍스트 포함 여부


class PromptAnalyzer:
    """
    프롬프트 분석기
    
    프롬프트의 특성을 분석하여 동적 모델 할당에 필요한 정보를 제공합니다.
    """
    
    # 토큰 추정 상수 (대략적 추정)
    # 한국어: 약 1.5자 = 1 토큰
    # 영어: 약 4자 = 1 토큰
    # 평균: 약 3자 = 1 토큰
    CHARS_PER_TOKEN = 3.0
    
    # 작업 유형별 기본 출력 토큰 수
    DEFAULT_OUTPUT_TOKENS = {
        "card_interpretation": 500,  # 카드 해석 (배치당)
        "overall_reading": 2000,  # 종합 리딩
        "relationships": 800,  # 관계 분석
        "advice": 600,  # 조언
    }
    
    def __init__(self):
        """프롬프트 분석기 초기화"""
        logger.info("PromptAnalyzer initialized")
    
    def analyze(
        self,
        prompt: str,
        task_type: str,
        card_count: int = 0,
        question: Optional[str] = None,
        category: Optional[str] = None,
        rag_context: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None
    ) -> PromptAnalysis:
        """
        프롬프트 분석 수행
        
        Args:
            prompt: 분석할 프롬프트 텍스트
            task_type: 작업 유형 ("card_interpretation", "overall_reading" 등)
            card_count: 카드 수 (0이면 프롬프트에서 추정)
            question: 사용자 질문 (선택적)
            category: 카테고리 (선택적)
            rag_context: RAG 컨텍스트 (선택적)
            system_prompt: 시스템 프롬프트 (선택적)
        
        Returns:
            PromptAnalysis: 분석 결과
        """
        # 기본 정보 추출
        prompt_length = len(prompt)
        question_length = len(question) if question else 0
        
        # 카드 수 추정 (프롬프트에서)
        if card_count == 0:
            card_count = self._estimate_card_count(prompt)
        
        # 입력 토큰 수 추정
        input_tokens = self._estimate_input_tokens(
            prompt, system_prompt, rag_context
        )
        
        # 출력 토큰 수 추정
        output_tokens = self._estimate_output_tokens(
            task_type, card_count, prompt_length, question_length
        )
        
        # 복잡도 점수 계산
        complexity_score = self._calculate_complexity(
            card_count, question_length, prompt_length, category, rag_context
        )
        
        # 긴급도 결정
        urgency = self._determine_urgency(task_type, complexity_score)
        
        # 고품질 필요 여부
        requires_high_quality = self._requires_high_quality(
            task_type, complexity_score, card_count
        )
        
        # 적합한 성능 등급 결정
        suitable_tiers = self._determine_suitable_tiers(
            complexity_score, output_tokens, requires_high_quality
        )
        
        analysis = PromptAnalysis(
            estimated_input_tokens=input_tokens,
            estimated_output_tokens=output_tokens,
            complexity_score=complexity_score,
            urgency=urgency,
            requires_high_quality=requires_high_quality,
            suitable_tiers=suitable_tiers,
            prompt_length=prompt_length,
            card_count=card_count,
            question_length=question_length,
            has_rag_context=rag_context is not None
        )
        
        logger.debug(
            f"Prompt analysis: tokens={input_tokens}→{output_tokens}, "
            f"complexity={complexity_score:.2f}, tiers={suitable_tiers}"
        )
        
        return analysis
    
    def _estimate_input_tokens(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        rag_context: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        입력 토큰 수 추정
        
        Args:
            prompt: 사용자 프롬프트
            system_prompt: 시스템 프롬프트
            rag_context: RAG 컨텍스트
        
        Returns:
            예상 입력 토큰 수
        """
        total_chars = len(prompt)
        
        if system_prompt:
            total_chars += len(system_prompt)
        
        if rag_context:
            # RAG 컨텍스트의 대략적인 크기 추정
            context_str = str(rag_context)
            total_chars += len(context_str) * 0.5  # 구조화된 데이터는 압축됨
        
        # 문자 수를 토큰 수로 변환 (대략적 추정)
        tokens = int(total_chars / self.CHARS_PER_TOKEN)
        
        return max(tokens, 100)  # 최소 100 토큰
    
    def _estimate_output_tokens(
        self,
        task_type: str,
        card_count: int,
        prompt_length: int,
        question_length: int
    ) -> int:
        """
        출력 토큰 수 추정
        
        Args:
            task_type: 작업 유형
            card_count: 카드 수
            prompt_length: 프롬프트 길이
            question_length: 질문 길이
        
        Returns:
            예상 출력 토큰 수
        """
        # 기본 출력 토큰 수
        base_tokens = self.DEFAULT_OUTPUT_TOKENS.get(task_type, 1000)
        
        # 카드 수에 따른 조정
        if task_type == "card_interpretation":
            # 카드당 약 300-500 토큰
            base_tokens = card_count * 400
        
        # 질문 길이에 따른 조정 (긴 질문은 긴 답변 필요)
        if question_length > 200:
            base_tokens = int(base_tokens * 1.3)
        elif question_length > 100:
            base_tokens = int(base_tokens * 1.1)
        
        # 프롬프트 길이에 따른 조정
        if prompt_length > 5000:
            base_tokens = int(base_tokens * 1.2)
        elif prompt_length > 3000:
            base_tokens = int(base_tokens * 1.1)
        
        return base_tokens
    
    def _estimate_card_count(self, prompt: str) -> int:
        """
        프롬프트에서 카드 수 추정
        
        Args:
            prompt: 프롬프트 텍스트
        
        Returns:
            추정된 카드 수
        """
        # "card" 또는 "카드" 키워드 개수 세기
        card_patterns = [
            r'\bcard\b',
            r'카드',
            r'Card \d+',
            r'카드 \d+',
            r'"id":\s*\d+',  # JSON 형식의 카드 ID
        ]
        
        max_count = 0
        for pattern in card_patterns:
            matches = len(re.findall(pattern, prompt, re.IGNORECASE))
            max_count = max(max_count, matches)
        
        # JSON 배열에서 카드 수 추정
        json_array_pattern = r'\[.*?\]'
        arrays = re.findall(json_array_pattern, prompt)
        for array in arrays:
            # 배열 내 카드 ID 개수 세기
            card_ids = len(re.findall(r'"id"', array))
            max_count = max(max_count, card_ids)
        
        return max(max_count, 1)  # 최소 1개
    
    def _calculate_complexity(
        self,
        card_count: int,
        question_length: int,
        prompt_length: int,
        category: Optional[str] = None,
        rag_context: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        복잡도 점수 계산 (0.0 ~ 1.0)
        
        Args:
            card_count: 카드 수
            question_length: 질문 길이
            prompt_length: 프롬프트 길이
            category: 카테고리
            rag_context: RAG 컨텍스트
        
        Returns:
            복잡도 점수 (0.0 = 단순, 1.0 = 매우 복잡)
        """
        score = 0.0
        
        # 카드 수 기반 복잡도 (0.0 ~ 0.4)
        if card_count == 1:
            score += 0.1
        elif card_count <= 3:
            score += 0.2
        elif card_count <= 5:
            score += 0.3
        else:
            score += 0.4
        
        # 질문 길이 기반 복잡도 (0.0 ~ 0.2)
        if question_length > 300:
            score += 0.2
        elif question_length > 150:
            score += 0.1
        elif question_length > 50:
            score += 0.05
        
        # 프롬프트 길이 기반 복잡도 (0.0 ~ 0.2)
        if prompt_length > 5000:
            score += 0.2
        elif prompt_length > 3000:
            score += 0.15
        elif prompt_length > 2000:
            score += 0.1
        elif prompt_length > 1000:
            score += 0.05
        
        # 카테고리 기반 복잡도 (0.0 ~ 0.1)
        complex_categories = ["spirituality", "personal_growth"]
        if category in complex_categories:
            score += 0.1
        
        # RAG 컨텍스트 기반 복잡도 (0.0 ~ 0.1)
        if rag_context:
            # RAG 컨텍스트가 있으면 더 복잡한 분석 필요
            score += 0.1
        
        # 점수를 0.0 ~ 1.0 범위로 제한
        return min(score, 1.0)
    
    def _determine_urgency(self, task_type: str, complexity_score: float) -> str:
        """
        긴급도 결정
        
        Args:
            task_type: 작업 유형
            complexity_score: 복잡도 점수
        
        Returns:
            "low", "medium", "high"
        """
        # 빠른 응답이 필요한 작업
        urgent_tasks = ["card_interpretation"]
        
        if task_type in urgent_tasks:
            return "high"
        
        # 복잡도가 높으면 중간 긴급도
        if complexity_score > 0.6:
            return "medium"
        
        return "low"
    
    def _requires_high_quality(
        self,
        task_type: str,
        complexity_score: float,
        card_count: int
    ) -> bool:
        """
        고품질 응답 필요 여부 결정
        
        Args:
            task_type: 작업 유형
            complexity_score: 복잡도 점수
            card_count: 카드 수
        
        Returns:
            고품질 필요 여부
        """
        # 종합 리딩은 항상 고품질 필요
        if task_type == "overall_reading":
            return True
        
        # 복잡도가 높으면 고품질 필요
        if complexity_score > 0.7:
            return True
        
        # 카드가 많으면 고품질 필요
        if card_count >= 10:
            return True
        
        return False
    
    def _determine_suitable_tiers(
        self,
        complexity_score: float,
        output_tokens: int,
        requires_high_quality: bool
    ) -> List[str]:
        """
        적합한 성능 등급 결정
        
        Args:
            complexity_score: 복잡도 점수
            output_tokens: 예상 출력 토큰 수
            requires_high_quality: 고품질 필요 여부
        
        Returns:
            적합한 성능 등급 리스트
        """
        tiers = []
        
        # 고품질이 필요하면 고성능 모델만
        if requires_high_quality:
            tiers.append("high")
            if complexity_score < 0.5:
                tiers.append("balanced")
        else:
            # 복잡도에 따라 결정
            if complexity_score < 0.3:
                tiers.extend(["fast", "balanced"])
            elif complexity_score < 0.6:
                tiers.extend(["balanced", "high"])
            else:
                tiers.extend(["balanced", "high"])
        
        # 출력 토큰 수가 많으면 고성능 모델 필요
        if output_tokens > 2000:
            if "high" not in tiers:
                tiers.append("high")
        
        # 중복 제거 및 정렬
        tier_order = ["fast", "balanced", "high"]
        return [t for t in tier_order if t in tiers]

