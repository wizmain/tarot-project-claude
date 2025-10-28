/**
 * Authentication Provider Interface
 *
 * 이 인터페이스를 구현하면 어떤 인증 시스템(Firebase, JWT, Auth0 등)이든 사용 가능합니다.
 */

export interface AuthUser {
  id: string;
  email: string | null;
  displayName: string | null;
  photoURL: string | null;
}

export interface SignUpParams {
  email: string;
  password: string;
  displayName?: string;
}

export interface SignInParams {
  email: string;
  password: string;
}

export interface AuthProvider {
  /**
   * 회원가입
   */
  signUp(params: SignUpParams): Promise<AuthUser>;

  /**
   * 로그인
   */
  signIn(params: SignInParams): Promise<AuthUser>;

  /**
   * 로그아웃
   */
  signOut(): Promise<void>;

  /**
   * 비밀번호 재설정 이메일 전송
   */
  sendPasswordResetEmail(email: string): Promise<void>;

  /**
   * 현재 사용자의 인증 토큰 가져오기 (API 요청에 사용)
   */
  getAuthToken(): Promise<string | null>;

  /**
   * 현재 로그인한 사용자 정보 가져오기
   */
  getCurrentUser(): Promise<AuthUser | null>;

  /**
   * 인증 상태 변경 감지
   */
  onAuthStateChanged(callback: (user: AuthUser | null) => void): () => void;
}
