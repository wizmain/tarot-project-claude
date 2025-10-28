"""
PostgreSQL 데이터를 Firestore로 마이그레이션하는 스크립트

사용법:
    python scripts/migrate_to_firestore.py --cards     # 카드만 마이그레이션
    python scripts/migrate_to_firestore.py --readings  # 리딩만 마이그레이션
    python scripts/migrate_to_firestore.py --all       # 전체 마이그레이션
"""
import asyncio
import argparse
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.orm import Session
from firebase_admin import firestore
from src.core.database import SessionLocal
from src.core.firebase_admin import initialize_firebase_admin
from src.models.card import Card as CardModel
from src.models.reading import Reading as ReadingModel


async def migrate_cards(dry_run: bool = False):
    """
    카드 데이터를 PostgreSQL에서 Firestore로 마이그레이션

    Args:
        dry_run: True면 실제 쓰기 없이 로그만 출력
    """
    print("\n=== 카드 마이그레이션 시작 ===")

    # PostgreSQL 세션
    db: Session = SessionLocal()
    cards = db.query(CardModel).all()

    print(f"총 {len(cards)}개의 카드를 마이그레이션합니다.")

    if dry_run:
        print("(DRY RUN 모드 - 실제 쓰기는 하지 않습니다)")
        for card in cards[:5]:  # 처음 5개만 출력
            print(f"  - {card.name} ({card.name_ko})")
        if len(cards) > 5:
            print(f"  ... 외 {len(cards) - 5}개")
        db.close()
        return

    # Firestore 클라이언트
    firestore_db = firestore.client()
    cards_collection = firestore_db.collection('cards')

    # 마이그레이션
    success_count = 0
    error_count = 0

    for card in cards:
        try:
            doc_data = {
                'id': card.id,
                'name_en': card.name,
                'name_ko': card.name_ko,
                'arcana_type': card.arcana_type.value,
                'number': card.number,
                'suit': card.suit.value if card.suit else None,
                'keywords_upright': card.keywords_upright,
                'keywords_reversed': card.keywords_reversed,
                'meaning_upright': card.meaning_upright,
                'meaning_reversed': card.meaning_reversed,
                'description_ko': card.description or '',
                'symbolism': card.symbolism,
                'image_url': card.image_url or '',
                'created_at': card.created_at,
                'updated_at': card.updated_at,
            }

            # Document ID는 card.id 사용
            cards_collection.document(str(card.id)).set(doc_data)
            success_count += 1
            print(f"  ✓ {card.name} ({card.id})")

        except Exception as e:
            error_count += 1
            print(f"  ✗ {card.name} 실패: {e}")

    db.close()

    print(f"\n카드 마이그레이션 완료: 성공 {success_count}, 실패 {error_count}")


async def migrate_readings(dry_run: bool = False, limit: int = None):
    """
    리딩 데이터를 PostgreSQL에서 Firestore로 마이그레이션

    Args:
        dry_run: True면 실제 쓰기 없이 로그만 출력
        limit: 마이그레이션할 최대 개수 (None이면 전체)
    """
    print("\n=== 리딩 마이그레이션 시작 ===")

    # PostgreSQL 세션
    db: Session = SessionLocal()
    query = db.query(ReadingModel)

    if limit:
        query = query.limit(limit)
        print(f"최대 {limit}개의 리딩을 마이그레이션합니다.")

    readings = query.all()
    print(f"총 {len(readings)}개의 리딩을 마이그레이션합니다.")

    if dry_run:
        print("(DRY RUN 모드 - 실제 쓰기는 하지 않습니다)")
        for reading in readings[:3]:  # 처음 3개만 출력
            print(f"  - Reading {reading.id}: {reading.spread_type}")
            print(f"    카드 {len(reading.cards)}개")
        if len(readings) > 3:
            print(f"  ... 외 {len(readings) - 3}개")
        db.close()
        return

    # Firestore 클라이언트
    firestore_db = firestore.client()
    readings_collection = firestore_db.collection('readings')

    # 마이그레이션
    success_count = 0
    error_count = 0

    for reading in readings:
        try:
            # Reading document
            reading_doc_data = {
                'user_id': str(reading.user_id) if reading.user_id else None,
                'spread_type': reading.spread_type,
                'question': reading.question,
                'category': reading.category,
                'card_relationships': reading.card_relationships,
                'overall_reading': reading.overall_reading,
                'advice': reading.advice,
                'summary': reading.summary,
                'created_at': reading.created_at,
                'updated_at': reading.updated_at,
            }

            # Reading document 생성
            reading_doc_ref = readings_collection.document(str(reading.id))
            reading_doc_ref.set(reading_doc_data)

            # Reading cards subcollection
            cards_ref = reading_doc_ref.collection('reading_cards')

            for reading_card in reading.cards:
                card_data = {
                    'card_id': reading_card.card_id,
                    'position': reading_card.position,
                    'orientation': reading_card.orientation,
                    'interpretation': reading_card.interpretation,
                    'key_message': reading_card.key_message,
                    # Card 정보도 포함 (denormalized)
                    'card': {
                        'id': reading_card.card.id,
                        'name_en': reading_card.card.name,
                        'name_ko': reading_card.card.name_ko,
                        'arcana_type': reading_card.card.arcana_type.value,
                        'suit': reading_card.card.suit.value if reading_card.card.suit else None,
                        'image_url': reading_card.card.image_url,
                    }
                }
                cards_ref.add(card_data)

            success_count += 1
            print(f"  ✓ Reading {reading.id} ({reading.spread_type})")

        except Exception as e:
            error_count += 1
            print(f"  ✗ Reading {reading.id} 실패: {e}")

    db.close()

    print(f"\n리딩 마이그레이션 완료: 성공 {success_count}, 실패 {error_count}")


async def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description='PostgreSQL 데이터를 Firestore로 마이그레이션')
    parser.add_argument('--cards', action='store_true', help='카드 데이터 마이그레이션')
    parser.add_argument('--readings', action='store_true', help='리딩 데이터 마이그레이션')
    parser.add_argument('--all', action='store_true', help='전체 데이터 마이그레이션')
    parser.add_argument('--dry-run', action='store_true', help='실제 쓰기 없이 테스트만 수행')
    parser.add_argument('--limit', type=int, help='리딩 마이그레이션 개수 제한')

    args = parser.parse_args()

    # 옵션이 하나도 없으면 도움말 출력
    if not (args.cards or args.readings or args.all):
        parser.print_help()
        return

    try:
        # Firebase Admin 초기화
        print("Firebase Admin SDK 초기화 중...")
        initialize_firebase_admin()
        print("✓ Firebase Admin SDK 초기화 완료")

        # 마이그레이션 실행
        if args.all or args.cards:
            await migrate_cards(dry_run=args.dry_run)

        if args.all or args.readings:
            await migrate_readings(dry_run=args.dry_run, limit=args.limit)

        print("\n✓ 마이그레이션 완료!")

    except Exception as e:
        print(f"\n✗ 마이그레이션 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
