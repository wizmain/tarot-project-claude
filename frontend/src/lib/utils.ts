/**
 * Utility functions for the application
 */

/**
 * Fisher-Yates shuffle algorithm for randomizing array order
 * Creates a new shuffled array without modifying the original
 * 
 * @param array Array to shuffle
 * @returns New shuffled array (original array is not modified)
 * 
 * @example
 * const cards = [1, 2, 3, 4, 5];
 * const shuffled = shuffleArray(cards);
 * // shuffled: [3, 1, 5, 2, 4] (random order)
 * // cards: [1, 2, 3, 4, 5] (unchanged)
 */
export function shuffleArray<T>(array: T[]): T[] {
  const shuffled = [...array]; // Create a copy to avoid mutating original
  
  for (let i = shuffled.length - 1; i > 0; i--) {
    // Pick a random index from 0 to i
    const j = Math.floor(Math.random() * (i + 1));
    
    // Swap elements at positions i and j
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  
  return shuffled;
}

