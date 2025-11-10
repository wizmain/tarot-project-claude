# Firebase 비밀번호 리셋 구현 계획

## 📋 현재 상황 분석

### ✅ 이미 구현된 부분

1. **백엔드 (Backend)**
   - `FirebaseAuthProvider.reset_password()`: Firebase REST API를 통한 이메일 발송 ✅
   - `FirebaseAuthProvider.confirm_password_reset()`: oobCode를 사용한 비밀번호 재설정 ✅
   - API 엔드포인트: `/api/v1/auth/password-reset` ✅
   - API 엔드포인트: `/api/v1/auth/password-reset/confirm` ✅

2. **프론트엔드 (Frontend)**
   - `/forgot-password` 페이지: 비밀번호 재설정 요청 ✅
   - `/reset-password` 페이지: 새 비밀번호 설정 ✅
   - 백엔드 API 호출 로직 ✅

### ⚠️ 확인 및 설정이 필요한 부분

1. **Firebase 콘솔 설정**
   - 이메일 템플릿 커스터마이징
   - Action URL 설정 (리셋 링크가 우리 앱으로 리다이렉트되도록)
   - 이메일 발송 설정 활성화 확인

2. **환경 변수 설정**
   - `FIREBASE_API_KEY`: Firebase Web API Key 설정 확인
   - `FIREBASE_CREDENTIALS_PATH`: Firebase Admin SDK 인증 파일 경로 확인
   - `FRONTEND_URL`: 프론트엔드 URL 설정 확인

3. **프론트엔드 URL 파라미터 처리**
   - Firebase가 보내는 이메일의 링크는 `oobCode` 파라미터를 사용
   - 현재 프론트엔드는 `token` 파라미터를 기대함
   - URL 파라미터 매핑 필요

---

## 🎯 구현 계획

### Phase 1: Firebase 콘솔 설정 확인 및 구성

#### 1.1 Firebase 콘솔에서 이메일 템플릿 설정

**위치**: Firebase Console → Authentication → Templates → Password reset

**설정 항목**:
- **Subject**: `비밀번호 재설정 요청` (또는 원하는 제목)
- **Action URL**: 
  - 개발 환경: `http://localhost:3000/reset-password?oobCode=%LINK%`
  - 프로덕션: `https://your-domain.com/reset-password?oobCode=%LINK%`
- **Email body**: 커스텀 HTML 템플릿 사용 가능 (선택사항)

**중요**: Firebase는 `%LINK%` 플레이스홀더를 자동으로 oobCode가 포함된 링크로 교체합니다.

#### 1.2 Firebase API Key 확인

**확인 위치**: Firebase Console → Project Settings → General → Web API Key

**설정 방법**:
```bash
# backend/.env 파일에 추가
FIREBASE_API_KEY=your-firebase-web-api-key-here
```

#### 1.3 Firebase Admin SDK 인증 파일 확인

**확인 위치**: Firebase Console → Project Settings → Service Accounts

**설정 방법**:
```bash
# backend/.env 파일에 추가
FIREBASE_CREDENTIALS_PATH=./firebase-service-account.json
```

또는 환경 변수로 직접 설정 (Cloud Run 등)

---

### Phase 2: 프론트엔드 URL 파라미터 처리 수정

#### 2.1 문제점
- Firebase 이메일 링크: `https://your-domain.com/reset-password?oobCode=ABC123...`
- 현재 프론트엔드 코드: `token` 파라미터를 기대함

#### 2.2 해결 방법

**옵션 A: 프론트엔드에서 `oobCode` 파라미터 지원 추가** (권장)

`frontend/src/app/reset-password/page.tsx` 수정:
- `token` 또는 `oobCode` 파라미터 모두 지원
- 백엔드 API 호출 시 `reset_token`으로 전달

**옵션 B: Firebase 이메일 템플릿에서 `token` 파라미터 사용**
- Firebase 콘솔에서 Action URL을 커스텀하여 `token` 파라미터로 변환
- 하지만 Firebase는 기본적으로 `oobCode`를 사용하므로 권장하지 않음

---

### Phase 3: 백엔드 설정 확인

#### 3.1 환경 변수 확인

`backend/.env` 파일에 다음 설정이 있는지 확인:

```env
# Firebase Configuration
FIREBASE_API_KEY=your-firebase-web-api-key
FIREBASE_CREDENTIALS_PATH=./firebase-service-account.json

# Authentication Provider
AUTH_PRIMARY_PROVIDER=firebase

# Frontend URL
FRONTEND_URL=http://localhost:3000  # 개발 환경
# FRONTEND_URL=https://your-domain.com  # 프로덕션
```

#### 3.2 Firebase Provider 초기화 확인

`backend/src/api/dependencies/auth.py`에서 Firebase Provider가 올바르게 초기화되는지 확인:

```python
# Firebase Provider 설정
firebase_config = {}
if getattr(settings, 'FIREBASE_CREDENTIALS_PATH', None):
    firebase_config['credentials_path'] = settings.FIREBASE_CREDENTIALS_PATH
if getattr(settings, 'FIREBASE_API_KEY', None):
    firebase_config['api_key'] = settings.FIREBASE_API_KEY
if firebase_config:
    configs['firebase'] = firebase_config
```

---

### Phase 4: 테스트 계획

