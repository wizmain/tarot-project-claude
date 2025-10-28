'use client';

/**
 * Forgot Password Page
 *
 * Allows users to request a password reset email
 */

import { useState } from 'react';
import Link from 'next/link';
import { API_BASE_URL } from '@/lib/constants';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/password-reset`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '비밀번호 재설정 요청에 실패했습니다.');
      }

      setSuccess(true);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : '비밀번호 재설정 요청에 실패했습니다.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 to-indigo-100 px-4">
      <div className="max-w-md w-full space-y-8 bg-white p-8 rounded-xl shadow-lg">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            비밀번호 재설정
          </h1>
          <p className="text-gray-600">
            가입하신 이메일 주소를 입력하시면 비밀번호 재설정 링크를 보내드립니다.
          </p>
        </div>

        {/* Success Message */}
        {success ? (
          <div className="space-y-6">
            <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg">
              <p className="font-medium mb-1">이메일이 전송되었습니다!</p>
              <p className="text-sm">
                {email}으로 비밀번호 재설정 링크를 보냈습니다.
                이메일을 확인하고 링크를 클릭하여 비밀번호를 재설정하세요.
              </p>
            </div>

            {/* Links */}
            <div className="space-y-3">
              <Link
                href="/login"
                className="block w-full text-center py-3 px-4 border border-purple-600 text-purple-600 rounded-lg font-medium hover:bg-purple-50 transition-colors"
              >
                로그인으로 돌아가기
              </Link>
              <button
                onClick={() => {
                  setSuccess(false);
                  setEmail('');
                }}
                className="block w-full text-center text-sm text-gray-600 hover:text-gray-900"
              >
                다시 시도하기
              </button>
            </div>
          </div>
        ) : (
          <>
            {/* Error Message */}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                {error}
              </div>
            )}

            {/* Reset Form */}
            <form onSubmit={handleSubmit} className="mt-8 space-y-6">
              <div>
                <label
                  htmlFor="email"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  이메일
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    if (error) setError('');
                  }}
                  className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="your@email.com"
                />
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isLoading}
                className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-lg text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isLoading ? '전송 중...' : '재설정 링크 보내기'}
              </button>
            </form>

            {/* Back to Login Link */}
            <div className="text-center">
              <Link
                href="/login"
                className="text-sm font-medium text-purple-600 hover:text-purple-500"
              >
                ← 로그인으로 돌아가기
              </Link>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
