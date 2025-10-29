/**
 * Reading Types and Spread Configuration
 */

import { Card, DrawnCard } from './card';

// Re-export DrawnCard from card module
export type { DrawnCard } from './card';

export type ReadingType = 'one-card' | 'three-card' | 'celtic-cross';

export interface ReadingSpread {
  type: ReadingType;
  name: string;
  name_ko: string;
  description: string;
  description_ko: string;
  cardCount: number;
  positions: ReadingPosition[];
}

export interface ReadingPosition {
  index: number;
  name: string;
  name_ko: string;
  description: string;
  description_ko: string;
}

// DrawnCard is imported from './card'

export interface Reading {
  id?: number;
  type: ReadingType;
  question?: string;
  drawnCards: DrawnCard[];
  interpretation?: string;
  createdAt?: string;
}

// Spread configurations
export const READING_SPREADS: Record<ReadingType, ReadingSpread> = {
  'one-card': {
    type: 'one-card',
    name: 'One Card Reading',
    name_ko: '원카드 리딩',
    description: 'Draw a single card for quick guidance and daily insight',
    description_ko: '하나의 카드로 오늘의 운세와 빠른 조언을 받아보세요',
    cardCount: 1,
    positions: [
      {
        index: 0,
        name: 'Present Situation',
        name_ko: '현재 상황',
        description: 'The current energy and situation',
        description_ko: '현재의 에너지와 상황',
      },
    ],
  },
  'three-card': {
    type: 'three-card',
    name: 'Three Card Reading',
    name_ko: '쓰리카드 리딩',
    description: 'Explore past, present, and future with three cards',
    description_ko: '세 장의 카드로 과거-현재-미래를 탐색하세요',
    cardCount: 3,
    positions: [
      {
        index: 0,
        name: 'Past',
        name_ko: '과거',
        description: 'Past influences and foundations',
        description_ko: '과거의 영향과 기반',
      },
      {
        index: 1,
        name: 'Present',
        name_ko: '현재',
        description: 'Current situation and challenges',
        description_ko: '현재 상황과 도전',
      },
      {
        index: 2,
        name: 'Future',
        name_ko: '미래',
        description: 'Potential outcome and direction',
        description_ko: '잠재적 결과와 방향',
      },
    ],
  },
  'celtic-cross': {
    type: 'celtic-cross',
    name: 'Celtic Cross',
    name_ko: '켈틱 크로스',
    description: 'In-depth 10-card spread for comprehensive guidance',
    description_ko: '10장의 카드로 심층적인 조언을 받아보세요',
    cardCount: 10,
    positions: [
      {
        index: 0,
        name: 'Present',
        name_ko: '현재',
        description: 'The current situation',
        description_ko: '현재 상황',
      },
      {
        index: 1,
        name: 'Challenge',
        name_ko: '도전',
        description: 'The immediate challenge',
        description_ko: '즉각적인 도전',
      },
      {
        index: 2,
        name: 'Past',
        name_ko: '과거',
        description: 'Distant past foundation',
        description_ko: '먼 과거의 기반',
      },
      {
        index: 3,
        name: 'Future',
        name_ko: '미래',
        description: 'Near future',
        description_ko: '가까운 미래',
      },
      {
        index: 4,
        name: 'Above',
        name_ko: '위',
        description: 'Conscious goals',
        description_ko: '의식적 목표',
      },
      {
        index: 5,
        name: 'Below',
        name_ko: '아래',
        description: 'Unconscious influences',
        description_ko: '무의식적 영향',
      },
      {
        index: 6,
        name: 'Advice',
        name_ko: '조언',
        description: 'Advice and guidance',
        description_ko: '조언과 안내',
      },
      {
        index: 7,
        name: 'External',
        name_ko: '외부',
        description: 'External influences',
        description_ko: '외부 영향',
      },
      {
        index: 8,
        name: 'Hopes/Fears',
        name_ko: '희망/두려움',
        description: 'Hopes and fears',
        description_ko: '희망과 두려움',
      },
      {
        index: 9,
        name: 'Outcome',
        name_ko: '결과',
        description: 'Final outcome',
        description_ko: '최종 결과',
      },
    ],
  },
};

// ============================================================================
// Backend API Types (aligned with backend/src/schemas/reading.py)
// ============================================================================

/**
 * Reading request payload for backend API
 */
export interface ReadingRequest {
  question: string;  // 5-500 characters
  spread_type: 'one_card' | 'three_card_past_present_future' | 'three_card_situation_action_outcome';
  category?: 'love' | 'career' | 'finance' | 'health' | 'personal_growth' | 'spirituality' | null;
  user_context?: string | null;  // max 1000 characters
}

/**
 * Individual card in a reading (from backend)
 */
export interface ReadingCardResponse {
  id: number;  // ReadingCard ID
  reading_id: string;  // Reading UUID
  card_id: number;  // Card ID
  position: 'single' | 'past' | 'present' | 'future' | 'situation' | 'action' | 'outcome';
  orientation: 'upright' | 'reversed';
  interpretation: string;  // AI-generated interpretation
  key_message: string;  // One-line key message
  card: Card;  // Full card details
}

/**
 * Advice structure from backend
 */
export interface Advice {
  immediate_action: string;
  short_term: string;
  long_term: string;
  mindset: string;
  cautions: string;
}

/**
 * Complete reading response from backend API
 */
export interface ReadingResponse {
  id: string;  // UUID
  user_id: string | null;
  spread_type: string;
  question: string;
  category: string | null;
  cards: ReadingCardResponse[];
  card_relationships: string | null;  // For 3+ card spreads
  overall_reading: string;  // AI-generated overall reading
  advice: Advice;
  summary: string;  // One-line summary
  created_at: string;  // ISO 8601 datetime
  updated_at: string;  // ISO 8601 datetime
}

/**
 * Paginated reading list response from backend
 */
export interface ReadingListResponse {
  total: number;
  page: number;
  page_size: number;
  readings: ReadingResponse[];
}