#### 4.1 단위 테스트
- [ ] Firebase Provider의 `reset_password()` 메서드 테스트
- [ ] Firebase Provider의 `confirm_password_reset()` 메서드 테스트
- [ ] API 엔드포인트 테스트

#### 4.2 통합 테스트
- [ ] 전체 플로우 테스트:
  1. `/forgot-password` 페이지에서 이메일 입력
  2. 백엔드 API 호출 확인
  3. Firebase 이메일 수신 확인
  4. 이메일 링크 클릭
  5. `/reset-password` 페이지에서 새 비밀번호 입력
  6. 비밀번호 재설정 완료 확인
  7. 새 비밀번호로 로그인 확인

#### 4.3 에러 케이스 테스트
- [ ] 존재하지 않는 이메일로 요청
- [ ] 만료된 oobCode 사용
- [ ] 잘못된 oobCode 사용
- [ ] 약한 비밀번호 입력

---

## 🔧 구현 작업 목록

### 작업 1: 프론트엔드 URL 파라미터 처리 수정

**파일**: `frontend/src/app/reset-password/page.tsx`

**변경 사항**:
- `token` 파라미터 외에 `oobCode` 파라미터도 지원
- 두 파라미터 모두 백엔드 API의 `reset_token`으로 전달

**예상 코드 변경**:
```typescript
const token = searchParams.get('token') || searchParams.get('oobCode');
```

### 작업 2: Firebase 콘솔 설정 가이드 문서 작성

**파일**: `docs/FIREBASE_EMAIL_SETUP.md` (새 파일)

**내용**:
- Firebase 콘솔 접근 방법
- 이메일 템플릿 설정 단계별 가이드
- Action URL 설정 방법
- 테스트 방법

### 작업 3: 환경 변수 설정 확인 및 문서화

**파일**: `backend/.env.example` 업데이트

**추가할 내용**:
```env
# Firebase Configuration
FIREBASE_API_KEY=your-firebase-web-api-key-here
FIREBASE_CREDENTIALS_PATH=./firebase-service-account.json
```

### 작업 4: 에러 처리 개선

**파일**: `backend/src/auth/providers/firebase_provider.py`

**개선 사항**:
- 더 명확한 에러 메시지
- 로깅 개선
- 사용자 친화적인 에러 응답

---

## 📝 Firebase 이메일 링크 형식

Firebase가 보내는 비밀번호 리셋 이메일의 링크 형식:

```
https://your-domain.com/reset-password?oobCode=ABC123XYZ...&mode=resetPassword&apiKey=your-api-key&lang=ko
```

**파라미터 설명**:
- `oobCode`: Firebase가 생성한 일회용 코드 (Out-of-band code)
- `mode`: `resetPassword` (고정값)
- `apiKey`: Firebase Web API Key
- `lang`: 언어 설정 (선택사항)

**중요**: 백엔드 API는 `oobCode`만 필요합니다. 다른 파라미터는 무시해도 됩니다.

---

## 🚀 배포 체크리스트

### 개발 환경
- [ ] `FIREBASE_API_KEY` 설정 확인
- [ ] `FIREBASE_CREDENTIALS_PATH` 설정 확인
- [ ] `FRONTEND_URL`이 `http://localhost:3000`으로 설정되어 있는지 확인
- [ ] Firebase 콘솔에서 개발용 Action URL 설정

### 프로덕션 환경
- [ ] `FIREBASE_API_KEY` 환경 변수 설정
- [ ] `FIREBASE_CREDENTIALS_PATH` 환경 변수 설정 (또는 서비스 계정 JSON 파일 배포)
- [ ] `FRONTEND_URL`이 프로덕션 도메인으로 설정되어 있는지 확인
- [ ] Firebase 콘솔에서 프로덕션용 Action URL 설정
- [ ] CORS 설정에 프로덕션 도메인 추가 확인

---

## 📚 참고 자료

- [Firebase Authentication - Password Reset](https://firebase.google.com/docs/auth/web/manage-users#send_a_password_reset_email)
- [Firebase REST API - sendOobCode](https://firebase.google.com/docs/reference/rest/auth#section-send-password-reset-email)
- [Firebase REST API - resetPassword](https://firebase.google.com/docs/reference/rest/auth#section-confirm-password-reset)

---

## ⚠️ 주의사항

1. **보안**: Firebase API Key는 공개되어도 상대적으로 안전하지만, 가능하면 도메인 제한을 설정하는 것이 좋습니다.

2. **이메일 발송 제한**: Firebase는 무료 플랜에서도 이메일 발송 제한이 있을 수 있습니다. 프로덕션 환경에서는 모니터링이 필요합니다.

3. **oobCode 만료 시간**: Firebase의 기본 만료 시간은 1시간입니다. 사용자에게 명확히 안내해야 합니다.

4. **이메일 템플릿**: Firebase 기본 템플릿을 사용하거나 커스텀 HTML을 사용할 수 있습니다. 브랜딩이 중요하다면 커스텀 템플릿을 고려하세요.

---

## ✅ 완료 기준

- [ ] Firebase 콘솔에서 이메일 템플릿 설정 완료
- [ ] 환경 변수 설정 완료
- [ ] 프론트엔드에서 `oobCode` 파라미터 지원
- [ ] 전체 플로우 테스트 통과
- [ ] 에러 케이스 처리 확인
- [ ] 문서화 완료

