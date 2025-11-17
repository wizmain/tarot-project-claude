'use client';

import Link from 'next/link';
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

interface DetailedReadingOption {
  id: string;
  name: string;
  nameKo: string;
  description: string;
  descriptionKo: string;
  available: boolean;
  route?: string;
}

const DETAILED_READING_OPTIONS: DetailedReadingOption[] = [
  {
    id: 'alternatively',
    name: 'Alternatively',
    nameKo: '양자택익',
    description: 'Choose between two paths',
    descriptionKo: '두 가지 선택지 중 하나를 선택하세요',
    available: false,
  },
  {
    id: 'hexagram',
    name: 'Hexagram',
    nameKo: '헥사그램',
    description: 'Six-card spread for comprehensive insight',
    descriptionKo: '6장의 카드로 포괄적인 통찰을 얻으세요',
    available: false,
  },
  {
    id: 'celtic-cross',
    name: 'Celtic Cross',
    nameKo: '켈틱 크로스',
    description: 'In-depth 10-card spread for comprehensive guidance',
    descriptionKo: '10장의 카드로 심층적인 조언을 받아보세요',
    available: true,
    route: '/reading/celtic-cross',
  },
  {
    id: 'horseshoe',
    name: 'Horseshoe',
    nameKo: '호스슈',
    description: 'Seven-card horseshoe spread',
    descriptionKo: '7장의 카드로 말굽 형태의 리딩을 받으세요',
    available: false,
  },
  {
    id: 'horoscope',
    name: 'Horoscope',
    nameKo: '호로스코프',
    description: 'Astrological tarot spread',
    descriptionKo: '점성술 기반 타로 스프레드',
    available: false,
  },
  {
    id: 'heart-sonar',
    name: 'Heart Sonar',
    nameKo: '하트소나',
    description: 'Deep emotional reading',
    descriptionKo: '깊은 감정 리딩',
    available: false,
  },
];

