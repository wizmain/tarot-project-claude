'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';

interface StarRatingProps {
  rating: number;
  onRatingChange: (rating: number) => void;
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
  showLabel?: boolean;
}

const sizeClasses = {
  small: 'text-lg',
  medium: 'text-2xl',
  large: 'text-3xl',
};

const labelMap: Record<number, string> = {
  1: '별로예요',
  2: '아쉬워요',
  3: '괜찮아요',
  4: '좋아요',
  5: '최고예요',
};

export default function StarRating({
  rating,
  onRatingChange,
  size = 'medium',
  disabled = false,
  showLabel = true,
}: StarRatingProps) {
  const [hoveredRating, setHoveredRating] = useState<number | null>(null);

  const handleClick = (value: number) => {
    if (!disabled) {
      onRatingChange(value);
    }
  };

  const displayRating = hoveredRating ?? rating;

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="flex items-center gap-1">
        {[1, 2, 3, 4, 5].map((value) => (
          <button
            key={value}
            type="button"
            onClick={() => handleClick(value)}
            onMouseEnter={() => !disabled && setHoveredRating(value)}
            onMouseLeave={() => setHoveredRating(null)}
            disabled={disabled}
            className={`${sizeClasses[size]} transition-all ${
              disabled
                ? 'cursor-not-allowed opacity-50'
                : 'cursor-pointer hover:scale-110'
            }`}
            aria-label={`${value}점`}
          >
            <motion.span
              initial={false}
              animate={{
                scale: hoveredRating === value ? 1.2 : 1,
              }}
              transition={{ duration: 0.1 }}
            >
              {value <= displayRating ? '⭐' : '☆'}
            </motion.span>
          </button>
        ))}
      </div>
      {showLabel && displayRating > 0 && (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-sm font-medium text-gray-600 dark:text-gray-400"
        >
          {labelMap[displayRating]}
        </motion.p>
      )}
    </div>
  );
}

