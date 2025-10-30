"""
Firestore Database Provider

Firebase Firestore를 사용하는 DatabaseProvider 구현체
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import random
import uuid

from firebase_admin import firestore
from google.cloud.firestore_v1 import FieldFilter

from .provider import (
    DatabaseProvider,
    Card as CardDTO,
    Reading as ReadingDTO,
    Feedback as FeedbackDTO,
    LLMUsageLog as LLMUsageLogDTO,
)


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
        self.feedback_collection = self.db.collection('feedback')

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
        for index, card_data in enumerate(reading_data.get('cards', [])):
            card_payload = {
                **card_data,
                'order_index': index,
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP,
            }
            cards_ref.add(card_payload)

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
