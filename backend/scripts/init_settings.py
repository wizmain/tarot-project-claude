"""
Firestore Settings 초기화 스크립트

이 스크립트의 목적:
- Firestore에 settings 컬렉션이 있는지 확인
- 없으면 기본 설정으로 초기화
- 관리자 이메일을 환경 변수 또는 명령줄 인자로 설정
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.firebase_admin import initialize_firebase_admin
from src.database.factory import get_database_provider
from src.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


async def check_and_init_settings(admin_email: str = None):
    """
    Settings 컬렉션 확인 및 초기화
    
    Args:
        admin_email: 초기 관리자 이메일 (선택사항)
    """
    try:
        # Initialize Firebase
        initialize_firebase_admin()
        logger.info("Firebase initialized")
        
        # Get database provider
        db_provider = get_database_provider()
        logger.info("Database provider initialized")
        
        # Check if settings exist
        settings = await db_provider.get_app_settings()
        
        if settings and settings.get('id') == 'app_settings':
            logger.info("✅ Settings 컬렉션이 이미 존재합니다")
            logger.info(f"   - 관리자 이메일: {settings.get('admin', {}).get('admin_emails', [])}")
            logger.info(f"   - AI Provider 우선순위: {settings.get('ai', {}).get('provider_priority', [])}")
            logger.info(f"   - 마지막 업데이트: {settings.get('updated_at')}")
            
            # Show provider settings (masked)
            providers = settings.get('ai', {}).get('providers', [])
            if providers:
                logger.info(f"   - 설정된 Providers: {len(providers)}개")
                for provider in providers:
                    api_key = provider.get('api_key', '')
                    masked_key = f"{api_key[:7]}***{api_key[-4:]}" if len(api_key) > 10 else "***"
                    logger.info(
                        f"      • {provider.get('name')}: {provider.get('model')} "
                        f"(enabled={provider.get('enabled')}, key={masked_key})"
                    )
            else:
                logger.info("   - 설정된 Providers: 없음")
            
            return True
        
        # Settings don't exist - create default
        logger.warning("⚠️  Settings 컬렉션이 존재하지 않습니다. 초기화를 시작합니다...")
        
        # Get admin email
        if not admin_email:
            admin_email = os.getenv('ADMIN_EMAIL')
        
        if not admin_email:
            logger.error("❌ 관리자 이메일이 제공되지 않았습니다")
            logger.info("사용법: python scripts/init_settings.py your-email@example.com")
            logger.info("또는: ADMIN_EMAIL=your-email@example.com python scripts/init_settings.py")
            return False
        
        # Validate email format
        if '@' not in admin_email:
            logger.error(f"❌ 유효하지 않은 이메일 형식: {admin_email}")
            return False
        
        # Get OpenAI and Anthropic API keys from environment
        openai_key = os.getenv('OPENAI_API_KEY', '')
        anthropic_key = os.getenv('ANTHROPIC_API_KEY', '')
        
        # Create default settings
        default_settings = {
            'id': 'app_settings',
            'admin': {
                'admin_emails': [admin_email]
            },
            'ai': {
                'provider_priority': ['openai', 'anthropic'],
                'providers': [],
                'default_timeout': 30
            }
        }
        
        # Add providers if API keys are available
        if openai_key:
            default_settings['ai']['providers'].append({
                'name': 'openai',
                'api_key': openai_key,
                'model': 'gpt-4o-mini',
                'enabled': True,
                'timeout': 30
            })
            logger.info(f"   - OpenAI Provider 추가됨 (model: gpt-4o-mini)")
        
        if anthropic_key:
            default_settings['ai']['providers'].append({
                'name': 'anthropic',
                'api_key': anthropic_key,
                'model': 'claude-3-5-sonnet-20241022',
                'enabled': True,
                'timeout': 30
            })
            logger.info(f"   - Anthropic Provider 추가됨 (model: claude-3-5-sonnet-20241022)")
        
        # Save to database
        result = await db_provider.update_app_settings(
            default_settings,
            updated_by='system_init'
        )
        
        logger.info("✅ Settings 컬렉션이 성공적으로 생성되었습니다!")
        logger.info(f"   - 관리자 이메일: {admin_email}")
        logger.info(f"   - Providers: {len(default_settings['ai']['providers'])}개")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 오류 발생: {e}", exc_info=True)
        return False


async def main():
    """메인 함수"""
    # Get admin email from command line argument or environment
    admin_email = None
    if len(sys.argv) > 1:
        admin_email = sys.argv[1]
    
    logger.info("=" * 70)
    logger.info("Settings 컬렉션 확인 및 초기화 스크립트")
    logger.info("=" * 70)
    
    success = await check_and_init_settings(admin_email)
    
    logger.info("=" * 70)
    if success:
        logger.info("✅ 완료!")
    else:
        logger.info("❌ 실패!")
    logger.info("=" * 70)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

