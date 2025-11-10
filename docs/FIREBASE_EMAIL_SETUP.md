# Firebase 비밀번호 리셋 이메일 설정 가이드

## 📧 Firebase 콘솔에서 이메일 템플릿 설정

Firebase Authentication을 사용하여 비밀번호 리셋 이메일을 보내려면 Firebase 콘솔에서 이메일 템플릿을 설정해야 합니다.

### 1단계: Firebase 콘솔 접근

1. [Firebase Console](https://console.firebase.google.com/)에 접속
2. 프로젝트 선택
3. 왼쪽 메뉴에서 **Authentication** 클릭
4. 상단 탭에서 **Templates** 클릭

### 2단계: Password reset 템플릿 설정

1. **Password reset** 템플릿 찾기
2. 템플릿 옆의 **편집** 버튼 클릭

### 3단계: Action URL 설정

**Action URL** 필드에 다음 URL을 입력:

#### 개발 환경
```
http://localhost:3000/reset-password?oobCode=%LINK%
```

#### 프로덕션 환경
```
https://your-domain.com/reset-password?oobCode=%LINK%
```

**중요**: 
- `%LINK%`는 Firebase가 자동으로 실제 링크로 교체하는 플레이스홀더입니다.
- Firebase는 기본적으로 `oobCode` 파라미터를 포함한 전체 링크를 생성합니다.
- 우리 앱은 `oobCode` 파라미터만 추출하여 백엔드 API로 전달합니다.

### 4단계: 이메일 제목 및 본문 설정 (선택사항)

#### 제목 (Subject)
```
비밀번호 재설정 요청
```

#### 본문 (Email body)

기본 템플릿을 사용하거나 커스텀 HTML을 사용할 수 있습니다.

**기본 템플릿 예시**:
```
안녕하세요,

비밀번호 재설정을 요청하셨습니다.
아래 링크를 클릭하여 새 비밀번호를 설정하세요:

%LINK%

이 링크는 1시간 동안만 유효합니다.

본인이 요청하지 않으셨다면 이 이메일을 무시하셔도 됩니다.

감사합니다,
Tarot AI 팀
```

**커스텀 HTML 사용 시**:
- Firebase 콘솔에서 HTML 편집 모드 사용
- `%LINK%` 플레이스홀더를 반드시 포함해야 합니다.

### 5단계: 저장

설정을 완료한 후 **저장** 버튼을 클릭합니다.

---

## 🔑 Firebase API Key 확인

비밀번호 리셋 기능이 작동하려면 Firebase Web API Key가 필요합니다.

### API Key 확인 방법

1. Firebase Console → **Project Settings** (톱니바퀴 아이콘)
2. **General** 탭
3. **Your apps** 섹션에서 Web 앱 선택
4. **Web API Key** 복사

### 환경 변수 설정

`backend/.env` 파일에 추가:

```env
FIREBASE_API_KEY=your-firebase-web-api-key-here
```

---

## 🔐 Firebase Admin SDK 인증 파일 설정

백엔드에서 Firebase Admin SDK를 사용하려면 서비스 계정 키 파일이 필요합니다.

### 서비스 계정 키 파일 다운로드

1. Firebase Console → **Project Settings**
2. **Service accounts** 탭
3. **Generate new private key** 클릭
4. JSON 파일 다운로드

### 파일 배치

다운로드한 JSON 파일을 `backend/` 디렉토리에 배치:

```
backend/firebase-service-account.json
```

### 환경 변수 설정

`backend/.env` 파일에 추가:

```env
FIREBASE_CREDENTIALS_PATH=./firebase-service-account.json
```

**보안 주의사항**:
- 이 파일은 절대 Git에 커밋하지 마세요
- `.gitignore`에 추가되어 있는지 확인하세요
- 프로덕션 환경에서는 환경 변수로 직접 설정하는 것을 권장합니다

---

## 🧪 테스트 방법

### 1. 개발 환경 테스트

1. 백엔드 서버 실행:
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn main:app --reload
   ```

2. 프론트엔드 서버 실행:
   ```bash
   cd frontend
   npm run dev
   ```

3. 브라우저에서 `http://localhost:3000/forgot-password` 접속

4. 테스트 이메일 주소 입력

5. 이메일 수신 확인

6. 이메일의 링크 클릭

7. `http://localhost:3000/reset-password?oobCode=...` 페이지로 이동하는지 확인

8. 새 비밀번호 입력 및 제출

9. 로그인 페이지로 리다이렉트되는지 확인

### 2. 이메일 발송 확인

Firebase Console → Authentication → Users에서:
- 사용자 이메일이 등록되어 있는지 확인
- 이메일이 발송되었는지 확인 (로그 확인)

---

## ⚠️ 문제 해결

### 문제 1: 이메일이 발송되지 않음

**가능한 원인**:
- Firebase API Key가 설정되지 않음
- Firebase Admin SDK 인증 파일이 없음
- 이메일 주소가 Firebase에 등록되지 않음

**해결 방법**:
1. 환경 변수 확인: `FIREBASE_API_KEY`, `FIREBASE_CREDENTIALS_PATH`
2. 백엔드 로그 확인
3. Firebase Console에서 사용자 확인

### 문제 2: 링크가 작동하지 않음

**가능한 원인**:
- Action URL이 잘못 설정됨
- `oobCode` 파라미터가 누락됨
- 프론트엔드 URL 파라미터 처리 오류

**해결 방법**:
1. Firebase 콘솔에서 Action URL 확인
2. 브라우저 개발자 도구에서 URL 파라미터 확인
3. 프론트엔드 코드에서 `oobCode` 파라미터 추출 확인

### 문제 3: 비밀번호 재설정 실패

**가능한 원인**:
- oobCode가 만료됨 (기본 1시간)
- 잘못된 oobCode
- 약한 비밀번호

**해결 방법**:
1. 백엔드 로그에서 에러 메시지 확인
2. 새로운 비밀번호 리셋 이메일 요청
3. 비밀번호 강도 확인 (최소 6자)

---

## 📚 참고 자료

- [Firebase Authentication - Email Templates](https://firebase.google.com/docs/auth/custom-email-handler)
- [Firebase REST API - sendOobCode](https://firebase.google.com/docs/reference/rest/auth#section-send-password-reset-email)
- [Firebase REST API - resetPassword](https://firebase.google.com/docs/reference/rest/auth#section-confirm-password-reset)

---

## ✅ 체크리스트

- [ ] Firebase 콘솔에서 Password reset 템플릿 설정 완료
- [ ] Action URL 설정 완료 (개발/프로덕션)
- [ ] Firebase API Key 환경 변수 설정 완료
- [ ] Firebase Admin SDK 인증 파일 설정 완료
- [ ] 개발 환경 테스트 완료
- [ ] 프로덕션 환경 설정 완료

