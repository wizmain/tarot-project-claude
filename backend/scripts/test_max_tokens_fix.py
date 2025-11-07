#!/usr/bin/env python3
"""
max_tokens 증가 수정이 제대로 작동하는지 테스트
- 원카드 리딩을 생성하여 응답이 완전한지 확인
- LLM 로그가 기록되는지 확인
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.database.factory import get_database_provider


async def test_new_reading():
    """새로 생성된 리딩 확인"""
    provider = get_database_provider()

    print("=" * 80)
    print("테스트: 최근 리딩 LLM 로그 확인")
    print("=" * 80)
    print("\n💡 프론트엔드나 API를 통해 새로운 리딩을 생성한 후,")
    print("   이 스크립트를 다시 실행하여 LLM 로그를 확인하세요.\n")

    # Get the most recent reading
    readings_list = provider.db.collection('readings').order_by(
        'created_at', direction='DESCENDING'
    ).limit(1).get()

    if not readings_list:
        print("❌ 리딩이 없습니다.")
        return

    doc = list(readings_list)[0]
    data = doc.to_dict()

    print(f"📖 최근 리딩: {doc.id}")
    print(f"   Question: {data.get('question')}")
    print(f"   Spread: {data.get('spread_type')}")
    print(f"   Created: {data.get('created_at')}")
    print(f"   Summary: {data.get('summary', '')[:80]}...")

    # Check completeness
    has_summary = bool(data.get('summary'))
    has_advice = bool(data.get('advice'))
    has_overall = bool(data.get('overall_reading'))

    print(f"\n✅ 응답 완전성 체크:")
    print(f"   - summary: {'✓' if has_summary else '✗'}")
    print(f"   - advice: {'✓' if has_advice else '✗'}")
    print(f"   - overall_reading: {'✓' if has_overall else '✗'}")

    if has_advice:
        advice = data.get('advice', {})
        print(f"\n📝 Advice 상세:")
        for key in ['immediate_action', 'short_term', 'long_term', 'mindset', 'cautions']:
            value = advice.get(key, '')
            status = '✓' if value else '✗'
            preview = value[:50] + '...' if len(value) > 50 else value
            print(f"   {status} {key}: {preview}")

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
            print(f"       Tokens: {log.get('total_tokens', 0):,} = {log.get('prompt_tokens', 0):,} + {log.get('completion_tokens', 0):,}")
            print(f"       Cost: ${log.get('estimated_cost', 0):.6f}")
            print(f"       Latency: {log.get('latency_seconds', 0):.2f}s")
    else:
        print(f"   ❌ 로그 없음 (이전에 생성된 리딩일 수 있음)")

    print("\n" + "=" * 80)
    if llm_usage and has_summary and has_advice and has_overall:
        print("✅ 모든 테스트 통과!")
        print("   - 응답이 완전함")
        print("   - LLM 로그가 기록됨")
    elif not llm_usage:
        print("⚠️  LLM 로그가 없습니다.")
        print("   새로운 리딩을 생성하여 다시 테스트하세요.")
    else:
        print("⚠️  일부 데이터가 누락되었습니다.")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_new_reading())
