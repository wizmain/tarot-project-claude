/**
 * JWT Authentication Provider Implementation (기존 시스템)
 */
import {
  AuthProvider,
  AuthUser,
  SignUpParams,
  SignInParams,
} from './AuthProvider.interface';
import { config } from '@/config/env';

interface AuthResponse {
  access_token: string;
  refresh_token: string;
  user: {
    id: string;
    email: string;
    username?: string;
  };
}

const API_BASE_URL = config.apiUrl;
const TOKEN_KEY = 'tarot_access_token';
const REFRESH_TOKEN_KEY = 'tarot_refresh_token';

export class JWTAuthProvider implements AuthProvider {
  private currentUser: AuthUser | null = null;
  private authStateListeners: Array<(user: AuthUser | null) => void> = [];

  constructor() {
    // 초기화 시 현재 사용자 확인
    this.initializeAuth();
  }

  private async initializeAuth() {
    try {
      const token = this.getStoredToken();
      if (token) {
        const user = await this.fetchCurrentUser();
        this.setCurrentUser(user);
      }
    } catch (error) {
      console.error('Auth initialization error:', error);
      this.clearTokens();
    }
  }

  private getStoredToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(TOKEN_KEY);
  }

  private getStoredRefreshToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  }

  private setTokens(accessToken: string, refreshToken: string): void {
    if (typeof window === 'undefined') return;
    localStorage.setItem(TOKEN_KEY, accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  }

  private clearTokens(): void {
    if (typeof window === 'undefined') return;
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  }

  private setCurrentUser(user: AuthUser | null): void {
    this.currentUser = user;
    this.notifyListeners(user);
  }

  private notifyListeners(user: AuthUser | null): void {
    this.authStateListeners.forEach((listener) => listener(user));
  }

  private async fetchCurrentUser(): Promise<AuthUser> {
    const token = this.getStoredToken();
    if (!token) throw new Error('No token available');

    const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch user');
    }

    const data = await response.json();
    return {
      id: data.id,
      email: data.email,
      displayName: data.username || null,
      photoURL: null,
    };
  }

  async signUp(params: SignUpParams): Promise<AuthUser> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: params.email,
          password: params.password,
          username: params.displayName,
        }),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || '회원가입에 실패했습니다');
      }

      const data: AuthResponse = await response.json();
      this.setTokens(data.access_token, data.refresh_token);

      const user: AuthUser = {
        id: data.user.id,
        email: data.user.email,
        displayName: data.user.username || null,
        photoURL: null,
      };

      this.setCurrentUser(user);
      return user;
    } catch (error: any) {
      console.error('Sign up error:', error);
      throw error;
    }
  }

  async signIn(params: SignInParams): Promise<AuthUser> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: params.email,
          password: params.password,
        }),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || '로그인에 실패했습니다');
      }

      const data: AuthResponse = await response.json();
      this.setTokens(data.access_token, data.refresh_token);

      const user: AuthUser = {
        id: data.user.id,
        email: data.user.email,
        displayName: data.user.username || null,
        photoURL: null,
      };

      this.setCurrentUser(user);
      return user;
    } catch (error: any) {
      console.error('Sign in error:', error);
      throw error;
    }
  }

  async signOut(): Promise<void> {
    this.clearTokens();
    this.setCurrentUser(null);
  }

  async sendPasswordResetEmail(email: string): Promise<void> {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/auth/password-reset-request`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email }),
        }
      );

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(
          error.detail || '비밀번호 재설정 이메일 전송에 실패했습니다'
        );
      }
    } catch (error: any) {
      console.error('Password reset error:', error);
      throw error;
    }
  }

  async getAuthToken(): Promise<string | null> {
    return this.getStoredToken();
  }

  async getCurrentUser(): Promise<AuthUser | null> {
    if (this.currentUser) {
      return this.currentUser;
    }

    try {
      const user = await this.fetchCurrentUser();
      this.setCurrentUser(user);
      return user;
    } catch (error) {
      return null;
    }
  }

  onAuthStateChanged(callback: (user: AuthUser | null) => void): () => void {
    this.authStateListeners.push(callback);

    // 현재 사용자 정보를 즉시 콜백으로 전달
    callback(this.currentUser);

    // Unsubscribe 함수 반환
    return () => {
      this.authStateListeners = this.authStateListeners.filter(
        (listener) => listener !== callback
      );
    };
  }
}