export default function Home() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();
  const [showDetailedReadings, setShowDetailedReadings] = useState(false);

  // 모달이 열릴 때 인증 상태 확인
  useEffect(() => {
    if (showDetailedReadings && !isLoading && !isAuthenticated) {
      // 모달이 열린 상태에서 인증되지 않은 경우 모달 닫기
      setShowDetailedReadings(false);
      const shouldLogin = window.confirm('상세 리딩을 사용하려면 로그인이 필요합니다.\n로그인 페이지로 이동하시겠습니까?');
      if (shouldLogin) {
        router.push('/login');
      }
    }
  }, [showDetailedReadings, isAuthenticated, isLoading, router]);

  const handleDetailedReadingClick = () => {
    // 로딩 중이면 대기
    if (isLoading) {
      return;
    }

    // 인증 확인
    if (!isAuthenticated) {
      // 인증되지 않은 경우 로그인 페이지로 리다이렉트
      const shouldLogin = window.confirm('상세 리딩을 사용하려면 로그인이 필요합니다.\n로그인 페이지로 이동하시겠습니까?');
      if (shouldLogin) {
        router.push('/login');
      }
      return;
    }
    
    setShowDetailedReadings(true);
  };

  const handleOptionClick = (option: DetailedReadingOption) => {
    if (!option.available || !option.route) {
      return;
    }

    // 로딩 중이면 대기
    if (isLoading) {
      return;
    }

    // 상세 리딩 옵션 클릭 시 인증 확인
    if (!isAuthenticated) {
      // 인증되지 않은 경우 로그인 페이지로 리다이렉트
      const shouldLogin = window.confirm('상세 리딩을 사용하려면 로그인이 필요합니다.\n로그인 페이지로 이동하시겠습니까?');
      if (shouldLogin) {
        router.push('/login');
      }
      return;
    }

    router.push(option.route);
  };

  const handleCloseModal = () => {
    setShowDetailedReadings(false);
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gradient-to-br from-purple-50 to-indigo-100 dark:from-gray-900 dark:to-indigo-950">
      <div className="z-10 w-full max-w-5xl items-center justify-between font-mono text-sm">
        <h1 className="text-4xl font-bold text-center mb-4 text-gray-900 dark:text-white">
          Tarot AI Reading Service
        </h1>
        <p className="text-center mb-8 text-gray-600 dark:text-gray-300">
          AI 기반 타로 카드 리딩 서비스
        </p>

        <div className="mb-12 grid text-center lg:mb-0 lg:w-full lg:max-w-5xl lg:grid-cols-3 lg:text-left gap-4">
          <Link
            href="/reading/one-card"
            className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-300 hover:bg-gray-100 dark:hover:border-neutral-700 dark:hover:bg-neutral-800/30"
          >
            <h2 className="mb-3 text-2xl font-semibold">
              원카드 리딩
              <span className="inline-block transition-transform group-hover:translate-x-1 motion-reduce:transform-none">
                →
              </span>
            </h2>
            <p className="m-0 max-w-[30ch] text-sm opacity-50">
              오늘의 운세를 한 장의 카드로 확인하세요
            </p>
          </Link>

          <Link
            href="/reading/three-card"
            className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-300 hover:bg-gray-100 dark:hover:border-neutral-700 dark:hover:bg-neutral-800/30"
          >
            <h2 className="mb-3 text-2xl font-semibold">
              쓰리카드 리딩
              <span className="inline-block transition-transform group-hover:translate-x-1 motion-reduce:transform-none">
                →
              </span>
            </h2>
            <p className="m-0 max-w-[30ch] text-sm opacity-50">
              과거-현재-미래를 세 장의 카드로 살펴보세요
            </p>
          </Link>

          <button
            onClick={handleDetailedReadingClick}
            className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-300 hover:bg-gray-100 dark:hover:border-neutral-700 dark:hover:bg-neutral-800/30 text-left cursor-pointer"
          >
            <h2 className="mb-3 text-2xl font-semibold">
              상세 리딩
              <span className="inline-block transition-transform group-hover:translate-x-1 motion-reduce:transform-none">
                →
              </span>
            </h2>
            <p className="m-0 max-w-[30ch] text-sm opacity-50">
              AI가 제공하는 심층적인 타로 해석
            </p>
          </button>
        </div>

        <div className="mt-8 flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/history"
            className="inline-block px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-semibold"
          >
            📖 리딩 히스토리
          </Link>
          <Link
            href="/cards"
            className="inline-block px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-semibold"
          >
            📚 타로 카드 컬렉션 보기
          </Link>
        </div>

        <div className="mt-16 text-center">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Powered by Wizma
          </p>
        </div>
      </div>

      {/* Detailed Readings Modal */}
      <AnimatePresence>
        {showDetailedReadings && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={handleCloseModal}
              className="fixed inset-0 bg-black/50 z-40"
            />

            {/* Modal */}
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              className="fixed inset-0 z-50 flex items-center justify-center p-4"
            >
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
                {/* Header */}
                <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between">
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                    상세 리딩 선택
                  </h2>
                  <button
                    onClick={handleCloseModal}
                    className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 text-2xl font-bold"
                  >
                    ×
                  </button>
                </div>

                {/* Options Grid */}
                <div className="p-6">
                  {/* 로딩 중 표시 */}
                  {isLoading && (
                    <div className="mb-4 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                        <p className="text-sm text-blue-700 dark:text-blue-300">
                          인증 상태를 확인하는 중...
                        </p>
                      </div>
                    </div>
                  )}

                  {/* 인증 상태 경고 */}
                  {!isLoading && !isAuthenticated && (
                    <div className="mb-4 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                      <div className="flex items-start gap-3">
                        <span className="text-2xl">⚠️</span>
                        <div className="flex-1">
                          <h3 className="font-semibold text-yellow-800 dark:text-yellow-200 mb-1">
                            로그인이 필요합니다
                          </h3>
                          <p className="text-sm text-yellow-700 dark:text-yellow-300 mb-3">
                            상세 리딩을 사용하려면 로그인이 필요합니다.
                          </p>
                          <button
                            onClick={() => {
                              setShowDetailedReadings(false);
                              router.push('/login');
                            }}
                            className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg text-sm font-semibold transition-colors"
                          >
                            로그인 페이지로 이동
                          </button>
                        </div>
                      </div>
                    </div>
                  )}

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {DETAILED_READING_OPTIONS.map((option, index) => (
                      <motion.div
                        key={option.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.1 }}
                        onClick={() => handleOptionClick(option)}
                        className={`
                          rounded-lg border-2 p-5 transition-all
                          ${
                            !option.available
                              ? 'border-gray-200 dark:border-gray-700 opacity-60 cursor-not-allowed'
                              : !isAuthenticated
                              ? 'border-yellow-300 dark:border-yellow-600 opacity-75 cursor-not-allowed'
                              : 'border-purple-300 dark:border-purple-600 hover:border-purple-500 dark:hover:border-purple-400 hover:bg-purple-50 dark:hover:bg-purple-900/20 hover:shadow-lg cursor-pointer'
                          }
                        `}
                      >
                        <div className="flex items-start justify-between mb-2">
                          <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
                            {option.nameKo}
                          </h3>
                          {option.available ? (
                            <span className="px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded text-xs font-semibold">
                              이용 가능
                            </span>
                          ) : (
                            <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 rounded text-xs font-semibold">
                              준비 중
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                          {option.name}
                        </p>
                        <p className="text-sm text-gray-500 dark:text-gray-500">
                          {option.descriptionKo}
                        </p>
                        {option.available && (
                          <div className="mt-3">
                            {isAuthenticated ? (
                              <div className="text-purple-600 dark:text-purple-400 text-sm font-semibold">
                                클릭하여 시작 →
                              </div>
                            ) : (
                              <div className="text-yellow-600 dark:text-yellow-400 text-sm font-semibold">
                                ⚠️ 로그인이 필요합니다
                              </div>
                            )}
                          </div>
                        )}
                      </motion.div>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </main>
  );
}
