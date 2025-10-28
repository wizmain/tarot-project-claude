/**
 * Authentication types
 */

export interface User {
  id: string;
  email: string;
  display_name: string | null;
  photo_url: string | null;
  phone_number: string | null;
  provider_id: string;
  email_verified: boolean;
  is_active: boolean;
  created_at: string;
  last_login_at: string | null;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface AuthResponse extends AuthTokens {
  user: User;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface SignupRequest {
  email: string;
  password: string;
  display_name?: string;
  phone_number?: string;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface UserProfileUpdate {
  display_name?: string;
  phone_number?: string;
  photo_url?: string;
}
