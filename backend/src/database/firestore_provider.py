"""
Firestore Database Provider

Firebase Firestore를 사용하는 DatabaseProvider 구현체

Phase 2 Optimization: Added in-memory card caching
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import random
import uuid
import time

from firebase_admin import firestore
from google.cloud.firestore_v1 import FieldFilter

from .provider import (
    DatabaseProvider,
    Card as CardDTO,
    Reading as ReadingDTO,
    Feedback as FeedbackDTO,
    LLMUsageLog as LLMUsageLogDTO,
    Conversation as ConversationDTO,
    Message as MessageDTO,
)


class FirestoreProvider(DatabaseProvider):
    """
    Firestore 데이터베이스 Provider

    Firebase Firestore를 DatabaseProvider 인터페이스로 래핑합니다.

    컬렉션 구조:
    - cards: 타로 카드 데이터 (78개 문서)
    - readings: 타로 리딩 데이터
      - reading_cards (subcollection): 각 리딩의 카드 정보

    Phase 2 Optimization: Card data is cached in memory to avoid repeated Firestore queries
    """

    def __init__(self):
        """Initialize Firestore provider"""
        self.db = firestore.client()
        self.cards_collection = self.db.collection('cards')
        self.readings_collection = self.db.collection('readings')
        self.feedback_collection = self.db.collection('feedback')
        self.conversations_collection = self.db.collection('conversations')

        # Phase 2 Optimization: In-memory card cache
        self._cards_cache: Optional[List[CardDTO]] = None
        self._cache_timestamp: float = 0
        self._cache_ttl: int = 3600  # 1 hour TTL (cards don't change often)

    # ==================== Conversion Methods ====================

    def _doc_to_card_dto(self, doc) -> CardDTO:
        """Convert Firestore document to Card DTO"""
        data = doc.to_dict()
        created_at = data.get('created_at')
        updated_at = data.get('updated_at')

        if hasattr(created_at, "to_datetime"):
            created_at = created_at.to_datetime()
        if hasattr(updated_at, "to_datetime"):
            updated_at = updated_at.to_datetime()

        return CardDTO(
            id=data['id'],
            name_en=data['name_en'],
            name_ko=data['name_ko'],
            arcana_type=data['arcana_type'],
            number=data.get('number'),
            suit=data.get('suit'),
            keywords_upright=data['keywords_upright'],
            keywords_reversed=data['keywords_reversed'],
            meaning_upright=data.get('meaning_upright', ''),
            meaning_reversed=data.get('meaning_reversed', ''),
            description=data.get('description'),
            symbolism=data.get('symbolism'),
            image_url=data.get('image_url'),
            created_at=created_at,
            updated_at=updated_at,
        )

    def _doc_to_reading_dto(self, doc) -> ReadingDTO:
        """Convert Firestore document to Reading DTO"""
        data = doc.to_dict()

        # Get reading_cards subcollection
        cards_ref = doc.reference.collection('reading_cards')
        cards_docs = cards_ref.order_by('order_index').stream()

        cards: List[Dict[str, Any]] = []
        for card_doc in cards_docs:
            card_data = card_doc.to_dict()
            card_data['id'] = card_doc.id
            cards.append(card_data)

        created_at = data.get('created_at')
        updated_at = data.get('updated_at')

        if hasattr(created_at, "to_datetime"):
            created_at = created_at.to_datetime()
        if hasattr(updated_at, "to_datetime"):
            updated_at = updated_at.to_datetime()

        return ReadingDTO(
            id=doc.id,
            user_id=data.get('user_id', 'anonymous'),
            question=data['question'],
            spread_type=data['spread_type'],
            category=data.get('category'),
            cards=cards,
            card_relationships=data.get('card_relationships'),
            overall_reading=data['overall_reading'],
            advice=data['advice'],
            summary=data['summary'],
            created_at=created_at,
            updated_at=updated_at,
        )

    def _doc_to_feedback_dto(self, doc) -> FeedbackDTO:
        """Convert Firestore document to Feedback DTO"""
        data = doc.to_dict()
        created_at = data.get('created_at')
        updated_at = data.get('updated_at')

        if hasattr(created_at, "to_datetime"):
            created_at = created_at.to_datetime()
        if hasattr(updated_at, "to_datetime"):
            updated_at = updated_at.to_datetime()

        return FeedbackDTO(
            id=data.get('id', doc.id),
            reading_id=data['reading_id'],
            user_id=data['user_id'],
            rating=data['rating'],
            comment=data.get('comment'),
            helpful=data.get('helpful', True),
            accurate=data.get('accurate', True),
            created_at=created_at or datetime.utcnow().replace(tzinfo=timezone.utc),
            updated_at=updated_at or created_at or datetime.utcnow().replace(tzinfo=timezone.utc),
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
        """
        랜덤 카드 추출 (Phase 2 Optimization: Uses cached cards)

        This method now uses in-memory cache instead of querying Firestore every time.
        Performance improvement: 1-3 seconds -> 0.1 seconds
        """
        # Get all cards from cache
        all_cards = await self.get_all_cards_cached()

        # Randomly sample
        if count >= len(all_cards):
            return all_cards.copy()

        selected_cards = random.sample(all_cards, count)
        return selected_cards

    async def get_all_cards_cached(self) -> List[CardDTO]:
        """
        Get all cards with in-memory caching (Phase 2 Optimization)

        Cards are cached for 1 hour since they rarely change.
        This drastically reduces database queries during card selection.

        Returns:
            List of all card DTOs
        """
        now = time.time()

        # Check if cache is valid
        if self._cards_cache and (now - self._cache_timestamp < self._cache_ttl):
            return self._cards_cache

        # Cache miss or expired - fetch from Firestore
        all_docs = list(self.cards_collection.stream())
        self._cards_cache = [self._doc_to_card_dto(doc) for doc in all_docs]
        self._cache_timestamp = now

        return self._cards_cache

    def invalidate_cards_cache(self):
        """
        Invalidate the cards cache

        Call this method when cards are created, updated, or deleted
        to ensure cache consistency.
        """
        self._cards_cache = None
        self._cache_timestamp = 0

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
            'meaning_upright': card_data.get('meaning_upright', ''),
            'meaning_reversed': card_data.get('meaning_reversed', ''),
            'description': card_data.get('description'),
            'symbolism': card_data.get('symbolism'),
            'image_url': card_data.get('image_url'),
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP,
        }

        # Use card ID as document ID
        doc_ref = self.cards_collection.document(str(card_data['id']))
        doc_ref.set(doc_data)

        # Invalidate cache
        self.invalidate_cards_cache()

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

        # Invalidate cache
        self.invalidate_cards_cache()

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

        # Invalidate cache
        self.invalidate_cards_cache()

        return True

    # ==================== Reading Operations ====================

    async def create_reading(self, reading_data: Dict[str, Any]) -> ReadingDTO:
        """리딩 생성 (배치 쓰기 지원)"""
        reading_id = reading_data.get('id') or str(uuid.uuid4())
        doc_ref = self.readings_collection.document(reading_id)

        created_at = reading_data.get('created_at')
        updated_at = reading_data.get('updated_at')

        reading_doc_data = {
            'id': reading_id,
            'user_id': reading_data.get('user_id'),
            'spread_type': reading_data['spread_type'],
            'question': reading_data['question'],
            'category': reading_data.get('category'),
            'card_relationships': reading_data.get('card_relationships'),
            'overall_reading': reading_data['overall_reading'],
            'advice': reading_data['advice'],
            'summary': reading_data['summary'],
            'llm_usage': reading_data.get('llm_usage', []),
            'status': reading_data.get('status', 'completed'),
            'created_at': created_at or firestore.SERVER_TIMESTAMP,
            'updated_at': updated_at or firestore.SERVER_TIMESTAMP,
            'persisted_at': firestore.SERVER_TIMESTAMP,
        }

        batch = self.db.batch()
        batch.set(doc_ref, reading_doc_data)

        cards = reading_data.get('cards', [])
        for index, card_data in enumerate(cards):
            card_ref = doc_ref.collection('reading_cards').document()
            card_payload = {
                **card_data,
                'order_index': index,
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP,
            }
            batch.set(card_ref, card_payload)

        batch.commit()

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

        # Update cards if provided
        if 'cards' in reading_data:
            cards_ref = doc_ref.collection('reading_cards')
            # Clear existing cards
            existing_cards = list(cards_ref.stream())
            for card_doc in existing_cards:
                card_doc.reference.delete()

            for index, card_data in enumerate(reading_data['cards']):
                cards_ref.add({
                    **card_data,
                    'order_index': index,
                    'created_at': firestore.SERVER_TIMESTAMP,
                    'updated_at': firestore.SERVER_TIMESTAMP,
                })

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

    # ==================== LLM Usage Log Operations ====================

    async def create_llm_usage_log(self, log_data: Dict[str, Any]) -> LLMUsageLogDTO:
        """LLM 사용 로그 생성 (Firestore는 readings 문서의 llm_usage 배열에 추가)"""
        import uuid
        from datetime import datetime, timezone

        reading_id = log_data['reading_id']
        log_id = log_data.get('id') or str(uuid.uuid4())

        log_entry = {
            'id': log_id,
            'reading_id': reading_id,
            'provider': log_data['provider'],
            'model': log_data['model'],
            'prompt_tokens': log_data['prompt_tokens'],
            'completion_tokens': log_data['completion_tokens'],
            'total_tokens': log_data['total_tokens'],
            'estimated_cost': log_data['estimated_cost'],
            'latency_seconds': log_data['latency_seconds'],
            'purpose': log_data.get('purpose', 'main_reading'),
            'created_at': log_data.get('created_at') or datetime.now(timezone.utc),
        }

        # readings 문서의 llm_usage 배열에 추가
        doc_ref = self.readings_collection.document(reading_id)
        doc_ref.update({
            'llm_usage': firestore.ArrayUnion([log_entry])
        })

        return LLMUsageLogDTO(
            id=log_id,
            reading_id=reading_id,
            provider=log_entry['provider'],
            model=log_entry['model'],
            prompt_tokens=log_entry['prompt_tokens'],
            completion_tokens=log_entry['completion_tokens'],
            total_tokens=log_entry['total_tokens'],
            estimated_cost=log_entry['estimated_cost'],
            latency_seconds=log_entry['latency_seconds'],
            purpose=log_entry['purpose'],
            created_at=log_entry['created_at'],
        )

    async def get_llm_usage_logs(self, reading_id: str) -> List[LLMUsageLogDTO]:
        """특정 리딩의 LLM 사용 로그 조회"""
        doc_ref = self.readings_collection.document(reading_id)
        doc = doc_ref.get()

        if not doc.exists:
            return []

        data = doc.to_dict()
        llm_usage = data.get('llm_usage', [])

        return [
            LLMUsageLogDTO(
                id=log['id'],
                reading_id=log['reading_id'],
                provider=log['provider'],
                model=log['model'],
                prompt_tokens=log['prompt_tokens'],
                completion_tokens=log['completion_tokens'],
                total_tokens=log['total_tokens'],
                estimated_cost=log['estimated_cost'],
                latency_seconds=log['latency_seconds'],
                purpose=log.get('purpose', 'main_reading'),
                created_at=log.get('created_at'),
            )
            for log in llm_usage
        ]

    # ==================== Feedback Operations ====================

    async def create_feedback(self, feedback_data: Dict[str, Any]) -> FeedbackDTO:
        """피드백 생성"""
        feedback_id = feedback_data.get('id') or str(uuid.uuid4())

        doc_payload = {
            'id': feedback_id,
            'reading_id': feedback_data['reading_id'],
            'user_id': feedback_data['user_id'],
            'rating': feedback_data['rating'],
            'comment': feedback_data.get('comment'),
            'helpful': feedback_data.get('helpful', True),
            'accurate': feedback_data.get('accurate', True),
            'spread_type': feedback_data.get('spread_type'),
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP,
        }

        doc_ref = self.feedback_collection.document(feedback_id)
        doc_ref.set(doc_payload)

        doc = doc_ref.get()
        return self._doc_to_feedback_dto(doc)

    async def get_feedback_by_id(self, feedback_id: str) -> Optional[FeedbackDTO]:
        """ID로 피드백 조회"""
        doc = self.feedback_collection.document(feedback_id).get()
        if not doc.exists:
            return None
        return self._doc_to_feedback_dto(doc)

    async def get_feedback_by_reading(
        self,
        reading_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[FeedbackDTO]:
        """특정 리딩의 피드백 목록 조회"""
        query = (
            self.feedback_collection
            .where(filter=FieldFilter('reading_id', '==', reading_id))
            .order_by('created_at', direction=firestore.Query.DESCENDING)
            .offset(skip)
            .limit(limit)
        )
        docs = query.stream()
        return [self._doc_to_feedback_dto(doc) for doc in docs]

    async def get_feedback_by_reading_and_user(
        self,
        reading_id: str,
        user_id: str,
    ) -> Optional[FeedbackDTO]:
        """리딩과 사용자 조합으로 피드백 조회"""
        query = (
            self.feedback_collection
            .where(filter=FieldFilter('reading_id', '==', reading_id))
            .where(filter=FieldFilter('user_id', '==', user_id))
            .limit(1)
        )
        for doc in query.stream():
            return self._doc_to_feedback_dto(doc)
        return None

    async def update_feedback(
        self,
        feedback_id: str,
        feedback_data: Dict[str, Any],
    ) -> Optional[FeedbackDTO]:
        """피드백 수정"""
        doc_ref = self.feedback_collection.document(feedback_id)
        doc = doc_ref.get()

        if not doc.exists:
            return None

        update_payload = {k: v for k, v in feedback_data.items() if v is not None}
        update_payload['updated_at'] = firestore.SERVER_TIMESTAMP

        if update_payload:
            doc_ref.update(update_payload)

        updated_doc = doc_ref.get()
        return self._doc_to_feedback_dto(updated_doc)

    async def delete_feedback(self, feedback_id: str) -> bool:
        """피드백 삭제"""
        doc_ref = self.feedback_collection.document(feedback_id)
        doc = doc_ref.get()
        if not doc.exists:
            return False
        doc_ref.delete()
        return True

    async def get_feedback_statistics(self) -> Dict[str, Any]:
        """전체 피드백 통계"""
        docs = list(self.feedback_collection.stream())

        total_count = len(docs)
        if total_count == 0:
            return {
                "total_feedback_count": 0,
                "average_rating": 0.0,
                "helpful_count": 0,
                "accurate_count": 0,
                "helpful_rate": 0.0,
                "accurate_rate": 0.0,
            }

        ratings = []
        helpful_count = 0
        accurate_count = 0

        for doc in docs:
            data = doc.to_dict()
            ratings.append(data.get('rating', 0))
            if data.get('helpful'):
                helpful_count += 1
            if data.get('accurate'):
                accurate_count += 1

        avg_rating = sum(ratings) / total_count if ratings else 0

        return {
            "total_feedback_count": total_count,
            "average_rating": round(avg_rating, 2),
            "helpful_count": helpful_count,
            "accurate_count": accurate_count,
            "helpful_rate": round((helpful_count / total_count) * 100, 1),
            "accurate_rate": round((accurate_count / total_count) * 100, 1),
        }

    async def get_feedback_statistics_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """기간별 피드백 통계"""
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)

        query = (
            self.feedback_collection
            .where(filter=FieldFilter('created_at', '>=', start_date))
            .where(filter=FieldFilter('created_at', '<', end_date))
        )

        docs = list(query.stream())
        total_count = len(docs)

        if total_count == 0:
            return {
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "total_feedback_count": 0,
                "average_rating": 0.0,
                "helpful_count": 0,
                "accurate_count": 0,
                "helpful_rate": 0.0,
                "accurate_rate": 0.0,
            }

        ratings = []
        helpful_count = 0
        accurate_count = 0

        for doc in docs:
            data = doc.to_dict()
            ratings.append(data.get('rating', 0))
            if data.get('helpful'):
                helpful_count += 1
            if data.get('accurate'):
                accurate_count += 1

        avg_rating = sum(ratings) / total_count if ratings else 0

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "total_feedback_count": total_count,
            "average_rating": round(avg_rating, 2),
            "helpful_count": helpful_count,
            "accurate_count": accurate_count,
            "helpful_rate": round((helpful_count / total_count) * 100, 1),
            "accurate_rate": round((accurate_count / total_count) * 100, 1),
        }

    async def get_feedback_statistics_by_spread_type(self) -> List[Dict[str, Any]]:
        """스프레드 타입별 피드백 통계"""
        docs = list(self.feedback_collection.stream())

        spread_stats: Dict[str, Dict[str, Any]] = {}
        for doc in docs:
            data = doc.to_dict()
            spread_type = data.get('spread_type') or "unknown"
            bucket = spread_stats.setdefault(
                spread_type,
                {
                    "spread_type": spread_type,
                    "feedback_count": 0,
                    "rating_total": 0,
                    "helpful_count": 0,
                    "accurate_count": 0,
                },
            )
            bucket["feedback_count"] += 1
            bucket["rating_total"] += data.get('rating', 0)
            if data.get('helpful'):
                bucket["helpful_count"] += 1
            if data.get('accurate'):
                bucket["accurate_count"] += 1

        results: List[Dict[str, Any]] = []
        for spread_type, bucket in spread_stats.items():
            total = bucket["feedback_count"]
            avg_rating = bucket["rating_total"] / total if total else 0
            helpful_rate = round((bucket["helpful_count"] / total) * 100, 1) if total else 0.0
            accurate_rate = round((bucket["accurate_count"] / total) * 100, 1) if total else 0.0

            results.append({
                "spread_type": spread_type,
                "feedback_count": total,
                "average_rating": round(avg_rating, 2),
                "helpful_count": bucket["helpful_count"],
                "accurate_count": bucket["accurate_count"],
                "helpful_rate": helpful_rate,
                "accurate_rate": accurate_rate,
            })

        return results

    # ==================== Admin Statistics Operations ====================

    async def get_total_users_count(self) -> int:
        """전체 사용자 수 조회 (관리자 대시보드용)"""
        # Firestore에는 users 컬렉션이 없으므로 readings에서 고유한 user_id 집계
        readings = list(self.readings_collection.stream())
        unique_user_ids = set()
        for doc in readings:
            data = doc.to_dict()
            user_id = data.get('user_id')
            if user_id:
                unique_user_ids.add(user_id)
        return len(unique_user_ids)

    async def get_total_readings_count_all(self) -> int:
        """전체 리딩 수 조회 (관리자 대시보드용, user_id 필터 없음)"""
        # Firestore는 count 쿼리를 지원하지만, 모든 문서를 스트림하는 것이 더 안정적
        readings = list(self.readings_collection.stream())
        return len(readings)

    async def get_readings_count_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> int:
        """기간별 리딩 수 조회 (관리자 대시보드용)"""
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)

        query = (
            self.readings_collection
            .where(filter=FieldFilter('created_at', '>=', start_date))
            .where(filter=FieldFilter('created_at', '<', end_date))
        )

        readings = list(query.stream())
        return len(readings)

    async def get_total_llm_cost(self) -> float:
        """전체 LLM 비용 합계 조회 (관리자 대시보드용)"""
        readings = list(self.readings_collection.stream())
        total_cost = 0.0

        for doc in readings:
            data = doc.to_dict()
            llm_usage = data.get('llm_usage', [])
            if isinstance(llm_usage, list):
                for log in llm_usage:
                    if isinstance(log, dict):
                        cost = log.get('estimated_cost', 0.0)
                        if isinstance(cost, (int, float)):
                            total_cost += cost

        return round(total_cost, 2)

    # ==================== Settings Operations ====================

    async def get_app_settings(self) -> Optional[Dict[str, Any]]:
        """애플리케이션 설정 조회"""
        settings_ref = self.db.collection('settings').document('app_settings')
        doc = settings_ref.get()
        
        if not doc.exists:
            # Return default settings
            return {
                "id": "app_settings",
                "admin": {
                    "admin_emails": []
                },
                "ai": {
                    "provider_priority": ["openai", "anthropic"],
                    "providers": [],
                    "default_timeout": 30
                },
                "updated_at": None,
                "updated_by": None
            }
        
        data = doc.to_dict()
        
        # Convert timestamp
        updated_at = data.get('updated_at')
        if hasattr(updated_at, "to_datetime"):
            data['updated_at'] = updated_at.to_datetime()
        
        return data

    async def update_app_settings(
        self,
        settings_data: Dict[str, Any],
        updated_by: str
    ) -> Dict[str, Any]:
        """애플리케이션 설정 업데이트"""
        settings_ref = self.db.collection('settings').document('app_settings')
        
        update_data = {
            **settings_data,
            'updated_at': firestore.SERVER_TIMESTAMP,
            'updated_by': updated_by
        }
        
        # Upsert (create or update)
        settings_ref.set(update_data, merge=True)
        
        # Fetch updated document
        doc = settings_ref.get()
        data = doc.to_dict()
        
        # Convert timestamp
        updated_at = data.get('updated_at')
        if hasattr(updated_at, "to_datetime"):
            data['updated_at'] = updated_at.to_datetime()
        
        return data

    async def get_admin_emails(self) -> List[str]:
        """관리자 이메일 목록 조회"""
        settings = await self.get_app_settings()
        return settings.get('admin', {}).get('admin_emails', [])

    async def add_admin_email(self, email: str, updated_by: str) -> bool:
        """관리자 이메일 추가"""
        settings_ref = self.db.collection('settings').document('app_settings')
        
        # Use ArrayUnion to add email if not exists
        settings_ref.set({
            'admin': {
                'admin_emails': firestore.ArrayUnion([email])
            },
            'updated_at': firestore.SERVER_TIMESTAMP,
            'updated_by': updated_by
        }, merge=True)
        
        return True

    async def remove_admin_email(self, email: str, updated_by: str) -> bool:
        """관리자 이메일 제거"""
        settings_ref = self.db.collection('settings').document('app_settings')
        
        # Use ArrayRemove to remove email
        settings_ref.set({
            'admin': {
                'admin_emails': firestore.ArrayRemove([email])
            },
            'updated_at': firestore.SERVER_TIMESTAMP,
            'updated_by': updated_by
        }, merge=True)
        
        return True

    # ==================== Connection Management ====================

    # ==================== Conversation Operations ====================

    def _doc_to_conversation_dto(self, doc) -> ConversationDTO:
        """Convert Firestore document to Conversation DTO"""
        data = doc.to_dict()
        created_at = data.get('created_at')
        updated_at = data.get('updated_at')

        if hasattr(created_at, "to_datetime"):
            created_at = created_at.to_datetime()
        if hasattr(updated_at, "to_datetime"):
            updated_at = updated_at.to_datetime()

        return ConversationDTO(
            id=doc.id,
            user_id=data['user_id'],
            title=data['title'],
            created_at=created_at or datetime.now(timezone.utc),
            updated_at=updated_at or datetime.now(timezone.utc),
        )

    async def create_conversation(self, conversation_data: Dict[str, Any]) -> ConversationDTO:
        """대화 생성"""
        conversation_id = conversation_data.get('id') or str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        doc_data = {
            'user_id': conversation_data['user_id'],
            'title': conversation_data['title'],
            'created_at': now,
            'updated_at': now,
        }

        doc_ref = self.conversations_collection.document(conversation_id)
        doc_ref.set(doc_data)

        doc = doc_ref.get()
        return self._doc_to_conversation_dto(doc)

    async def get_conversation_by_id(self, conversation_id: str) -> Optional[ConversationDTO]:
        """ID로 대화 조회"""
        doc = self.conversations_collection.document(conversation_id).get()
        if not doc.exists:
            return None
        return self._doc_to_conversation_dto(doc)

    async def get_conversations_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ConversationDTO]:
        """사용자별 대화 목록 조회"""
        query = self.conversations_collection.where(
            filter=FieldFilter('user_id', '==', user_id)
        ).order_by('updated_at', direction=firestore.Query.DESCENDING)

        conversations = []
        for doc in query.offset(skip).limit(limit).stream():
            conversations.append(self._doc_to_conversation_dto(doc))

        return conversations

    async def update_conversation(
        self,
        conversation_id: str,
        conversation_data: Dict[str, Any],
    ) -> Optional[ConversationDTO]:
        """대화 수정"""
        doc_ref = self.conversations_collection.document(conversation_id)
        doc = doc_ref.get()

        if not doc.exists:
            return None

        update_data = {'updated_at': datetime.now(timezone.utc)}
        for key, value in conversation_data.items():
            if key != 'id' and key != 'user_id':  # Don't allow changing these
                update_data[key] = value

        doc_ref.update(update_data)
        doc = doc_ref.get()
        return self._doc_to_conversation_dto(doc)

    async def delete_conversation(self, conversation_id: str) -> bool:
        """대화 삭제"""
        doc_ref = self.conversations_collection.document(conversation_id)
        doc = doc_ref.get()

        if not doc.exists:
            return False

        # Delete messages subcollection first
        messages_ref = doc_ref.collection('messages')
        for msg_doc in messages_ref.stream():
            msg_doc.reference.delete()

        # Delete conversation
        doc_ref.delete()
        return True

    # ==================== Message Operations ====================

    def _doc_to_message_dto(self, doc) -> MessageDTO:
        """Convert Firestore document to Message DTO"""
        data = doc.to_dict()
        created_at = data.get('created_at')

        if hasattr(created_at, "to_datetime"):
            created_at = created_at.to_datetime()

        return MessageDTO(
            id=doc.id,
            conversation_id=data['conversation_id'],
            role=data['role'],
            content=data['content'],
            message_metadata=data.get('metadata', {}),  # Firestore에서는 metadata로 저장하지만 DTO는 message_metadata
            created_at=created_at or datetime.now(timezone.utc),
        )

    async def create_message(self, message_data: Dict[str, Any]) -> MessageDTO:
        """메시지 생성"""
        message_id = message_data.get('id') or str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        doc_data = {
            'conversation_id': message_data['conversation_id'],
            'role': message_data['role'],
            'content': message_data['content'],
            'metadata': message_data.get('metadata', {}),  # Firestore에는 metadata로 저장
            'created_at': now,
        }

        # Store message in conversation's messages subcollection
        conversation_ref = self.conversations_collection.document(
            message_data['conversation_id']
        )
        messages_ref = conversation_ref.collection('messages')
        doc_ref = messages_ref.document(message_id)
        doc_ref.set(doc_data)

        # Also update conversation's updated_at
        conversation_ref.update({'updated_at': now})

        doc = doc_ref.get()
        return self._doc_to_message_dto(doc)

    async def get_message_by_id(self, message_id: str) -> Optional[MessageDTO]:
        """ID로 메시지 조회"""
        # Need to search through all conversations' messages subcollections
        # This is inefficient but Firestore doesn't support direct subcollection queries
        # In production, consider storing message_id -> conversation_id mapping
        for conv_doc in self.conversations_collection.stream():
            msg_doc = conv_doc.reference.collection('messages').document(message_id).get()
            if msg_doc.exists:
                return self._doc_to_message_dto(msg_doc)
        return None

    async def get_messages_by_conversation(
        self,
        conversation_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[MessageDTO]:
        """대화별 메시지 목록 조회"""
        conversation_ref = self.conversations_collection.document(conversation_id)
        messages_ref = conversation_ref.collection('messages')

        messages = []
        query = messages_ref.order_by('created_at', direction=firestore.Query.ASCENDING)
        for doc in query.offset(skip).limit(limit).stream():
            messages.append(self._doc_to_message_dto(doc))

        return messages

    async def get_recent_messages_by_conversation(
        self,
        conversation_id: str,
        limit: int = 5,
    ) -> List[MessageDTO]:
        """대화별 최근 메시지 조회 (단기 메모리용)"""
        conversation_ref = self.conversations_collection.document(conversation_id)
        messages_ref = conversation_ref.collection('messages')

        messages = []
        query = messages_ref.order_by('created_at', direction=firestore.Query.DESCENDING)
        for doc in query.limit(limit).stream():
            messages.append(self._doc_to_message_dto(doc))

        # Reverse to get chronological order
        return list(reversed(messages))

    async def delete_message(self, message_id: str) -> bool:
        """메시지 삭제"""
        # Need to find which conversation this message belongs to
        for conv_doc in self.conversations_collection.stream():
            msg_doc_ref = conv_doc.reference.collection('messages').document(message_id)
            msg_doc = msg_doc_ref.get()
            if msg_doc.exists:
                msg_doc_ref.delete()
                return True
        return False

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
