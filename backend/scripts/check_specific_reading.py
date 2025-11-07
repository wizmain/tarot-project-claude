#!/usr/bin/env python3
"""
특정 리딩 ID의 상세 정보 확인
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.database.factory import get_database_provider


async def check_reading(reading_id: str):
    """특정 리딩의 상세 정보 확인"""
    provider = get_database_provider()

    print("=" * 80)
    print(f"리딩 ID: {reading_id}")
    print("=" * 80)

    # Get the specific reading
    doc = provider.db.collection('readings').document(reading_id).get()

    if not doc.exists:
        print("❌ 리딩을 찾을 수 없습니다.")
        return

    data = doc.to_dict()

    print(f"\n📖 리딩 정보:")
    print(f"   Question: {data.get('question')}")
    print(f"   Spread: {data.get('spread_type')}")
    print(f"   Category: {data.get('category')}")
    print(f"   User ID: {data.get('user_id')}")
    print(f"   Created: {data.get('created_at')}")

    # Check completeness
    has_summary = bool(data.get('summary'))
    has_advice = bool(data.get('advice'))
    has_overall = bool(data.get('overall_reading'))
    has_cards = bool(data.get('cards'))

    # Check subcollection for cards (Firestore structure)
    cards_subcollection = provider.db.collection('readings').document(reading_id).collection('reading_cards').stream()
    cards_from_subcollection = [card.to_dict() for card in cards_subcollection]

    if cards_from_subcollection:
        has_cards = True

    print(f"\n✅ 응답 완전성:")
    print(f"   - summary: {'✓' if has_summary else '✗'}")
    print(f"   - cards: {'✓' if has_cards else '✗'}")
    print(f"   - overall_reading: {'✓' if has_overall else '✗'}")
    print(f"   - advice: {'✓' if has_advice else '✗'}")

    if cards_from_subcollection:
        print(f"\n📇 카드 정보: (서브컬렉션)")
        for i, card in enumerate(sorted(cards_from_subcollection, key=lambda x: x.get('order_index', 0)), 1):
            card_info = card.get('card', {})
            print(f"   [{i}] {card_info.get('name_ko', 'Unknown')} ({card.get('orientation', 'unknown')})")
            interpretation = card.get('interpretation', '')
            print(f"       Interpretation length: {len(interpretation)} chars")
            print(f"       Key message: {card.get('key_message', '')[:60]}...")
    elif has_cards:
        cards = data.get('cards', [])
        print(f"\n📇 카드 정보:")
        for i, card in enumerate(cards, 1):
            print(f"   [{i}] {card.get('card', {}).get('name_ko')} ({card.get('orientation')})")
            interpretation = card.get('interpretation', '')
            print(f"       Interpretation length: {len(interpretation)} chars")
            print(f"       Key message: {card.get('key_message', '')[:60]}...")

    if has_advice:
        advice = data.get('advice', {})
        print(f"\n📝 Advice:")
        for key in ['immediate_action', 'short_term', 'long_term', 'mindset', 'cautions']:
            value = advice.get(key, '')
            status = '✓' if value else '✗'
            print(f"   {status} {key}: {len(value)} chars")

    # Check LLM usage
    llm_usage = data.get('llm_usage', [])

    print(f"\n📊 LLM Usage 로그:")
    if llm_usage:
        print(f"   ✅ {len(llm_usage)}개의 로그 발견!")

        total_tokens = sum(log.get('total_tokens', 0) for log in llm_usage)
        total_cost = sum(log.get('estimated_cost', 0) for log in llm_usage)

        print(f"\n   전체 요약:")
        print(f"   - 시도 횟수: {len(llm_usage)}")
        print(f"   - 총 토큰: {total_tokens:,}")
        print(f"   - 총 비용: ${total_cost:.6f}")

        for idx, log in enumerate(llm_usage, 1):
            print(f"\n   [{idx}] {log.get('purpose', 'unknown').upper()}")
            print(f"       Provider: {log.get('provider')}")
            print(f"       Model: {log.get('model')}")
            print(f"       Tokens: {log.get('total_tokens', 0):,} = {log.get('prompt_tokens', 0):,} (prompt) + {log.get('completion_tokens', 0):,} (completion)")
            print(f"       Cost: ${log.get('estimated_cost', 0):.6f}")
            print(f"       Latency: {log.get('latency_seconds', 0):.2f}s")

            # Check finish_reason
            finish_reason = log.get('finish_reason', 'unknown')
            if finish_reason in ['max_tokens', 'length']:
                print(f"       ⚠️  Finish Reason: {finish_reason} (응답이 잘렸을 수 있음)")
            else:
                print(f"       Finish Reason: {finish_reason}")
    else:
        print(f"   ❌ 로그 없음")
        print(f"\n   🔍 가능한 원인:")
        print(f"   1. LLM 로깅 기능이 추가되기 전에 생성된 리딩")
        print(f"   2. 백엔드 코드가 업데이트되지 않은 상태에서 생성")
        print(f"   3. 리딩 생성 중 오류 발생")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_specific_reading.py <reading_id>")
        sys.exit(1)

    reading_id = sys.argv[1]
    asyncio.run(check_reading(reading_id))
