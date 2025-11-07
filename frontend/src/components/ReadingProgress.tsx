/**
 * Reading Progress Component
 *
 * Displays real-time progress during tarot reading generation with SSE
 */
'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { ProgressEvent, CardDrawnEvent, ReadingStage } from '@/lib/sse-client';
import type { Card } from '@/types';
import TarotCard from './TarotCard';

interface ReadingProgressProps {
  isStreaming: boolean;
  progress: number;
  stage: ReadingStage | null;
  message: string;
  drawnCards: CardDrawnEvent[];
  allCards?: Card[];
  error?: string;
  onRetry?: () => void;
}

const stageLabels: Record<ReadingStage, string> = {
  initializing: '준비 중',
  drawing_cards: '카드 선택',
  enriching_context: '의미 분석',
  generating_ai: 'AI 해석',
  finalizing: '저장 중',
  completed: '완료',
};

const stageEmojis: Record<ReadingStage, string> = {
  initializing: '✨',
  drawing_cards: '🎴',
  enriching_context: '📚',
  generating_ai: '🤖',
  finalizing: '💾',
  completed: '✅',
};

export default function ReadingProgress({
  isStreaming,
  progress,
  stage,
  message,
  drawnCards,
  allCards,
  error,
  onRetry,
}: ReadingProgressProps) {
  if (!isStreaming && !error) {
    return null;
  }

  // Helper function to find card by ID
  const findCardById = (cardId: number): Card | null => {
    return allCards?.find(card => card.id === cardId) || null;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="w-full max-w-2xl mx-auto p-6 bg-white dark:bg-gray-800 rounded-lg shadow-lg"
    >
      {/* Error State */}
      {error && (
        <div className="text-center">
          <div className="text-6xl mb-4">❌</div>
          <h3 className="text-xl font-bold text-red-600 dark:text-red-400 mb-2">
            오류가 발생했습니다
          </h3>
          <p className="text-gray-600 dark:text-gray-300 mb-4">{error}</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors shadow-md"
            >
              다시 시도하기
            </button>
          )}
        </div>
      )}

      {/* Loading State */}
      {!error && (
        <>
          {/* Stage Indicator */}
          <div className="text-center mb-6">
            <motion.div
              key={stage}
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="text-6xl mb-3"
            >
              {stage && stageEmojis[stage]}
            </motion.div>
            <h3 className="text-xl font-bold text-gray-800 dark:text-gray-100 mb-1">
              {stage && stageLabels[stage]}
            </h3>
            <p className="text-gray-600 dark:text-gray-300 text-sm">
              {message}
            </p>
          </div>

          {/* Progress Bar */}
          <div className="mb-6">
            <div className="flex justify-between text-sm text-gray-600 dark:text-gray-300 mb-2">
              <span>진행률</span>
              <span className="font-semibold">{progress}%</span>
            </div>
            <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-purple-500 via-pink-500 to-purple-600"
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.5, ease: 'easeOut' }}
              />
            </div>
          </div>

          {/* Drawn Cards */}
          {drawnCards.length > 0 && (
            <div className="space-y-4">
              <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-3">
                뽑힌 카드
              </h4>
              <AnimatePresence>
                {drawnCards.map((drawnCard, index) => {
                  const fullCard = findCardById(drawnCard.card_id);

                  return (
                    <motion.div
                      key={`${drawnCard.card_id}-${index}`}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="flex items-center gap-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg"
                    >
                      {/* Card Image */}
                      {fullCard ? (
                        <div className="flex-shrink-0">
                          <TarotCard
                            card={fullCard}
                            isRevealed={true}
                            isReversed={drawnCard.is_reversed}
                            size="small"
                          />
                        </div>
                      ) : (
                        <div className="text-2xl">🎴</div>
                      )}

                      {/* Card Info */}
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs font-medium text-purple-600 dark:text-purple-400 uppercase">
                            {drawnCard.position}
                          </span>
                          {drawnCard.is_reversed && (
                            <span className="text-xs px-2 py-0.5 bg-orange-100 dark:bg-orange-900 text-orange-700 dark:text-orange-200 rounded">
                              역방향
                            </span>
                          )}
                        </div>
                        <p className="font-medium text-gray-800 dark:text-gray-100">
                          {drawnCard.card_name_ko}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {drawnCard.card_name}
                        </p>
                      </div>
                    </motion.div>
                  );
                })}
              </AnimatePresence>
            </div>
          )}

          {/* Loading Animation */}
          <div className="flex justify-center mt-6">
            <div className="flex gap-2">
              {[0, 1, 2].map((i) => (
                <motion.div
                  key={i}
                  className="w-3 h-3 bg-purple-500 rounded-full"
                  animate={{
                    scale: [1, 1.2, 1],
                    opacity: [0.5, 1, 0.5],
                  }}
                  transition={{
                    duration: 1.5,
                    repeat: Infinity,
                    delay: i * 0.2,
                  }}
                />
              ))}
            </div>
          </div>
        </>
      )}
    </motion.div>
  );
}
