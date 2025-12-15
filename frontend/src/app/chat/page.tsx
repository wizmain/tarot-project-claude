'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import ChatContainer from '@/components/chat/ChatContainer';
import ChatSidebar from '@/components/chat/ChatSidebar';
import { chatAPI, Conversation } from '@/lib/api';

function ChatPageContent() {
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadConversations = useCallback(async () => {
    try {
      setIsLoading(true);
      console.log('[ChatPage] Loading conversations...');
      const response = await chatAPI.getConversations();
      console.log('[ChatPage] Conversations loaded:', response.conversations.length, 'conversations');
      console.log('[ChatPage] Response:', response);
      setConversations(response.conversations);

      // 첫 번째 대화 선택 또는 새 대화 생성
      if (response.conversations.length > 0 && !currentConversationId) {
        console.log('[ChatPage] Setting first conversation:', response.conversations[0].id);
        setCurrentConversationId(response.conversations[0].id);
      } else {
        console.log('[ChatPage] No conversations or already has currentConversationId:', currentConversationId);
      }
    } catch (error) {
      console.error('[ChatPage] Failed to load conversations:', error);
      if (error instanceof Error) {
        console.error('[ChatPage] Error details:', {
          message: error.message,
          stack: error.stack,
        });
      }
      setError('대화 목록을 불러오는데 실패했습니다.');
    } finally {
      console.log('[ChatPage] loadConversations finished, setting isLoading to false');
      setIsLoading(false);
    }
  }, []); // 의존성 없음 - 한 번만 생성

  useEffect(() => {
    if (isAuthenticated && !authLoading) {
      console.log('[ChatPage] useEffect triggered - isAuthenticated:', isAuthenticated, 'authLoading:', authLoading);
      loadConversations();
    } else {
      console.log('[ChatPage] useEffect skipped - isAuthenticated:', isAuthenticated, 'authLoading:', authLoading);
    }
  }, [isAuthenticated, authLoading, loadConversations]);

  const handleCreateNew = async () => {
    try {
      setIsCreating(true);
      setError(null);
      console.log('[Chat] Creating new conversation...');
      const newConv = await chatAPI.createConversation({});
      console.log('[Chat] Conversation created:', newConv);
      setConversations((prev) => [newConv, ...prev]);
      setCurrentConversationId(newConv.id);
    } catch (error) {
      console.error('[Chat] Failed to create conversation:', error);
      const errorMessage = error instanceof Error ? error.message : '대화 생성에 실패했습니다.';
      setError(errorMessage);
      // 에러 메시지를 5초 후 자동으로 제거
      setTimeout(() => setError(null), 5000);
    } finally {
      setIsCreating(false);
    }
  };

  const handleSelectConversation = (conversationId: string) => {
    setCurrentConversationId(conversationId);
  };

  const handleDeleteConversation = async (conversationId: string) => {
    try {
      setError(null);
      console.log('[Chat] Deleting conversation:', conversationId);
      await chatAPI.deleteConversation(conversationId);
      console.log('[Chat] Conversation deleted successfully');
      
      // 목록에서 제거
      removeConversationFromList(conversationId);
    } catch (error) {
      console.error('[Chat] Failed to delete conversation:', error);
      const errorMessage = error instanceof Error ? error.message : '대화 삭제에 실패했습니다.';
      
      // 404 에러: 이미 삭제된 대화로 간주하고 목록에서 제거
      if (errorMessage.includes('404') || errorMessage.includes('Not Found')) {
        console.log('[Chat] Conversation not found, removing from list');
        removeConversationFromList(conversationId);
        return;
      }
      
      setError(errorMessage);
      // 에러 메시지를 5초 후 자동으로 제거
      setTimeout(() => setError(null), 5000);
    }
  };

  const removeConversationFromList = (conversationId: string) => {
    setConversations((prev) => prev.filter((conv) => conv.id !== conversationId));
    
    // 현재 선택된 대화가 삭제된 경우 다른 대화 선택
    if (currentConversationId === conversationId) {
      const remaining = conversations.filter((conv) => conv.id !== conversationId);
      setCurrentConversationId(remaining.length > 0 ? remaining[0].id : null);
    }
  };

  const handleTitleUpdate = (conversationId: string, newTitle: string) => {
    console.log('[Chat] Title updated for conversation:', conversationId, 'to:', newTitle);
    setConversations((prev) =>
      prev.map((conv) =>
        conv.id === conversationId
          ? { ...conv, title: newTitle, updated_at: new Date().toISOString() }
          : conv
      )
    );
  };

  const handleTarotSuggestion = () => {
    // 타로 리딩 제안 UI 표시 (추후 구현)
    console.log('Tarot reading suggested');
  };

  // 모든 hooks는 조건부 return 이전에 호출되어야 함
  // 렌더링 로그는 useEffect 대신 직접 사용 (조건부 hooks 방지)
  // useEffect(() => {
  //   console.log('[ChatPage] Render - currentConversationId:', currentConversationId, 'conversations:', conversations.length);
  // }, [currentConversationId, conversations.length]);

  if (authLoading || isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-white dark:bg-gray-900 overflow-hidden">
      <ChatSidebar
        conversations={conversations}
        currentConversationId={currentConversationId || undefined}
        onSelectConversation={handleSelectConversation}
        onCreateNew={handleCreateNew}
        onDeleteConversation={handleDeleteConversation}
        isCreating={isCreating}
      />
      {error && (
        <div className="fixed top-4 right-4 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg z-50">
          {error}
        </div>
      )}
      <div className="flex-1 flex flex-col min-w-0">
        {currentConversationId ? (
          <ChatContainer
            conversationId={currentConversationId}
            onTarotSuggestion={handleTarotSuggestion}
            onTitleUpdate={handleTitleUpdate}
          />
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500 dark:text-gray-400">
            대화를 선택하거나 새로 시작하세요
          </div>
        )}
      </div>
    </div>
  );
}

export default function ChatPage() {
  return (
    <ProtectedRoute>
      <ChatPageContent />
    </ProtectedRoute>
  );
}

