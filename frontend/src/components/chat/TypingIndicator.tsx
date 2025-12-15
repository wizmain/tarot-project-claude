'use client';

/**
 * TypingIndicator - AI가 답변을 생성 중일 때 표시되는 애니메이션 컴포넌트
 */
export default function TypingIndicator() {
  return (
    <div className="flex items-start gap-3 mb-4">
      {/* AI 아바타 */}
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center text-white text-sm font-semibold">
        AI
      </div>
      
      {/* 타이핑 인디케이터 */}
      <div className="flex-1 max-w-[80%]">
        <div className="inline-block bg-gray-200 dark:bg-gray-700 rounded-2xl px-4 py-3">
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 bg-gray-500 dark:bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
            <div className="w-2 h-2 bg-gray-500 dark:bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
            <div className="w-2 h-2 bg-gray-500 dark:bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
          </div>
        </div>
        <div className="mt-1 text-xs text-gray-500 dark:text-gray-400 ml-2">
          AI가 답변을 생성하고 있습니다...
        </div>
      </div>
    </div>
  );
}

