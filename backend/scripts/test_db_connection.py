"""
Test database connection script
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text
from src.core.database import engine
from src.core.config import settings


def test_connection():
    """Test database connection"""
    print("Testing database connection...")
    print(f"Database URL: {settings.DATABASE_URL}")

    try:
        # Try to connect and execute a simple query
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Connection successful!")
            print(f"PostgreSQL version: {version}")

            # Test if we can query the database
            result = connection.execute(text("SELECT current_database()"))
            db_name = result.fetchone()[0]
            print(f"Connected to database: {db_name}")

        return True

    except Exception as e:
        print(f"❌ Connection failed!")
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
