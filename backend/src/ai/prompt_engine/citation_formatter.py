"""
Citation Formatter - 카드 인용 포맷팅 및 검증

이 모듈의 목적:
- 종합 리딩에서 카드 참조를 감지하고 인용 표시 추가
- 인용 형식 검증 및 표준화
- 카드 이름과 포지션 매핑 관리
"""
import re
from typing import List, Dict, Any, Optional, Set
import logging

logger = logging.getLogger(__name__)


class CitationFormatter:
    """
    카드 인용 포맷터
    
    종합 리딩 텍스트에서 카드 참조를 감지하고 표준화된 인용 형식으로 변환합니다.
    """
    
    # 인용 형식 패턴
    CITATION_PATTERNS = [
        r'\[([^\]]+)\]',  # [카드명] 또는 [카드명(포지션)]
        r'\(([^)]+)\)',   # (카드명) 또는 (포지션)
    ]
    
    def __init__(self, card_mapping: Dict[str, Dict[str, str]]):
        """
        인용 포맷터 초기화
        
        Args:
            card_mapping: 카드 ID를 키로 하는 딕셔너리
                {
                    "card_id": {
                        "name": "카드명",
                        "position": "포지션명",
                        "position_korean": "포지션 한글명"
                    }
                }
        """
        self.card_mapping = card_mapping
        # 카드명과 포지션명으로 역참조 맵 생성
        self.name_to_card = {
            info["name"]: card_id
            for card_id, info in card_mapping.items()
        }
        self.position_to_cards = {}
        for card_id, info in card_mapping.items():
            pos = info.get("position_korean") or info.get("position")
            if pos:
                if pos not in self.position_to_cards:
                    self.position_to_cards[pos] = []
                self.position_to_cards[pos].append(card_id)
    
    def format_citation(self, card_id: str, include_position: bool = True) -> str:
        """
        카드 인용 형식 생성
        
        Args:
            card_id: 카드 ID
            include_position: 포지션 포함 여부
        
        Returns:
            인용 형식 문자열 예: "[바보 카드(현재)]" 또는 "[바보 카드]"
        """
        if card_id not in self.card_mapping:
            logger.warning(f"Unknown card_id for citation: {card_id}")
            return f"[카드 {card_id}]"
        
        card_info = self.card_mapping[card_id]
        card_name = card_info.get("name", card_id)
        position = card_info.get("position_korean") or card_info.get("position", "")
        
        if include_position and position:
            return f"[{card_name}({position})]"
        else:
            return f"[{card_name}]"
    
    def detect_card_references(self, text: str) -> Set[str]:
        """
        텍스트에서 카드 참조 감지
        
        Args:
            text: 분석할 텍스트
        
        Returns:
            감지된 카드 ID 집합
        """
        detected = set()
        
        # 카드명으로 검색
        for card_name, card_id in self.name_to_card.items():
            # 간단한 패턴 매칭 (부분 일치)
            if card_name.lower() in text.lower():
                detected.add(card_id)
        
        # 포지션명으로 검색
        for position, card_ids in self.position_to_cards.items():
            if position in text:
                detected.update(card_ids)
        
        return detected
    
    def add_citations(self, text: str, card_ids: Optional[List[str]] = None) -> str:
        """
        텍스트에 카드 인용 추가
        
        카드명이나 포지션명이 언급된 부분에 인용 표시를 추가합니다.
        이미 인용이 있는 경우 중복 추가하지 않습니다.
        
        Args:
            text: 원본 텍스트
            card_ids: 특정 카드만 인용할 경우 지정 (None이면 모든 카드)
        
        Returns:
            인용이 추가된 텍스트
        """
        if not text:
            return text
        
        result = text
        cards_to_cite = set(card_ids) if card_ids else set(self.card_mapping.keys())
        
        # 각 카드에 대해 인용 추가
        for card_id in cards_to_cite:
            if card_id not in self.card_mapping:
                continue
            
            card_info = self.card_mapping[card_id]
            card_name = card_info.get("name", "")
            position = card_info.get("position_korean") or card_info.get("position", "")
            
            if not card_name:
                continue
            
            # 이미 인용이 있는지 확인
            citation_pattern = re.escape(f"[{card_name}")
            if re.search(citation_pattern, result):
                continue  # 이미 인용됨
            
            # 카드명 패턴 찾기 (단어 경계 고려)
            # 예: "바보 카드" 또는 "바보카드"
            patterns = [
                rf'\b{re.escape(card_name)}\b',  # 단어 경계
                re.escape(card_name),  # 부분 일치
            ]
            
            for pattern in patterns:
                matches = list(re.finditer(pattern, result, re.IGNORECASE))
                # 뒤에서부터 교체하여 인덱스 변경 방지
                for match in reversed(matches):
                    start, end = match.span()
                    citation = self.format_citation(card_id, include_position=True)
                    result = result[:end] + citation + result[end:]
        
        return result
    
    def validate_citations(self, text: str, expected_cards: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        인용 검증
        
        텍스트에 필요한 카드 인용이 있는지 확인합니다.
        
        Args:
            text: 검증할 텍스트
            expected_cards: 기대되는 카드 ID 리스트 (None이면 모든 카드)
        
        Returns:
            검증 결과 딕셔너리:
            {
                "valid": bool,
                "detected_citations": List[str],
                "missing_citations": List[str],
                "citation_count": int
            }
        """
        detected = self.detect_card_references(text)
        expected = set(expected_cards) if expected_cards else set(self.card_mapping.keys())
        
        # 인용 표시가 있는 카드 찾기
        citation_pattern = r'\[([^\]]+)\]'
        citations_found = re.findall(citation_pattern, text)
        
        missing = expected - detected
        citation_count = len(citations_found)
        
        return {
            "valid": len(missing) == 0,
            "detected_citations": list(detected),
            "missing_citations": list(missing),
            "citation_count": citation_count,
            "citations_found": citations_found
        }
    
    @staticmethod
    def create_card_mapping(
        cards: List[Dict[str, Any]],
        position_names: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, str]]:
        """
        카드 리스트로부터 매핑 생성
        
        Args:
            cards: 카드 정보 리스트
                [
                    {
                        "card_id": "major_0",
                        "name": "바보 카드",
                        "position": "present",
                        ...
                    }
                ]
            position_names: 포지션 한글명 리스트 (선택사항)
        
        Returns:
            카드 매핑 딕셔너리
        """
        mapping = {}
        
        # 켈틱 크로스 포지션 한글명 (기본값)
        default_positions = [
            "현재", "도전", "과거", "미래",
            "의식적 목표", "무의식적 영향",
            "조언", "외부 영향", "희망과 두려움", "최종 결과"
        ]
        
        position_korean_map = {
            "present": "현재",
            "challenge": "도전",
            "past": "과거",
            "future": "미래",
            "above": "의식적 목표",
            "below": "무의식적 영향",
            "advice": "조언",
            "external": "외부 영향",
            "hopes_fears": "희망과 두려움",
            "outcome": "최종 결과",
        }
        
        for idx, card in enumerate(cards):
            card_id = card.get("card_id") or card.get("id")
            if not card_id:
                continue
            
            position = card.get("position", "")
            position_korean = None
            
            if position_names and idx < len(position_names):
                position_korean = position_names[idx]
            elif position in position_korean_map:
                position_korean = position_korean_map[position]
            
            mapping[card_id] = {
                "name": card.get("name", ""),
                "position": position,
                "position_korean": position_korean or position
            }
        
        return mapping

