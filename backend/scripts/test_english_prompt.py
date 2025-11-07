#!/usr/bin/env python3
"""
Test English Prompt vs Korean Prompt
영어 프롬프트와 한국어 프롬프트의 토큰 사용량 및 품질 비교
"""
import asyncio
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ai import GenerationConfig
from src.core.card_shuffle import CardShuffleService, DrawnCard
from src.ai.prompt_engine.context_builder import ContextBuilder
from src.database.factory import get_database_provider
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

# Import get_orchestrator from readings_stream
from src.api.routes.readings_stream import get_orchestrator


PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
jinja_env = Environment(loader=FileSystemLoader(str(PROMPTS_DIR)))


async def test_prompt_comparison():
    """영어 vs 한국어 프롬프트 비교"""

    # Setup
    db_provider = get_database_provider()
    shuffle_service = CardShuffleService()

    # Draw one card
    drawn_cards = await shuffle_service.draw_cards(count=1, provider=db_provider)
    card_context = ContextBuilder.build_card_context(drawn_cards[0])

    question = "새로운 프로젝트를 시작하는 것에 대해 조언을 구합니다"

    # Prepare context
    prompt_context = {
        "question": question,
        "category": "career",
        "card": card_context,
        "rag_context": None,
    }

    print("=" * 80)
    print("테스트 카드:", card_context["name"], f"({card_context['orientation_korean']})")
    print("질문:", question)
    print("=" * 80)

    # Test 1: Korean Prompt
    print("\n[1] 한국어 프롬프트 테스트")
    print("-" * 80)

    ko_template = jinja_env.get_template("reading/one_card.txt")
    ko_prompt = ko_template.render(**prompt_context)

    print(f"프롬프트 길이: {len(ko_prompt)} 문자")
    print(f"프롬프트 첫 200자:")
    print(ko_prompt[:200])
    print("...")

    orchestrator = get_orchestrator()

    ko_result = await orchestrator.generate(
        prompt=ko_prompt,
        system_prompt="당신은 전문 타로 리더입니다.",
        config=GenerationConfig(
            max_tokens=1500,
            temperature=0.7,
            timeout=60,
        )
    )

    ko_resp = ko_result.response
    print(f"\n결과:")
    print(f"  Provider: {ko_resp.provider}")
    print(f"  Model: {ko_resp.model}")
    print(f"  Prompt Tokens: {ko_resp.prompt_tokens:,}")
    print(f"  Completion Tokens: {ko_resp.completion_tokens:,}")
    print(f"  Total Tokens: {ko_resp.total_tokens:,}")
    print(f"  Estimated Cost: ${ko_resp.estimated_cost:.6f}")
    print(f"  Latency: {ko_resp.latency_ms/1000:.2f}s")

    # Test 2: English Prompt
    print("\n[2] 영어 프롬프트 테스트")
    print("-" * 80)

    en_template = jinja_env.get_template("reading/one_card_en.txt")
    en_prompt = en_template.render(**prompt_context)

    print(f"프롬프트 길이: {len(en_prompt)} 문자")
    print(f"프롬프트 첫 200자:")
    print(en_prompt[:200])
    print("...")

    en_result = await orchestrator.generate(
        prompt=en_prompt,
        system_prompt="You are a professional tarot reader.",
        config=GenerationConfig(
            max_tokens=1500,
            temperature=0.7,
            timeout=60,
        )
    )

    en_resp = en_result.response
    print(f"\n결과:")
    print(f"  Provider: {en_resp.provider}")
    print(f"  Model: {en_resp.model}")
    print(f"  Prompt Tokens: {en_resp.prompt_tokens:,}")
    print(f"  Completion Tokens: {en_resp.completion_tokens:,}")
    print(f"  Total Tokens: {en_resp.total_tokens:,}")
    print(f"  Estimated Cost: ${en_resp.estimated_cost:.6f}")
    print(f"  Latency: {en_resp.latency_ms/1000:.2f}s")

    # Comparison
    print("\n" + "=" * 80)
    print("비교 결과")
    print("=" * 80)

    prompt_token_diff = ko_resp.prompt_tokens - en_resp.prompt_tokens
    prompt_token_pct = (prompt_token_diff / ko_resp.prompt_tokens) * 100

    total_token_diff = ko_resp.total_tokens - en_resp.total_tokens
    total_token_pct = (total_token_diff / ko_resp.total_tokens) * 100

    cost_diff = ko_resp.estimated_cost - en_resp.estimated_cost
    cost_pct = (cost_diff / ko_resp.estimated_cost) * 100

    print(f"\n프롬프트 토큰:")
    print(f"  한국어: {ko_resp.prompt_tokens:,}")
    print(f"  영어:   {en_resp.prompt_tokens:,}")
    print(f"  절감:   {prompt_token_diff:,} ({prompt_token_pct:.1f}%)")

    print(f"\n총 토큰:")
    print(f"  한국어: {ko_resp.total_tokens:,}")
    print(f"  영어:   {en_resp.total_tokens:,}")
    print(f"  절감:   {total_token_diff:,} ({total_token_pct:.1f}%)")

    print(f"\n비용:")
    print(f"  한국어: ${ko_resp.estimated_cost:.6f}")
    print(f"  영어:   ${en_resp.estimated_cost:.6f}")
    print(f"  절감:   ${cost_diff:.6f} ({cost_pct:.1f}%)")

    print(f"\n응답 미리보기 (영어 프롬프트):")
    print("-" * 80)
    print(en_resp.content[:500])
    print("...")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(test_prompt_comparison())
