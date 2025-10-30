'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { ReadingResponse } from '@/types/reading';
import { readingAPI } from '@/lib/api';
import { motion } from 'framer-motion';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

const SPREAD_TYPE_LABELS: Record<string, string> = {
  'one_card': '원카드',
  'three_card_past_present_future': '쓰리카드 (과거/현재/미래)',
  'three_card_situation_action_outcome': '쓰리카드 (상황/행동/결과)',
};

function HistoryPageContent() {
  const router = useRouter();
  const [readings, setReadings] = useState<ReadingResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [selectedSpread, setSelectedSpread] = useState<string | undefined>();

  const pageSize = 10;

  const fetchReadings = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await readingAPI.getReadings({
        page,
        page_size: pageSize,
        spread_type: selectedSpread,
      });

      setReadings(response.readings);
      setTotal(response.total);
    } catch (err) {
      console.error('Failed to fetch readings:', err);
      setError(err instanceof Error ? err.message : '리딩 목록을 불러오는데 실패했습니다');
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, selectedSpread]);

  useEffect(() => {
    fetchReadings();
  }, [fetchReadings]);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
  };

  const totalPages = Math.ceil(total / pageSize);

  return (
    <main className="min-h-screen p-8 bg-gradient-to-br from-purple-50 to-indigo-100 dark:from-gray-900 dark:to-indigo-950">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8 text-center">
          <button
            onClick={() => router.push('/')}
            className="mb-4 text-purple-600 dark:text-purple-400 hover:underline"
          >
            ← 홈으로 돌아가기
          </button>
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
            📖 리딩 히스토리
          </h1>
          <p className="text-gray-600 dark:text-gray-300">
            이전에 받은 타로 리딩을 다시 확인해보세요
          </p>
        </div>

        {/* Filter */}
        <div className="mb-6 bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            스프레드 타입 필터
          </label>
          <select
            value={selectedSpread || ''}
            onChange={(e) => {
              setSelectedSpread(e.target.value || undefined);
              setPage(1);
            }}
            className="w-full md:w-64 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          >
            <option value="">전체</option>
            <option value="one_card">원카드</option>
            <option value="three_card_past_present_future">쓰리카드 (과거/현재/미래)</option>
            <option value="three_card_situation_action_outcome">쓰리카드 (상황/행동/결과)</option>
          </select>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-12 text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-purple-600 mx-auto mb-4"></div>
            <p className="text-gray-600 dark:text-gray-400">리딩 목록을 불러오는 중...</p>
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <div className="bg-red-50 dark:bg-red-900/20 rounded-lg shadow-lg p-6">
            <p className="text-red-600 dark:text-red-400 mb-4">{error}</p>
            <button
              onClick={fetchReadings}
              className="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-semibold transition-all"
            >
              다시 시도
            </button>
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && readings.length === 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-12 text-center">
            <div className="text-6xl mb-4">🔮</div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              아직 리딩 기록이 없습니다
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              첫 번째 타로 리딩을 받아보세요!
            </p>
            <button
              onClick={() => router.push('/')}
              className="px-6 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-lg font-semibold transition-all shadow-lg"
            >
              리딩 시작하기
            </button>
          </div>
        )}

        {/* Readings List */}
        {!loading && !error && readings.length > 0 && (
          <div className="space-y-4">
            {readings.map((reading, index) => (
              <motion.div
                key={reading.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                onClick={() => router.push(`/history/detail?id=${reading.id}`)}
                className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow cursor-pointer"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    {/* Spread Type Badge */}
                    <span className="inline-block px-3 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-full text-sm font-semibold mb-3">
                      {SPREAD_TYPE_LABELS[reading.spread_type] || reading.spread_type}
                    </span>

                    {/* Question */}
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                      {reading.question}
                    </h3>

                    {/* Summary */}
                    <p className="text-gray-600 dark:text-gray-300 mb-3 line-clamp-2">
                      {reading.summary}
                    </p>

                    {/* Cards Preview */}
                    <div className="flex flex-wrap gap-2 mb-3">
                      {reading.cards.slice(0, 3).map((cardData, i) => (
                        <span
                          key={i}
                          className="text-sm px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded"
                        >
                          {cardData.card.name_ko}
                          {cardData.orientation === 'reversed' && ' (역방향)'}
                        </span>
                      ))}
                      {reading.cards.length > 3 && (
                        <span className="text-sm px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 rounded">
                          +{reading.cards.length - 3}
                        </span>
                      )}
                    </div>

                    {/* Date */}
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {formatDate(reading.created_at)}
                    </p>
                  </div>

                  {/* Arrow */}
                  <div className="ml-4 text-purple-600 dark:text-purple-400">
                    →
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}

        {/* Pagination */}
        {!loading && !error && totalPages > 1 && (
          <div className="mt-8 flex justify-center items-center gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-4 py-2 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              이전
            </button>

            <span className="px-4 py-2 text-gray-700 dark:text-gray-300">
              {page} / {totalPages}
            </span>

            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="px-4 py-2 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              다음
            </button>
          </div>
        )}
      </div>
    </main>
  );
}

export default function HistoryPage() {
  return (
    <ProtectedRoute>
      <HistoryPageContent />
    </ProtectedRoute>
  );
}
