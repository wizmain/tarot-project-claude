"""
Card API Routes
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.api.repositories import CardRepository
from src.schemas.card import CardResponse, CardListResponse
from src.models import ArcanaType, Suit
from src.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/cards", tags=["cards"])


@router.get("/", response_model=CardListResponse)
async def list_cards(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    arcana_type: Optional[str] = Query(None, description="Filter by arcana type (major/minor)"),
    suit: Optional[str] = Query(None, description="Filter by suit (wands/cups/swords/pentacles)"),
    search: Optional[str] = Query(None, description="Search by name"),
    db: Session = Depends(get_db)
):
    """
    Get list of cards with pagination and filters

    - **page**: Page number (starts at 1)
    - **page_size**: Number of items per page (max 100)
    - **arcana_type**: Filter by arcana type (major or minor)
    - **suit**: Filter by suit (wands, cups, swords, or pentacles)
    - **search**: Search by card name (English or Korean)
    """
    skip = (page - 1) * page_size

    try:
        # Apply filters
        if search:
            cards = CardRepository.search_by_name(db, search, skip, page_size)
            total = len(CardRepository.search_by_name(db, search))
        elif arcana_type and suit:
            # Both filters
            suit_enum = Suit[suit.upper()]
            cards = CardRepository.get_by_suit(db, suit_enum, skip, page_size)
            total = CardRepository.count_by_suit(db, suit_enum)
        elif arcana_type:
            arcana_enum = ArcanaType.MAJOR if arcana_type.lower() == "major" else ArcanaType.MINOR
            cards = CardRepository.get_by_arcana_type(db, arcana_enum, skip, page_size)
            total = CardRepository.count_by_arcana_type(db, arcana_enum)
        elif suit:
            suit_enum = Suit[suit.upper()]
            cards = CardRepository.get_by_suit(db, suit_enum, skip, page_size)
            total = CardRepository.count_by_suit(db, suit_enum)
        else:
            cards = CardRepository.get_all(db, skip, page_size)
            total = CardRepository.count_all(db)

        logger.info(f"Retrieved {len(cards)} cards (page {page}, total {total})")

        return CardListResponse(
            total=total,
            page=page,
            page_size=page_size,
            cards=[CardResponse.model_validate(card) for card in cards]
        )

    except KeyError as e:
        logger.error(f"Invalid filter value: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid filter value: {e}")
    except Exception as e:
        logger.error(f"Error retrieving cards: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{card_id}", response_model=CardResponse)
async def get_card(
    card_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific card by ID

    - **card_id**: The ID of the card
    """
    try:
        card = CardRepository.get_by_id(db, card_id)

        if not card:
            logger.warning(f"Card not found: {card_id}")
            raise HTTPException(status_code=404, detail="Card not found")

        logger.info(f"Retrieved card: {card.name} (ID: {card_id})")
        return CardResponse.model_validate(card)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving card {card_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/name/{card_name}", response_model=CardResponse)
async def get_card_by_name(
    card_name: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific card by name (case-insensitive)

    - **card_name**: The name of the card (e.g., "The Fool", "Ace of Wands")
    """
    try:
        card = CardRepository.get_by_name(db, card_name)

        if not card:
            logger.warning(f"Card not found: {card_name}")
            raise HTTPException(status_code=404, detail="Card not found")

        logger.info(f"Retrieved card by name: {card.name}")
        return CardResponse.model_validate(card)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving card '{card_name}': {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/major-arcana/all", response_model=CardListResponse)
async def get_major_arcana(
    page: int = Query(1, ge=1),
    page_size: int = Query(22, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get all Major Arcana cards

    - **page**: Page number
    - **page_size**: Items per page (default 22 for all Major Arcana)
    """
    skip = (page - 1) * page_size

    try:
        cards = CardRepository.get_major_arcana(db, skip, page_size)
        total = CardRepository.count_by_arcana_type(db, ArcanaType.MAJOR)

        logger.info(f"Retrieved {len(cards)} Major Arcana cards")

        return CardListResponse(
            total=total,
            page=page,
            page_size=page_size,
            cards=[CardResponse.model_validate(card) for card in cards]
        )

    except Exception as e:
        logger.error(f"Error retrieving Major Arcana: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/minor-arcana/all", response_model=CardListResponse)
async def get_minor_arcana(
    page: int = Query(1, ge=1),
    page_size: int = Query(56, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get all Minor Arcana cards

    - **page**: Page number
    - **page_size**: Items per page (default 56 for all Minor Arcana)
    """
    skip = (page - 1) * page_size

    try:
        cards = CardRepository.get_minor_arcana(db, skip, page_size)
        total = CardRepository.count_by_arcana_type(db, ArcanaType.MINOR)

        logger.info(f"Retrieved {len(cards)} Minor Arcana cards")

        return CardListResponse(
            total=total,
            page=page,
            page_size=page_size,
            cards=[CardResponse.model_validate(card) for card in cards]
        )

    except Exception as e:
        logger.error(f"Error retrieving Minor Arcana: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/suit/{suit_name}", response_model=CardListResponse)
async def get_cards_by_suit(
    suit_name: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(14, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get all cards of a specific suit

    - **suit_name**: Suit name (wands, cups, swords, or pentacles)
    - **page**: Page number
    - **page_size**: Items per page (default 14 for all cards in a suit)
    """
    skip = (page - 1) * page_size

    try:
        suit_enum = Suit[suit_name.upper()]
        cards = CardRepository.get_by_suit(db, suit_enum, skip, page_size)
        total = CardRepository.count_by_suit(db, suit_enum)

        logger.info(f"Retrieved {len(cards)} {suit_name} cards")

        return CardListResponse(
            total=total,
            page=page,
            page_size=page_size,
            cards=[CardResponse.model_validate(card) for card in cards]
        )

    except KeyError:
        logger.error(f"Invalid suit name: {suit_name}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid suit. Must be one of: wands, cups, swords, pentacles"
        )
    except Exception as e:
        logger.error(f"Error retrieving {suit_name} cards: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/random/draw", response_model=List[CardResponse])
async def draw_random_cards(
    count: int = Query(1, ge=1, le=10, description="Number of cards to draw"),
    arcana_type: Optional[str] = Query(None, description="Filter by arcana type"),
    suit: Optional[str] = Query(None, description="Filter by suit"),
    db: Session = Depends(get_db)
):
    """
    Draw random cards with orientation (upright/reversed)

    Uses the Card Shuffle Service (TASK-014) to ensure:
    - No duplicate cards in a single draw
    - 50/50 probability for upright/reversed orientation

    - **count**: Number of cards to draw (1-10)
    - **arcana_type**: Optional filter by arcana type (major/minor)
    - **suit**: Optional filter by suit (wands/cups/swords/pentacles)

    Note: Cards are returned without orientation info in the response.
    For full reading functionality with orientation, use the Reading API.
    """
    from src.core.card_shuffle import CardShuffleService

    try:
        arcana_enum = None
        if arcana_type:
            arcana_enum = ArcanaType.MAJOR if arcana_type.lower() == "major" else ArcanaType.MINOR

        suit_enum = None
        if suit:
            suit_enum = Suit[suit.upper()]

        # Use CardShuffleService instead of direct repository call
        # This ensures proper shuffling logic with orientation
        drawn_cards = CardShuffleService.draw_cards(db, count, arcana_enum, suit_enum)

        logger.info(f"Drew {len(drawn_cards)} random cards with orientation")

        # Return just the cards (orientation is handled by frontend for now)
        return [CardResponse.model_validate(dc.card) for dc in drawn_cards]

    except ValueError as e:
        logger.error(f"Card draw error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except KeyError as e:
        logger.error(f"Invalid filter value: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid filter value: {e}")
    except Exception as e:
        logger.error(f"Error drawing random cards: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
