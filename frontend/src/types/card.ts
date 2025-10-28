/**
 * Tarot Card Types
 */

export type ArcanaType = 'major' | 'minor';
export type Suit = 'wands' | 'cups' | 'swords' | 'pentacles';

export interface Card {
  id: number;
  name: string;
  name_ko: string;
  number: number | null;
  arcana_type: ArcanaType;
  suit: Suit | null;
  keywords_upright: string[];
  keywords_reversed: string[];
  meaning_upright: string;
  meaning_reversed: string;
  description: string | null;
  symbolism: string | null;
  image_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface CardListResponse {
  total: number;
  page: number;
  page_size: number;
  cards: Card[];
}

export interface DrawnCard {
  card: Card;
  is_reversed: boolean;
  position: number;
}

export interface CardDrawRequest {
  count: number;
  allow_reversed?: boolean;
  arcana_filter?: ArcanaType;
  suit_filter?: Suit;
}
