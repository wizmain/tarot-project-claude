'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card } from '@/types';
import { API_BASE_URL } from '@/lib/constants';

interface CardDeckProps {
  cardCount: number;
  onCardsDrawn: (cards: Card[], reversedStates: boolean[]) => void;
  disabled?: boolean;
}

export default function CardDeck({
  cardCount,
  onCardsDrawn,
  disabled = false,
}: CardDeckProps) {
  const [isShuffling, setIsShuffling] = useState(false);
  const [drawnCount, setDrawnCount] = useState(0);
  const [allCards, setAllCards] = useState<Card[]>([]);

  const handleShuffle = async () => {
    if (disabled || isShuffling) return;

    setIsShuffling(true);
    setDrawnCount(0);

    // Simulate shuffling animation
    await new Promise((resolve) => setTimeout(resolve, 1500));

    // Fetch random cards from backend
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/cards/random/draw?count=${cardCount}`
      );
      const cards = await response.json();

      // Randomly determine if each card is reversed (30% chance)
      const reversedStates = cards.map(() => Math.random() < 0.3);

      setAllCards(cards);
      setIsShuffling(false);

      // Draw cards one by one
      drawCardsSequentially(cards, reversedStates);
    } catch (error) {
      console.error('Failed to draw cards:', error);
      setIsShuffling(false);
    }
  };

  const drawCardsSequentially = (cards: Card[], reversedStates: boolean[]) => {
    let count = 0;
    const interval = setInterval(() => {
      count++;
      setDrawnCount(count);

      if (count >= cardCount) {
        clearInterval(interval);
        onCardsDrawn(cards, reversedStates);
      }
    }, 600);
  };

  return (
    <div className="flex flex-col items-center gap-8">
      {/* Card Deck Display */}
      <div className="relative w-64 h-96">
        <AnimatePresence>
          {!isShuffling && drawnCount === 0 && (
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              className="absolute inset-0"
            >
              {/* Stack of cards */}
              {[0, 1, 2, 3, 4].map((index) => (
                <motion.div
                  key={index}
                  className="absolute inset-0 bg-gradient-to-br from-purple-900 via-indigo-800 to-purple-900 rounded-lg border-4 border-yellow-600 shadow-2xl"
                  style={{
                    transform: `translateY(${index * -4}px) translateX(${
                      index * 2
                    }px) rotate(${index * 0.5}deg)`,
                    zIndex: 5 - index,
                  }}
                  animate={
                    isShuffling
                      ? {
                          y: [0, -20, 0],
                          rotate: [0, 5, -5, 0],
                        }
                      : {}
                  }
                  transition={{
                    duration: 0.5,
                    repeat: isShuffling ? Infinity : 0,
                    delay: index * 0.1,
                  }}
                >
                  <div className="w-full h-full flex items-center justify-center p-8">
                    <div className="text-center">
                      <div className="text-yellow-300 text-8xl mb-4">✦</div>
                      <div className="text-yellow-300 text-2xl font-serif tracking-widest">
                        TAROT
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </motion.div>
          )}

          {isShuffling && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 flex items-center justify-center"
            >
              <div className="text-center">
                <motion.div
                  animate={{
                    rotate: 360,
                    scale: [1, 1.2, 1],
                  }}
                  transition={{
                    duration: 1.5,
                    repeat: Infinity,
                    ease: 'linear',
                  }}
                  className="text-purple-600 text-8xl mb-4"
                >
                  ✦
                </motion.div>
                <p className="text-purple-600 dark:text-purple-400 text-xl font-semibold">
                  카드를 섞는 중...
                </p>
              </div>
            </motion.div>
          )}

          {drawnCount > 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="absolute inset-0 flex items-center justify-center"
            >
              <div className="text-center">
                <div className="text-green-600 dark:text-green-400 text-6xl mb-4">
                  ✓
                </div>
                <p className="text-gray-700 dark:text-gray-300 text-lg">
                  {drawnCount}장의 카드를 뽑았습니다
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Shuffle Button */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={handleShuffle}
        disabled={disabled || isShuffling || drawnCount > 0}
        className={`px-8 py-4 rounded-lg font-semibold text-lg shadow-lg transition-all ${
          disabled || isShuffling || drawnCount > 0
            ? 'bg-gray-400 cursor-not-allowed text-gray-700'
            : 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white'
        }`}
      >
        {isShuffling
          ? '섞는 중...'
          : drawnCount > 0
          ? '카드 뽑기 완료'
          : `카드 ${cardCount}장 뽑기`}
      </motion.button>

      {drawnCount > 0 && (
        <p className="text-sm text-gray-500 dark:text-gray-400">
          아래로 스크롤하여 카드를 확인하세요
        </p>
      )}
    </div>
  );
}
