"""
Firestore Database Provider

Firebase Firestore를 사용하는 DatabaseProvider 구현체
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import random

from firebase_admin import firestore
from google.cloud.firestore_v1 import FieldFilter

from .provider import DatabaseProvider, Card as CardDTO, Reading as ReadingDTO


class FirestoreProvider(DatabaseProvider):
    """
    Firestore 데이터베이스 Provider

    Firebase Firestore를 DatabaseProvider 인터페이스로 래핑합니다.

    컬렉션 구조:
    - cards: 타로 카드 데이터 (78개 문서)
    - readings: 타로 리딩 데이터
      - reading_cards (subcollection): 각 리딩의 카드 정보
    """

    def __init__(self):
        """Initialize Firestore provider"""
        self.db = firestore.client()
        self.cards_collection = self.db.collection('cards')
        self.readings_collection = self.db.collection('readings')

    # ==================== Conversion Methods ====================

    def _doc_to_card_dto(self, doc) -> CardDTO:
        """Convert Firestore document to Card DTO"""
        data = doc.to_dict()
        return CardDTO(
            id=data['id'],
            name_en=data['name_en'],
            name_ko=data['name_ko'],
            arcana_type=data['arcana_type'],
            number=data.get('number'),
            suit=data.get('suit'),
            keywords_upright=data['keywords_upright'],
            keywords_reversed=data['keywords_reversed'],
            description_ko=data.get('description_ko', ''),
            image_url=data.get('image_url', ''),
        )

    def _doc_to_reading_dto(self, doc) -> ReadingDTO:
        """Convert Firestore document to Reading DTO"""
        data = doc.to_dict()

        # Get reading_cards subcollection
        cards_ref = doc.reference.collection('reading_cards')
        cards_docs = cards_ref.stream()

        cards = []
        for card_doc in cards_docs:
            card_data = card_doc.to_dict()
            cards.append(card_data)

        interpretation = {
            "card_relationships": data.get('card_relationships'),
            "overall_reading": data['overall_reading'],
            "advice": data['advice'],
            "summary": data['summary'],
        }

        return ReadingDTO(
            id=doc.id,
            user_id=data.get('user_id', 'anonymous'),
            question=data['question'],
            spread_type=data['spread_type'],
            category=data.get('category'),
            cards=cards,
            interpretation=interpretation,
            created_at=data['created_at'],
        )

    # ==================== Card Operations ====================

    async def get_card_by_id(self, card_id: int) -> Optional[CardDTO]:
        """ID로 카드 조회"""
        docs = self.cards_collection.where(
            filter=FieldFilter('id', '==', card_id)
        ).limit(1).stream()

        for doc in docs:
            return self._doc_to_card_dto(doc)

        return None

    async def get_card_by_name(self, name: str) -> Optional[CardDTO]:
        """이름으로 카드 조회"""
        # Try English name first
        docs = self.cards_collection.where(
            filter=FieldFilter('name_en', '==', name)
        ).limit(1).stream()

        for doc in docs:
            return self._doc_to_card_dto(doc)

        # Try Korean name
        docs = self.cards_collection.where(
            filter=FieldFilter('name_ko', '==', name)
        ).limit(1).stream()

        for doc in docs:
            return self._doc_to_card_dto(doc)

        return None

    async def get_cards(
        self,
        skip: int = 0,
        limit: int = 100,
        arcana_type: Optional[str] = None,
        suit: Optional[str] = None,
    ) -> List[CardDTO]:
        """카드 목록 조회 (필터링 및 페이지네이션)"""
        query = self.cards_collection

        # Apply filters
        if arcana_type:
            query = query.where(filter=FieldFilter('arcana_type', '==', arcana_type))
        if suit:
            query = query.where(filter=FieldFilter('suit', '==', suit))

        # Order by id
        query = query.order_by('id')

        # Apply pagination
        query = query.offset(skip).limit(limit)

        docs = query.stream()
        return [self._doc_to_card_dto(doc) for doc in docs]

    async def get_total_cards_count(
        self,
        arcana_type: Optional[str] = None,
        suit: Optional[str] = None,
    ) -> int:
        """전체 카드 수 조회 (필터링 적용)"""
        query = self.cards_collection

        # Apply filters
        if arcana_type:
            query = query.where(filter=FieldFilter('arcana_type', '==', arcana_type))
        if suit:
            query = query.where(filter=FieldFilter('suit', '==', suit))

        # Count documents
        docs = query.stream()
        return sum(1 for _ in docs)

    async def get_random_cards(self, count: int) -> List[CardDTO]:
        """랜덤 카드 추출"""
        # Get all cards
        all_docs = list(self.cards_collection.stream())

        # Randomly sample
        selected_docs = random.sample(all_docs, min(count, len(all_docs)))

        return [self._doc_to_card_dto(doc) for doc in selected_docs]

    async def create_card(self, card_data: Dict[str, Any]) -> CardDTO:
        """카드 생성"""
        doc_data = {
            'id': card_data['id'],
            'name_en': card_data['name_en'],
            'name_ko': card_data['name_ko'],
            'arcana_type': card_data['arcana_type'],
            'number': card_data.get('number'),
            'suit': card_data.get('suit'),
            'keywords_upright': card_data['keywords_upright'],
            'keywords_reversed': card_data['keywords_reversed'],
            'description_ko': card_data.get('description_ko', ''),
            'image_url': card_data.get('image_url', ''),
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP,
        }

        # Use card ID as document ID
        doc_ref = self.cards_collection.document(str(card_data['id']))
        doc_ref.set(doc_data)

        # Fetch created document
        doc = doc_ref.get()
        return self._doc_to_card_dto(doc)

    async def update_card(self, card_id: int, card_data: Dict[str, Any]) -> CardDTO:
        """카드 수정"""
        doc_ref = self.cards_collection.document(str(card_id))
        doc = doc_ref.get()

        if not doc.exists:
            raise ValueError(f"Card with id {card_id} not found")

        # Update fields
        update_data = {**card_data, 'updated_at': firestore.SERVER_TIMESTAMP}
        doc_ref.update(update_data)

        # Fetch updated document
        doc = doc_ref.get()
        return self._doc_to_card_dto(doc)

    async def delete_card(self, card_id: int) -> bool:
        """카드 삭제"""
        doc_ref = self.cards_collection.document(str(card_id))
        doc = doc_ref.get()

        if not doc.exists:
            return False

        doc_ref.delete()
        return True

    # ==================== Reading Operations ====================

    async def create_reading(self, reading_data: Dict[str, Any]) -> ReadingDTO:
        """리딩 생성"""
        # Create Reading document
        reading_doc_data = {
            'user_id': reading_data.get('user_id'),
            'spread_type': reading_data['spread_type'],
            'question': reading_data['question'],
            'category': reading_data.get('category'),
            'card_relationships': reading_data.get('card_relationships'),
            'overall_reading': reading_data['overall_reading'],
            'advice': reading_data['advice'],
            'summary': reading_data['summary'],
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP,
        }

        # Create reading document
        _, doc_ref = self.readings_collection.add(reading_doc_data)

        # Create reading_cards subcollection
        cards_ref = doc_ref.collection('reading_cards')
        for card_data in reading_data.get('cards', []):
            cards_ref.add(card_data)

        # Fetch created document
        doc = doc_ref.get()
        return self._doc_to_reading_dto(doc)

    async def get_reading_by_id(self, reading_id: str) -> Optional[ReadingDTO]:
        """ID로 리딩 조회"""
        doc_ref = self.readings_collection.document(reading_id)
        doc = doc_ref.get()

        if not doc.exists:
            return None

        return self._doc_to_reading_dto(doc)

    async def get_readings_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        spread_type: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[ReadingDTO]:
        """사용자별 리딩 목록 조회"""
        query = self.readings_collection.where(
            filter=FieldFilter('user_id', '==', user_id)
        )

        # Apply filters
        if spread_type:
            query = query.where(filter=FieldFilter('spread_type', '==', spread_type))
        if category:
            query = query.where(filter=FieldFilter('category', '==', category))

        # Order by created_at descending
        query = query.order_by('created_at', direction=firestore.Query.DESCENDING)

        # Apply pagination
        query = query.offset(skip).limit(limit)

        docs = query.stream()
        return [self._doc_to_reading_dto(doc) for doc in docs]

    async def get_total_readings_count(
        self,
        user_id: str,
        spread_type: Optional[str] = None,
        category: Optional[str] = None,
    ) -> int:
        """사용자별 전체 리딩 수 조회"""
        query = self.readings_collection.where(
            filter=FieldFilter('user_id', '==', user_id)
        )

        # Apply filters
        if spread_type:
            query = query.where(filter=FieldFilter('spread_type', '==', spread_type))
        if category:
            query = query.where(filter=FieldFilter('category', '==', category))

        # Count documents
        docs = query.stream()
        return sum(1 for _ in docs)

    async def update_reading(self, reading_id: str, reading_data: Dict[str, Any]) -> ReadingDTO:
        """리딩 수정"""
        doc_ref = self.readings_collection.document(reading_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise ValueError(f"Reading with id {reading_id} not found")

        # Update fields (excluding cards subcollection)
        update_data = {
            k: v for k, v in reading_data.items()
            if k != 'cards'
        }
        update_data['updated_at'] = firestore.SERVER_TIMESTAMP

        doc_ref.update(update_data)

        # Fetch updated document
        doc = doc_ref.get()
        return self._doc_to_reading_dto(doc)

    async def delete_reading(self, reading_id: str) -> bool:
        """리딩 삭제"""
        doc_ref = self.readings_collection.document(reading_id)
        doc = doc_ref.get()

        if not doc.exists:
            return False

        # Delete reading_cards subcollection first
        cards_ref = doc_ref.collection('reading_cards')
        cards_docs = cards_ref.stream()
        for card_doc in cards_docs:
            card_doc.reference.delete()

        # Delete reading document
        doc_ref.delete()
        return True

    # ==================== Connection Management ====================

    async def connect(self) -> None:
        """데이터베이스 연결"""
        # Firestore client is already initialized
        pass

    async def disconnect(self) -> None:
        """데이터베이스 연결 해제"""
        # Firestore doesn't require explicit disconnect
        pass

    async def health_check(self) -> bool:
        """데이터베이스 상태 확인"""
        try:
            # Simple query to check connection
            list(self.cards_collection.limit(1).stream())
            return True
        except Exception:
            return False
