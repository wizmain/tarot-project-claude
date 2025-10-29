"""
Firestore Reading Document Backfill Utility

이 스크립트는 기존 Firestore `readings` 문서에서 누락된 필드를 채워
백엔드 응답 직렬화 과정에서 발생하는 KeyError를 방지합니다.

기능:
- top-level 필드(`overall_reading`, `summary`, `advice`, `card_relationships`)의 누락을 기본값으로 채움
- `advice` 딕셔너리의 하위 키를 보장
- `reading_cards` 서브컬렉션 문서에서 `key_message`, `interpretation`, `card` 필드를 보완

사용법:
    GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json \\
    python scripts/backfill_firestore_readings.py

옵션:
    --dry-run   실제 업데이트 없이 변경 예정 사항만 출력
    --limit N   처음 N개의 리딩만 처리 (테스트 용도)
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict

# Ensure backend package is importable when script executed from repo root
CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
import sys

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from firebase_admin import firestore

from src.core.firebase_admin import initialize_firebase_admin

DEFAULT_ADVICE: Dict[str, str] = {
    "immediate_action": "지금은 내면의 목소리에 귀 기울이며 작은 행동부터 시작해보세요.",
    "short_term": "향후 1-2주 동안 자신감을 높이는 실천을 이어가면 도움이 됩니다.",
    "long_term": "장기적으로 꾸준한 자기 성찰과 계획 수정이 긍정적인 변화를 만듭니다.",
    "mindset": "과정을 즐기며 배움의 태도를 유지하세요.",
    "cautions": "성급한 결정은 피하고 충분한 정보를 수집한 뒤 움직이세요.",
}


def ensure_advice(advice: Any) -> Dict[str, str]:
    """Ensure advice dict has all required keys with sensible defaults."""
    if not isinstance(advice, dict):
        advice = {}

    updated = dict(DEFAULT_ADVICE)
    for key, value in advice.items():
        if isinstance(value, str) and value.strip():
            updated[key] = value

    return updated


def ensure_card_payload(card_data: Dict[str, Any]) -> Dict[str, Any]:
    """Fill missing card payload fields with safe defaults."""
    card_data = dict(card_data) if card_data else {}

    if "key_message" not in card_data or not card_data.get("key_message"):
        card_data["key_message"] = "핵심 메시지가 준비되지 않았습니다. 카드의 상징을 참고해보세요."

    if "interpretation" not in card_data or not card_data.get("interpretation"):
        card_data["interpretation"] = (
            "이 카드는 현재 상황과 연결된 중요한 통찰을 전달합니다. "
            "당신의 질문과 연관된 감정과 행동을 다시 한 번 살펴보세요."
        )

    return card_data


def ensure_embedded_card(card_payload: Dict[str, Any], card_id: Any, cards_ref) -> Dict[str, Any]:
    """Ensure `card` field exists by fetching inlined card metadata if possible."""
    if card_payload.get("card"):
        return card_payload

    try:
        card_id_int = int(card_id)
    except (TypeError, ValueError):
        return card_payload

    card_doc = cards_ref.document(str(card_id_int)).get()
    if not card_doc.exists:
        return card_payload

    card_data = card_doc.to_dict() or {}
    card_payload["card"] = {
        "id": card_data.get("id", card_id_int),
        "name_en": card_data.get("name_en") or card_data.get("name"),
        "name_ko": card_data.get("name_ko") or card_data.get("nameKo"),
        "arcana_type": card_data.get("arcana_type"),
        "suit": card_data.get("suit"),
        "image_url": card_data.get("image_url"),
        "keywords_upright": card_data.get("keywords_upright", []),
        "keywords_reversed": card_data.get("keywords_reversed", []),
    }
    return card_payload


def process_reading_doc(doc, cards_collection, dry_run: bool = False) -> Dict[str, Any]:
    """Inspect a single reading document and apply missing-field patches."""
    data = doc.to_dict() or {}
    updates: Dict[str, Any] = {}

    if not data.get("overall_reading"):
        updates["overall_reading"] = data.get("summary") or "리딩 해석이 준비되지 않았습니다."

    if "summary" not in data or not data.get("summary"):
        updates["summary"] = data.get("overall_reading") or "이번 리딩의 핵심은 내면의 목소리를 따르는 것입니다."

    updates["advice"] = ensure_advice(data.get("advice"))

    if "card_relationships" not in data:
        updates["card_relationships"] = None

    card_updates = []
    cards_ref = doc.reference.collection("reading_cards")
    card_docs = list(cards_ref.stream())
    for card_doc in card_docs:
        card_payload = ensure_card_payload(card_doc.to_dict() or {})
        card_payload = ensure_embedded_card(card_payload, card_payload.get("card_id"), cards_collection)
        card_updates.append((card_doc.reference, card_payload))

    if dry_run:
        return {
            "reading_id": doc.id,
            "reading_updates": updates,
            "card_updates": [
                {
                    "card_doc_id": ref.id,
                    "fields": payload,
                }
                for ref, payload in card_updates
            ],
        }

    if updates:
        doc.reference.update(updates)

    for ref, payload in card_updates:
        ref.update(payload)

    return {
        "reading_id": doc.id,
        "reading_updates": updates,
        "card_updates": [
            {
                "card_doc_id": ref.id,
                "updated_fields": payload,
            }
            for ref, payload in card_updates
        ],
    }


def backfill_readings(dry_run: bool = False, limit: int | None = None) -> None:
    initialize_firebase_admin()
    db = firestore.client()
    readings_ref = db.collection("readings")
    cards_ref = db.collection("cards")

    docs_iter = readings_ref.stream()
    processed = 0
    patched = 0

    for doc in docs_iter:
        if limit is not None and processed >= limit:
            break

        result = process_reading_doc(doc, cards_ref, dry_run=dry_run)
        processed += 1

        reading_updates = result.get("reading_updates", {})
        card_updates = result.get("card_updates", [])
        if reading_updates or any(update.get("fields") or update.get("updated_fields") for update in card_updates):
            patched += 1

        print(f"[{doc.id}] updates -> {reading_updates}")
        for card_update in card_updates:
            print(f"  - card[{card_update['card_doc_id']}] updated")

    print(f"\nProcessed readings: {processed}")
    print(f"Patched readings  : {patched}")
    if dry_run:
        print("Dry-run complete (no writes performed).")
    else:
        print("Backfill complete.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill missing reading fields in Firestore.")
    parser.add_argument("--dry-run", action="store_true", help="Print changes without writing to Firestore")
    parser.add_argument("--limit", type=int, default=None, help="Limit the number of readings to process")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    backfill_readings(dry_run=args.dry_run, limit=args.limit)
