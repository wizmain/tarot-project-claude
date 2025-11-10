'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import StarRating from '@/components/StarRating';
import { feedbackAPI, FeedbackResponse, FeedbackCreate } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';

interface FeedbackSectionProps {
  readingId: string;
  onFeedbackSubmitted?: () => void;
}

export default function FeedbackSection({
  readingId,
  onFeedbackSubmitted,
}: FeedbackSectionProps) {
  const { accessToken } = useAuth();
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState('');
  const [helpful, setHelpful] = useState(true);
  const [accurate, setAccurate] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [existingFeedback, setExistingFeedback] = useState<FeedbackResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isCollapsed, setIsCollapsed] = useState(false);

  // Load existing feedback
  useEffect(() => {
    const loadFeedback = async () => {
      if (!accessToken || !readingId) return;

      try {
        setIsLoading(true);
        const feedbackList = await feedbackAPI.getFeedback(readingId, 1, 1);
        if (feedbackList.length > 0) {
          const feedback = feedbackList[0];
          setExistingFeedback(feedback);
          setRating(feedback.rating);
          setComment(feedback.comment || '');
          setHelpful(feedback.helpful);
          setAccurate(feedback.accurate);
        }
      } catch (err) {
        // If no feedback exists, that's okay
        console.log('No existing feedback found');
      } finally {
        setIsLoading(false);
      }
    };

    loadFeedback();
  }, [readingId, accessToken]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (rating === 0) {
      setError('별점을 선택해주세요');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const feedbackData: FeedbackCreate = {
        rating,
        comment: comment.trim() || undefined,
        helpful,
        accurate,
      };

      if (existingFeedback) {
        // Update existing feedback
        await feedbackAPI.updateFeedback(existingFeedback.id, feedbackData);
      } else {
        // Create new feedback
        await feedbackAPI.createFeedback(readingId, feedbackData);
      }

      setSuccess(true);
      if (onFeedbackSubmitted) {
        onFeedbackSubmitted();
      }

      // Reset form after 2 seconds
      setTimeout(() => {
        setIsCollapsed(true);
      }, 2000);
    } catch (err: any) {
      console.error('Feedback submission error:', err);
      setError(
        err.message || '피드백 제출 중 오류가 발생했습니다. 다시 시도해주세요.'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return null; // Don't show anything while loading
  }

  if (isCollapsed && success) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-green-50 dark:bg-green-900/20 border-2 border-green-300 dark:border-green-700 rounded-lg p-6"
      >
        <div className="flex items-center gap-3">
          <span className="text-2xl">✅</span>
          <div>
            <h3 className="font-semibold text-green-900 dark:text-green-200">
              피드백 감사합니다!
            </h3>
            <p className="text-sm text-green-700 dark:text-green-300">
              소중한 의견이 서비스 개선에 도움이 됩니다.
            </p>
          </div>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 md:p-8"
    >
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-1">
            {existingFeedback ? '📝 피드백 수정하기' : '⭐ 리딩 평가하기'}
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {existingFeedback
              ? '피드백을 수정할 수 있습니다'
              : '이 리딩이 도움이 되었나요? 평가해주세요!'}
          </p>
        </div>
        {success && (
          <button
            onClick={() => setIsCollapsed(true)}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            aria-label="닫기"
          >
            ✕
          </button>
        )}
      </div>

      <AnimatePresence>
        {success ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
            className="text-center py-4"
          >
            <div className="text-4xl mb-2">🎉</div>
            <p className="text-lg font-semibold text-green-600 dark:text-green-400">
              감사합니다!
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              소중한 피드백이 전달되었습니다.
            </p>
          </motion.div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Star Rating */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3 text-center">
                별점을 선택해주세요 <span className="text-red-500">*</span>
              </label>
              <StarRating
                rating={rating}
                onRatingChange={setRating}
                size="large"
                disabled={isSubmitting}
              />
            </div>

            {/* Comment */}
            <div>
              <label
                htmlFor="comment"
                className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
              >
                코멘트 (선택사항)
              </label>
              <textarea
                id="comment"
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="리딩에 대한 의견을 남겨주세요..."
                rows={4}
                maxLength={1000}
                disabled={isSubmitting}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white resize-none disabled:opacity-50"
              />
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400 text-right">
                {comment.length}/1000
              </p>
            </div>

            {/* Checkboxes */}
            <div className="space-y-3">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={helpful}
                  onChange={(e) => setHelpful(e.target.checked)}
                  disabled={isSubmitting}
                  className="w-5 h-5 text-purple-600 focus:ring-purple-500 rounded disabled:opacity-50"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  💡 이 리딩이 도움이 되었어요
                </span>
              </label>
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={accurate}
                  onChange={(e) => setAccurate(e.target.checked)}
                  disabled={isSubmitting}
                  className="w-5 h-5 text-purple-600 focus:ring-purple-500 rounded disabled:opacity-50"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  🎯 이 리딩이 정확했어요
                </span>
              </label>
            </div>

            {/* Error Message */}
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3"
              >
                <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
              </motion.div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isSubmitting || rating === 0}
              className="w-full px-6 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-lg font-semibold transition-all shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="animate-spin">⏳</span>
                  제출 중...
                </span>
              ) : existingFeedback ? (
                '📝 피드백 수정하기'
              ) : (
                '⭐ 피드백 제출하기'
              )}
            </button>
          </form>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

