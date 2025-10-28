'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Card } from '@/types';
import { API_BASE_URL } from '@/lib/constants';

interface CardSelectorProps {
  cardCount: number;
  onCardsSelected: (cards: Card[], reversedStates: boolean[]) => void;
  disabled?: boolean;
}

export default function CardSelector({
  cardCount,
  onCardsSelected,
  disabled = false,
}: CardSelectorProps) {
  const [allCards, setAllCards] = useState<Card[]>([]);
  const [selectedCards, setSelectedCards] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch all cards on mount
  useEffect(() => {
    fetchAllCards();
  }, []);

  const fetchAllCards = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/v1/cards?page_size=78`);
      if (!response.ok) throw new Error('Failed to fetch cards');
      const data = await response.json();
      setAllCards(data.cards || []);
    } catch (err) {
      console.error('Failed to load cards:', err);
      setError(err instanceof Error ? err.message : '카드 로딩에 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  const handleCardClick = (cardId: number) => {
    if (disabled) return;

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

  const handleConfirm = () => {
    if (selectedCards.length !== cardCount) return;

    const selected = selectedCards
      .map((id) => allCards.find((card) => card.id === id))
      .filter((card): card is Card => card !== undefined);

    // Randomly determine if each card is reversed (30% chance)
    const reversedStates = selected.map(() => Math.random() < 0.3);

    onCardsSelected(selected, reversedStates);
  };

  const handleReset = () => {
    setSelectedCards([]);
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
    <div className="space-y-6">
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
      <div className="relative">
        <div className="overflow-x-auto overflow-y-visible pb-4 scrollbar-thin scrollbar-thumb-purple-500 scrollbar-track-purple-100">
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
                    ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
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

        {/* Scroll Hint */}
        <div className="absolute right-0 top-0 bottom-0 w-16 bg-gradient-to-l from-purple-50 to-transparent dark:from-gray-900 pointer-events-none" />
      </div>

      {/* Action Buttons */}
      <div className="flex gap-4 justify-center">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleReset}
          disabled={disabled || selectedCards.length === 0}
          className={`px-6 py-3 rounded-lg font-semibold transition-all ${
            disabled || selectedCards.length === 0
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
          disabled={disabled || selectedCards.length !== cardCount}
          className={`px-8 py-3 rounded-lg font-semibold text-lg shadow-lg transition-all ${
            disabled || selectedCards.length !== cardCount
              ? 'bg-gray-400 cursor-not-allowed text-gray-700'
              : 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white'
          }`}
        >
          {selectedCards.length === cardCount
            ? '선택 완료'
            : `${cardCount - selectedCards.length}장 더 선택하세요`}
        </motion.button>
      </div>
    </div>
  );
}
