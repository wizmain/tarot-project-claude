'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/types';
import { READING_SPREADS } from '@/types/reading';
import { readingAPI } from '@/lib/api';
import CelticCrossCardSelector, { CelticCrossPosition } from '@/components/CelticCrossCardSelector';
import TarotCard from '@/components/TarotCard';
import { motion } from 'framer-motion';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { useSSEReading } from '@/lib/use-sse-reading';
import { useAuth } from '@/contexts/AuthContext';
import ReadingProgress from '@/components/ReadingProgress';
import { config } from '@/config/env';
import { shuffleArray } from '@/lib/utils';
import FeedbackSection from '@/components/FeedbackSection';

function CelticCrossReadingContent() {
  const router = useRouter();
  const { accessToken, user, isAuthenticated, isLoading } = useAuth();
  const spread = READING_SPREADS['celtic-cross'];

  const [question, setQuestion] = useState('');
  const [selectedCards, setSelectedCards] = useState<Card[]>([]);
  const [selectedReversedStates, setSelectedReversedStates] = useState<boolean[]>([]);
  const [positionOrder, setPositionOrder] = useState<number[]>([]);
  const [allCards, setAllCards] = useState<Card[]>([]);
  const [step, setStep] = useState<'question' | 'draw' | 'streaming' | 'result'>('question');
  const [isAdmin, setIsAdmin] = useState(false);

  // SSE Hook
  const {
    isStreaming,
    progress,
    stage,
    message,
    drawnCards,
    readingId,
    error: sseError,
    summary,
    cards,
    overallReading,
    advice,
    startReading,
    reset: resetSSE,
  } = useSSEReading(
    config.apiUrl,
    accessToken || ''
  );

  // Convert spread positions to CelticCrossPosition format
  const positions: CelticCrossPosition[] = spread.positions.map((pos, idx) => {
    // Map position names to backend format
    const positionMap: Record<string, string> = {
      'Present': 'present',
      'Challenge': 'challenge',
      'Past': 'past',
      'Future': 'future',
      'Above': 'above',
      'Below': 'below',
      'Advice': 'advice',
      'External': 'external',
      'Hopes/Fears': 'hopes_fears',
      'Outcome': 'outcome',
    };
    
    return {
      index: idx,
      position: (positionMap[pos.name] || pos.name.toLowerCase().replace(/\s+/g, '_')) as any,
      name: pos.name,
      name_ko: pos.name_ko,
      description: pos.description,
      description_ko: pos.description_ko,
    };
  });

  // Check if current user is admin
  useEffect(() => {
    const checkAdminStatus = async () => {
      if (!accessToken || !user?.email) {
        setIsAdmin(false);
        return;
      }

      try {
        const response = await fetch(`${config.apiUrl}/api/v1/settings`, {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        });

        if (response.ok) {
          const data = await response.json();
          const adminEmails = data.admin?.admin_emails || [];
          setIsAdmin(adminEmails.includes(user.email));
        } else {
          setIsAdmin(false);
        }
      } catch (error) {
        console.error('Failed to check admin status:', error);
        setIsAdmin(false);
      }
    };

    checkAdminStatus();
  }, [accessToken, user?.email]);

  // Fetch all cards on mount
  useEffect(() => {
    const fetchAllCards = async () => {
      try {
        const response = await fetch(`${config.apiUrl}/api/v1/cards?page_size=78`, {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
          },
        });
        if (response.ok) {
          const data = await response.json();
          const cards: Card[] = data.items || [];
          const shuffledCards = shuffleArray(cards);
          setAllCards(shuffledCards);
        }
      } catch (error) {
        console.error('Failed to fetch cards:', error);
      }
    };

    if (accessToken) {
      fetchAllCards();
    }
  }, [accessToken]);

  const handleQuestionSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!isLoading && !isAuthenticated) {
      const returnUrl = encodeURIComponent('/reading/celtic-cross');
      router.push(`/login?returnUrl=${returnUrl}`);
      return;
    }
    
    setStep('draw');
  };

  const handleCardsSelected = async (cards: Card[], reversedStates: boolean[], order: number[]) => {
    setSelectedCards(cards);
    setSelectedReversedStates(reversedStates);
    setPositionOrder(order);
    setStep('streaming');

    try {
      await startReading({
        question: question || '켈틱 크로스로 깊이 있는 조언을 받고 싶습니다',
        spread_type: 'celtic_cross',
        selected_card_ids: cards.map(c => c.id),
        reversed_states: reversedStates,
      });
    } catch (err) {
      console.error('Failed to start reading:', err);
    }
  };

  const handleReset = () => {
    setQuestion('');
    setSelectedCards([]);
    setPositionOrder([]);
    setStep('question');
    resetSSE();
  };

  return (
    <main className="min-h-screen p-4 md:p-8 bg-gradient-to-br from-purple-50 to-indigo-100 dark:from-gray-900 dark:to-indigo-950">
      <div className="max-w-7xl mx-auto">
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
            className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4 md:p-8"
          >
            <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
              질문을 입력하세요
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              타로 카드에게 묻고 싶은 질문을 적어주세요. 켈틱 크로스는 10장의 카드로
              상황의 모든 층위를 깊이 있게 분석합니다.
            </p>

            <form onSubmit={handleQuestionSubmit}>
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="예: 내 인생의 다음 단계는 무엇일까요?"
                className="w-full h-32 p-4 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white resize-none"
              />

              <div className="mt-6 flex gap-4">
                <button
                  type="submit"
                  className="flex-1 px-6 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-lg font-semibold transition-all shadow-lg"
                >
                  카드 선택하기 →
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
            className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4 md:p-8"
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

            <CelticCrossCardSelector
              positions={positions}
              onCardsSelected={handleCardsSelected}
              disabled={false}
              isAdmin={isAdmin}
              allCards={allCards}
            />
          </motion.div>
        )}

        {/* Step 3: SSE Streaming Progress with Incremental Results */}
        {step === 'streaming' && (
          <div className="space-y-8">
            {/* Progress indicator */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <ReadingProgress
                isStreaming={isStreaming}
                progress={progress}
                stage={stage}
                message={message}
                drawnCards={drawnCards}
                allCards={allCards}
                error={sseError || undefined}
              />
            </motion.div>

            {/* Summary Section */}
            {summary && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-lg shadow-lg p-6"
              >
                <p className="text-white text-xl font-semibold text-center">
                  {summary}
                </p>
              </motion.div>
            )}

            {/* Cards Section */}
            {cards && cards.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4 md:p-8"
              >
                <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-6 text-center">
                  켈틱 크로스 카드 해석
                </h2>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {cards.map((cardData: any, index: number) => {
                    const position = positions.find(p => p.position === cardData.position);
                    return (
                      <div
                        key={index}
                        className="border border-gray-200 dark:border-gray-700 rounded-lg p-4"
                      >
                        <div className="flex items-start gap-4">
                          <TarotCard
                            card={cardData.card}
                            isRevealed={true}
                            isReversed={cardData.orientation === 'reversed'}
                            size="small"
                          />
                          <div className="flex-1">
                            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                              {position?.name_ko || cardData.position}: {cardData.card.name_ko}
                              <span className="ml-2 text-sm text-gray-500">
                                ({cardData.orientation === 'upright' ? '정방향' : '역방향'})
                              </span>
                            </h3>
                            <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-3 mb-3">
                              <h4 className="font-semibold text-purple-900 dark:text-purple-200 mb-1 text-sm">
                                핵심 메시지
                              </h4>
                              <p className="text-gray-800 dark:text-gray-200 text-sm">
                                {cardData.key_message}
                              </p>
                            </div>
                            <div>
                              <h4 className="font-semibold text-gray-900 dark:text-white mb-2 text-sm">
                                해석
                              </h4>
                              <p className="text-gray-700 dark:text-gray-300 text-sm leading-relaxed whitespace-pre-line">
                                {cardData.interpretation}
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </motion.div>
            )}

            {/* Overall Reading Section */}
            {overallReading && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4 md:p-8"
              >
                <h3 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
                  종합 리딩
                </h3>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-line">
                  {overallReading}
                </p>
              </motion.div>
            )}

            {/* Advice Section */}
            {advice && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4 md:p-8"
              >
                <h3 className="text-2xl font-semibold text-gray-900 dark:text-white mb-6">
                  조언
                </h3>

                <div className="space-y-4">
                  {advice.immediate_action && (
                    <div className="border-l-4 border-purple-500 pl-4">
                      <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                        즉시 실천할 행동
                      </h4>
                      <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                        {advice.immediate_action}
                      </p>
                    </div>
                  )}

                  {advice.short_term && (
                    <div className="border-l-4 border-indigo-500 pl-4">
                      <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                        단기 목표
                      </h4>
                      <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                        {advice.short_term}
                      </p>
                    </div>
                  )}

                  {advice.long_term && (
                    <div className="border-l-4 border-blue-500 pl-4">
                      <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                        장기 전망
                      </h4>
                      <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                        {advice.long_term}
                      </p>
                    </div>
                  )}

                  {advice.mindset && (
                    <div className="border-l-4 border-green-500 pl-4">
                      <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                        마음가짐
                      </h4>
                      <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                        {advice.mindset}
                      </p>
                    </div>
                  )}

                  {advice.cautions && (
                    <div className="border-l-4 border-yellow-500 pl-4">
                      <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                        주의사항
                      </h4>
                      <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                        {advice.cautions}
                      </p>
                    </div>
                  )}
                </div>
              </motion.div>
            )}

            {/* Feedback Section */}
            {!isStreaming && readingId && (
              <FeedbackSection readingId={readingId} />
            )}

            {/* Action Buttons */}
            {!isStreaming && readingId && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="flex flex-col gap-4"
              >
                <button
                  onClick={() => router.push(`/history/detail?id=${readingId}`)}
                  className="w-full px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white rounded-lg font-semibold transition-all shadow-lg"
                >
                  히스토리에서 보기
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
              </motion.div>
            )}
          </div>
        )}
      </div>
    </main>
  );
}

export default function CelticCrossReadingPage() {
  return (
    <ProtectedRoute>
      <CelticCrossReadingContent />
    </ProtectedRoute>
  );
}

