'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Card } from '@/types';
import { config } from '@/config/env';
import { shuffleArray } from '@/lib/utils';

interface CardSelectorProps {
  cardCount: number;
  onCardsSelected: (cards: Card[], reversedStates: boolean[]) => void | Promise<void>;
  disabled?: boolean;
  isAdmin?: boolean;  // Show admin info if true
  allCards?: Card[];  // Optional: Pre-fetched and shuffled cards from parent
  useParentScroll?: boolean;  // If true, parent container handles horizontal scrolling
}

export default function CardSelector({
  cardCount,
  onCardsSelected,
  disabled = false,
  isAdmin = false,
  allCards: providedCards,
  useParentScroll = false,
}: CardSelectorProps) {
  const [allCards, setAllCards] = useState<Card[]>(providedCards || []);
  const [selectedCards, setSelectedCards] = useState<number[]>([]);
  const [reversedStatesMap, setReversedStatesMap] = useState<Map<number, boolean>>(new Map());  // Track reversed states by card ID
  const [loading, setLoading] = useState(!providedCards);  // If cards provided, no need to load
  const [error, setError] = useState<string | null>(null);
  const [hasConfirmed, setHasConfirmed] = useState(false);

  const isInteractionDisabled = disabled || hasConfirmed;

  // Pre-determine reversed states for all cards when cards are loaded/shuffled
  // This ensures the same card always has the same reversed state during a session
  useEffect(() => {
    if (allCards.length > 0) {
      const newReversedStatesMap = new Map<number, boolean>();
      allCards.forEach((card) => {
        // Determine reversed state once when cards are loaded (30% chance)
        newReversedStatesMap.set(card.id, Math.random() < 0.3);
      });
      setReversedStatesMap(newReversedStatesMap);
    }
  }, [allCards]);

  // Use provided cards if available, otherwise fetch
  useEffect(() => {
    if (providedCards && providedCards.length > 0) {
      setAllCards(providedCards);
      setLoading(false);
      return;
    }
    // Only fetch if cards not provided
    fetchAllCards();
  }, [providedCards]);

  const fetchAllCards = async () => {
    try {
      setLoading(true);

      const apiBaseUrl = config.apiUrl.replace(/\/$/, '');
      console.log('[CardSelector V2] Fetching cards from configured API URL:', apiBaseUrl);

      const controller = new AbortController();
      const timeoutId = window.setTimeout(() => controller.abort(), 15000);

      const response = await fetch(`${apiBaseUrl}/api/v1/cards?page_size=78`, {
        signal: controller.signal,
      });

      window.clearTimeout(timeoutId);

      if (!response.ok) throw new Error('Failed to fetch cards');
      const data = await response.json();
      const cards: Card[] = data.cards || [];
      // Randomize card order for better user experience
      const shuffledCards = shuffleArray(cards);
      setAllCards(shuffledCards);
    } catch (err) {
      if ((err as Error).name === 'AbortError') {
        console.error('Card fetch timed out');
        setError('카드 데이터를 불러오는데 시간이 너무 오래 걸립니다. 잠시 후 다시 시도해주세요.');
        return;
      }
      console.error('Failed to load cards:', err);
      setError(err instanceof Error ? err.message : '카드 로딩에 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  const handleCardClick = (cardId: number) => {
    if (isInteractionDisabled) return;

    setSelectedCards((prev) => {
      // If already selected, remove it
      if (prev.includes(cardId)) {
        return prev.filter((id) => id !== cardId);
      }
      // If we haven't reached the limit, add it
      if (prev.length < cardCount) {
        return [...prev, cardId];
      }
      // If we're at the limit, do nothing
      return prev;
    });
  };

  const handleConfirm = async () => {
    if (selectedCards.length !== cardCount || isInteractionDisabled) return;

    const selected = selectedCards
      .map((id) => allCards.find((card) => card.id === id))
      .filter((card): card is Card => card !== undefined);

    // Use pre-calculated reversed states from map, in the order of selectedCards
    const finalReversedStates = selectedCards.map((cardId) => 
      reversedStatesMap.get(cardId) ?? Math.random() < 0.3
    );

    setHasConfirmed(true);

    try {
      await onCardsSelected(selected, finalReversedStates);
    } catch (err) {
      // 실패 시 다시 선택할 수 있도록 상태를 복구한다.
      console.error('카드 선택 처리 중 오류:', err);
      setHasConfirmed(false);
    }
  };

  const handleReset = () => {
    setSelectedCards([]);
    // Don't reset reversedStatesMap - it's determined when cards are loaded/shuffled
    setHasConfirmed(false);
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center gap-4 py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
        <p className="text-gray-600 dark:text-gray-400">카드를 불러오는 중...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-6 text-center">
        <p className="text-red-600 dark:text-red-400 mb-4">{error}</p>
        <button
          onClick={fetchAllCards}
          className="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-semibold transition-all"
        >
          다시 시도
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6 w-full max-w-full">
      {/* Instructions */}
      <div className="text-center space-y-2">
        <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
          {cardCount}장의 카드를 선택하세요
        </h3>
        <p className="text-gray-600 dark:text-gray-400">
          선택된 카드: {selectedCards.length} / {cardCount}
        </p>
      </div>

      {/* Horizontal Scrollable Card List */}
      <div className="relative w-full max-w-full">
        {/* Scroll Hint */}
        <div className="mb-3 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-purple-50 dark:bg-purple-900/20 rounded-full">
            <span className="text-purple-600 dark:text-purple-400 text-sm font-semibold">
              ← →
            </span>
            <span className="text-purple-600 dark:text-purple-400 text-xs">
              좌우로 스크롤하여 더 많은 카드를 확인하세요
            </span>
          </div>
        </div>

        <div className="relative">
          {/* Left Fade Gradient */}
          <div className="absolute left-0 top-0 bottom-0 w-20 bg-gradient-to-r from-white via-white/80 to-transparent dark:from-gray-800 dark:via-gray-800/80 dark:to-transparent pointer-events-none z-10" />
          
          {/* Right Fade Gradient */}
          <div className="absolute right-0 top-0 bottom-0 w-20 bg-gradient-to-l from-white via-white/80 to-transparent dark:from-gray-800 dark:via-gray-800/80 dark:to-transparent pointer-events-none z-10" />

          <div
            className={
              useParentScroll
                ? "pb-4 w-full"
                : "overflow-x-auto overflow-y-visible pb-4 scrollbar-thin scrollbar-thumb-purple-500 scrollbar-track-purple-100 w-full"
            }
          >
            <div className="flex gap-4 min-w-max px-4 py-4">
              {allCards.map((card, index) => {
                const isSelected = selectedCards.includes(card.id);
                const selectionOrder = selectedCards.indexOf(card.id);

                return (
                  <motion.div
                    key={card.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.01 }}
                    onClick={() => handleCardClick(card.id)}
                    className={`
                      relative flex-shrink-0 w-32 h-48 rounded-lg cursor-pointer transition-all
                      ${
                        isSelected
                          ? 'ring-4 ring-purple-500 scale-105 shadow-2xl'
                          : 'hover:scale-105 hover:shadow-lg'
                      }
                      ${isInteractionDisabled ? 'opacity-50 cursor-not-allowed' : ''}
                    `}
                  >
                    {/* Card Image */}
                    <div className="w-full h-full bg-gradient-to-br from-purple-600 to-indigo-600 dark:from-purple-800 dark:to-indigo-800 rounded-lg border-2 border-purple-400 dark:border-purple-600 flex flex-col items-center justify-center p-4 overflow-hidden">
                      {/* Card Back Pattern */}
                      <div className="w-full h-full flex items-center justify-center">
                        <div className="text-center">
                          <div className="text-4xl mb-2 text-white">🌟</div>
                          <div className="text-xs text-purple-100 dark:text-purple-200 font-semibold">
                            TAROT
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Selection Indicator */}
                    {isSelected && (
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        className="absolute -top-3 -right-3 w-10 h-10 bg-purple-600 rounded-full flex items-center justify-center text-white font-bold shadow-xl z-10 border-2 border-white"
                      >
                        {selectionOrder + 1}
                      </motion.div>
                    )}

                    {/* Checkmark */}
                    {isSelected && (
                      <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="absolute inset-0 bg-purple-600/20 rounded-lg flex items-center justify-center"
                      >
                        <div className="text-4xl text-white drop-shadow-lg">✓</div>
                      </motion.div>
                    )}
                  </motion.div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Scroll Indicator Arrows */}
        <div className="flex justify-between items-center mt-2 px-4">
          <div className="flex items-center gap-2 text-purple-600 dark:text-purple-400 text-sm">
            <span className="animate-pulse">←</span>
            <span className="text-xs">스크롤</span>
          </div>
          <div className="flex items-center gap-2 text-purple-600 dark:text-purple-400 text-sm">
            <span className="text-xs">스크롤</span>
            <span className="animate-pulse">→</span>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-4 justify-center">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleReset}
          disabled={isInteractionDisabled || selectedCards.length === 0}
          className={`px-6 py-3 rounded-lg font-semibold transition-all ${
            isInteractionDisabled || selectedCards.length === 0
              ? 'bg-gray-300 cursor-not-allowed text-gray-500'
              : 'bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-900 dark:text-white'
          }`}
        >
          선택 초기화
        </motion.button>

        <motion.button
          whileHover={{ scale: selectedCards.length === cardCount ? 1.05 : 1 }}
          whileTap={{ scale: selectedCards.length === cardCount ? 0.95 : 1 }}
          onClick={handleConfirm}
          disabled={isInteractionDisabled || selectedCards.length !== cardCount}
          className={`px-8 py-3 rounded-lg font-semibold text-lg shadow-lg transition-all ${
            isInteractionDisabled || selectedCards.length !== cardCount
              ? 'bg-gray-400 cursor-not-allowed text-gray-700'
              : 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white'
          }`}
        >
          {selectedCards.length === cardCount
            ? '선택 완료'
            : `${cardCount - selectedCards.length}장 더 선택하세요`}
        </motion.button>
      </div>

      {/* Admin Info Panel - Show selected card details */}
      {isAdmin && selectedCards.length > 0 && (
        <div className="mt-6 bg-amber-50 dark:bg-amber-900/20 border-2 border-amber-300 dark:border-amber-700 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-xl">👨‍💼</span>
            <h4 className="text-sm font-semibold text-amber-900 dark:text-amber-200">
              관리자 정보 - 선택된 카드
            </h4>
          </div>
          <div className="space-y-2">
            {selectedCards.map((cardId, index) => {
              const card = allCards.find(c => c.id === cardId);
              const isReversed = reversedStatesMap.get(cardId) ?? false;
              return (
                <div key={cardId} className="text-sm text-amber-800 dark:text-amber-300">
                  <span className="font-medium">{index + 1}번:</span>
                  <span className="ml-2 font-mono">#{cardId}</span>
                  {card && (
                    <>
                      <span className="ml-2">{card.name_ko || card.name}</span>
                      {card.arcana_type && (
                        <span className="ml-2 text-xs text-amber-600 dark:text-amber-400">
                          ({card.arcana_type === 'major' ? '대아르카나' : card.suit || '소아르카나'})
                        </span>
                      )}
                      {reversedStatesMap.has(cardId) && (
                        <span className="ml-2 text-xs font-semibold text-amber-700 dark:text-amber-500">
                          [{isReversed ? '역방향' : '정방향'}]
                        </span>
                      )}
                    </>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
