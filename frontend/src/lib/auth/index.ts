/**
 * Authentication Provider Factory
 *
 * 환경 변수를 통해 사용할 인증 Provider를 선택합니다.
 */
import { AuthProvider } from './AuthProvider.interface';
import { FirebaseAuthProvider } from './FirebaseAuthProvider';
import { JWTAuthProvider } from './JWTAuthProvider';

// 환경 변수로 Provider 선택 (기본값: firebase)
const AUTH_PROVIDER_TYPE = process.env.NEXT_PUBLIC_AUTH_PROVIDER || 'firebase';

/**
 * 인증 Provider 인스턴스 생성
 */
export function createAuthProvider(): AuthProvider {
  switch (AUTH_PROVIDER_TYPE) {
    case 'firebase':
      return new FirebaseAuthProvider();
    case 'jwt':
      return new JWTAuthProvider();
    default:
      console.warn(
        `Unknown auth provider: ${AUTH_PROVIDER_TYPE}, falling back to Firebase`
      );
      return new FirebaseAuthProvider();
  }
}

// Singleton 인스턴스
let authProviderInstance: AuthProvider | null = null;

/**
 * 인증 Provider 싱글톤 인스턴스 가져오기
 */
export function getAuthProvider(): AuthProvider {
  if (!authProviderInstance) {
    authProviderInstance = createAuthProvider();
  }
  return authProviderInstance;
}

// Re-export types
export * from './AuthProvider.interface';
