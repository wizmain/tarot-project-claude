/**
 * Centralized Environment Configuration
 *
 * This file manages all environment-specific configurations
 * for development, production, and deployment environments.
 *
 * Build timestamp: 2025-10-28T15:50:00Z
 * Cache-busting build for HTTPS enforcement
 */

export type Environment = 'development' | 'production' | 'test';

interface EnvironmentConfig {
  apiUrl: string;
  authProvider: 'firebase' | 'jwt';
  firebase?: {
    apiKey: string;
    authDomain: string;
    projectId: string;
    storageBucket: string;
    messagingSenderId: string;
    appId: string;
    measurementId?: string;
  };
}

/**
 * Get current environment
 */
export const getCurrentEnvironment = (): Environment => {
  return (process.env.NODE_ENV as Environment) || 'development';
};

/**
 * Environment-specific configurations
 */
const environmentConfigs: Record<Environment, Partial<EnvironmentConfig>> = {
  development: {
    apiUrl: 'http://localhost:8000',
  },
  production: {
    apiUrl: 'https://tarot-backend-414870328191.asia-northeast3.run.app',
  },
  test: {
    apiUrl: 'http://localhost:8000',
  },
};

/**
 * Get API Base URL with automatic HTTPS enforcement in production
 */
export const getApiBaseUrl = (): string => {
  // Priority: Environment variable > Environment config > Default
  const envVar = process.env.NEXT_PUBLIC_API_URL;
  if (envVar) {
    // Force HTTPS in production
    return getCurrentEnvironment() === 'production'
      ? envVar.replace('http://', 'https://')
      : envVar;
  }

  const currentEnv = getCurrentEnvironment();
  const config = environmentConfigs[currentEnv];

  if (!config.apiUrl) {
    throw new Error(`API URL not configured for environment: ${currentEnv}`);
  }

  return config.apiUrl;
};

/**
 * Get Authentication Provider
 */
export const getAuthProvider = (): 'firebase' | 'jwt' => {
  return (process.env.NEXT_PUBLIC_AUTH_PROVIDER as 'firebase' | 'jwt') || 'firebase';
};

/**
 * Get Firebase Configuration
 */
export const getFirebaseConfig = () => {
  return {
    apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY || '',
    authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN || '',
    projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID || '',
    storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET || '',
    messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID || '',
    appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID || '',
    measurementId: process.env.NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID,
  };
};

/**
 * Centralized configuration object
 */
export const config = {
  env: getCurrentEnvironment(),
  apiUrl: getApiBaseUrl(),
  authProvider: getAuthProvider(),
  firebase: getFirebaseConfig(),

  // Feature flags
  features: {
    enableAnalytics: getCurrentEnvironment() === 'production',
    enableDevTools: getCurrentEnvironment() === 'development',
  },

  // API settings
  api: {
    timeout: 30000, // 30 seconds
    retryAttempts: 3,
  },
};

/**
 * Validate configuration
 */
export const validateConfig = (): void => {
  const errors: string[] = [];

  if (!config.apiUrl) {
    errors.push('API URL is not configured');
  }

  if (config.authProvider === 'firebase') {
    if (!config.firebase.apiKey) {
      errors.push('Firebase API Key is missing');
    }
    if (!config.firebase.projectId) {
      errors.push('Firebase Project ID is missing');
    }
  }

  if (errors.length > 0) {
    console.error('Configuration errors:', errors);
    // Don't throw errors in production to allow graceful degradation
    // Firebase auth can be disabled if not configured
  }
};

// Validate on import (only in browser)
if (typeof window !== 'undefined') {
  validateConfig();
}
