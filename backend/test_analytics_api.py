"""
Test script for Analytics API endpoints

This script tests the three analytics endpoints:
1. /api/v1/analytics/llm-usage/summary
2. /api/v1/analytics/llm-usage/daily-trend
3. /api/v1/analytics/llm-usage/recent
"""
import requests
import json

BASE_URL = "http://localhost:8000"

# First, we need to authenticate to get a token
# For testing, let's try to access without auth first to see the error
print("=" * 60)
print("Testing Analytics API Endpoints")
print("=" * 60)

# Test 1: Summary endpoint
print("\n1. Testing /api/v1/analytics/llm-usage/summary")
print("-" * 60)
try:
    response = requests.get(f"{BASE_URL}/api/v1/analytics/llm-usage/summary?days=30")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: Daily trend endpoint
print("\n2. Testing /api/v1/analytics/llm-usage/daily-trend")
print("-" * 60)
try:
    response = requests.get(f"{BASE_URL}/api/v1/analytics/llm-usage/daily-trend?days=7")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2, default=str))
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Error: {e}")

# Test 3: Recent logs endpoint
print("\n3. Testing /api/v1/analytics/llm-usage/recent")
print("-" * 60)
try:
    response = requests.get(f"{BASE_URL}/api/v1/analytics/llm-usage/recent?page=1&page_size=10")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Total logs: {data.get('total', 0)}")
        print(f"Page: {data.get('page', 0)}")
        print(f"Page size: {data.get('page_size', 0)}")
        print(f"Number of logs returned: {len(data.get('logs', []))}")
        if data.get('logs'):
            print("\nFirst log entry:")
            print(json.dumps(data['logs'][0], indent=2, default=str))
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("Test completed")
print("=" * 60)
