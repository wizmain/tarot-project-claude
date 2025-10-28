"""
Pydantic schemas for Tarot Card API
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class ArcanaTypeEnum(str):
    """Arcana type values"""
    MAJOR = "major"
    MINOR = "minor"


class SuitEnum(str):
    """Suit type values"""
    WANDS = "wands"
    CUPS = "cups"
    SWORDS = "swords"
    PENTACLES = "pentacles"


class CardBase(BaseModel):
    """Base card schema with common attributes"""
    name: str = Field(..., min_length=1, max_length=100, description="Card name in English")
    name_ko: str = Field(..., min_length=1, max_length=100, description="Card name in Korean")
    number: Optional[int] = Field(None, ge=0, le=21, description="Card number (0-21 for Major, 1-14 for Minor)")
    arcana_type: str = Field(..., description="Arcana type (major or minor)")
    suit: Optional[str] = Field(None, description="Suit for Minor Arcana (wands, cups, swords, pentacles)")
    keywords_upright: List[str] = Field(..., min_length=1, description="Upright keywords")
    keywords_reversed: List[str] = Field(..., min_length=1, description="Reversed keywords")
    meaning_upright: str = Field(..., min_length=1, description="Detailed upright meaning")
    meaning_reversed: str = Field(..., min_length=1, description="Detailed reversed meaning")
    description: Optional[str] = Field(None, description="General card description")
    symbolism: Optional[str] = Field(None, description="Symbolic interpretation")
    image_url: Optional[str] = Field(None, max_length=255, description="Image URL or path")


class CardCreate(CardBase):
    """Schema for creating a new card"""
    pass


class CardUpdate(BaseModel):
    """Schema for updating an existing card"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    name_ko: Optional[str] = Field(None, min_length=1, max_length=100)
    number: Optional[int] = Field(None, ge=0, le=21)
    arcana_type: Optional[str] = None
    suit: Optional[str] = None
    keywords_upright: Optional[List[str]] = Field(None, min_length=1)
    keywords_reversed: Optional[List[str]] = Field(None, min_length=1)
    meaning_upright: Optional[str] = Field(None, min_length=1)
    meaning_reversed: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    symbolism: Optional[str] = None
    image_url: Optional[str] = Field(None, max_length=255)


class CardResponse(CardBase):
    """Schema for card response"""
    id: int = Field(..., description="Card ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class CardListResponse(BaseModel):
    """Schema for paginated card list response"""
    total: int = Field(..., description="Total number of cards")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Items per page")
    cards: List[CardResponse] = Field(..., description="List of cards")


class CardDrawRequest(BaseModel):
    """Schema for card draw request"""
    count: int = Field(1, ge=1, le=10, description="Number of cards to draw")
    allow_reversed: bool = Field(True, description="Allow reversed cards")
    arcana_filter: Optional[str] = Field(None, description="Filter by arcana type (major/minor)")
    suit_filter: Optional[str] = Field(None, description="Filter by suit")


class DrawnCard(BaseModel):
    """Schema for a drawn card with orientation"""
    card: CardResponse = Field(..., description="The drawn card")
    is_reversed: bool = Field(..., description="Whether the card is reversed")
    position: int = Field(..., ge=0, description="Position in the spread")


class CardDrawResponse(BaseModel):
    """Schema for card draw response"""
    cards: List[DrawnCard] = Field(..., description="List of drawn cards")
    spread_type: str = Field(..., description="Type of spread (single, three-card, etc.)")
    drawn_at: datetime = Field(default_factory=datetime.utcnow, description="Draw timestamp")
