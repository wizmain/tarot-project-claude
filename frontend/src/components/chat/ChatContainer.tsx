'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Message } from '@/lib/api';
import MessageBubble from './MessageBubble';
import TypingIndicator from './TypingIndicator';
import { chatAPI } from '@/lib/api';
import ChatCardSelector from './ChatCardSelector';
import { Card } from '@/types';

interface ChatContainerProps {
  conversationId: string;
  onTarotSuggestion?: () => void;
  onTitleUpdate?: (conversationId: string, newTitle: string) => void;
}

export default function ChatContainer({
  conversationId,
  onTarotSuggestion,
  onTitleUpdate,
}: ChatContainerProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingMessages, setIsLoadingMessages] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showTarotSelector, setShowTarotSelector] = useState(false);
  const [isCreatingReading, setIsCreatingReading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    console.log('[ChatContainer] Component mounted/updated with conversationId:', conversationId);
  }, [conversationId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadMessages = useCallback(async () => {
    try {
      setIsLoadingMessages(true);
      setError(null);
      console.log('[ChatContainer] Loading messages for conversation:', conversationId);
      const response = await chatAPI.getMessages(conversationId);
      console.log('[ChatContainer] Messages loaded:', response.messages.length);
      setMessages(response.messages);
    } catch (error) {
      console.error('[ChatContainer] Failed to load messages:', error);
      const errorMessage = error instanceof Error ? error.message : '메시지를 불러오는데 실패했습니다.';
      setError(errorMessage);
    } finally {
      setIsLoadingMessages(false);
    }
  }, [conversationId]);

  useEffect(() => {
    if (conversationId) {
      loadMessages();
    }
  }, [conversationId, loadMessages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    
    // Optimistically add user message
    const tempUserMessage: Message = {
      id: `temp-${Date.now()}`,
      conversation_id: conversationId,
      role: 'user',
      content: userMessage,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMessage]);
    
    // 로딩 상태는 사용자 메시지가 화면에 보인 후에 시작
    setIsLoading(true);

    try {
      const response = await chatAPI.sendMessage(conversationId, {
        content: userMessage,
      });

      // 메시지 전송 후 전체 메시지 목록 다시 로드하여 사용자 메시지와 AI 응답 모두 가져오기
      const updatedMessages = await chatAPI.getMessages(conversationId);
      setMessages(updatedMessages.messages);

      // 제목이 업데이트된 경우 부모에 알림
      if (response.conversation_title && onTitleUpdate) {
        onTitleUpdate(conversationId, response.conversation_title);
      }

      // Show tarot suggestion if suggested
      if (response.suggest_tarot) {
        setShowTarotSelector(true);
        if (onTarotSuggestion) {
          onTarotSuggestion();
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      // Remove temp message on error
      setMessages((prev) => prev.filter((m) => m.id !== tempUserMessage.id));
    } finally {
      setIsLoading(false);
    }
  };

  const handleTarotCardsSelected = async (cards: Card[], reversedStates: boolean[]) => {
    try {
      setShowTarotSelector(false);

      // 최근 사용자 메시지를 질문으로 사용
      const recentUserMessage = messages
        .filter(m => m.role === 'user')
        .slice(-1)[0]?.content || '타로 리딩을 해주세요';

      // 카드 정보 구성 (모든 선택된 카드 포함 - 이미지 URL 포함)
      const cardsInfoWithImage = cards.map((card, idx) => {
        let position = '';
        if (cards.length === 3) {
          const positions = ['과거', '현재', '미래'];
          position = positions[idx];
        } else if (cards.length === 1) {
          position = '오늘의 카드';
        }
        return {
          id: card.id,
          name: card.name_ko || card.name,
          is_reversed: reversedStates[idx],
          image_url: card.image_url,
          position,
        };
      });

      // API용 카드 정보 (이미지 제외)
      const cardsInfo = cardsInfoWithImage.map(({ id, name, is_reversed }) => ({
        id,
        name,
        is_reversed,
      }));

      // 사용자가 선택한 카드를 메시지로 표시
      const userCardMessage = '🃏 선택한 카드';
      
      // 사용자 카드 선택 메시지를 먼저 표시 (optimistic update)
      const tempUserMessage: Message = {
        id: `temp-card-${Date.now()}`,
        conversation_id: conversationId,
        role: 'user',
        content: userCardMessage,
        metadata: {
          type: 'card_selection',
          cards: cardsInfoWithImage,
        },
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, tempUserMessage]);
      
      // 로딩 상태 시작
      setIsCreatingReading(true);

      console.log('[ChatContainer] Tarot reading request:', {
        question: recentUserMessage,
        cards_info: cardsInfo,
        totalCards: cards.length,
      });

      // 사용자 카드 선택 메시지를 먼저 저장
      await chatAPI.sendMessage(conversationId, {
        content: userCardMessage,
        metadata: {
          type: 'card_selection',
          cards: cardsInfoWithImage,
        },
      });

      // 타로 마스터(AI)에게 리딩 요청
      await chatAPI.addTarotReading(conversationId, {
        question: recentUserMessage,
        cards_info: cardsInfo,
      });

      // 메시지 목록 새로고침
      const updatedMessages = await chatAPI.getMessages(conversationId);
      setMessages(updatedMessages.messages);
    } catch (error) {
      console.error('[ChatContainer] Failed to create reading:', error);
      setError('타로 리딩 생성에 실패했습니다.');
      setShowTarotSelector(true); // 다시 카드 선택 UI 표시
    } finally {
      setIsCreatingReading(false);
    }
  };

  const handleCancelTarotSelection = () => {
    setShowTarotSelector(false);
  };

  if (isLoadingMessages) {
    return (
      <div className="flex flex-col h-full">
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
            <div className="text-gray-500 dark:text-gray-400">메시지를 불러오는 중...</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full min-w-0">
      {error && (
        <div className="bg-red-100 dark:bg-red-900 border-l-4 border-red-500 text-red-700 dark:text-red-200 p-4 m-4 rounded">
          <p className="font-semibold">오류</p>
          <p>{error}</p>
          <button
            onClick={loadMessages}
            className="mt-2 text-sm underline hover:no-underline"
          >
            다시 시도
          </button>
        </div>
      )}
      <div className="flex-1 overflow-y-auto p-4 min-w-0">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
            대화를 시작해보세요!
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            {(isLoading || isCreatingReading) && <TypingIndicator />}
          </>
        )}
        {showTarotSelector && (
          <div className="mt-4 p-3 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg border-2 border-indigo-300 dark:border-indigo-700 w-full max-w-full overflow-hidden">
            <div className="mb-3">
              <h3 className="text-base font-semibold text-indigo-900 dark:text-indigo-100 mb-1">
                타로 카드를 선택해주세요
              </h3>
              <p className="text-xs text-indigo-700 dark:text-indigo-300">
                대화 내용을 바탕으로 타로 리딩을 진행합니다.
              </p>
            </div>
            <ChatCardSelector
              cardCount={3}
              onCardsSelected={handleTarotCardsSelected}
              onCancel={handleCancelTarotSelection}
              disabled={isCreatingReading}
            />
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <div className="border-t border-gray-300 dark:border-gray-700 p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.nativeEvent.isComposing && handleSend()}
            placeholder="메시지를 입력하세요..."
            className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            disabled={isLoading}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400 text-white rounded-lg font-semibold transition-colors"
          >
            전송
          </button>
        </div>
      </div>
    </div>
  );
}

