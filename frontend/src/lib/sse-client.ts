/**
 * SSE (Server-Sent Events) Client for Tarot Reading Streaming
 *
 * This module provides a type-safe SSE client for consuming real-time
 * reading generation events from the backend.
 */

export type SSEEventType =
  | 'started'
  | 'progress'
  | 'card_drawn'
  | 'rag_enrichment'
  | 'ai_generation'
  | 'section_complete'
  | 'complete'
  | 'error';

export type ReadingStage =
  | 'initializing'
  | 'drawing_cards'
  | 'enriching_context'
  | 'generating_ai'
  | 'finalizing'
  | 'completed';

export interface ProgressEvent {
  stage: ReadingStage;
  progress: number;
  message: string;
  details?: string;
}

export interface CardDrawnEvent {
  card_id: number;
  card_name: string;
  card_name_ko: string;
  position: string;
  is_reversed: boolean;
  progress: number;
}

export interface RAGEnrichmentEvent {
  cards_enriched: number;
  spread_context_loaded: boolean;
  category_context_loaded: boolean;
  message: string;
}

export interface AIGenerationEvent {
  provider: string;
  model: string;
  message: string;
}

export interface CompleteEvent {
  reading_id: string;
  total_time: number;
  message: string;
  reading_summary?: {
    reading_id: string;
    question: string;
    spread_type: string;
    card_count: number;
    category?: string;
  };
}

export interface ErrorEvent {
  error_type: string;
  message: string;
  details?: string;
  stage?: ReadingStage;
}

export interface SectionCompleteEvent {
  section: 'summary' | 'cards' | 'overall_reading' | 'advice';
  data: any;
  progress: number;
}

export interface SSEEventHandlers {
  onStarted?: () => void;
  onProgress?: (data: ProgressEvent) => void;
  onCardDrawn?: (data: CardDrawnEvent) => void;
  onRAGEnrichment?: (data: RAGEnrichmentEvent) => void;
  onAIGeneration?: (data: AIGenerationEvent) => void;
  onSectionComplete?: (data: SectionCompleteEvent) => void;
  onComplete?: (data: CompleteEvent) => void;
  onError?: (data: ErrorEvent) => void;
  onConnectionError?: (error: Error) => void;
}

export interface ReadingRequest {
  spread_type: 'one_card' | 'three_card_past_present_future' | 'three_card_situation_action_outcome';
  question: string;
  category?: string;
  selected_card_ids?: number[];  // User Selection Mode: 선택한 카드 ID 목록
  reversed_states?: boolean[];  // 카드의 역방향 상태 목록 (selected_card_ids와 함께 사용)
}

/**
 * SSE Client for streaming tarot readings
 */
export class SSEReadingClient {
  private eventSource: EventSource | null = null;
  private handlers: SSEEventHandlers;
  private apiUrl: string;
  private accessToken: string;

  constructor(apiUrl: string, accessToken: string, handlers: SSEEventHandlers) {
    this.apiUrl = apiUrl;
    this.accessToken = accessToken;
    this.handlers = handlers;
  }

  /**
   * Start streaming a reading
   */
  async startReading(request: ReadingRequest): Promise<void> {
    // Close any existing connection
    this.close();

    try {
      // Create SSE connection
      // Note: EventSource doesn't support custom headers, so we need to pass token as query param
      // or use fetch with streaming
      const url = `${this.apiUrl}/api/v1/readings/stream`;

      // Use fetch API for streaming with authorization header
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.accessToken}`,
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      if (!response.body) {
        throw new Error('Response body is null');
      }

      // Process the stream
      await this.processStream(response.body);

    } catch (error) {
      console.error('[SSE] Connection error:', error);
      if (this.handlers.onConnectionError) {
        this.handlers.onConnectionError(error as Error);
      }
    }
  }

  /**
   * Process the SSE stream
   */
  private async processStream(body: ReadableStream<Uint8Array>): Promise<void> {
    const reader = body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          break;
        }

        // Decode chunk and add to buffer
        buffer += decoder.decode(value, { stream: true });

        // Process complete SSE messages
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer

        let currentEvent: SSEEventType | null = null;

        for (const line of lines) {
          if (line.startsWith('event:')) {
            currentEvent = line.substring(6).trim() as SSEEventType;
          } else if (line.startsWith('data:')) {
            const data = line.substring(5).trim();
            if (currentEvent && data) {
              this.handleEvent(currentEvent, data);
            }
          }
        }
      }
    } catch (error) {
      console.error('[SSE] Stream processing error:', error);
      if (this.handlers.onConnectionError) {
        this.handlers.onConnectionError(error as Error);
      }
    } finally {
      reader.releaseLock();
    }
  }

  /**
   * Handle a single SSE event
   */
  private handleEvent(eventType: SSEEventType, dataStr: string): void {
    try {
      const data = JSON.parse(dataStr);

      switch (eventType) {
        case 'started':
          if (this.handlers.onStarted) {
            this.handlers.onStarted();
          }
          break;

        case 'progress':
          if (this.handlers.onProgress) {
            this.handlers.onProgress(data as ProgressEvent);
          }
          break;

        case 'card_drawn':
          if (this.handlers.onCardDrawn) {
            this.handlers.onCardDrawn(data as CardDrawnEvent);
          }
          break;

        case 'rag_enrichment':
          if (this.handlers.onRAGEnrichment) {
            this.handlers.onRAGEnrichment(data as RAGEnrichmentEvent);
          }
          break;

        case 'ai_generation':
          if (this.handlers.onAIGeneration) {
            this.handlers.onAIGeneration(data as AIGenerationEvent);
          }
          break;

        case 'section_complete':
          if (this.handlers.onSectionComplete) {
            this.handlers.onSectionComplete(data as SectionCompleteEvent);
          }
          break;

        case 'complete':
          if (this.handlers.onComplete) {
            this.handlers.onComplete(data as CompleteEvent);
          }
          break;

        case 'error':
          if (this.handlers.onError) {
            this.handlers.onError(data as ErrorEvent);
          }
          break;

        default:
          console.warn('[SSE] Unknown event type:', eventType);
      }
    } catch (error) {
      console.error('[SSE] Error parsing event data:', error, dataStr);
    }
  }

  /**
   * Close the SSE connection
   */
  close(): void {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }
}

/**
 * Hook-friendly SSE client creator
 */
export function createSSEReadingClient(
  apiUrl: string,
  accessToken: string,
  handlers: SSEEventHandlers
): SSEReadingClient {
  return new SSEReadingClient(apiUrl, accessToken, handlers);
}
