'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card } from '@/types';
import { config } from '@/config/env';
import { shuffleArray } from '@/lib/utils';
import CelticCrossLayout, { CelticCrossPosition } from './CelticCrossLayout';
import TarotCard from './TarotCard';

interface CelticCrossCardSelectorProps {
  positions: CelticCrossPosition[];
  onCardsSelected: (cards: Card[], reversedStates: boolean[], positionOrder: number[]) => void | Promise<void>;
  disabled?: boolean;
  isAdmin?: boolean;
  allCards?: Card[];
}

export default function CelticCrossCardSelector({
  positions,
  onCardsSelected,
  disabled = false,
  isAdmin = false,
  allCards: providedCards,
}: CelticCrossCardSelectorProps) {
  const [allCards, setAllCards] = useState<Card[]>(providedCards || []);
  const [selectedCards, setSelectedCards] = useState<Map<number, Card & { isReversed: boolean; positionIndex: number }>>(new Map());
  const [selectedCardIds, setSelectedCardIds] = useState<Set<number>>(new Set());
  const [reversedStatesMap, setReversedStatesMap] = useState<Map<number, boolean>>(new Map());
  const [positionOrder, setPositionOrder] = useState<number[]>([]); // Track which position each card goes to
  const [loading, setLoading] = useState(!providedCards);
  const [error, setError] = useState<string | null>(null);
  const [hasConfirmed, setHasConfirmed] = useState(false);
  const [currentPositionIndex, setCurrentPositionIndex] = useState(0); // Track which position we're selecting for

  const isInteractionDisabled = disabled || hasConfirmed;

  // Pre-determine reversed states for all cards
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
      const cards: Card[] = data.items || data.cards || [];
      const shuffledCards = shuffleArray(cards);
      setAllCards(shuffledCards);
    } catch (err) {
      if ((err as Error).name === 'AbortError') {
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
    if (isInteractionDisabled || selectedCardIds.has(cardId)) return;
    if (currentPositionIndex >= positions.length) return; // All positions filled

    const card = allCards.find(c => c.id === cardId);
    if (!card) return;

    const isReversed = reversedStatesMap.get(cardId) ?? Math.random() < 0.3;
    const positionIdx = currentPositionIndex;

    // Add card to selected cards map
    const newSelectedCards = new Map(selectedCards);
    newSelectedCards.set(positionIdx, { ...card, isReversed, positionIndex: positionIdx });
    setSelectedCards(newSelectedCards);

    // Add to selected IDs
    const newSelectedIds = new Set(selectedCardIds);
    newSelectedIds.add(cardId);
    setSelectedCardIds(newSelectedIds);

    // Update position order
    const newPositionOrder = [...positionOrder, positionIdx];
    setPositionOrder(newPositionOrder);

    // Move to next position
    setCurrentPositionIndex(positionIdx + 1);
  };

  const handlePositionClick = (positionIndex: number) => {
    if (isInteractionDisabled) return;
    
    // Remove card from this position
    const cardAtPosition = selectedCards.get(positionIndex);
    if (cardAtPosition) {
      const newSelectedCards = new Map(selectedCards);
      newSelectedCards.delete(positionIndex);
      setSelectedCards(newSelectedCards);

      const newSelectedIds = new Set(selectedCardIds);
      newSelectedIds.delete(cardAtPosition.id);
      setSelectedCardIds(newSelectedIds);

      const newPositionOrder = positionOrder.filter(idx => idx !== positionIndex);
      setPositionOrder(newPositionOrder);

      // Update current position index
      setCurrentPositionIndex(Math.min(currentPositionIndex, positionIndex));
    }
  };

  const handleConfirm = async () => {
    if (selectedCards.size !== positions.length || isInteractionDisabled) return;

    // Build arrays in position order
    const cards: Card[] = [];
    const reversedStates: boolean[] = [];
    const finalPositionOrder: number[] = [];

    for (let i = 0; i < positions.length; i++) {
      const cardData = selectedCards.get(i);
      if (cardData) {
        cards.push(cardData);
        reversedStates.push(cardData.isReversed);
        finalPositionOrder.push(i);
      }
    }

    setHasConfirmed(true);

    try {
      await onCardsSelected(cards, reversedStates, finalPositionOrder);
    } catch (err) {
      console.error('카드 선택 처리 중 오류:', err);
      setHasConfirmed(false);
    }
  };

  const handleReset = () => {
    setSelectedCards(new Map());
    setSelectedCardIds(new Set());
    setPositionOrder([]);
    setCurrentPositionIndex(0);
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

  // Build selected cards map for layout
  const layoutSelectedCards = new Map<number, Card & { isReversed: boolean }>();
  selectedCards.forEach((cardData, positionIdx) => {
    layoutSelectedCards.set(positionIdx, {
      ...cardData,
      isReversed: cardData.isReversed,
    });
  });

  return (
    <div className="space-y-8">
      {/* Instructions */}
      <div className="text-center space-y-2">
        <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
          {currentPositionIndex < positions.length
            ? `${positions[currentPositionIndex].name_ko} 포지션에 카드를 선택하세요`
            : '모든 카드가 선택되었습니다'}
        </h3>
        <p className="text-gray-600 dark:text-gray-400">
          선택된 카드: {selectedCards.size} / {positions.length}
        </p>
      </div>

      {/* Celtic Cross Layout */}
      <CelticCrossLayout
        positions={positions}
        selectedCards={layoutSelectedCards}
        onPositionClick={handlePositionClick}
        disabled={isInteractionDisabled}
      />

      {/* Card List */}
      <div className="relative">
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

          <div className="overflow-x-auto overflow-y-visible pb-4 scrollbar-thin scrollbar-thumb-purple-500 scrollbar-track-purple-100">
            <div className="flex gap-4 min-w-max px-4 py-4">
              <AnimatePresence>
                {allCards.map((card, index) => {
                  const isSelected = selectedCardIds.has(card.id);
                  const positionIdx = Array.from(selectedCards.values()).find(c => c.id === card.id)?.positionIndex;

                  return (
                    <motion.div
                      key={card.id}
                      layoutId={isSelected ? `card-${card.id}` : undefined}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: isSelected ? 0.3 : 1, y: 0 }}
                      exit={{ opacity: 0, scale: 0.8 }}
                      transition={{ delay: index * 0.01 }}
                      onClick={() => handleCardClick(card.id)}
                      className={`
                        relative flex-shrink-0 w-32 h-48 rounded-lg cursor-pointer transition-all
                        ${isSelected ? 'opacity-30 cursor-not-allowed' : 'hover:scale-105 hover:shadow-lg'}
                        ${isInteractionDisabled ? 'opacity-50 cursor-not-allowed' : ''}
                      `}
                    >
                      {/* Card Back */}
                      <div className="w-full h-full bg-gradient-to-br from-purple-600 to-indigo-600 dark:from-purple-800 dark:to-indigo-800 rounded-lg border-2 border-purple-400 dark:border-purple-600 flex flex-col items-center justify-center p-4 overflow-hidden">
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
                      {isSelected && positionIdx !== undefined && (
                        <motion.div
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          className="absolute -top-3 -right-3 w-10 h-10 bg-purple-600 rounded-full flex items-center justify-center text-white font-bold shadow-xl z-10 border-2 border-white"
                        >
                          {positionIdx + 1}
                        </motion.div>
                      )}
                    </motion.div>
                  );
                })}
              </AnimatePresence>
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
          disabled={isInteractionDisabled || selectedCards.size === 0}
          className={`px-6 py-3 rounded-lg font-semibold transition-all ${
            isInteractionDisabled || selectedCards.size === 0
              ? 'bg-gray-300 cursor-not-allowed text-gray-500'
              : 'bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-900 dark:text-white'
          }`}
        >
          선택 초기화
        </motion.button>

        <motion.button
          whileHover={{ scale: selectedCards.size === positions.length ? 1.05 : 1 }}
          whileTap={{ scale: selectedCards.size === positions.length ? 0.95 : 1 }}
          onClick={handleConfirm}
          disabled={isInteractionDisabled || selectedCards.size !== positions.length}
          className={`px-8 py-3 rounded-lg font-semibold text-lg shadow-lg transition-all ${
            isInteractionDisabled || selectedCards.size !== positions.length
              ? 'bg-gray-400 cursor-not-allowed text-gray-700'
              : 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white'
          }`}
        >
          {selectedCards.size === positions.length
            ? '선택 완료'
            : `${positions.length - selectedCards.size}장 더 선택하세요`}
        </motion.button>
      </div>

      {/* Admin Info Panel */}
      {isAdmin && selectedCards.size > 0 && (
        <div className="mt-6 bg-amber-50 dark:bg-amber-900/20 border-2 border-amber-300 dark:border-amber-700 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-xl">👨‍💼</span>
            <h4 className="text-sm font-semibold text-amber-900 dark:text-amber-200">
              관리자 정보 - 선택된 카드
            </h4>
          </div>
          <div className="space-y-2">
            {Array.from(selectedCards.entries())
              .sort(([a], [b]) => a - b)
              .map(([positionIdx, cardData]) => (
                <div key={positionIdx} className="text-sm text-amber-800 dark:text-amber-300">
                  <span className="font-medium">{positions[positionIdx].name_ko} ({positionIdx + 1}번):</span>
                  <span className="ml-2 font-mono">#{cardData.id}</span>
                  <span className="ml-2">{cardData.name_ko || cardData.name}</span>
                  <span className="ml-2 text-xs font-semibold">
                    [{cardData.isReversed ? '역방향' : '정방향'}]
                  </span>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}

