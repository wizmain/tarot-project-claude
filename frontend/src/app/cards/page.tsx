'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Card, ArcanaType, Suit } from '@/types';
import { cardAPI } from '@/lib/api';
import TarotCard from '@/components/TarotCard';
import { motion, AnimatePresence } from 'framer-motion';

export default function CardsPage() {
  const router = useRouter();
  const [cards, setCards] = useState<Card[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalCards, setTotalCards] = useState(0);
  const [selectedCard, setSelectedCard] = useState<Card | null>(null);

  // Filters
  const [arcanaFilter, setArcanaFilter] = useState<ArcanaType | undefined>();
  const [suitFilter, setSuitFilter] = useState<Suit | undefined>();
  const [searchQuery, setSearchQuery] = useState('');

  const pageSize = 12;

  const loadCards = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await cardAPI.getCards({
        page,
        page_size: pageSize,
        arcana_type: arcanaFilter,
        suit: suitFilter,
        search: searchQuery || undefined,
      });
      setCards(response.cards);
      setTotalCards(response.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load cards');
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, arcanaFilter, suitFilter, searchQuery]);

  useEffect(() => {
    loadCards();
  }, [loadCards]);

  const resetFilters = () => {
    setArcanaFilter(undefined);
    setSuitFilter(undefined);
    setSearchQuery('');
    setPage(1);
  };

  const totalPages = Math.ceil(totalCards / pageSize);

  return (
    <main className="min-h-screen p-8 bg-gradient-to-br from-purple-50 to-indigo-100 dark:from-gray-900 dark:to-indigo-950">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.push('/')}
            className="mb-4 text-purple-600 dark:text-purple-400 hover:underline"
          >
            ← 홈으로 돌아가기
          </button>
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
            📚 타로 카드 컬렉션
          </h1>
          <p className="text-gray-600 dark:text-gray-300">
            총 {totalCards}장의 타로 카드를 확인하세요
          </p>
        </div>

        {/* Filters */}
        <div className="mb-6 bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Search */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                검색
              </label>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setPage(1);
                }}
                placeholder="카드 이름으로 검색..."
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>

            {/* Arcana Type Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                아르카나 타입
              </label>
              <select
                value={arcanaFilter || ''}
                onChange={(e) => {
                  setArcanaFilter(e.target.value as ArcanaType || undefined);
                  setPage(1);
                }}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="">전체</option>
                <option value="major">Major Arcana</option>
                <option value="minor">Minor Arcana</option>
              </select>
            </div>

            {/* Suit Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                수트
              </label>
              <select
                value={suitFilter || ''}
                onChange={(e) => {
                  setSuitFilter(e.target.value as Suit || undefined);
                  setPage(1);
                }}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                disabled={arcanaFilter === 'major'}
              >
                <option value="">전체</option>
                <option value="wands">Wands (완드)</option>
                <option value="cups">Cups (컵)</option>
                <option value="swords">Swords (검)</option>
                <option value="pentacles">Pentacles (펜타클)</option>
              </select>
            </div>
          </div>

          {/* Reset Button */}
          {(arcanaFilter || suitFilter || searchQuery) && (
            <div className="mt-4">
              <button
                onClick={resetFilters}
                className="px-4 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-900 dark:text-white rounded-lg transition-colors"
              >
                필터 초기화
              </button>
            </div>
          )}
        </div>

        {/* Loading State */}
        {loading && (
          <div className="flex justify-center items-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-400 dark:border-red-700 text-red-700 dark:text-red-400 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {/* Cards Grid */}
        {!loading && !error && (
          <>
            {cards.length === 0 ? (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-12 text-center">
                <div className="text-6xl mb-4">🔍</div>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                  카드를 찾을 수 없습니다
                </h2>
                <p className="text-gray-600 dark:text-gray-400 mb-6">
                  다른 필터나 검색어를 시도해보세요
                </p>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4 mb-8">
                  {cards.map((card, index) => (
                    <motion.div
                      key={card.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="flex justify-center"
                    >
                      <div
                        onClick={() => setSelectedCard(card)}
                        className="cursor-pointer hover:scale-105 transition-transform"
                      >
                        <TarotCard card={card} size="small" isRevealed={true} />
                      </div>
                    </motion.div>
                  ))}
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="flex justify-center items-center gap-2">
                    <button
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={page === 1}
                      className="px-4 py-2 bg-purple-600 text-white rounded disabled:bg-gray-300 disabled:cursor-not-allowed hover:bg-purple-700 transition-colors"
                    >
                      이전
                    </button>

                    <span className="px-4 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-white rounded shadow">
                      {page} / {totalPages}
                    </span>

                    <button
                      onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                      disabled={page === totalPages}
                      className="px-4 py-2 bg-purple-600 text-white rounded disabled:bg-gray-300 disabled:cursor-not-allowed hover:bg-purple-700 transition-colors"
                    >
                      다음
                    </button>
                  </div>
                )}
              </>
            )}
          </>
        )}
      </div>

      {/* Card Detail Modal */}
      <AnimatePresence>
        {selectedCard && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
            onClick={() => setSelectedCard(null)}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              className="bg-white dark:bg-gray-800 rounded-lg shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto p-8"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Close Button */}
              <button
                onClick={() => setSelectedCard(null)}
                className="float-right text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 text-2xl"
              >
                ×
              </button>

              <div className="grid md:grid-cols-2 gap-8">
                {/* Card Image */}
                <div className="flex justify-center items-start">
                  <TarotCard card={selectedCard} size="large" isRevealed={true} />
                </div>

                {/* Card Info */}
                <div>
                  <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                    {selectedCard.name_ko}
                  </h2>
                  <p className="text-xl text-gray-600 dark:text-gray-400 mb-4">
                    {selectedCard.name}
                  </p>

                  {/* Card Type */}
                  <div className="mb-6">
                    <span className="inline-block px-3 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-full text-sm font-semibold mr-2">
                      {selectedCard.arcana_type === 'major' ? 'Major Arcana' : 'Minor Arcana'}
                    </span>
                    {selectedCard.suit && (
                      <span className="inline-block px-3 py-1 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 rounded-full text-sm font-semibold">
                        {selectedCard.suit.charAt(0).toUpperCase() + selectedCard.suit.slice(1)}
                      </span>
                    )}
                  </div>

                  {/* Description */}
                  {selectedCard.description && (
                    <div className="mb-6">
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                        설명
                      </h3>
                      <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                        {selectedCard.description}
                      </p>
                    </div>
                  )}

                  {/* Upright Keywords */}
                  <div className="mb-4">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                      정방향 키워드
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {selectedCard.keywords_upright.map((keyword, i) => (
                        <span
                          key={i}
                          className="px-3 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full text-sm"
                        >
                          {keyword}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Reversed Keywords */}
                  <div className="mb-4">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                      역방향 키워드
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {selectedCard.keywords_reversed.map((keyword, i) => (
                        <span
                          key={i}
                          className="px-3 py-1 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-full text-sm"
                        >
                          {keyword}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Upright Meaning */}
                  <div className="mb-4">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                      정방향 의미
                    </h3>
                    <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                      {selectedCard.meaning_upright}
                    </p>
                  </div>

                  {/* Reversed Meaning */}
                  <div className="mb-4">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                      역방향 의미
                    </h3>
                    <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                      {selectedCard.meaning_reversed}
                    </p>
                  </div>

                  {/* Symbolism */}
                  {selectedCard.symbolism && (
                    <div className="mb-4">
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                        상징
                      </h3>
                      <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                        {selectedCard.symbolism}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </main>
  );
}
