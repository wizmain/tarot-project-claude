# Page Refresh Issue - Debugging Guide

## Problem
페이지가 리딩 완료 후 자동으로 새로고침되는 현상 발생

## Potential Root Causes

### 1. **Firebase Token Refresh (Most Likely)**
Firebase ID 토큰은 기본적으로 1시간마다 만료됩니다. 토큰이 갱신될 때 `onAuthStateChanged` 콜백이 다시 호출되면서 상태 변경이 발생할 수 있습니다.

**증상:**
- 리딩이 완료되는 시점과 토큰 갱신 시점이 우연히 겹치면 페이지가 리프레시될 수 있음
- `ProtectedRoute`의 `useEffect`가 재실행되면서 컴포넌트가 언마운트/리마운트될 수 있음

**파일:**
- `frontend/src/contexts/AuthContext.tsx:67-96` - `onAuthStateChanged` 리스너
- `frontend/src/components/auth/ProtectedRoute.tsx:24-38` - 인증 상태 모니터링

### 2. **React StrictMode (Development Only)**
개발 모드에서 React StrictMode는 의도적으로 컴포넌트를 2번 마운트합니다.

**확인 방법:**
- 프로덕션 빌드로 테스트하여 이슈가 사라지는지 확인

### 3. **SSE Connection Closing**
SSE 연결이 닫힐 때 이상한 동작이 발생할 수 있습니다.

**파일:**
- `frontend/src/lib/use-sse-reading.ts:60-67` - cleanup on unmount
- `frontend/src/lib/sse-client.ts` - SSE connection management

### 4. **Navigation Side Effects**
`router.push()` 호출이 예상치 못한 곳에서 발생할 수 있습니다.

**확인 완료:** Grep으로 검색한 결과 리딩 완료 시 자동 navigation 코드는 없음

## Added Debug Logging

### 1. Component Lifecycle Tracking
**File:** `frontend/src/app/reading/one-card/page.tsx:27-38`
```typescript
useEffect(() => {
  console.log('[OneCard] Component mounted');
  const handleBeforeUnload = (e: BeforeUnloadEvent) => {
    console.warn('[OneCard] Page is about to unload/reload!', e);
  };
  window.addEventListener('beforeunload', handleBeforeUnload);

  return () => {
    console.log('[OneCard] Component unmounting');
    window.removeEventListener('beforeunload', handleBeforeUnload);
  };
}, []);
```

### 2. Auth State Change Tracking
**File:** `frontend/src/contexts/AuthContext.tsx:68-82`
```typescript
const unsubscribe = authProvider.onAuthStateChanged(async (user) => {
  console.log('[AuthContext] onAuthStateChanged fired', {
    hasUser: !!user,
    userId: user?.id,
    timestamp: new Date().toISOString(),
  });
  // ... token refresh
  console.log('[AuthContext] Got new token', {
    tokenLength: token?.length,
    timestamp: new Date().toISOString(),
  });
});
```

### 3. Protected Route Monitoring
**File:** `frontend/src/components/auth/ProtectedRoute.tsx:24-38`
```typescript
useEffect(() => {
  console.log('[ProtectedRoute] Auth state changed', {
    isLoading,
    isAuthenticated,
    pathname,
    timestamp: new Date().toISOString(),
  });

  if (!isLoading && !isAuthenticated) {
    console.warn('[ProtectedRoute] Redirecting to login - user not authenticated');
    // ...redirect
  }
}, [isAuthenticated, isLoading, router, pathname]);
```

### 4. SSE Completion Tracking
**File:** `frontend/src/lib/use-sse-reading.ts:163-175`
```typescript
onComplete: (data: CompleteEvent) => {
  console.log('[SSE Hook] Complete:', data);
  console.log('[SSE Hook] Setting state to completed - no navigation should occur');
  setState((prev) => ({...}));
  console.log('[SSE Hook] State update dispatched');
},
```

## How to Debug

### Step 1: 프론트엔드 재시작
```bash
cd frontend
npm run dev
```

### Step 2: 브라우저 DevTools 열기
- F12 또는 Cmd+Option+I
- Console 탭으로 이동
- "Preserve log" 옵션 활성화 (페이지 리프레시 시에도 로그 유지)

### Step 3: 리딩 생성하고 완료될 때까지 대기

### Step 4: 로그 분석
페이지가 리프레시되면 다음 순서로 로그를 확인:

1. **리딩 완료 로그:**
   ```
   [SSE Hook] Complete: {...}
   [SSE Hook] Setting state to completed - no navigation should occur
   [SSE Hook] State update dispatched
   ```

2. **Auth 상태 변경 로그 (의심 대상):**
   ```
   [AuthContext] onAuthStateChanged fired
   [AuthContext] Got new token
   ```

3. **ProtectedRoute 재실행 로그 (의심 대상):**
   ```
   [ProtectedRoute] Auth state changed
   ```

4. **컴포넌트 언마운트 로그 (리프레시 확정):**
   ```
   [OneCard] Component unmounting
   [OneCard] Page is about to unload/reload!
   [OneCard] Component mounted
   ```

### Step 5: 로그 패턴 분석

#### 패턴 A: 토큰 갱신으로 인한 리프레시
```
[SSE Hook] Complete
[AuthContext] onAuthStateChanged fired  ← 토큰 갱신
[ProtectedRoute] Auth state changed
[OneCard] Component unmounting  ← 리렌더 발생
```
**해결책:** Token refresh 시 불필요한 리렌더 방지 로직 추가

#### 패턴 B: 실제 페이지 리로드
```
[SSE Hook] Complete
[OneCard] Page is about to unload/reload!  ← beforeunload 이벤트
```
**해결책:** 어떤 코드가 window.location을 변경하는지 찾기

#### 패턴 C: 인증 실패로 인한 리다이렉트
```
[SSE Hook] Complete
[AuthContext] User logged out or token expired
[ProtectedRoute] Redirecting to login - user not authenticated
```
**해결책:** Token이 만료되지 않도록 자동 갱신 로직 개선

## Expected Behavior

정상 동작 시 예상되는 로그:
```
[SSE Hook] Complete: {reading_id: "...", total_time: 15.5}
[SSE Hook] Setting state to completed - no navigation should occur
[SSE Hook] State update dispatched
[OneCard] Interpretation length: 450
```

컴포넌트가 언마운트되거나 beforeunload 이벤트가 발생하지 않아야 합니다.

## Next Steps

1. 위의 Step 1-5를 수행하여 로그 수집
2. 로그를 분석하여 어느 패턴에 해당하는지 확인
3. 패턴에 따라 적절한 수정 적용

## Additional Resources

- [Firebase Token Expiration](https://firebase.google.com/docs/auth/admin/manage-sessions)
- [React useEffect Dependencies](https://react.dev/reference/react/useEffect)
- [Next.js Navigation](https://nextjs.org/docs/app/building-your-application/routing/linking-and-navigating)
