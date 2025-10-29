/**
 * Firebase Authentication Provider Implementation
 */
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut as firebaseSignOut,
  sendPasswordResetEmail as firebaseSendPasswordResetEmail,
  updateProfile,
  onAuthStateChanged,
  signInWithPopup,
  GoogleAuthProvider,
  User as FirebaseUser,
} from 'firebase/auth';
import { auth } from '../firebase';
import {
  AuthProvider,
  AuthUser,
  SignUpParams,
  SignInParams,
} from './AuthProvider.interface';

export class FirebaseAuthProvider implements AuthProvider {
  /**
   * Get auth instance with null check
   */
  private getAuth() {
    if (!auth) {
      throw new Error('Firebase auth is not initialized');
    }
    return auth;
  }

  /**
   * Convert Firebase User to AuthUser
   */
  private toAuthUser(user: FirebaseUser | null): AuthUser | null {
    if (!user) return null;

    return {
      id: user.uid,
      email: user.email,
      displayName: user.displayName,
      photoURL: user.photoURL,
    };
  }

  /**
   * Get user-friendly error messages
   */
  private getErrorMessage(errorCode: string): string {
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
        console.error('[FirebaseAuth] 처리되지 않은 오류 코드:', errorCode);

        // Handle Firebase configuration errors
        if (errorCode?.includes('invalid-value')) {
          return 'Firebase 인증 설정에 문제가 있습니다. 관리자에게 문의하세요.';
        }

        return '인증 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.';
    }
  }

  async signUp(params: SignUpParams): Promise<AuthUser> {
    try {
      const userCredential = await createUserWithEmailAndPassword(
        this.getAuth(),
        params.email,
        params.password
      );

      // Update profile with display name if provided
      if (params.displayName && userCredential.user) {
        await updateProfile(userCredential.user, {
          displayName: params.displayName,
        });
      }

      const authUser = this.toAuthUser(userCredential.user);
      if (!authUser) throw new Error('사용자 정보를 가져올 수 없습니다');

      return authUser;
    } catch (error: any) {
      console.error('Sign up error:', error);
      throw new Error(this.getErrorMessage(error.code));
    }
  }

  async signIn(params: SignInParams): Promise<AuthUser> {
    try {
      const userCredential = await signInWithEmailAndPassword(
        this.getAuth(),
        params.email,
        params.password
      );

      const authUser = this.toAuthUser(userCredential.user);
      if (!authUser) throw new Error('사용자 정보를 가져올 수 없습니다');

      return authUser;
    } catch (error: any) {
      console.error('Sign in error:', error);
      throw new Error(this.getErrorMessage(error.code));
    }
  }

  async signOut(): Promise<void> {
    try {
      await firebaseSignOut(this.getAuth());
    } catch (error: any) {
      console.error('Sign out error:', error);
      throw new Error('로그아웃에 실패했습니다');
    }
  }

  async sendPasswordResetEmail(email: string): Promise<void> {
    try {
      await firebaseSendPasswordResetEmail(this.getAuth(), email);
    } catch (error: any) {
      console.error('Password reset error:', error);
      throw new Error(this.getErrorMessage(error.code));
    }
  }

  async getAuthToken(): Promise<string | null> {
    const user = this.getAuth().currentUser;
    if (!user) return null;

    try {
      return await user.getIdToken();
    } catch (error) {
      console.error('Get ID token error:', error);
      return null;
    }
  }

  async getCurrentUser(): Promise<AuthUser | null> {
    const user = this.getAuth().currentUser;
    return this.toAuthUser(user);
  }

  onAuthStateChanged(callback: (user: AuthUser | null) => void): () => void {
    return onAuthStateChanged(this.getAuth(), (user) => {
      callback(this.toAuthUser(user));
    });
  }

  /**
   * Sign in with Google
   */
  async signInWithGoogle(): Promise<AuthUser> {
    try {
      const provider = new GoogleAuthProvider();
      const userCredential = await signInWithPopup(this.getAuth(), provider);

      const authUser = this.toAuthUser(userCredential.user);
      if (!authUser) throw new Error('사용자 정보를 가져올 수 없습니다');

      return authUser;
    } catch (error: any) {
      console.error('Google sign in error:', error);
      throw new Error(this.getErrorMessage(error.code));
    }
  }
}
