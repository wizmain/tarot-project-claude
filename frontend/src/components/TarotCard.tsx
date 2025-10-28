'use client';

import { Card } from '@/types';
import { motion } from 'framer-motion';
import { useState } from 'react';

interface TarotCardProps {
  card?: Card;
  isRevealed?: boolean;
  isReversed?: boolean;
  onClick?: () => void;
  className?: string;
  size?: 'small' | 'medium' | 'large';
}

export default function TarotCard({
  card,
  isRevealed = false,
  isReversed = false,
  onClick,
  className = '',
  size = 'medium',
}: TarotCardProps) {
  const [isFlipped, setIsFlipped] = useState(isRevealed);

  const handleClick = () => {
    if (onClick) {
      onClick();
    } else if (card) {
      setIsFlipped(!isFlipped);
    }
  };

  const sizeClasses = {
    small: 'w-24 h-36',
    medium: 'w-40 h-60',
    large: 'w-48 h-72',
  };

  return (
    <div
      className={`perspective-1000 ${sizeClasses[size]} ${className}`}
      onClick={handleClick}
    >
      <motion.div
        className="relative w-full h-full cursor-pointer preserve-3d"
        animate={{ rotateY: isFlipped ? 180 : 0 }}
        transition={{ duration: 0.6, type: 'spring' }}
        style={{
          transformStyle: 'preserve-3d',
        }}
      >
        {/* Card Back */}
        <div
          className="absolute w-full h-full backface-hidden rounded-lg shadow-lg"
          style={{
            backfaceVisibility: 'hidden',
          }}
        >
          <div className="w-full h-full bg-gradient-to-br from-purple-900 via-indigo-800 to-purple-900 rounded-lg border-4 border-gold-400 flex items-center justify-center p-4">
            <div className="text-center">
              <div className="text-gold-300 text-6xl mb-2">✦</div>
              <div className="text-gold-300 text-sm font-serif">TAROT</div>
            </div>
          </div>
        </div>

        {/* Card Front */}
        <div
          className="absolute w-full h-full backface-hidden rounded-lg shadow-lg"
          style={{
            backfaceVisibility: 'hidden',
            transform: `rotateY(180deg) ${isReversed ? 'rotate(180deg)' : ''}`,
          }}
        >
          {card ? (
            <div className="w-full h-full bg-white rounded-lg border-4 border-gray-300 flex flex-col p-3">
              {/* Card Image Placeholder */}
              <div className="flex-1 bg-gradient-to-br from-purple-100 to-indigo-100 rounded flex items-center justify-center mb-2 relative overflow-hidden">
                {card.image_url ? (
                  <img
                    src={card.image_url}
                    alt={card.name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="text-center p-2">
                    <div className="text-4xl mb-2">
                      {card.suit === 'wands' && '🔥'}
                      {card.suit === 'cups' && '🏆'}
                      {card.suit === 'swords' && '⚔️'}
                      {card.suit === 'pentacles' && '⭐'}
                      {card.arcana_type === 'major' && '✨'}
                    </div>
                    <div className="text-xs text-gray-600 font-bold">
                      {card.name_ko}
                    </div>
                  </div>
                )}
                {isReversed && (
                  <div className="absolute top-1 right-1 bg-red-500 text-white text-xs px-2 py-1 rounded">
                    역방향
                  </div>
                )}
              </div>

              {/* Card Name */}
              <div className="text-center">
                <div className="text-xs font-bold text-gray-800 truncate">
                  {card.name}
                </div>
                <div className="text-xs text-gray-600 truncate">
                  {card.name_ko}
                </div>
              </div>
            </div>
          ) : (
            <div className="w-full h-full bg-gray-200 rounded-lg flex items-center justify-center">
              <span className="text-gray-400">No Card</span>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
}
