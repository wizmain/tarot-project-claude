'use client';

import { Card } from '@/types';
import TarotCard from './TarotCard';
import { motion } from 'framer-motion';

export interface CelticCrossPosition {
  index: number;
  position: 'present' | 'challenge' | 'past' | 'future' | 'above' | 'below' | 'advice' | 'external' | 'hopes_fears' | 'outcome';
  name: string;
  name_ko: string;
  description: string;
  description_ko: string;
}

export interface CelticCrossLayoutProps {
  positions: CelticCrossPosition[];
  selectedCards: Map<number, Card & { isReversed: boolean }>; // position index -> card data
  onPositionClick?: (positionIndex: number) => void;
  disabled?: boolean;
}

export default function CelticCrossLayout({
  positions,
  selectedCards,
  onPositionClick,
  disabled = false,
}: CelticCrossLayoutProps) {
  return (
    <div className="w-full max-w-6xl mx-auto">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4 md:p-8">
        <h3 className="text-xl md:text-2xl font-semibold text-gray-900 dark:text-white mb-8 text-center">
          켈틱 크로스 레이아웃
        </h3>
        
        {/* Desktop Layout - 4 rows */}
        <div className="hidden md:block">
          <div className="flex flex-col items-center gap-6">
            {/* 첫번째 줄: 3번 (미래) */}
            <div className="flex justify-center">
              {renderPositionSlot(3, positions[3], selectedCards.get(3), onPositionClick, disabled, positions[3].name_ko)}
            </div>
            
            {/* 두번째 줄: 6번(위), 1번(현재), 2번(도전), 5번(아래) */}
            <div className="flex items-center justify-center gap-6">
              {renderPositionSlot(4, positions[4], selectedCards.get(4), onPositionClick, disabled, positions[4].name_ko)}
              {renderPositionSlot(0, positions[0], selectedCards.get(0), onPositionClick, disabled, positions[0].name_ko)}
              {renderPositionSlot(1, positions[1], selectedCards.get(1), onPositionClick, disabled, positions[1].name_ko)}
              {renderPositionSlot(5, positions[5], selectedCards.get(5), onPositionClick, disabled, positions[5].name_ko)}
            </div>
            
            {/* 세번째 줄: 4번 (과거) */}
            <div className="flex justify-center">
              {renderPositionSlot(2, positions[2], selectedCards.get(2), onPositionClick, disabled, positions[2].name_ko)}
            </div>
            
            {/* 네번째 줄: 10번(결과), 9번(희망/두려움), 8번(외부), 7번(조언) */}
            <div className="flex items-center justify-center gap-6">
              {renderPositionSlot(9, positions[9], selectedCards.get(9), onPositionClick, disabled, positions[9].name_ko)}
              {renderPositionSlot(8, positions[8], selectedCards.get(8), onPositionClick, disabled, positions[8].name_ko)}
              {renderPositionSlot(7, positions[7], selectedCards.get(7), onPositionClick, disabled, positions[7].name_ko)}
              {renderPositionSlot(6, positions[6], selectedCards.get(6), onPositionClick, disabled, positions[6].name_ko)}
            </div>
          </div>
        </div>

        {/* Mobile Layout - 5 rows */}
        <div className="md:hidden">
          <div className="flex flex-col items-center gap-4">
            {/* 첫번째: 3번 */}
            <div className="flex justify-center">
              {renderPositionSlot(3, positions[3], selectedCards.get(3), onPositionClick, disabled, positions[3].name_ko)}
            </div>
            
            {/* 두번째: 1번, 2번 */}
            <div className="flex items-center justify-center gap-4">
              {renderPositionSlot(0, positions[0], selectedCards.get(0), onPositionClick, disabled, positions[0].name_ko)}
              {renderPositionSlot(1, positions[1], selectedCards.get(1), onPositionClick, disabled, positions[1].name_ko)}
            </div>
            
            {/* 세번째: 6번, 5번 */}
            <div className="flex items-center justify-center gap-4">
              {renderPositionSlot(4, positions[4], selectedCards.get(4), onPositionClick, disabled, positions[4].name_ko)}
              {renderPositionSlot(5, positions[5], selectedCards.get(5), onPositionClick, disabled, positions[5].name_ko)}
            </div>
            
            {/* 네번째: 10번, 9번 */}
            <div className="flex items-center justify-center gap-4">
              {renderPositionSlot(9, positions[9], selectedCards.get(9), onPositionClick, disabled, positions[9].name_ko)}
              {renderPositionSlot(8, positions[8], selectedCards.get(8), onPositionClick, disabled, positions[8].name_ko)}
            </div>
            
            {/* 다섯째: 8번, 7번 */}
            <div className="flex items-center justify-center gap-4">
              {renderPositionSlot(7, positions[7], selectedCards.get(7), onPositionClick, disabled, positions[7].name_ko)}
              {renderPositionSlot(6, positions[6], selectedCards.get(6), onPositionClick, disabled, positions[6].name_ko)}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function renderPositionSlot(
  index: number,
  position: CelticCrossPosition,
  card: (Card & { isReversed: boolean }) | undefined,
  onPositionClick?: (positionIndex: number) => void,
  disabled?: boolean,
  label?: string
) {
  const isEmpty = !card;
  const displayLabel = label || position.name_ko;
  const isChallenge = index === 1; // 2번 카드 (도전)는 가로로 표시

  return (
    <div className="flex flex-col items-center">
      <motion.div
        layout
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
        onClick={() => !disabled && onPositionClick && onPositionClick(index)}
        className={`
          relative rounded-lg
          ${isChallenge 
            ? 'h-32 w-48 md:h-36 md:w-56' // 가로 카드 (높이 < 너비)
            : 'w-32 h-48 md:w-36 md:h-56' // 세로 카드
          }
          ${isEmpty ? 'border-2 border-dashed border-purple-300 dark:border-purple-600' : ''}
          ${onPositionClick && !disabled ? 'cursor-pointer hover:scale-105 transition-transform' : ''}
        `}
      >
        {card ? (
          <div 
            className="w-full h-full"
            style={isChallenge ? { transform: 'rotate(90deg)' } : {}}
          >
            <div style={isChallenge ? { transform: 'rotate(-90deg)', width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' } : {}}>
              <TarotCard
                card={card}
                isRevealed={true}
                isReversed={card.isReversed}
                size="medium"
              />
            </div>
          </div>
        ) : (
          <div className="w-full h-full bg-gradient-to-br from-purple-50 to-indigo-50 dark:from-purple-900/20 dark:to-indigo-900/20 rounded-lg flex flex-col items-center justify-center p-4 border-2 border-dashed border-purple-300 dark:border-purple-600">
            <div className="text-center" style={isChallenge ? { transform: 'rotate(90deg)' } : {}}>
              <div className="text-2xl mb-2 text-purple-400 dark:text-purple-500">✨</div>
              <div className="text-xs font-semibold text-purple-600 dark:text-purple-400">
                {displayLabel}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {index + 1}
              </div>
            </div>
          </div>
        )}
      </motion.div>
      
      {/* Position Label - 카드 아래에 표시 */}
      <div className="mt-2 text-center">
        <div className="text-xs font-semibold text-purple-600 dark:text-purple-400 bg-white dark:bg-gray-800 px-2 py-1 rounded">
          {displayLabel}
        </div>
      </div>
    </div>
  );
}
