'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/types';
import { READING_SPREADS } from '@/types/reading';
import { readingAPI } from '@/lib/api';
import CardSelector from '@/components/CardSelector';
import TarotCard from '@/components/TarotCard';
import { motion, AnimatePresence } from 'framer-motion';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { useSSEReading } from '@/lib/use-sse-reading';
import { useAuth } from '@/contexts/AuthContext';
import ReadingProgress from '@/components/ReadingProgress';
import { config } from '@/config/env';
import { shuffleArray } from '@/lib/utils';
import FeedbackSection from '@/components/FeedbackSection';

function OneCardReadingContent() {
  const router = useRouter();
  const { accessToken, user, isAuthenticated, isLoading } = useAuth();
  const spread = READING_SPREADS['one-card'];

  const [question, setQuestion] = useState('');
  const [selectedCards, setSelectedCards] = useState<Card[]>([]);
  const [selectedReversedStates, setSelectedReversedStates] = useState<boolean[]>([]);  // Store reversed states for admin info
  const [allCards, setAllCards] = useState<Card[]>([]);
  const [step, setStep] = useState<'question' | 'draw' | 'streaming' | 'result'>('question');
  const [selectionMode, setSelectionMode] = useState<'user' | 'random'>('user');  // Two modes
  const [isAdmin, setIsAdmin] = useState(false);  // Admin check state

  // Debug: Detect unexpected page reloads
  useEffect(() => {
    console.log('[OneCard] Component mounted');
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      console.warn('[OneCard] Page is about to unload/reload!', e);
    };
    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      console.log('[OneCard] Component unmounting');
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, []);

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

  const [isInterpretationTooShort, setIsInterpretationTooShort] = useState(false);

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
          // Randomize card order for better user experience
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

  // Check interpretation length when cards section is available
  useEffect(() => {
    if (cards && cards.length > 0) {
      const interpretation = cards[0]?.interpretation || '';
      const interpretationLength = interpretation.length;
      console.log('[OneCard] Interpretation length:', interpretationLength);

      // Check if interpretation is too short (less than 120 characters)
      if (interpretationLength > 0 && interpretationLength < 120) {
        setIsInterpretationTooShort(true);
      } else if (interpretationLength >= 120) {
        setIsInterpretationTooShort(false);
      }
    }
  }, [cards]);

  const handleQuestionSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Check if user is authenticated before proceeding to card selection
    if (!isLoading && !isAuthenticated) {
      // Save the current path to redirect back after login
      const returnUrl = encodeURIComponent('/reading/one-card');
      router.push(`/login?returnUrl=${returnUrl}`);
      return;
    }
    
    // If random mode, skip card selection and go straight to streaming
    if (selectionMode === 'random') {
      handleRandomReading();
    } else {
      setStep('draw');
    }
  };

  const handleRandomReading = async () => {
    // Check if user is authenticated before starting random reading
    if (!isLoading && !isAuthenticated) {
      const returnUrl = encodeURIComponent('/reading/one-card');
      router.push(`/login?returnUrl=${returnUrl}`);
      return;
    }
    
    setStep('streaming');
    
    try {
      // Random Mode: Don't pass selected_card_ids
      await startReading({
        question: question || '오늘의 운세를 알려주세요',
        spread_type: 'one_card',
        category: 'personal_growth',
        // selected_card_ids: undefined (Random Mode)
      });
    } catch (err) {
      console.error('Failed to start reading:', err);
    }
  };

  const handleCardsSelected = async (cards: Card[], reversedStates: boolean[]) => {
    setSelectedCards(cards);
    setSelectedReversedStates(reversedStates);  // Store reversed states for admin info
    setStep('streaming');

    try {
      // Start SSE streaming with selected card IDs and reversed states (User Selection Mode)
      await startReading({
        question: question || '오늘의 운세를 알려주세요',
        spread_type: 'one_card',
        category: 'personal_growth',
        selected_card_ids: cards.map(c => c.id),  // Pass selected card IDs
        reversed_states: reversedStates,  // Pass reversed states from frontend
      });
    } catch (err) {
      console.error('Failed to start reading:', err);
    }
  };

  const handleReset = () => {
    setQuestion('');
    setSelectedCards([]);
    setIsInterpretationTooShort(false);
    setStep('question');
    resetSSE();
  };

  const handleReRead = () => {
    // Keep the same question but reset everything else to redo the reading
    setSelectedCards([]);
    setIsInterpretationTooShort(false);
    setStep('draw');
    resetSSE();
  };

  return (
    <main className="min-h-screen p-8 bg-gradient-to-br from-purple-50 to-indigo-100 dark:from-gray-900 dark:to-indigo-950">
      <div className="max-w-4xl mx-auto">
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
              타로 카드에게 묻고 싶은 질문을 적어주세요. 질문은 선택사항이며,
              생략하고 바로 카드를 뽑을 수도 있습니다.
            </p>

            <form onSubmit={handleQuestionSubmit}>
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="예: 오늘 하루는 어떨까요?"
                className="w-full h-32 p-4 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white resize-none"
              />

              {/* Card Selection Mode */}
              <div className="mt-6 p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
                  카드 선택 방식
                </h3>
                <div className="flex gap-4">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="selectionMode"
                      value="user"
                      checked={selectionMode === 'user'}
                      onChange={(e) => setSelectionMode('user')}
                      className="w-4 h-4 text-purple-600 focus:ring-purple-500"
                    />
                    <span className="text-gray-700 dark:text-gray-300">
                      🎯 직접 선택 <span className="text-xs text-gray-500">(카드를 직접 고르기)</span>
                    </span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="selectionMode"
                      value="random"
                      checked={selectionMode === 'random'}
                      onChange={(e) => setSelectionMode('random')}
                      className="w-4 h-4 text-purple-600 focus:ring-purple-500"
                    />
                    <span className="text-gray-700 dark:text-gray-300">
                      🎲 랜덤 선택 <span className="text-xs text-gray-500">(운명에 맡기기)</span>
                    </span>
                  </label>
                </div>
              </div>

              <div className="mt-6 flex gap-4">
                <button
                  type="submit"
                  className="flex-1 px-6 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-lg font-semibold transition-all shadow-lg"
                >
                  {selectionMode === 'random' ? '🎲 바로 리딩 시작 →' : '🎯 카드 선택하기 →'}
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
              카드를 선택해주세요
            </h2>

            <CardSelector
              cardCount={spread.cardCount}
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

            {/* Incrementally show completed sections */}

            {/* 1. Summary Section */}
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

            {/* 2. Cards Section */}
            {cards && cards.length > 0 && cards.map((cardData: any, index: number) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8"
              >
                <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-6 text-center">
                  {cardData.card.name_ko}
                  <span className="ml-2 text-sm text-gray-500">
                    ({cardData.orientation === 'upright' ? '정방향' : '역방향'})
                  </span>
                </h2>

                <div className="flex flex-col items-center gap-6">
                  {/* Card Image */}
                  <TarotCard
                    card={cardData.card}
                    isRevealed={true}
                    isReversed={cardData.orientation === 'reversed'}
                    size="large"
                  />

                  {/* AI Key Message */}
                  <div className="max-w-2xl w-full">
                    <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4 mb-6">
                      <h4 className="font-semibold text-purple-900 dark:text-purple-200 mb-2">
                        핵심 메시지
                      </h4>
                      <p className="text-gray-800 dark:text-gray-200 leading-relaxed">
                        {cardData.key_message}
                      </p>
                    </div>

                    {/* AI Interpretation */}
                    <div className="mb-6">
                      <h4 className="font-semibold text-gray-900 dark:text-white mb-3">
                        AI 카드 해석
                      </h4>
                      <p className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-line">
                        {cardData.interpretation}
                      </p>
                    </div>

                    {/* Card Keywords */}
                    <div>
                      <h4 className="font-semibold text-gray-900 dark:text-white mb-3">
                        키워드
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {(cardData.orientation === 'reversed'
                          ? cardData.card.keywords_reversed
                          : cardData.card.keywords_upright
                        ).map((keyword: string, i: number) => (
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
              </motion.div>
            ))}

            {/* Warning banner for short interpretation */}
            {isInterpretationTooShort && cards && cards.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-yellow-50 dark:bg-yellow-900/20 border-l-4 border-yellow-500 rounded-lg p-4"
              >
                <div className="flex items-start gap-3">
                  <span className="text-2xl">⚠️</span>
                  <div className="flex-1">
                    <h4 className="font-semibold text-yellow-900 dark:text-yellow-200 mb-1">
                      해석이 짧습니다
                    </h4>
                    <p className="text-sm text-yellow-800 dark:text-yellow-300 mb-3">
                      AI가 생성한 해석이 120자 미만으로 다소 짧습니다. 더 자세한 해석을 원하시면 다시 리딩을 시도해보세요.
                    </p>
                    <button
                      onClick={handleReRead}
                      className="px-4 py-2 bg-yellow-500 hover:bg-yellow-600 text-white rounded-lg text-sm font-medium transition-colors"
                    >
                      다시 리딩하기
                    </button>
                  </div>
                </div>
              </motion.div>
            )}

            {/* 3. Overall Reading Section */}
            {overallReading && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8"
              >
                <h3 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
                  종합 리딩
                </h3>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-line">
                  {overallReading}
                </p>
              </motion.div>
            )}

            {/* 4. Advice Section */}
            {advice && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8"
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

            {/* Admin Info Panel - Show selected card details for admins */}
            {isAdmin && !isStreaming && (drawnCards.length > 0 || selectedCards.length > 0) && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="bg-amber-50 dark:bg-amber-900/20 border-2 border-amber-300 dark:border-amber-700 rounded-lg p-6"
              >
                <div className="flex items-center gap-2 mb-4">
                  <span className="text-2xl">👨‍💼</span>
                  <h3 className="text-lg font-semibold text-amber-900 dark:text-amber-200">
                    관리자 정보
                  </h3>
                </div>
                
                <div className="space-y-3 text-sm">
                  <div>
                    <span className="font-medium text-amber-800 dark:text-amber-300">
                      선택 모드:
                    </span>
                    <span className="ml-2 text-amber-700 dark:text-amber-400">
                      {selectionMode === 'user' ? '🎯 직접 선택' : '🎲 랜덤 선택'}
                    </span>
                  </div>
                  
                  {selectionMode === 'user' && selectedCards.length > 0 && (
                    <div>
                      <span className="font-medium text-amber-800 dark:text-amber-300">
                        선택된 카드 ID:
                      </span>
                      <div className="mt-2 space-y-1">
                        {selectedCards.map((card, idx) => (
                          <div key={idx} className="text-amber-700 dark:text-amber-400">
                            <span className="font-mono">#{card.id}</span>
                            <span className="ml-2">
                              {card.name_ko || card.name || 'Unknown'}
                            </span>
                            {selectedReversedStates[idx] !== undefined && (
                              <span className="ml-2 text-xs font-semibold">
                                [{selectedReversedStates[idx] ? '역방향' : '정방향'}]
                              </span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {drawnCards.length > 0 && (
                    <div>
                      <span className="font-medium text-amber-800 dark:text-amber-300">
                        실제 뽑힌 카드:
                      </span>
                      <div className="mt-2 space-y-1">
                        {drawnCards.map((drawnCard, idx) => (
                          <div key={idx} className="text-amber-700 dark:text-amber-400">
                            <span className="font-mono">#{drawnCard.card_id || 'N/A'}</span>
                            <span className="ml-2">
                              {drawnCard.card_name_ko || drawnCard.card_name || 'Unknown'}
                            </span>
                            <span className="ml-2 text-xs">
                              ({drawnCard.is_reversed ? '역방향' : '정방향'})
                            </span>
                            {drawnCard.position && (
                              <span className="ml-2 text-xs text-amber-600 dark:text-amber-500">
                                [{drawnCard.position}]
                              </span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {cards && cards.length > 0 && (
                    <div>
                      <span className="font-medium text-amber-800 dark:text-amber-300">
                        리딩에 사용된 카드:
                      </span>
                      <div className="mt-2 space-y-1">
                        {cards.map((cardData: any, idx: number) => (
                          <div key={idx} className="text-amber-700 dark:text-amber-400">
                            <span className="font-mono">#{cardData.card?.id || 'N/A'}</span>
                            <span className="ml-2">
                              {cardData.card?.name_ko || cardData.card?.name_en || 'Unknown'}
                            </span>
                            <span className="ml-2 text-xs">
                              ({cardData.orientation === 'reversed' ? '역방향' : '정방향'})
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {readingId && (
                    <div>
                      <span className="font-medium text-amber-800 dark:text-amber-300">
                        리딩 ID:
                      </span>
                      <span className="ml-2 text-amber-700 dark:text-amber-400 font-mono text-xs">
                        {readingId}
                      </span>
                    </div>
                  )}
                </div>
              </motion.div>
            )}

            {/* Feedback Section - Show when reading is complete */}
            {!isStreaming && readingId && (
              <FeedbackSection readingId={readingId} />
            )}

            {/* Action Buttons - Show when reading is complete */}
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

export default function OneCardReadingPage() {
  return (
    <ProtectedRoute>
      <OneCardReadingContent />
    </ProtectedRoute>
  );
}
