"""
Test script for SSE streaming endpoint

This script tests the Server-Sent Events streaming endpoint for tarot readings.
"""
import sys
import json
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from src.core.logging import get_logger

logger = get_logger(__name__)


def test_sse_stream():
    """Test SSE streaming endpoint"""
    print("\n" + "=" * 70)
    print("SSE Streaming Endpoint Test")
    print("=" * 70 + "\n")

    # First, we need to authenticate to get a token
    print("1. Authenticating...")

    # For testing purposes, we'll use the guest account or create a test user
    # Note: This assumes you have authentication set up
    auth_response = requests.post(
        "http://localhost:8000/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "test123"
        }
    )

    if auth_response.status_code != 200:
        print("   ⚠️  Authentication failed. Creating test user...")
        # Try to register first
        register_response = requests.post(
            "http://localhost:8000/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "test123",
                "name": "Test User"
            }
        )
        if register_response.status_code == 201:
            print("   ✓ Test user created")
            # Try login again
            auth_response = requests.post(
                "http://localhost:8000/api/v1/auth/login",
                json={
                    "email": "test@example.com",
                    "password": "test123"
                }
            )
        else:
            print("   ✗ Could not create test user")
            print(f"   Response: {register_response.text}")
            return

    if auth_response.status_code == 200:
        auth_data = auth_response.json()
        token = auth_data.get("access_token")
        print(f"   ✓ Authenticated successfully\n")
    else:
        print(f"   ✗ Authentication failed: {auth_response.text}")
        return

    # Test SSE streaming
    print("2. Starting SSE stream...")
    print("   Endpoint: POST /api/v1/readings/stream")
    print("   Content-Type: text/event-stream\n")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }

    payload = {
        "spread_type": "one_card",
        "question": "오늘의 운세는 어떤가요?",
        "category": "general"
    }

    start_time = time.time()

    try:
        response = requests.post(
            "http://localhost:8000/api/v1/readings/stream",
            json=payload,
            headers=headers,
            stream=True,  # Enable streaming
            timeout=60
        )

        if response.status_code != 200:
            print(f"   ✗ Request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return

        print("3. Receiving SSE events:\n")
        print("-" * 70)

        event_count = 0
        current_event = None

        for line in response.iter_lines():
            if not line:
                continue

            line = line.decode('utf-8')

            if line.startswith('event:'):
                current_event = line.split(':', 1)[1].strip()
                event_count += 1

            elif line.startswith('data:'):
                data = line.split(':', 1)[1].strip()
                try:
                    data_json = json.loads(data)
                    elapsed = time.time() - start_time

                    # Pretty print based on event type
                    if current_event == 'progress':
                        progress = data_json.get('progress', 0)
                        message = data_json.get('message', '')
                        stage = data_json.get('stage', '')
                        print(f"[{elapsed:5.1f}s] [{progress:3d}%] {stage}: {message}")

                    elif current_event == 'card_drawn':
                        card_name = data_json.get('card_name_ko', '')
                        position = data_json.get('position', '')
                        is_reversed = data_json.get('is_reversed', False)
                        orientation = "역방향" if is_reversed else "정방향"
                        print(f"[{elapsed:5.1f}s] 🎴 {position}: {card_name} ({orientation})")

                    elif current_event == 'rag_enrichment':
                        cards_enriched = data_json.get('cards_enriched', 0)
                        print(f"[{elapsed:5.1f}s] 📚 RAG: {cards_enriched}개 카드 지식 로드 완료")

                    elif current_event == 'ai_generation':
                        provider = data_json.get('provider', '')
                        model = data_json.get('model', '')
                        print(f"[{elapsed:5.1f}s] 🤖 AI: {provider}/{model}")

                    elif current_event == 'complete':
                        reading_id = data_json.get('reading_id', '')
                        total_time = data_json.get('total_time', 0)
                        print(f"[{elapsed:5.1f}s] ✅ 완료: reading_id={reading_id}, 소요시간={total_time}s")

                    elif current_event == 'error':
                        error_type = data_json.get('error_type', '')
                        message = data_json.get('message', '')
                        print(f"[{elapsed:5.1f}s] ❌ 오류: {error_type} - {message}")

                except json.JSONDecodeError:
                    print(f"[{elapsed:5.1f}s] {current_event}: {data}")

        print("-" * 70)
        print(f"\n4. Stream completed")
        print(f"   Total events: {event_count}")
        print(f"   Total time: {time.time() - start_time:.2f}s")

    except requests.exceptions.Timeout:
        print("   ✗ Request timed out")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    print("\n" + "=" * 70)
    print("Test Complete")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    test_sse_stream()
