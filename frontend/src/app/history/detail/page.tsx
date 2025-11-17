'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { motion } from 'framer-motion';
import TarotCard from '@/components/TarotCard';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { readingAPI } from '@/lib/api';
import type { ReadingResponse } from '@/types/reading';
import { useAuth } from '@/contexts/AuthContext';

const SPREAD_TYPE_LABELS: Record<string, string> = {
  one_card: '원카드 리딩',
  three_card_past_present_future: '쓰리카드 리딩 - 과거/현재/미래',
  three_card_situation_action_outcome: '쓰리카드 리딩 - 상황/행동/결과',
};

function formatDate(dateString: string) {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

function ReadingDetailPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const readingId = searchParams.get('id');
  const { isAuthenticated } = useAuth();

  const [reading, setReading] = useState<ReadingResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isAuthError, setIsAuthError] = useState(false);

  async function fetchReading(id: string) {
    setLoading(true);
    setError(null);
    setIsAuthError(false);

    try {
      const data = await readingAPI.getReading(id);
      setReading(data);
    } catch (err) {
      console.error('Failed to fetch reading:', err);
      const errorMessage = err instanceof Error ? err.message : '리딩을 불러오는데 실패했습니다';
      setError(errorMessage);
      
      // 인증 오류 확인
      if (errorMessage.includes('[AUTH_EXPIRED]') || errorMessage.includes('[AUTH_FORBIDDEN]')) {
        setIsAuthError(true);
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!readingId) {
      setReading(null);
      setLoading(false);
      setError('유효한 리딩 ID를 찾을 수 없습니다.');
      return;
    }

    fetchReading(readingId);
  }, [readingId]);

  return (
    <main className="min-h-screen p-8 bg-gradient-to-br from-purple-50 to-indigo-100 dark:from-gray-900 dark:to-indigo-950">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8 text-center">
          <button
            onClick={() => router.push('/history')}
            className="mb-4 text-purple-600 dark:text-purple-400 hover:underline"
          >
            ← 히스토리로 돌아가기
          </button>
        </div>

        {loading && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-12 text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-purple-600 mx-auto mb-4"></div>
            <p className="text-gray-600 dark:text-gray-400">리딩을 불러오는 중...</p>
          </div>
        )}

        {error && !loading && (
          <div className="bg-red-50 dark:bg-red-900/20 rounded-lg shadow-lg p-6">
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-red-800 dark:text-red-200 mb-2">
                {isAuthError ? '🔒 인증 오류' : '❌ 오류 발생'}
              </h3>
              <p className="text-red-600 dark:text-red-400">{error}</p>
            </div>
            <div className="flex flex-col sm:flex-row gap-4">
              {isAuthError ? (
                <>
                  <button
                    onClick={() => router.push('/login')}
                    className="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-semibold transition-all"
                  >
                    로그인 페이지로 이동
                  </button>
                  <button
                    onClick={() => router.push('/history')}
                    className="px-6 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-900 dark:text-white rounded-lg font-semibold transition-all"
                  >
                    목록으로
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={() => (readingId ? fetchReading(readingId) : router.push('/history'))}
                    className="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-semibold transition-all"
                  >
                    다시 시도
                  </button>
                  <button
                    onClick={() => router.push('/history')}
                    className="px-6 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-900 dark:text-white rounded-lg font-semibold transition-all"
                  >
                    목록으로
                  </button>
                </>
              )}
            </div>
          </div>
        )}

        {reading && !loading && !error && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-8"
          >
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                {SPREAD_TYPE_LABELS[reading.spread_type] || reading.spread_type}
              </h1>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {formatDate(reading.created_at)}
              </p>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
              <p className="text-sm text-purple-600 dark:text-purple-400 mb-1">당신의 질문</p>
              <p className="text-gray-900 dark:text-white text-lg font-medium">{reading.question}</p>
            </div>

            <div className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-lg shadow-lg p-6">
              <p className="text-white text-xl font-semibold text-center">{reading.summary}</p>
            </div>

            {reading.cards.length === 1 ? (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
                <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-6 text-center">
                  {reading.cards[0].card.name_ko}
                  <span className="ml-2 text-sm text-gray-500">
                    ({reading.cards[0].orientation === 'upright' ? '정방향' : '역방향'})
                  </span>
                </h2>

                <div className="flex flex-col items-center gap-6">
                  <TarotCard
                    card={reading.cards[0].card}
                    isRevealed
                    isReversed={reading.cards[0].orientation === 'reversed'}
                    size="large"
                  />

                  <div className="max-w-2xl w-full">
                    <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4 mb-6">
                      <h4 className="font-semibold text-purple-900 dark:text-purple-200 mb-2">💡 핵심 메시지</h4>
                      <p className="text-gray-800 dark:text-gray-200 leading-relaxed">
                        {reading.cards[0].key_message}
                      </p>
                    </div>

                    <div className="mb-6">
                      <h4 className="font-semibold text-gray-900 dark:text-white mb-3">🔮 AI 카드 해석</h4>
                      <p className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-line">
                        {reading.cards[0].interpretation}
                      </p>
                    </div>

                    <div>
                      <h4 className="font-semibold text-gray-900 dark:text-white mb-3">🏷️ 키워드</h4>
                      <div className="flex flex-wrap gap-2">
                        {(reading.cards[0].orientation === 'reversed'
                          ? reading.cards[0].card.keywords_reversed
                          : reading.cards[0].card.keywords_upright
                        ).map((keyword, i) => (
                          <span
                            key={i}
                            className="px-3 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-full text-sm"
                          >
                            {keyword}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
                <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-8 text-center">
                  당신의 타임라인
                </h2>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                  {reading.cards.map((cardData, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.2 }}
                      className="flex flex-col items-center gap-4"
                    >
                      <div className="text-center">
                        <div className="text-3xl mb-2">
                          {index === 0 ? '📅' : index === 1 ? '⏳' : '🔮'}
                        </div>
                        <h3 className="text-xl font-semibold text-purple-600 dark:text-purple-400">
                          {index === 0 ? '과거' : index === 1 ? '현재' : '미래'}
                        </h3>
                      </div>

                      <TarotCard
                        card={cardData.card}
                        isRevealed
                        isReversed={cardData.orientation === 'reversed'}
                        size="medium"
                      />

                      <h4 className="font-semibold text-gray-900 dark:text-white text-center">
                        {cardData.card.name_ko}
                        <span className="ml-2 text-sm text-gray-500">
                          ({cardData.orientation === 'upright' ? '정방향' : '역방향'})
                        </span>
                      </h4>

                      <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-3 w-full">
                        <h5 className="font-semibold text-purple-900 dark:text-purple-200 mb-2 text-sm">
                          💡 핵심 메시지
                        </h5>
                        <p className="text-gray-800 dark:text-gray-200 text-xs leading-relaxed">
                          {cardData.key_message}
                        </p>
                      </div>

                      <div className="w-full">
                        <h5 className="font-semibold text-gray-900 dark:text-white mb-2 text-sm">
                          🔮 AI 해석
                        </h5>
                        <p className="text-gray-700 dark:text-gray-300 text-xs leading-relaxed whitespace-pre-line">
                          {cardData.interpretation}
                        </p>
                      </div>

                      <div className="w-full">
                        <h5 className="font-semibold text-gray-900 dark:text-white mb-2 text-sm">
                          🏷️ 키워드
                        </h5>
                        <div className="flex flex-wrap gap-1 justify-center">
                          {(cardData.orientation === 'reversed'
                            ? cardData.card.keywords_reversed
                            : cardData.card.keywords_upright
                          )
                            .slice(0, 3)
                            .map((keyword, i) => (
                              <span
                                key={i}
                                className="px-2 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-full text-xs"
                              >
                                {keyword}
                              </span>
                            ))}
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            )}

            {reading.card_relationships && (
              <div className="bg-gradient-to-br from-purple-50 to-indigo-50 dark:from-purple-900/20 dark:to-indigo-900/20 rounded-lg shadow-lg p-6">
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-3">
                  🔗 카드 간의 관계
                </h3>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-line">
                  {reading.card_relationships}
                </p>
              </div>
            )}

            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
              <h3 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">📖 종합 리딩</h3>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-line">
                {reading.overall_reading}
              </p>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
              <h3 className="text-2xl font-semibold text-gray-900 dark:text-white mb-6">💬 조언</h3>

              <div className="space-y-4">
                <div className="border-l-4 border-purple-500 pl-4">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-2">즉시 실천할 행동</h4>
                  <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                    {reading.advice.immediate_action}
                  </p>
                </div>

                <div className="border-l-4 border-indigo-500 pl-4">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-2">단기 목표</h4>
                  <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                    {reading.advice.short_term}
                  </p>
                </div>

                <div className="border-l-4 border-blue-500 pl-4">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-2">장기 전망</h4>
                  <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                    {reading.advice.long_term}
                  </p>
                </div>

                <div className="border-l-4 border-green-500 pl-4">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-2">마음가짐</h4>
                  <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                    {reading.advice.mindset}
                  </p>
                </div>

                <div className="border-l-4 border-yellow-500 pl-4">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-2">주의사항</h4>
                  <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                    {reading.advice.cautions}
                  </p>
                </div>
              </div>
            </div>

            <div className="flex gap-4">
              <button
                onClick={() => router.push('/history')}
                className="flex-1 px-6 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-lg font-semibold transition-all shadow-lg"
              >
                목록으로
              </button>
              <button
                onClick={() => router.push('/')}
                className="flex-1 px-6 py-3 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-900 dark:text-white rounded-lg font-semibold transition-all"
              >
                홈으로
              </button>
            </div>
          </motion.div>
        )}
      </div>
    </main>
  );
}

export default function ReadingDetailPage() {
  return (
    <ProtectedRoute>
      <ReadingDetailPageContent />
    </ProtectedRoute>
  );
}
