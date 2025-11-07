"""
SSE Event Schemas for Streaming Reading Generation

This module defines the event types and data structures for Server-Sent Events
used during real-time tarot reading generation.
"""
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class SSEEventType(str, Enum):
    """SSE event types for reading generation"""
    STARTED = "started"
    PROGRESS = "progress"
    CARD_DRAWN = "card_drawn"
    RAG_ENRICHMENT = "rag_enrichment"
    AI_GENERATION = "ai_generation"
    CHUNK = "chunk"  # AI response chunk
    SECTION_COMPLETE = "section_complete"  # Individual section completed
    COMPLETE = "complete"
    ERROR = "error"


class ReadingStage(str, Enum):
    """Stages of reading generation"""
    INITIALIZING = "initializing"
    DRAWING_CARDS = "drawing_cards"
    ENRICHING_CONTEXT = "enriching_context"
    GENERATING_AI = "generating_ai"
    FINALIZING = "finalizing"
    COMPLETED = "completed"


class SSEEvent(BaseModel):
    """Base SSE event structure"""
    event: SSEEventType
    data: Dict[str, Any]

    def to_sse_format(self) -> str:
        """
        Convert to SSE format string

        Returns:
            SSE formatted string (e.g., "event: progress\\ndata: {...}\\n\\n")
        """
        import json
        return f"event: {self.event.value}\ndata: {json.dumps(self.data, ensure_ascii=False)}\n\n"


class StartedEvent(BaseModel):
    """Event sent when reading generation starts"""
    reading_id: Optional[str] = None
    message: str = "타로 리딩을 시작합니다..."


class ProgressEvent(BaseModel):
    """Event for progress updates"""
    stage: ReadingStage
    progress: int = Field(..., ge=0, le=100, description="Progress percentage (0-100)")
    message: str
    details: Optional[str] = None


class CardDrawnEvent(BaseModel):
    """Event when a card is drawn"""
    card_id: int
    card_name: str
    card_name_ko: str
    position: str
    is_reversed: bool
    progress: int = Field(..., ge=0, le=100)


class RAGEnrichmentEvent(BaseModel):
    """Event when RAG context enrichment completes"""
    cards_enriched: int
    spread_context_loaded: bool
    category_context_loaded: bool
    message: str = "카드 지식 검색 완료"


class AIGenerationEvent(BaseModel):
    """Event when AI generation starts"""
    provider: str
    model: str
    message: str = "AI 리딩 생성 중..."


class ChunkEvent(BaseModel):
    """Event for streaming AI response chunks"""
    chunk: str
    accumulated_length: int


class SectionCompleteEvent(BaseModel):
    """Event when a section of the reading is completed"""
    section: str = Field(..., description="Section name: 'summary', 'cards', 'overall_reading', 'advice'")
    data: Dict[str, Any] = Field(..., description="Section data ready to display")
    progress: int = Field(..., ge=0, le=100, description="Overall progress percentage")


class CompleteEvent(BaseModel):
    """Event when reading generation completes"""
    reading_id: str
    total_time: float
    message: str = "리딩 생성 완료"
    reading_summary: Optional[Dict[str, Any]] = None


class ErrorEvent(BaseModel):
    """Event when an error occurs"""
    error_type: str
    message: str
    details: Optional[str] = None
    stage: Optional[ReadingStage] = None


# Helper functions for creating events
def create_sse_event(event_type: SSEEventType, data: BaseModel) -> SSEEvent:
    """
    Create an SSE event from event type and data model

    Args:
        event_type: Type of SSE event
        data: Pydantic model containing event data

    Returns:
        SSEEvent instance ready to be sent
    """
    return SSEEvent(event=event_type, data=data.model_dump(exclude_none=True))


def create_progress_event(
    stage: ReadingStage,
    progress: int,
    message: str,
    details: Optional[str] = None
) -> SSEEvent:
    """Create a progress event"""
    return create_sse_event(
        SSEEventType.PROGRESS,
        ProgressEvent(stage=stage, progress=progress, message=message, details=details)
    )


def create_card_drawn_event(
    card_id: int,
    card_name: str,
    card_name_ko: str,
    position: str,
    is_reversed: bool,
    progress: int
) -> SSEEvent:
    """Create a card drawn event"""
    return create_sse_event(
        SSEEventType.CARD_DRAWN,
        CardDrawnEvent(
            card_id=card_id,
            card_name=card_name,
            card_name_ko=card_name_ko,
            position=position,
            is_reversed=is_reversed,
            progress=progress
        )
    )


def create_complete_event(
    reading_id: str,
    total_time: float,
    reading_summary: Optional[Dict[str, Any]] = None
) -> SSEEvent:
    """Create a completion event"""
    return create_sse_event(
        SSEEventType.COMPLETE,
        CompleteEvent(
            reading_id=reading_id,
            total_time=total_time,
            reading_summary=reading_summary
        )
    )


def create_section_complete_event(
    section: str,
    data: Dict[str, Any],
    progress: int
) -> SSEEvent:
    """Create a section completion event"""
    return create_sse_event(
        SSEEventType.SECTION_COMPLETE,
        SectionCompleteEvent(
            section=section,
            data=data,
            progress=progress
        )
    )


def create_error_event(
    error_type: str,
    message: str,
    details: Optional[str] = None,
    stage: Optional[ReadingStage] = None
) -> SSEEvent:
    """Create an error event"""
    return create_sse_event(
        SSEEventType.ERROR,
        ErrorEvent(
            error_type=error_type,
            message=message,
            details=details,
            stage=stage
        )
    )
