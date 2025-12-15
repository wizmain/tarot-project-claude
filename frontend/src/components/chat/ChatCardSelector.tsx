'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Card } from '@/types';
import { config } from '@/config/env';
import { shuffleArray } from '@/lib/utils';

interface ChatCardSelectorProps {
  cardCount: number;
  onCardsSelected: (cards: Card[], reversedStates: boolean[]) => void | Promise<void>;
  onCancel?: () => void;
  disabled?: boolean;
  allCards?: Card[];
}

export default function ChatCardSelector({
  cardCount,
  onCardsSelected,
  onCancel,
  disabled = false,
  allCards: providedCards,
}: ChatCardSelectorProps) {
  const [allCards, setAllCards] = useState<Card[]>(providedCards || []);
  const [selectedCards, setSelectedCards] = useState<number[]>([]);
  const [reversedStatesMap, setReversedStatesMap] = useState<Map<number, boolean>>(new Map());
  const [loading, setLoading] = useState(!providedCards);
  const [error, setError] = useState<string | null>(null);
  const [hasConfirmed, setHasConfirmed] = useState(false);

  const isInteractionDisabled = disabled || hasConfirmed;

  // Pre-determine reversed states for all cards when cards are loaded/shuffled
  useEffect(() => {
    if (allCards.length > 0) {
      const newReversedStatesMap = new Map<number, boolean>();
      allCards.forEach((card) => {
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
    fetchAllCards();
  }, [providedCards]);

  const fetchAllCards = async () => {
    try {
      setLoading(true);

      const apiBaseUrl = config.apiUrl.replace(/\/$/, '');
      const controller = new AbortController();
      const timeoutId = window.setTimeout(() => controller.abort(), 15000);

      const response = await fetch(`${apiBaseUrl}/api/v1/cards?page_size=78`, {
        signal: controller.signal,
      });

      window.clearTimeout(timeoutId);

      if (!response.ok) throw new Error('Failed to fetch cards');
      const data = await response.json();
      const cards: Card[] = data.cards || [];
      const shuffledCards = shuffleArray(cards);
      setAllCards(shuffledCards);
    } catch (err) {
      if ((err as Error).name === 'AbortError') {
        console.error('Card fetch timed out');
        setError('카드 데이터를 불러오는데 시간이 너무 오래 걸립니다.');
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
      if (prev.includes(cardId)) {
        return prev.filter((id) => id !== cardId);
      }
      if (prev.length < cardCount) {
        return [...prev, cardId];
      }
      return prev;
    });
  };

  const handleConfirm = async () => {
    if (selectedCards.length !== cardCount || isInteractionDisabled) return;

    const selected = selectedCards
      .map((id) => allCards.find((card) => card.id === id))
      .filter((card): card is Card => card !== undefined);

    const finalReversedStates = selectedCards.map((cardId) => 
      reversedStatesMap.get(cardId) ?? Math.random() < 0.3
    );

    setHasConfirmed(true);

    try {
      await onCardsSelected(selected, finalReversedStates);
    } catch (err) {
      console.error('카드 선택 처리 중 오류:', err);
      setHasConfirmed(false);
    }
  };

  const handleReset = () => {
    setSelectedCards([]);
    setHasConfirmed(false);
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center gap-2 py-4">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
        <p className="text-gray-600 dark:text-gray-400 text-sm">카드를 불러오는 중...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-3 text-center">
        <p className="text-red-600 dark:text-red-400 text-sm mb-2">{error}</p>
        <button
          onClick={fetchAllCards}
          className="px-4 py-1.5 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-semibold transition-all"
        >
          다시 시도
        </button>
      </div>
    );
  }

  return (
    <div className="w-full min-w-0 space-y-3">
      {/* Instructions */}
      <div className="text-center space-y-1">
        <h3 className="text-base font-semibold text-gray-900 dark:text-white">
          {cardCount}장의 카드를 선택하세요
        </h3>
        <p className="text-xs text-gray-600 dark:text-gray-400">
          선택된 카드: {selectedCards.length} / {cardCount}
        </p>
      </div>

      {/* Horizontal Scrollable Card List */}
      <div className="relative w-full min-w-0">
        {/* Left Fade Gradient */}
        <div className="absolute left-0 top-0 bottom-0 w-12 bg-gradient-to-r from-indigo-50 via-indigo-50/80 to-transparent dark:from-indigo-900/20 dark:via-indigo-900/10 dark:to-transparent pointer-events-none z-10" />

        {/* Right Fade Gradient */}
        <div className="absolute right-0 top-0 bottom-0 w-12 bg-gradient-to-l from-indigo-50 via-indigo-50/80 to-transparent dark:from-indigo-900/20 dark:via-indigo-900/10 dark:to-transparent pointer-events-none z-10" />

        <div className="overflow-x-auto overflow-y-visible pb-2 scrollbar-thin scrollbar-thumb-indigo-500 scrollbar-track-indigo-100 w-full">
          <div className="flex gap-2 px-2 py-2 w-max">
            {allCards.map((card, index) => {
              const isSelected = selectedCards.includes(card.id);
              const selectionOrder = selectedCards.indexOf(card.id);

              return (
                <motion.div
                  key={card.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.005 }}
                  onClick={() => handleCardClick(card.id)}
                  className={`
                    relative flex-shrink-0 w-16 h-24 rounded-md cursor-pointer transition-all
                    ${
                      isSelected
                        ? 'ring-2 ring-indigo-500 scale-105 shadow-lg'
                        : 'hover:scale-105 hover:shadow-md'
                    }
                    ${isInteractionDisabled ? 'opacity-50 cursor-not-allowed' : ''}
                  `}
                >
                  {/* Card Image */}
                  <div className="w-full h-full bg-gradient-to-br from-indigo-600 to-purple-600 dark:from-indigo-800 dark:to-purple-800 rounded-md border border-indigo-400 dark:border-indigo-600 flex flex-col items-center justify-center p-2 overflow-hidden">
                    {/* Card Back Pattern */}
                    <div className="w-full h-full flex items-center justify-center">
                      <div className="text-center">
                        <div className="text-xl mb-1 text-white">🌟</div>
                        <div className="text-[8px] text-indigo-100 dark:text-indigo-200 font-semibold">
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
                      className="absolute -top-1.5 -right-1.5 w-6 h-6 bg-indigo-600 rounded-full flex items-center justify-center text-white font-bold text-xs shadow-lg z-10 border border-white"
                    >
                      {selectionOrder + 1}
                    </motion.div>
                  )}

                  {/* Checkmark */}
                  {isSelected && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="absolute inset-0 bg-indigo-600/30 rounded-md flex items-center justify-center"
                    >
                      <div className="text-xl text-white drop-shadow-lg">✓</div>
                    </motion.div>
                  )}
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2 justify-center">
        {onCancel && (
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={onCancel}
            disabled={isInteractionDisabled}
            className={`px-4 py-1.5 rounded-lg text-sm font-semibold transition-all ${
              isInteractionDisabled
                ? 'bg-gray-300 cursor-not-allowed text-gray-500'
                : 'bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-900 dark:text-white'
            }`}
          >
            취소
          </motion.button>
        )}
        <motion.button
          whileHover={{ scale: selectedCards.length === cardCount ? 1.02 : 1 }}
          whileTap={{ scale: selectedCards.length === cardCount ? 0.98 : 1 }}
          onClick={handleReset}
          disabled={isInteractionDisabled || selectedCards.length === 0}
          className={`px-4 py-1.5 rounded-lg text-sm font-semibold transition-all ${
            isInteractionDisabled || selectedCards.length === 0
              ? 'bg-gray-300 cursor-not-allowed text-gray-500'
              : 'bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-900 dark:text-white'
          }`}
        >
          초기화
        </motion.button>
        <motion.button
          whileHover={{ scale: selectedCards.length === cardCount ? 1.05 : 1 }}
          whileTap={{ scale: selectedCards.length === cardCount ? 0.95 : 1 }}
          onClick={handleConfirm}
          disabled={isInteractionDisabled || selectedCards.length !== cardCount}
          className={`px-5 py-1.5 rounded-lg text-sm font-semibold shadow-md transition-all ${
            isInteractionDisabled || selectedCards.length !== cardCount
              ? 'bg-gray-400 cursor-not-allowed text-gray-700'
              : 'bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white'
          }`}
        >
          {selectedCards.length === cardCount
            ? '선택 완료'
            : `${cardCount - selectedCards.length}장 더`}
        </motion.button>
      </div>
    </div>
  );
}

