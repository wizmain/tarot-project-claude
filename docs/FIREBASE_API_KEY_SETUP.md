# Firebase API Key 설정 가이드

## 🔑 Firebase API Key 확인 및 설정

비밀번호 리셋 기능을 사용하려면 Firebase Web API Key가 필요합니다.

### 1단계: Firebase API Key 확인

1. [Firebase Console](https://console.firebase.google.com/)에 접속
2. 프로젝트 선택
3. 왼쪽 상단의 **⚙️ Project Settings** 클릭
4. **General** 탭 선택
5. **Your apps** 섹션에서 Web 앱 선택 (없으면 추가)
6. **Web API Key** 복사

### 2단계: 환경 변수 설정

#### 개발 환경 (로컬)

`backend/.env` 파일을 생성하거나 수정:

```bash
# Firebase Configuration
FIREBASE_API_KEY=your-firebase-web-api-key-here

# Firebase Admin SDK (선택사항, 비밀번호 리셋에는 필수 아님)
FIREBASE_CREDENTIALS_PATH=./firebase-service-account.json

# Authentication Provider 설정
AUTH_PRIMARY_PROVIDER=firebase

# Frontend URL (비밀번호 리셋 이메일 링크용)
FRONTEND_URL=http://localhost:3000
```

#### 프로덕션 환경

환경 변수로 설정 (Cloud Run, Docker 등):

```bash
FIREBASE_API_KEY=your-firebase-web-api-key-here
AUTH_PRIMARY_PROVIDER=firebase
FRONTEND_URL=https://your-domain.com
```

### 3단계: 서버 재시작

환경 변수를 변경한 후에는 백엔드 서버를 재시작해야 합니다:

```bash
# 개발 환경
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

### 4단계: 설정 확인

서버 시작 시 로그에서 다음 메시지를 확인하세요:

```
[AuthOrchestrator] Auth Orchestrator initialized: primary=firebase, fallback=[]
```

에러가 발생하면:

```
[AuthOrchestrator] ERROR - FIREBASE_API_KEY 환경 변수가 설정되지 않았습니다...
```

---

## ⚠️ 문제 해결

### 에러: "Firebase API key not configured"

**원인**: `FIREBASE_API_KEY` 환경 변수가 설정되지 않았습니다.

**해결 방법**:
1. `backend/.env` 파일에 `FIREBASE_API_KEY` 추가
2. 서버 재시작
3. 환경 변수가 올바르게 로드되었는지 확인:
   ```python
   # Python에서 확인
   from src.core.config import settings
   print(settings.FIREBASE_API_KEY)
   ```

### 에러: "Auth Provider 초기화 실패"

**원인**: Firebase Provider 초기화 중 오류 발생

**해결 방법**:
1. `FIREBASE_API_KEY`가 올바른지 확인
2. `FIREBASE_CREDENTIALS_PATH`가 올바른지 확인 (선택사항)
3. 백엔드 로그에서 상세 에러 메시지 확인

---

## 📝 환경 변수 체크리스트

- [ ] `FIREBASE_API_KEY` 설정 완료
- [ ] `AUTH_PRIMARY_PROVIDER=firebase` 설정 확인
- [ ] `FRONTEND_URL` 설정 확인 (비밀번호 리셋 링크용)
- [ ] 서버 재시작 완료
- [ ] 로그에서 초기화 성공 메시지 확인

---

## 🔗 관련 문서

- [Firebase 비밀번호 리셋 구현 계획](./FIREBASE_PASSWORD_RESET_PLAN.md)
- [Firebase 이메일 설정 가이드](./docs/FIREBASE_EMAIL_SETUP.md)

