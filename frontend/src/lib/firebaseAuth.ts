/**
 * Firebase Authentication Service
 */
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut as firebaseSignOut,
  sendPasswordResetEmail,
  updateProfile,
  User as FirebaseUser,
  onAuthStateChanged,
} from 'firebase/auth';
import { auth } from './firebase';

/**
 * Get auth instance with null check
 */
function getAuth() {
  if (!auth) {
    throw new Error('Firebase auth is not initialized');
  }
  return auth;
}

export interface AuthUser {
  uid: string;
  email: string | null;
  displayName: string | null;
  photoURL: string | null;
}

/**
 * Convert Firebase User to AuthUser
 */
export function toAuthUser(user: FirebaseUser | null): AuthUser | null {
  if (!user) return null;

  return {
    uid: user.uid,
    email: user.email,
    displayName: user.displayName,
    photoURL: user.photoURL,
  };
}

/**
 * Sign up with email and password
 */
export async function signUp(email: string, password: string, displayName?: string): Promise<AuthUser> {
  try {
    const userCredential = await createUserWithEmailAndPassword(getAuth(), email, password);

    // Update profile with display name if provided
    if (displayName && userCredential.user) {
      await updateProfile(userCredential.user, { displayName });
    }

    return toAuthUser(userCredential.user)!;
  } catch (error: any) {
    console.error('Sign up error:', error);
    throw new Error(getAuthErrorMessage(error.code));
  }
}

/**
 * Sign in with email and password
 */
export async function signIn(email: string, password: string): Promise<AuthUser> {
  try {
    const userCredential = await signInWithEmailAndPassword(getAuth(), email, password);
    return toAuthUser(userCredential.user)!;
  } catch (error: any) {
    console.error('Sign in error:', error);
    throw new Error(getAuthErrorMessage(error.code));
  }
}

/**
 * Sign out
 */
export async function signOut(): Promise<void> {
  try {
    await firebaseSignOut(getAuth());
  } catch (error: any) {
    console.error('Sign out error:', error);
    throw new Error('로그아웃에 실패했습니다');
  }
}

/**
 * Send password reset email
 */
export async function resetPassword(email: string): Promise<void> {
  try {
    await sendPasswordResetEmail(getAuth(), email);
  } catch (error: any) {
    console.error('Password reset error:', error);
    throw new Error(getAuthErrorMessage(error.code));
  }
}

/**
 * Get current user's ID token
 */
export async function getIdToken(): Promise<string | null> {
  const user = getAuth().currentUser;
  if (!user) return null;

  try {
    return await user.getIdToken();
  } catch (error) {
    console.error('Get ID token error:', error);
    return null;
  }
}

/**
 * Listen to auth state changes
 */
export function onAuthStateChange(callback: (user: AuthUser | null) => void): () => void {
  return onAuthStateChanged(getAuth(), (user) => {
    callback(toAuthUser(user));
  });
}

/**
 * Get user-friendly error messages
 */
function getAuthErrorMessage(errorCode: string): string {
  switch (errorCode) {
    case 'auth/email-already-in-use':
      return '이미 사용 중인 이메일입니다. 다른 이메일을 사용하거나 로그인해주세요.';
    case 'auth/invalid-email':
      return '올바른 이메일 형식이 아닙니다. 이메일 주소를 확인해주세요.';
    case 'auth/operation-not-allowed':
      return '이메일/비밀번호 로그인이 비활성화되어 있습니다. 관리자에게 문의하세요.';
    case 'auth/weak-password':
      return '비밀번호가 너무 간단합니다. 최소 6자 이상의 안전한 비밀번호를 사용해주세요.';
    case 'auth/user-disabled':
      return '이 계정은 비활성화되었습니다. 관리자에게 문의하세요.';
    case 'auth/user-not-found':
      return '등록되지 않은 이메일입니다. 이메일을 확인하거나 회원가입을 진행해주세요.';
    case 'auth/wrong-password':
      return '비밀번호가 일치하지 않습니다. 다시 확인해주세요.';
    case 'auth/invalid-credential':
      return '이메일 또는 비밀번호가 올바르지 않습니다. 다시 확인해주세요.';
    case 'auth/too-many-requests':
      return '로그인 시도가 너무 많아 일시적으로 차단되었습니다. 잠시 후 다시 시도해주세요.';
    case 'auth/network-request-failed':
      return '네트워크 연결이 불안정합니다. 인터넷 연결을 확인해주세요.';
    case 'auth/missing-password':
      return '비밀번호를 입력해주세요.';
    case 'auth/requires-recent-login':
      return '보안을 위해 다시 로그인이 필요합니다.';
    case 'auth/invalid-action-code':
      return '인증 코드가 유효하지 않거나 만료되었습니다.';
    case 'auth/expired-action-code':
      return '인증 코드가 만료되었습니다. 새로운 인증 이메일을 요청해주세요.';
    case 'auth/popup-blocked':
      return '팝업이 차단되었습니다. 팝업 차단을 해제하고 다시 시도해주세요.';
    case 'auth/popup-closed-by-user':
      return '로그인 팝업이 닫혔습니다. 다시 시도해주세요.';
    case 'auth/unauthorized-domain':
      return '허용되지 않은 도메인입니다. 관리자에게 문의하세요.';
    case 'auth/invalid-api-key':
      return 'Firebase API 키가 유효하지 않습니다. 관리자에게 문의하세요.';
    case 'auth/app-deleted':
      return 'Firebase 앱이 삭제되었습니다. 관리자에게 문의하세요.';
    case 'auth/account-exists-with-different-credential':
      return '이 이메일은 다른 로그인 방식으로 이미 등록되어 있습니다.';
    case 'auth/credential-already-in-use':
      return '이 인증 정보는 이미 다른 계정에서 사용 중입니다.';
    default:
      // Log unhandled error codes for debugging
      console.error('[FirebaseAuth Legacy] 처리되지 않은 오류 코드:', errorCode);
      return '인증 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.';
  }
}
