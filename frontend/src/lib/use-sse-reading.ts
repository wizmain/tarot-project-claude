/**
 * React Hook for SSE-based Tarot Reading
 *
 * Manages SSE connection state and provides real-time updates
 */
'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import {
  createSSEReadingClient,
  type SSEReadingClient,
  type ReadingRequest,
  type ProgressEvent,
  type CardDrawnEvent,
  type SectionCompleteEvent,
  type CompleteEvent,
  type ErrorEvent,
  type ReadingStage,
} from './sse-client';

interface UseSSEReadingState {
  isStreaming: boolean;
  progress: number;
  stage: ReadingStage | null;
  message: string;
  drawnCards: CardDrawnEvent[];
  readingId: string | null;
  error: string | null;
  totalTime: number | null;
  // Incremental sections
  summary: string | null;
  cards: any[] | null;
  overallReading: string | null;
  advice: any | null;
}

interface UseSSEReadingResult extends UseSSEReadingState {
  startReading: (request: ReadingRequest) => Promise<void>;
  reset: () => void;
}

export function useSSEReading(apiUrl: string, accessToken: string): UseSSEReadingResult {
  const [state, setState] = useState<UseSSEReadingState>({
    isStreaming: false,
    progress: 0,
    stage: null,
    message: '',
    drawnCards: [],
    readingId: null,
    error: null,
    totalTime: null,
    summary: null,
    cards: null,
    overallReading: null,
    advice: null,
  });

  const clientRef = useRef<SSEReadingClient | null>(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (clientRef.current) {
        clientRef.current.close();
      }
    };
  }, []);

  const reset = useCallback(() => {
    setState({
      isStreaming: false,
      progress: 0,
      stage: null,
      message: '',
      drawnCards: [],
      readingId: null,
      error: null,
      totalTime: null,
      summary: null,
      cards: null,
      overallReading: null,
      advice: null,
    });
    if (clientRef.current) {
      clientRef.current.close();
      clientRef.current = null;
    }
  }, []);

  const startReading = useCallback(
    async (request: ReadingRequest) => {
      // Reset state
      setState({
        isStreaming: true,
        progress: 0,
        stage: 'initializing',
        message: '리딩을 시작합니다...',
        drawnCards: [],
        readingId: null,
        error: null,
        totalTime: null,
        summary: null,
        cards: null,
        overallReading: null,
        advice: null,
      });

      // Create SSE client
      const client = createSSEReadingClient(apiUrl, accessToken, {
        onStarted: () => {
          console.log('[SSE Hook] Started');
        },

        onProgress: (data: ProgressEvent) => {
          console.log('[SSE Hook] Progress:', data);
          setState((prev) => ({
            ...prev,
            progress: data.progress,
            stage: data.stage,
            message: data.message,
          }));
        },

        onCardDrawn: (data: CardDrawnEvent) => {
          console.log('[SSE Hook] Card Drawn:', data);
          setState((prev) => ({
            ...prev,
            drawnCards: [...prev.drawnCards, data],
            progress: data.progress,
          }));
        },

        onRAGEnrichment: (data) => {
          console.log('[SSE Hook] RAG Enrichment:', data);
        },

        onAIGeneration: (data) => {
          console.log('[SSE Hook] AI Generation:', data);
        },

        onSectionComplete: (data: SectionCompleteEvent) => {
          console.log('[SSE Hook] Section Complete:', data);
          setState((prev) => {
            const updates: Partial<UseSSEReadingState> = {
              progress: data.progress,
            };

            // Update specific section based on type
            if (data.section === 'summary') {
              updates.summary = data.data.summary;
            } else if (data.section === 'cards') {
              updates.cards = data.data.cards;
            } else if (data.section === 'overall_reading') {
              updates.overallReading = data.data.overall_reading;
            } else if (data.section === 'advice') {
              updates.advice = data.data.advice;
            }

            return { ...prev, ...updates };
          });
        },

        onComplete: (data: CompleteEvent) => {
          console.log('[SSE Hook] Complete:', data);
          console.log('[SSE Hook] Setting state to completed - no navigation should occur');
          setState((prev) => ({
            ...prev,
            isStreaming: false,
            progress: 100,
            stage: 'completed',
            message: '리딩이 완료되었습니다!',
            readingId: data.reading_id,
            totalTime: data.total_time,
          }));
          console.log('[SSE Hook] State update dispatched');
        },

        onError: (data: ErrorEvent) => {
          console.error('[SSE Hook] Error:', data);
          setState((prev) => ({
            ...prev,
            isStreaming: false,
            error: data.message,
          }));
        },

        onConnectionError: (error: Error) => {
          console.error('[SSE Hook] Connection Error:', error);
          setState((prev) => ({
            ...prev,
            isStreaming: false,
            error: `연결 오류: ${error.message}`,
          }));
        },
      });

      clientRef.current = client;

      try {
        await client.startReading(request);
      } catch (error) {
        console.error('[SSE Hook] Start Reading Error:', error);
        setState((prev) => ({
          ...prev,
          isStreaming: false,
          error: error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다',
        }));
      }
    },
    [apiUrl, accessToken]
  );

  return {
    ...state,
    startReading,
    reset,
  };
}
