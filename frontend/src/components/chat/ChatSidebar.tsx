'use client';

import { Conversation } from '@/lib/api';
import { useState, useEffect } from 'react';

interface ChatSidebarProps {
  conversations: Conversation[];
  currentConversationId?: string;
  onSelectConversation: (conversationId: string) => void;
  onCreateNew: () => void;
  onDeleteConversation: (conversationId: string) => void;
  isCreating?: boolean;
}

export default function ChatSidebar({
  conversations,
  currentConversationId,
  onSelectConversation,
  onCreateNew,
  onDeleteConversation,
  isCreating = false,
}: ChatSidebarProps) {
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleDelete = async (e: React.MouseEvent, conversationId: string) => {
    e.stopPropagation(); // 대화 선택 이벤트 방지
    if (!confirm('이 대화를 삭제하시겠습니까?')) {
      return;
    }
    setDeletingId(conversationId);
    try {
      await onDeleteConversation(conversationId);
    } finally {
      setDeletingId(null);
    }
  };
  return (
    <div className="w-64 bg-gray-100 dark:bg-gray-800 border-r border-gray-300 dark:border-gray-700 flex flex-col h-full">
      <div className="p-4 border-b border-gray-300 dark:border-gray-700">
        <button
          onClick={onCreateNew}
          disabled={isCreating}
          className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 disabled:cursor-not-allowed text-white rounded-lg px-4 py-2 font-semibold transition-colors flex items-center justify-center gap-2"
        >
          {isCreating ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              <span>생성 중...</span>
            </>
          ) : (
            '새 대화 시작'
          )}
        </button>
      </div>
      <div className="flex-1 overflow-y-auto">
        {conversations.length === 0 ? (
          <div className="p-4 text-gray-500 dark:text-gray-400 text-sm text-center">
            대화가 없습니다
          </div>
        ) : (
          <div className="p-2">
            {conversations.map((conv) => (
              <div
                key={conv.id}
                className={`relative group rounded-lg mb-2 transition-colors ${
                  currentConversationId === conv.id
                    ? 'bg-indigo-100 dark:bg-indigo-900'
                    : 'hover:bg-gray-200 dark:hover:bg-gray-700'
                }`}
              >
                <button
                  onClick={() => onSelectConversation(conv.id)}
                  className={`w-full text-left p-3 pr-10 transition-colors ${
                    currentConversationId === conv.id
                      ? 'text-indigo-900 dark:text-indigo-100'
                      : 'text-gray-900 dark:text-gray-100'
                  }`}
                >
                  <div className="font-semibold truncate">{conv.title}</div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    {new Date(conv.updated_at).toLocaleDateString('ko-KR')}
                  </div>
                </button>
                <button
                  onClick={(e) => handleDelete(e, conv.id)}
                  disabled={deletingId === conv.id}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-md opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-100 dark:hover:bg-red-900/30 text-red-600 dark:text-red-400 disabled:opacity-50"
                  title="대화 삭제"
                >
                  {deletingId === conv.id ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-red-600 dark:border-red-400"></div>
                  ) : (
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      className="h-4 w-4"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                      />
                    </svg>
                  )}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

