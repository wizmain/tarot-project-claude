"""
Test SSE Streaming Endpoint

Tests the /api/v1/readings/stream endpoint to verify SSE functionality
"""
import asyncio
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from src.core.config import settings


async def test_sse_streaming():
    """Test SSE streaming with a simple reading request (no auth)"""

    api_base = "http://localhost:8000"
    api_v1 = "/api/v1"

    async with httpx.AsyncClient(base_url=api_base) as client:
        # Test SSE streaming (no authentication required for test endpoint)
        print("🌊 Starting SSE streaming test...")
        print("=" * 60)

        reading_request = {
            "spread_type": "one_card",
            "question": "SSE 스트리밍 테스트를 위한 간단한 질문입니다.",
            "category": "personal_growth"
        }

        stream_url = f"{api_v1}/readings/stream/test"
        headers = {
            "Accept": "text/event-stream"
        }

        print(f"📡 Connecting to: {stream_url}")
        print(f"📦 Request: {json.dumps(reading_request, ensure_ascii=False)}")
        print("=" * 60)
        print()

        event_count = 0

        async with client.stream(
            "POST",
            stream_url,
            json=reading_request,
            headers=headers,
            timeout=120.0
        ) as response:
            if response.status_code != 200:
                print(f"❌ Stream failed: {response.status_code}")
                print(await response.aread())
                return

            current_event = None

            async for line in response.aiter_lines():
                if not line:
                    continue

                if line.startswith("event:"):
                    current_event = line[6:].strip()
                    event_count += 1
                    print(f"\n[Event #{event_count}] {current_event}")
                    print("-" * 60)

                elif line.startswith("data:"):
                    data_str = line[5:].strip()
                    try:
                        data = json.loads(data_str)
                        # Pretty print the data
                        print(json.dumps(data, indent=2, ensure_ascii=False))
                    except json.JSONDecodeError:
                        print(data_str)

        print("\n" + "=" * 60)
        print(f"✅ SSE stream completed successfully!")
        print(f"📊 Total events received: {event_count}")
        print("=" * 60)


if __name__ == "__main__":
    print("🚀 SSE Streaming Test")
    print("=" * 60)
    print()

    try:
        asyncio.run(test_sse_streaming())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
