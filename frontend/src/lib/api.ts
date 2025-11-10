/**
 * API Client for Tarot Backend
 * Last updated: 2025-10-28 - Fixed HTTPS enforcement
 */

import { Card, CardListResponse, ArcanaType, Suit } from '@/types';
import {
  ReadingRequest,
  ReadingResponse,
  ReadingListResponse,
} from '@/types/reading';
import { getAuthProvider } from '@/lib/auth';
import { config } from '@/config/env';

const API_BASE_URL = config.apiUrl.replace(/\/$/, '');

interface FetchOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined>;
  requiresAuth?: boolean;
}

/**
 * Event emitter for authentication errors
 */
class AuthEventEmitter {
  private listeners: Array<() => void> = [];

  on(callback: () => void) {
    this.listeners.push(callback);
  }

  off(callback: () => void) {
    this.listeners = this.listeners.filter((listener) => listener !== callback);
  }

  emit() {
    this.listeners.forEach((listener) => listener());
  }
}

export const authEvents = new AuthEventEmitter();

/**
 * Generic fetch wrapper with error handling and automatic token refresh
 */
async function fetchAPI<T>(
  endpoint: string,
  options: FetchOptions = {}
): Promise<T> {
  const { params, requiresAuth = false, ...fetchOptions } = options;

  // Build URL with query parameters
  let url = `${API_BASE_URL}${endpoint}`;
  if (params) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value));
      }
    });
    const queryString = searchParams.toString();
    if (queryString) {
      url += `?${queryString}`;
    }
  }

  // Build headers
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(fetchOptions.headers as Record<string, string> || {}),
  };

  // Add Authorization header if required
  if (requiresAuth) {
    const authProvider = getAuthProvider();
    const token = await authProvider.getAuthToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      headers,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));

      // Handle 401 Unauthorized
      if (response.status === 401) {
        // Auth token is invalid or expired
        // Let the AuthProvider handle re-authentication
        authEvents.emit();
        throw new Error('세션이 만료되었습니다. 다시 로그인해주세요. [AUTH_EXPIRED]');
      }

      throw new Error(
        errorData.detail || `API Error: ${response.status} ${response.statusText}`
      );
    }

    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
}

/**
 * Card API endpoints
 */
export const cardAPI = {
  /**
   * Get list of cards with pagination and filters
   */
  getCards: async (params?: {
    page?: number;
    page_size?: number;
    arcana_type?: ArcanaType;
    suit?: Suit;
    search?: string;
  }): Promise<CardListResponse> => {
    return fetchAPI<CardListResponse>('/api/v1/cards', { params });
  },

  /**
   * Get a specific card by ID
   */
  getCardById: async (cardId: number): Promise<Card> => {
    return fetchAPI<Card>(`/api/v1/cards/${cardId}`);
  },

  /**
   * Get a specific card by name
   */
  getCardByName: async (cardName: string): Promise<Card> => {
    return fetchAPI<Card>(`/api/v1/cards/name/${encodeURIComponent(cardName)}`);
  },

  /**
   * Get all Major Arcana cards
   */
  getMajorArcana: async (params?: {
    page?: number;
    page_size?: number;
  }): Promise<CardListResponse> => {
    return fetchAPI<CardListResponse>('/api/v1/cards/major-arcana/all', {
      params,
    });
  },

  /**
   * Get all Minor Arcana cards
   */
  getMinorArcana: async (params?: {
    page?: number;
    page_size?: number;
  }): Promise<CardListResponse> => {
    return fetchAPI<CardListResponse>('/api/v1/cards/minor-arcana/all', {
      params,
    });
  },

  /**
   * Get cards by suit
   */
  getCardsBySuit: async (
    suit: Suit,
    params?: {
      page?: number;
      page_size?: number;
    }
  ): Promise<CardListResponse> => {
    return fetchAPI<CardListResponse>(`/api/v1/cards/suit/${suit}`, { params });
  },

  /**
   * Draw random cards
   */
  drawRandomCards: async (params: {
    count: number;
    arcana_type?: ArcanaType;
    suit?: Suit;
  }): Promise<Card[]> => {
    return fetchAPI<Card[]>('/api/v1/cards/random/draw', { params });
  },
};

/**
 * Reading API endpoints
 */
export const readingAPI = {
  /**
   * Create a new tarot reading (requires authentication)
   */
  createReading: async (request: ReadingRequest): Promise<ReadingResponse> => {
    return fetchAPI<ReadingResponse>('/api/v1/readings', {
      method: 'POST',
      body: JSON.stringify(request),
      requiresAuth: true,
    });
  },

  /**
   * Get a specific reading by ID (requires authentication)
   */
  getReading: async (readingId: string): Promise<ReadingResponse> => {
    return fetchAPI<ReadingResponse>(`/api/v1/readings/${readingId}`, {
      requiresAuth: true,
    });
  },

  /**
   * Get list of readings with pagination (requires authentication)
   */
  getReadings: async (params?: {
    page?: number;
    page_size?: number;
    spread_type?: string;
    category?: string;
  }): Promise<ReadingListResponse> => {
    return fetchAPI<ReadingListResponse>('/api/v1/readings/', {
      params,
      requiresAuth: true,
    });
  },

  /**
   * Delete a reading (requires authentication)
   */
  deleteReading: async (readingId: string): Promise<void> => {
    return fetchAPI<void>(`/api/v1/readings/${readingId}`, {
      method: 'DELETE',
      requiresAuth: true,
    });
  },
};

/**
 * Feedback API endpoints
 */
export interface FeedbackCreate {
  rating: number;
  comment?: string;
  helpful?: boolean;
  accurate?: boolean;
}

export interface FeedbackUpdate {
  rating?: number;
  comment?: string;
  helpful?: boolean;
  accurate?: boolean;
}

export interface FeedbackResponse {
  id: string;
  reading_id: string;
  user_id: string;
  rating: number;
  comment?: string;
  helpful: boolean;
  accurate: boolean;
  created_at: string;
  updated_at: string;
}

export const feedbackAPI = {
  /**
   * Create feedback for a reading (requires authentication)
   */
  createFeedback: async (
    readingId: string,
    feedback: FeedbackCreate
  ): Promise<FeedbackResponse> => {
    return fetchAPI<FeedbackResponse>(
      `/api/v1/readings/${readingId}/feedback`,
      {
        method: 'POST',
        body: JSON.stringify(feedback),
        requiresAuth: true,
      }
    );
  },

  /**
   * Get feedback for a reading (requires authentication)
   */
  getFeedback: async (
    readingId: string,
    page: number = 1,
    pageSize: number = 10
  ): Promise<FeedbackResponse[]> => {
    return fetchAPI<FeedbackResponse[]>(
      `/api/v1/readings/${readingId}/feedback`,
      {
        params: { page, page_size: pageSize },
        requiresAuth: true,
      }
    );
  },

  /**
   * Update feedback (requires authentication)
   */
  updateFeedback: async (
    feedbackId: string,
    feedback: FeedbackUpdate
  ): Promise<FeedbackResponse> => {
    return fetchAPI<FeedbackResponse>(`/api/v1/feedback/${feedbackId}`, {
      method: 'PUT',
      body: JSON.stringify(feedback),
      requiresAuth: true,
    });
  },
};

// Auth API is now handled by AuthProvider

/**
 * API health check
 */
export async function checkAPIHealth(): Promise<{
  status: string;
  app_name: string;
  version: string;
}> {
  return fetchAPI('/health');
}
