"""
Test Redis connection and cache functionality
"""
import sys
from pathlib import Path
import time

# Add parent directory to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.core.cache import cache, cached
from src.core.config import settings


def test_connection():
    """Test Redis connection"""
    print("Testing Redis connection...")
    print(f"Redis URL: {settings.REDIS_URL}")

    try:
        # Test ping
        if cache.ping():
            print("✅ Redis PING successful!")
        else:
            print("❌ Redis PING failed!")
            return False

        return True

    except Exception as e:
        print(f"❌ Connection failed!")
        print(f"Error: {e}")
        return False


def test_basic_operations():
    """Test basic cache operations"""
    print("\n--- Testing Basic Cache Operations ---")

    # Test SET and GET
    print("\n1. Testing SET and GET...")
    test_key = "test:key"
    test_value = {"message": "Hello Redis!", "number": 42}

    if cache.set(test_key, test_value):
        print(f"✅ SET successful: {test_key}")
    else:
        print(f"❌ SET failed: {test_key}")
        return False

    retrieved = cache.get(test_key)
    if retrieved == test_value:
        print(f"✅ GET successful: {retrieved}")
    else:
        print(f"❌ GET failed. Expected: {test_value}, Got: {retrieved}")
        return False

    # Test EXISTS
    print("\n2. Testing EXISTS...")
    if cache.exists(test_key):
        print(f"✅ EXISTS successful: {test_key} exists")
    else:
        print(f"❌ EXISTS failed: {test_key} should exist")
        return False

    # Test DELETE
    print("\n3. Testing DELETE...")
    if cache.delete(test_key):
        print(f"✅ DELETE successful: {test_key}")
    else:
        print(f"❌ DELETE failed: {test_key}")
        return False

    if not cache.exists(test_key):
        print(f"✅ Confirmed: {test_key} no longer exists")
    else:
        print(f"❌ DELETE verification failed: {test_key} still exists")
        return False

    # Test TTL
    print("\n4. Testing TTL (Time To Live)...")
    ttl_key = "test:ttl"
    ttl_value = "expires in 2 seconds"

    if cache.set(ttl_key, ttl_value, ttl=2):
        print(f"✅ SET with TTL successful: {ttl_key}")
    else:
        print(f"❌ SET with TTL failed: {ttl_key}")
        return False

    print("Waiting 3 seconds for key to expire...")
    time.sleep(3)

    if not cache.exists(ttl_key):
        print(f"✅ TTL worked: {ttl_key} expired")
    else:
        print(f"❌ TTL failed: {ttl_key} still exists")
        return False

    return True


def test_decorator():
    """Test cache decorator"""
    print("\n--- Testing Cache Decorator ---")

    call_count = 0

    @cached(ttl=60, key_prefix="test_func")
    def expensive_function(x: int, y: int) -> int:
        """Simulate an expensive operation"""
        nonlocal call_count
        call_count += 1
        time.sleep(0.1)  # Simulate slow operation
        return x + y

    # First call - should execute function
    print("\n1. First call (should execute function)...")
    start = time.time()
    result1 = expensive_function(10, 20)
    duration1 = time.time() - start
    print(f"Result: {result1}, Duration: {duration1:.3f}s, Calls: {call_count}")

    if call_count == 1 and result1 == 30:
        print("✅ First call successful")
    else:
        print("❌ First call failed")
        return False

    # Second call - should use cache
    print("\n2. Second call (should use cache)...")
    start = time.time()
    result2 = expensive_function(10, 20)
    duration2 = time.time() - start
    print(f"Result: {result2}, Duration: {duration2:.3f}s, Calls: {call_count}")

    if call_count == 1 and result2 == 30 and duration2 < duration1:
        print("✅ Cache hit successful (faster than first call)")
    else:
        print("❌ Cache hit failed")
        return False

    # Different arguments - should execute function again
    print("\n3. Different arguments (should execute function)...")
    start = time.time()
    result3 = expensive_function(5, 15)
    duration3 = time.time() - start
    print(f"Result: {result3}, Duration: {duration3:.3f}s, Calls: {call_count}")

    if call_count == 2 and result3 == 20:
        print("✅ New arguments triggered function call")
    else:
        print("❌ New arguments test failed")
        return False

    return True


def test_pattern_deletion():
    """Test pattern-based deletion"""
    print("\n--- Testing Pattern Deletion ---")

    # Create multiple keys with same prefix
    keys = ["user:1", "user:2", "user:3", "other:1"]
    for key in keys:
        cache.set(key, f"value_{key}")

    print(f"Created keys: {keys}")

    # Delete all user:* keys
    deleted = cache.clear_pattern("user:*")
    print(f"Deleted {deleted} keys matching 'user:*'")

    # Verify
    user_keys_exist = any(cache.exists(k) for k in keys[:3])
    other_key_exists = cache.exists("other:1")

    if not user_keys_exist and other_key_exists:
        print("✅ Pattern deletion successful")
        cache.delete("other:1")  # Cleanup
        return True
    else:
        print("❌ Pattern deletion failed")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Redis Connection and Cache Functionality Test")
    print("=" * 60)

    all_passed = True

    # Run tests
    all_passed &= test_connection()
    all_passed &= test_basic_operations()
    all_passed &= test_decorator()
    all_passed &= test_pattern_deletion()

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All tests passed!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        print("=" * 60)
        sys.exit(1)
