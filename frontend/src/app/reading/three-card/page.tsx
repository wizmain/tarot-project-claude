'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/types';
import { READING_SPREADS, DrawnCard, ReadingResponse } from '@/types/reading';
import { readingAPI } from '@/lib/api';
import CardSelector from '@/components/CardSelector';
import TarotCard from '@/components/TarotCard';
import { motion } from 'framer-motion';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

function ThreeCardReadingContent() {
  const router = useRouter();
  const spread = READING_SPREADS['three-card'];

  const [question, setQuestion] = useState('');
  const [drawnCards, setDrawnCards] = useState<DrawnCard[]>([]);
  const [step, setStep] = useState<'question' | 'draw' | 'result'>('question');
  const [reading, setReading] = useState<ReadingResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleQuestionSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setStep('draw');
  };

  const handleCardsSelected = async (cards: Card[], reversedStates: boolean[]) => {
    const drawn: DrawnCard[] = cards.map((card, index) => ({
      card,
      position: spread.positions[index],
      isReversed: reversedStates[index],
    }));

    setDrawnCards(drawn);
    setLoading(true);
    setError(null);

    try {
      // Call backend API to create reading with AI interpretation
      const readingResponse = await readingAPI.createReading({
        question: question || '이 상황은 어떻게 전개될까요?',
        spread_type: 'three_card_past_present_future',
        category: null,
        user_context: null,
      });

      setReading(readingResponse);
      setTimeout(() => {
        setStep('result');
        setLoading(false);
      }, 1000);
    } catch (err) {
      console.error('Failed to create reading:', err);
      setError(err instanceof Error ? err.message : '리딩 생성에 실패했습니다');
      setLoading(false);
    }
  };

  const handleReset = () => {
    setQuestion('');
    setDrawnCards([]);
    setReading(null);
    setError(null);
    setStep('question');
  };

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
            {spread.name_ko}
          </h1>
          <p className="text-gray-600 dark:text-gray-300">
            {spread.description_ko}
          </p>
        </div>

        {/* Step 1: Question Input */}
        {step === 'question' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8"
          >
            <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
              질문을 입력하세요
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              타로 카드에게 묻고 싶은 질문을 적어주세요. 쓰리카드 리딩은
              과거-현재-미래의 흐름을 보여줍니다.
            </p>

            <form onSubmit={handleQuestionSubmit}>
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="예: 이 프로젝트는 어떻게 진행될까요?"
                className="w-full h-32 p-4 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white resize-none"
              />

              <div className="mt-6 flex gap-4">
                <button
                  type="submit"
                  className="flex-1 px-6 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-lg font-semibold transition-all shadow-lg"
                >
                  카드 3장 뽑기 →
                </button>
              </div>
            </form>
          </motion.div>
        )}

        {/* Step 2: Draw Cards */}
        {step === 'draw' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8"
          >
            {question && (
              <div className="mb-8 p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                <p className="text-sm text-purple-600 dark:text-purple-400 mb-1">
                  당신의 질문
                </p>
                <p className="text-gray-900 dark:text-white font-medium">
                  {question}
                </p>
              </div>
            )}

            <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-6 text-center">
              카드 3장을 선택해주세요
            </h2>

            <CardSelector
              cardCount={spread.cardCount}
              onCardsSelected={handleCardsSelected}
              disabled={loading}
            />
          </motion.div>
        )}

        {/* Loading State */}
        {loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-12 text-center"
          >
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-purple-600 mx-auto mb-4"></div>
            <p className="text-gray-600 dark:text-gray-400">AI가 카드를 해석하고 있습니다...</p>
          </motion.div>
        )}

        {/* Error State */}
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-red-50 dark:bg-red-900/20 rounded-lg shadow-lg p-6"
          >
            <p className="text-red-600 dark:text-red-400 mb-4">{error}</p>
            <button
              onClick={handleReset}
              className="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-semibold transition-all"
            >
              다시 시도
            </button>
          </motion.div>
        )}

        {/* Step 3: Result */}
        {step === 'result' && reading && !loading && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-8"
          >
            {/* Question */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
              <p className="text-sm text-purple-600 dark:text-purple-400 mb-1">
                당신의 질문
              </p>
              <p className="text-gray-900 dark:text-white text-lg font-medium">
                {reading.question}
              </p>
            </div>

            {/* Summary */}
            <div className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-lg shadow-lg p-6">
              <p className="text-white text-xl font-semibold text-center">
                {reading.summary}
              </p>
            </div>

            {/* Three Cards Display */}
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
                    {/* Position Header */}
                    <div className="text-center">
                      <div className="text-3xl mb-2">
                        {index === 0 ? '📅' : index === 1 ? '⏳' : '🔮'}
                      </div>
                      <h3 className="text-xl font-semibold text-purple-600 dark:text-purple-400">
                        {index === 0 ? '과거' : index === 1 ? '현재' : '미래'}
                      </h3>
                    </div>

                    {/* Card */}
                    <TarotCard
                      card={cardData.card}
                      isRevealed={true}
                      isReversed={cardData.orientation === 'reversed'}
                      size="medium"
                    />

                    {/* Card Name */}
                    <h4 className="font-semibold text-gray-900 dark:text-white text-center">
                      {cardData.card.name_ko}
                      <span className="ml-2 text-sm text-gray-500">
                        ({cardData.orientation === 'upright' ? '정방향' : '역방향'})
                      </span>
                    </h4>

                    {/* AI Key Message */}
                    <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-3 w-full">
                      <h5 className="font-semibold text-purple-900 dark:text-purple-200 mb-2 text-sm">
                        💡 핵심 메시지
                      </h5>
                      <p className="text-gray-800 dark:text-gray-200 text-xs leading-relaxed">
                        {cardData.key_message}
                      </p>
                    </div>

                    {/* AI Interpretation */}
                    <div className="w-full">
                      <h5 className="font-semibold text-gray-900 dark:text-white mb-2 text-sm">
                        🔮 AI 해석
                      </h5>
                      <p className="text-gray-700 dark:text-gray-300 text-xs leading-relaxed whitespace-pre-line">
                        {cardData.interpretation}
                      </p>
                    </div>

                    {/* Keywords */}
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

            {/* Card Relationships */}
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

            {/* Overall Reading */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
              <h3 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
                📖 종합 리딩
              </h3>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-line">
                {reading.overall_reading}
              </p>
            </div>

            {/* Advice */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
              <h3 className="text-2xl font-semibold text-gray-900 dark:text-white mb-6">
                💬 조언
              </h3>

              <div className="space-y-4">
                <div className="border-l-4 border-purple-500 pl-4">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                    즉시 실천할 행동
                  </h4>
                  <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                    {reading.advice.immediate_action}
                  </p>
                </div>

                <div className="border-l-4 border-indigo-500 pl-4">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                    단기 목표
                  </h4>
                  <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                    {reading.advice.short_term}
                  </p>
                </div>

                <div className="border-l-4 border-blue-500 pl-4">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                    장기 전망
                  </h4>
                  <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                    {reading.advice.long_term}
                  </p>
                </div>

                <div className="border-l-4 border-green-500 pl-4">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                    마음가짐
                  </h4>
                  <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                    {reading.advice.mindset}
                  </p>
                </div>

                <div className="border-l-4 border-yellow-500 pl-4">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                    주의사항
                  </h4>
                  <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                    {reading.advice.cautions}
                  </p>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col gap-4">
              <button
                onClick={() => router.push(`/history/detail?id=${reading.id}`)}
                className="w-full px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white rounded-lg font-semibold transition-all shadow-lg"
              >
                📖 히스토리에서 보기
              </button>
              <div className="flex gap-4">
                <button
                  onClick={handleReset}
                  className="flex-1 px-6 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-lg font-semibold transition-all shadow-lg"
                >
                  다시 뽑기
                </button>
                <button
                  onClick={() => router.push('/')}
                  className="flex-1 px-6 py-3 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-900 dark:text-white rounded-lg font-semibold transition-all"
                >
                  홈으로
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </main>
  );
}

export default function ThreeCardReadingPage() {
  return (
    <ProtectedRoute>
      <ThreeCardReadingContent />
    </ProtectedRoute>
  );
}
