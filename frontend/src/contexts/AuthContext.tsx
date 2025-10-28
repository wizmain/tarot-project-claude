'use client';

/**
 * Authentication Context Provider
 *
 * Provider 패턴을 사용하여 다양한 인증 시스템(Firebase, JWT 등)을 지원합니다.
 * .env.local의 NEXT_PUBLIC_AUTH_PROVIDER 설정으로 Provider를 선택할 수 있습니다.
 */

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from 'react';
import { useRouter } from 'next/navigation';
import { getAuthProvider, AuthUser } from '@/lib/auth';

interface AuthContextType {
  user: AuthUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  signup: (email: string, password: string, displayName?: string) => Promise<void>;
  signupWithGoogle: () => Promise<void>;
  logout: () => Promise<void>;
  sendPasswordResetEmail: (email: string) => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: React.ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const authProvider = getAuthProvider();

  /**
   * Fetch current user
   */
  const refreshUser = useCallback(async () => {
    try {
      const currentUser = await authProvider.getCurrentUser();
      setUser(currentUser);
    } catch (error) {
      console.error('Failed to fetch user:', error);
      setUser(null);
    }
  }, [authProvider]);

  /**
   * Initialize auth state on mount
   */
  useEffect(() => {
    setIsLoading(true);

    // Listen to auth state changes
    const unsubscribe = authProvider.onAuthStateChanged(async (user) => {
      setUser(user);
      setIsLoading(false);
    });

    // Cleanup subscription on unmount
    return () => {
      unsubscribe();
    };
  }, [authProvider]);

  /**
   * Login handler
   */
  const login = useCallback(async (email: string, password: string) => {
    try {
      setIsLoading(true);
      const user = await authProvider.signIn({ email, password });
      setUser(user);

      // Redirect to home page after successful login
      router.push('/');
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [authProvider, router]);

  /**
   * Signup handler
   */
  const signup = useCallback(async (
    email: string,
    password: string,
    displayName?: string
  ) => {
    try {
      setIsLoading(true);
      const user = await authProvider.signUp({ email, password, displayName });
      setUser(user);

      // Redirect to home page after successful signup
      router.push('/');
    } catch (error) {
      console.error('Signup error:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [authProvider, router]);

  /**
   * Logout handler
   */
  const logout = useCallback(async () => {
    try {
      await authProvider.signOut();
      setUser(null);
      router.push('/login');
    } catch (error) {
      console.error('Logout error:', error);
      throw error;
    }
  }, [authProvider, router]);

  /**
   * Google Login handler
   */
  const loginWithGoogle = useCallback(async () => {
    try {
      setIsLoading(true);
      const firebaseProvider = authProvider as any;
      if (!firebaseProvider.signInWithGoogle) {
        throw new Error('Google 로그인이 지원되지 않습니다.');
      }
      const user = await firebaseProvider.signInWithGoogle();
      setUser(user);

      // Redirect to home page after successful login
      router.push('/');
    } catch (error) {
      console.error('Google login error:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [authProvider, router]);

  /**
   * Google Signup handler (same as login for Google)
   */
  const signupWithGoogle = useCallback(async () => {
    try {
      setIsLoading(true);
      const firebaseProvider = authProvider as any;
      if (!firebaseProvider.signInWithGoogle) {
        throw new Error('Google 회원가입이 지원되지 않습니다.');
      }
      const user = await firebaseProvider.signInWithGoogle();
      setUser(user);

      // Redirect to home page after successful signup
      router.push('/');
    } catch (error) {
      console.error('Google signup error:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [authProvider, router]);

  /**
   * Send password reset email
   */
  const sendPasswordResetEmail = useCallback(async (email: string) => {
    try {
      await authProvider.sendPasswordResetEmail(email);
    } catch (error) {
      console.error('Password reset error:', error);
      throw error;
    }
  }, [authProvider]);

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    loginWithGoogle,
    signup,
    signupWithGoogle,
    logout,
    sendPasswordResetEmail,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * Custom hook to use auth context
 * Must be used within AuthProvider
 */
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
