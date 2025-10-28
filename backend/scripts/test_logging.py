"""
Test logging configuration
"""
import sys
from pathlib import Path
import time

# Add parent directory to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.core.logging import setup_logging, get_logger, log_with_context


def test_basic_logging():
    """Test basic logging functionality"""
    print("=" * 60)
    print("Testing Basic Logging")
    print("=" * 60)

    logger = get_logger(__name__)

    print("\n--- Testing different log levels ---")

    # Debug
    logger.debug("This is a DEBUG message")

    # Info
    logger.info("This is an INFO message")

    # Warning
    logger.warning("This is a WARNING message")

    # Error
    logger.error("This is an ERROR message")

    # Critical
    logger.critical("This is a CRITICAL message")

    print("\n✅ Basic logging test completed")


def test_exception_logging():
    """Test exception logging"""
    print("\n" + "=" * 60)
    print("Testing Exception Logging")
    print("=" * 60)

    logger = get_logger(__name__)

    try:
        # Intentionally cause an error
        result = 1 / 0
    except ZeroDivisionError:
        logger.exception("Caught a division by zero error")

    print("\n✅ Exception logging test completed")


def test_context_logging():
    """Test logging with context"""
    print("\n" + "=" * 60)
    print("Testing Context Logging")
    print("=" * 60)

    logger = get_logger(__name__)

    # Log with additional context
    log_with_context(
        logger,
        "info",
        "User performed an action",
        user_id=12345,
        action="login",
        ip_address="192.168.1.100",
        timestamp=time.time()
    )

    log_with_context(
        logger,
        "warning",
        "Unusual activity detected",
        user_id=67890,
        reason="multiple_failed_attempts",
        count=5
    )

    print("\n✅ Context logging test completed")


def test_module_logging():
    """Test logging from different modules"""
    print("\n" + "=" * 60)
    print("Testing Module Logging")
    print("=" * 60)

    # Create loggers for different modules
    api_logger = get_logger("api.endpoints")
    db_logger = get_logger("database.queries")
    ai_logger = get_logger("ai.providers")

    api_logger.info("Processing API request to /api/v1/readings")
    db_logger.debug("Executing SELECT query on cards table")
    ai_logger.warning("AI provider response time exceeded threshold")

    print("\n✅ Module logging test completed")


def test_file_logging():
    """Test that logs are written to files"""
    print("\n" + "=" * 60)
    print("Testing File Logging")
    print("=" * 60)

    logger = get_logger(__name__)

    # Write different levels
    logger.info("This should be in app.log")
    logger.warning("This should be in both app.log and app.json.log")
    logger.error("This should be in both files")

    # Check if log files exist
    log_dir = Path("logs")
    app_log = log_dir / "app.log"
    json_log = log_dir / "app.json.log"

    if app_log.exists():
        print(f"✅ app.log exists ({app_log.stat().st_size} bytes)")
    else:
        print("❌ app.log not found")

    if json_log.exists():
        print(f"✅ app.json.log exists ({json_log.stat().st_size} bytes)")
    else:
        print("❌ app.json.log not found")

    print("\n✅ File logging test completed")


def display_log_samples():
    """Display sample log content"""
    print("\n" + "=" * 60)
    print("Sample Log Content")
    print("=" * 60)

    log_dir = Path("logs")

    # Show last 5 lines of app.log
    app_log = log_dir / "app.log"
    if app_log.exists():
        print("\n--- Last 5 lines of app.log ---")
        with open(app_log, "r") as f:
            lines = f.readlines()
            for line in lines[-5:]:
                print(line.rstrip())

    # Show last 2 lines of app.json.log
    json_log = log_dir / "app.json.log"
    if json_log.exists():
        print("\n--- Last 2 lines of app.json.log ---")
        with open(json_log, "r") as f:
            lines = f.readlines()
            for line in lines[-2:]:
                print(line.rstrip())


if __name__ == "__main__":
    # Initialize logging
    setup_logging()

    print("\n🚀 Starting Logging System Tests\n")

    # Run tests
    test_basic_logging()
    test_exception_logging()
    test_context_logging()
    test_module_logging()
    test_file_logging()
    display_log_samples()

    print("\n" + "=" * 60)
    print("✅ All logging tests completed!")
    print("=" * 60)
    print("\nLog files location: logs/")
    print("  - logs/app.log      (INFO level, rotated at 10MB)")
    print("  - logs/app.json.log (WARNING level, JSON format)")
    print("\n")
