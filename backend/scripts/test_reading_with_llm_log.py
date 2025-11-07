#!/usr/bin/env python3
"""
새로운 리딩을 생성하고 LLM 로그가 기록되는지 확인하는 테스트 스크립트
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.database.factory import get_database_provider


async def check_recent_reading_with_llm_log():
    """가장 최근 리딩의 LLM 로그 확인"""
    provider = get_database_provider()

    # Get the most recent reading
    readings_list = provider.db.collection('readings').order_by('created_at', direction='DESCENDING').limit(1).get()

    if not readings_list:
        print("❌ 리딩이 없습니다.")
        return

    doc = list(readings_list)[0]
    data = doc.to_dict()

    print('=' * 80)
    print(f'최근 리딩 확인: {doc.id}')
    print('=' * 80)
    print(f'Question: {data.get("question")}')
    print(f'Spread Type: {data.get("spread_type")}')
    print(f'Created At: {data.get("created_at")}')
    print(f'Summary: {data.get("summary", "")[:100]}...')

    # Check LLM usage
    llm_usage = data.get('llm_usage', [])

    if llm_usage:
        print(f'\n✅ LLM Usage 로그 발견! ({len(llm_usage)}개)')
        print('=' * 80)

        total_cost = sum(log.get('estimated_cost', 0) for log in llm_usage)
        total_tokens = sum(log.get('total_tokens', 0) for log in llm_usage)

        print(f'\n📊 전체 요약:')
        print(f'   시도 횟수: {len(llm_usage)}')
        print(f'   총 토큰: {total_tokens:,}')
        print(f'   총 비용: ${total_cost:.6f}')

        print(f'\n📝 상세 로그:')
        for idx, log in enumerate(llm_usage, 1):
            print(f'\n   [{idx}] {log.get("purpose", "unknown").upper()}')
            print(f'       Provider: {log.get("provider")}')
            print(f'       Model: {log.get("model")}')
            print(f'       Prompt Tokens: {log.get("prompt_tokens", 0):,}')
            print(f'       Completion Tokens: {log.get("completion_tokens", 0):,}')
            print(f'       Total Tokens: {log.get("total_tokens", 0):,}')
            print(f'       Cost: ${log.get("estimated_cost", 0):.6f}')
            print(f'       Latency: {log.get("latency_seconds", 0):.2f}s')
            print(f'       Created At: {log.get("created_at")}')
    else:
        print(f'\n❌ LLM Usage 로그 없음')
        print('\n💡 이 리딩은 LLM 로그 기능이 추가되기 전에 생성된 것 같습니다.')
        print('   새로운 리딩을 생성하면 LLM 로그가 기록됩니다.')


if __name__ == "__main__":
    asyncio.run(check_recent_reading_with_llm_log())
