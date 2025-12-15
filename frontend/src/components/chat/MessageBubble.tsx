'use client';

import Image from 'next/image';
import { Message } from '@/lib/api';

interface CardInfo {
  id: number;
  name: string;
  is_reversed: boolean;
  image_url?: string | null;
  position?: string;
}

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';
  
  // 카드 선택 메시지인지 확인
  const isCardSelection = message.metadata?.type === 'card_selection';
  const selectedCards: CardInfo[] = message.metadata?.cards || [];

  // 카드 이미지 URL 생성 함수
  const getCardImageUrl = (card: CardInfo) => {
    if (card.image_url) {
      // image_url이 상대 경로인 경우 그대로 사용
      if (card.image_url.startsWith('/')) {
        return card.image_url;
      }
      // 절대 URL인 경우 그대로 사용
      if (card.image_url.startsWith('http')) {
        return card.image_url;
      }
      // 파일명만 있는 경우 경로 추가
      return `/images/cards/${card.image_url}`;
    }
    // 기본 이미지 (카드 백)
    return '/images/cards/card-back.svg';
  };

  return (
    <div className={`flex ${isUser ? 'flex-row-reverse' : 'flex-row'} items-start gap-3 mb-4`}>
      {/* 아바타 */}
      {isAssistant ? (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center text-white text-sm font-semibold">
          AI
        </div>
      ) : (
        <div className="flex-shrink-0 w-8" />
      )}
      
      {/* 메시지 버블 */}
      <div className={`max-w-[80%] ${isUser ? 'text-right' : 'text-left'}`}>
        <div
          className={`inline-block rounded-2xl px-4 py-3 text-left ${
            isUser
              ? 'bg-indigo-600 text-white'
              : 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100'
          }`}
        >
          <div className="whitespace-pre-wrap">{message.content}</div>
          
          {/* 카드 선택 메시지인 경우 카드 이미지 표시 */}
          {isCardSelection && selectedCards.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-3 justify-center">
              {selectedCards.map((card) => (
                <div key={card.id} className="flex flex-col items-center">
                  {/* 카드 위치 레이블 */}
                  {card.position && (
                    <span className="text-xs font-semibold mb-1 text-indigo-200">
                      [{card.position}]
                    </span>
                  )}
                  {/* 카드 이미지 */}
                  <div 
                    className={`relative w-16 h-24 rounded-lg overflow-hidden shadow-lg border-2 border-indigo-300 ${
                      card.is_reversed ? 'transform rotate-180' : ''
                    }`}
                  >
                    <Image
                      src={getCardImageUrl(card)}
                      alt={card.name}
                      fill
                      className="object-cover"
                      sizes="64px"
                      onError={(e) => {
                        // 이미지 로드 실패 시 기본 이미지로 대체
                        const target = e.target as HTMLImageElement;
                        target.src = '/images/cards/card-back.svg';
                      }}
                    />
                  </div>
                  {/* 카드 이름 */}
                  <span className="text-xs mt-1 text-center max-w-[70px] truncate text-indigo-100">
                    {card.name}
                  </span>
                  {/* 역방향 표시 */}
                  {card.is_reversed && (
                    <span className="text-[10px] text-indigo-200">(역방향)</span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
        <div
          className={`text-xs mt-1 ${
            isUser ? 'text-right text-gray-500 dark:text-gray-400' : 'text-gray-500 dark:text-gray-400 ml-2'
          }`}
        >
          {new Date(message.created_at).toLocaleTimeString('ko-KR', {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </div>
      </div>
    </div>
  );
}

