# Firebase 마이그레이션 가이드

## 개요

이 프로젝트는 **Provider 패턴**을 사용하여 인증 및 데이터베이스 시스템을 추상화했습니다.
환경 변수만 변경하면 다른 Provider로 쉽게 전환할 수 있습니다.

## 완료된 작업

### ✅ Frontend (100% 완료)

#### 1. Authentication Provider 추상화
- **위치**: `frontend/src/lib/auth/`
- **구조**:
  ```
  AuthProvider (인터페이스)
  ├── FirebaseAuthProvider (Firebase 구현체)
  └── JWTAuthProvider (기존 JWT 구현체)
  ```

#### 2. 주요 파일
- `AuthProvider.interface.ts` - 인증 Provider 인터페이스
- `FirebaseAuthProvider.ts` - Firebase Authentication 구현
- `JWTAuthProvider.ts` - JWT 기반 인증 구현 (기존 시스템)
- `index.ts` - Provider Factory (환경 변수로 선택)
- `firebase.ts` - Firebase 초기화 설정

#### 3. 사용 방법

**Firebase 사용:**
```bash
# frontend/.env.local
NEXT_PUBLIC_AUTH_PROVIDER=firebase
NEXT_PUBLIC_FIREBASE_API_KEY=your-api-key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
# ... 기타 Firebase 설정
```

**기존 JWT 시스템 사용:**
```bash
# frontend/.env.local
NEXT_PUBLIC_AUTH_PROVIDER=jwt
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### ✅ Backend (30% 완료)

#### 1. Database Provider 추상화
- **위치**: `backend/src/database/`
- **구조**:
  ```
  DatabaseProvider (인터페이스)
  ├── PostgreSQLProvider (PostgreSQL 구현체) - TODO
  └── FirestoreProvider (Firestore 구현체) - TODO
  ```

#### 2. 완료된 파일
- `provider.py` - Database Provider 인터페이스 및 데이터 모델
- `factory.py` - Provider Factory
- `__init__.py` - 모듈 export

## 남은 작업

### 🔲 Backend 작업

#### 1. PostgreSQL Provider 구현
**파일**: `backend/src/database/postgresql_provider.py`

```python
from .provider import DatabaseProvider, Card, Reading
from src.core.database import get_db
from src.models.card import Card as CardModel
from src.models.reading import Reading as ReadingModel

class PostgreSQLProvider(DatabaseProvider):
    """PostgreSQL 데이터베이스 Provider"""

    async def get_card_by_id(self, card_id: int) -> Optional[Card]:
        db = next(get_db())
        card_model = db.query(CardModel).filter(CardModel.id == card_id).first()
        if not card_model:
            return None
        return self._model_to_card(card_model)

    # ... 나머지 메서드 구현
```

#### 2. Firestore Provider 구현
**파일**: `backend/src/database/firestore_provider.py`

```python
from firebase_admin import firestore
from .provider import DatabaseProvider, Card, Reading

class FirestoreProvider(DatabaseProvider):
    """Firestore 데이터베이스 Provider"""

    def __init__(self):
        self.db = firestore.client()

    async def get_card_by_id(self, card_id: int) -> Optional[Card]:
        doc = self.db.collection('cards').document(str(card_id)).get()
        if not doc.exists:
            return None
        return self._doc_to_card(doc)

    # ... 나머지 메서드 구현
```

#### 3. Firebase Admin SDK 설정
**파일**: `backend/src/core/firebase_admin.py`

```python
import firebase_admin
from firebase_admin import credentials
from src.core.config import settings

def initialize_firebase_admin():
    """Firebase Admin SDK 초기화"""
    if not firebase_admin._apps:
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
```

#### 4. Firebase 인증 미들웨어
**파일**: `backend/src/api/middleware/firebase_auth.py`

```python
from firebase_admin import auth
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_firebase_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Firebase ID 토큰 검증"""
    try:
        decoded_token = auth.verify_id_token(credentials.credentials)
        return decoded_token['uid']
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
```

#### 5. Config 업데이트
**파일**: `backend/.env`

```bash
# Database Provider 선택
DATABASE_PROVIDER=postgresql  # 또는 firestore

# Firebase Admin SDK
FIREBASE_CREDENTIALS_PATH=/path/to/serviceAccountKey.json
```

**파일**: `backend/src/core/config.py`

```python
class Settings(BaseSettings):
    # ... 기존 설정

    # Database Provider
    DATABASE_PROVIDER: str = "postgresql"  # postgresql | firestore

    # Firebase Admin
    FIREBASE_CREDENTIALS_PATH: Optional[str] = None
```

#### 6. 마이그레이션 스크립트
**파일**: `backend/scripts/migrate_to_firestore.py`

```python
"""PostgreSQL 데이터를 Firestore로 마이그레이션"""
import asyncio
from sqlalchemy.orm import Session
from firebase_admin import firestore
from src.core.database import SessionLocal
from src.models.card import Card
from src.models.reading import Reading as ReadingModel

async def migrate_cards():
    """카드 데이터 마이그레이션"""
    db: Session = SessionLocal()
    firestore_db = firestore.client()

    cards = db.query(Card).all()

    for card in cards:
        doc_data = {
            'id': card.id,
            'name_en': card.name_en,
            'name_ko': card.name_ko,
            'arcana_type': card.arcana_type.value,
            # ... 나머지 필드
        }
        firestore_db.collection('cards').document(str(card.id)).set(doc_data)

    print(f"Migrated {len(cards)} cards")

async def migrate_readings():
    """리딩 데이터 마이그레이션"""
    # 구현...

if __name__ == "__main__":
    asyncio.run(migrate_cards())
    asyncio.run(migrate_readings())
```

## 사용 예시

### Frontend에서 인증 사용

```typescript
import { useAuth } from '@/contexts/AuthContext';

function LoginPage() {
  const { login } = useAuth();

  const handleLogin = async (email: string, password: string) => {
    try {
      await login(email, password);
      // Firebase든 JWT든 동일한 인터페이스로 사용
    } catch (error) {
      console.error(error);
    }
  };
}
```

### Backend에서 Database 사용

```python
from src.database import get_database_provider

# Provider를 가져옵니다 (환경 변수에 따라 PostgreSQL 또는 Firestore)
db_provider = get_database_provider()

# 카드 조회
card = await db_provider.get_card_by_id(1)

# 리딩 생성
reading = await db_provider.create_reading({
    'user_id': user_id,
    'question': question,
    'spread_type': 'three_card',
    # ...
})
```

## 테스트

### Frontend 테스트
```bash
cd frontend
npm run dev

# JWT 모드로 테스트
NEXT_PUBLIC_AUTH_PROVIDER=jwt npm run dev

# Firebase 모드로 테스트
NEXT_PUBLIC_AUTH_PROVIDER=firebase npm run dev
```

### Backend 테스트
```bash
cd backend
source venv/bin/activate

# PostgreSQL 모드로 실행
DATABASE_PROVIDER=postgresql python main.py

# Firestore 모드로 실행
DATABASE_PROVIDER=firestore python main.py
```

## 참고사항

1. **Firebase Service Account Key 필요**
   - Firebase Console → Project Settings → Service accounts
   - "Generate new private key" 클릭
   - JSON 파일 다운로드 후 `backend/` 디렉토리에 저장

2. **Firestore 보안 규칙**
   ```javascript
   rules_version = '2';
   service cloud.firestore {
     match /databases/{database}/documents {
       // Cards는 읽기만 가능
       match /cards/{cardId} {
         allow read: if true;
         allow write: if false;
       }

       // Readings는 본인만 접근 가능
       match /readings/{readingId} {
         allow read, write: if request.auth != null
           && request.auth.uid == resource.data.user_id;
       }
     }
   }
   ```

3. **Firebase Authentication 설정**
   - Firebase Console → Authentication
   - Sign-in method에서 "Email/Password" 활성화

## 다음 단계

1. ✅ Frontend Provider 패턴 완료
2. ✅ Backend Provider 인터페이스 완료
3. ⏳ PostgreSQL Provider 구현
4. ⏳ Firestore Provider 구현
5. ⏳ Firebase Admin 인증 미들웨어
6. ⏳ 마이그레이션 스크립트
7. ⏳ 통합 테스트

## 문의

구현 중 문제가 발생하면 이 가이드를 참조하거나, 각 Provider 구현체의 인터페이스 정의를 확인하세요.
