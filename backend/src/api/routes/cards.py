"""
Card API Routes
"""
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query

from src.database.factory import get_database_provider
from src.database.provider import Card as CardDTO, DatabaseProvider
from src.schemas.card import CardResponse, CardListResponse
from src.models import ArcanaType
from src.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/cards", tags=["cards"])

# Database provider dependency
def get_db_provider() -> DatabaseProvider:
    return get_database_provider()


def _card_to_response(card: CardDTO) -> CardResponse:
    """Convert provider CardDTO to API response schema"""
    created_at = card.created_at or datetime.utcnow()
    updated_at = card.updated_at or created_at

    description = card.description if card.description is not None else ""
    symbolism = card.symbolism if card.symbolism is not None else ""

    return CardResponse(
        id=card.id,
        name=card.name_en,
        name_ko=card.name_ko,
        arcana_type=card.arcana_type,
        number=card.number,
        suit=card.suit,
        keywords_upright=card.keywords_upright,
        keywords_reversed=card.keywords_reversed,
        meaning_upright=card.meaning_upright,
        meaning_reversed=card.meaning_reversed,
        description=description,
        symbolism=symbolism,
        image_url=card.image_url,
        created_at=created_at,
        updated_at=updated_at,
    )


@router.get("", response_model=CardListResponse)
async def list_cards(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    arcana_type: Optional[str] = Query(None, description="Filter by arcana type (major/minor)"),
    suit: Optional[str] = Query(None, description="Filter by suit (wands/cups/swords/pentacles)"),
    search: Optional[str] = Query(None, description="Search by name"),
    db_provider: DatabaseProvider = Depends(get_db_provider)
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
        effective_skip = skip
        effective_limit = page_size

        # Fetch a larger window when searching to allow in-memory filtering
        if search:
            effective_skip = 0
            effective_limit = max(page_size * 5, 100)

        cards = await db_provider.get_cards(
            skip=effective_skip,
            limit=effective_limit,
            arcana_type=arcana_type,
            suit=suit,
        )

        if search:
            keyword = search.lower()
            filtered_cards = [
                card
                for card in cards
                if keyword in card.name_en.lower() or keyword in card.name_ko.lower()
            ]
            total = len(filtered_cards)
            cards = filtered_cards[skip: skip + page_size]
        else:
            total = await db_provider.get_total_cards_count(
                arcana_type=arcana_type,
                suit=suit,
            )

        logger.info(f"Retrieved {len(cards)} cards (page {page}, total {total})")

        # Convert CardDTO to CardResponse
        card_responses = [_card_to_response(card) for card in cards]

        return CardListResponse(
            total=total,
            page=page,
            page_size=page_size,
            cards=card_responses
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
    db_provider: DatabaseProvider = Depends(get_db_provider)
):
    """
    Get a specific card by ID

    - **card_id**: The ID of the card
    """
    try:
        card = await db_provider.get_card_by_id(card_id)

        if not card:
            logger.warning(f"Card not found: {card_id}")
            raise HTTPException(status_code=404, detail="Card not found")

        logger.info(f"Retrieved card: {card.name_en} (ID: {card_id})")
        return _card_to_response(card)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving card {card_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/name/{card_name}", response_model=CardResponse)
async def get_card_by_name(
    card_name: str,
    db_provider: DatabaseProvider = Depends(get_db_provider)
):
    """
    Get a specific card by name (case-insensitive)

    - **card_name**: The name of the card (e.g., "The Fool", "Ace of Wands")
    """
    try:
        card = await db_provider.get_card_by_name(card_name)

        if not card:
            logger.warning(f"Card not found: {card_name}")
            raise HTTPException(status_code=404, detail="Card not found")

        logger.info(f"Retrieved card by name: {card.name_en}")
        return _card_to_response(card)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving card '{card_name}': {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/major-arcana/all", response_model=CardListResponse)
async def get_major_arcana(
    page: int = Query(1, ge=1),
    page_size: int = Query(22, ge=1, le=100),
    db_provider: DatabaseProvider = Depends(get_db_provider)
):
    """
    Get all Major Arcana cards

    - **page**: Page number
    - **page_size**: Items per page (default 22 for all Major Arcana)
    """
    skip = (page - 1) * page_size

    try:
        cards = await db_provider.get_cards(
            skip=skip,
            limit=page_size,
            arcana_type=ArcanaType.MAJOR.value,
        )
        total = await db_provider.get_total_cards_count(
            arcana_type=ArcanaType.MAJOR.value
        )

        logger.info(f"Retrieved {len(cards)} Major Arcana cards")

        return CardListResponse(
            total=total,
            page=page,
            page_size=page_size,
            cards=[_card_to_response(card) for card in cards]
        )

    except Exception as e:
        logger.error(f"Error retrieving Major Arcana: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/minor-arcana/all", response_model=CardListResponse)
async def get_minor_arcana(
    page: int = Query(1, ge=1),
    page_size: int = Query(56, ge=1, le=100),
    db_provider: DatabaseProvider = Depends(get_db_provider)
):
    """
    Get all Minor Arcana cards

    - **page**: Page number
    - **page_size**: Items per page (default 56 for all Minor Arcana)
    """
    skip = (page - 1) * page_size

    try:
        cards = await db_provider.get_cards(
            skip=skip,
            limit=page_size,
            arcana_type=ArcanaType.MINOR.value,
        )
        total = await db_provider.get_total_cards_count(
            arcana_type=ArcanaType.MINOR.value
        )

        logger.info(f"Retrieved {len(cards)} Minor Arcana cards")

        return CardListResponse(
            total=total,
            page=page,
            page_size=page_size,
            cards=[_card_to_response(card) for card in cards]
        )

    except Exception as e:
        logger.error(f"Error retrieving Minor Arcana: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/suit/{suit_name}", response_model=CardListResponse)
async def get_cards_by_suit(
    suit_name: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(14, ge=1, le=100),
    db_provider: DatabaseProvider = Depends(get_db_provider),
):
    """
    Get all cards of a specific suit

    - **suit_name**: Suit name (wands, cups, swords, or pentacles)
    - **page**: Page number
    - **page_size**: Items per page (default 14 for all cards in a suit)
    """
    skip = (page - 1) * page_size

    try:
        suit_key = suit_name.lower()
        if suit_key not in {"wands", "cups", "swords", "pentacles"}:
            raise ValueError(
                "Invalid suit. Must be one of: wands, cups, swords, pentacles"
            )

        cards = await db_provider.get_cards(
            skip=skip,
            limit=page_size,
            suit=suit_key,
        )
        total = await db_provider.get_total_cards_count(suit=suit_key)

        logger.info(f"Retrieved {len(cards)} {suit_name} cards")

        return CardListResponse(
            total=total,
            page=page,
            page_size=page_size,
            cards=[_card_to_response(card) for card in cards],
        )

    except ValueError as e:
        logger.error(f"Invalid suit filter: {suit_name}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving {suit_name} cards: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/random/draw", response_model=List[CardResponse])
async def draw_random_cards(
    count: int = Query(1, ge=1, le=10, description="Number of cards to draw"),
    arcana_type: Optional[str] = Query(None, description="Filter by arcana type"),
    suit: Optional[str] = Query(None, description="Filter by suit"),
    db_provider: DatabaseProvider = Depends(get_db_provider),
):
    """
    Draw random cards with orientation (upright/reversed)

    - **count**: Number of cards to draw (1-10)
    - **arcana_type**: Optional filter by arcana type (major/minor)
    - **suit**: Optional filter by suit (wands/cups/swords/pentacles)

    Note: Currently returns random cards without filters.
    Full filter support coming soon.
    """
    try:
        # TODO: Apply arcana/suit filters in provider implementation
        cards = await db_provider.get_random_cards(count)

        logger.info(f"Drew {len(cards)} random cards")

        return [_card_to_response(card) for card in cards]

    except ValueError as e:
        logger.error(f"Card draw error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error drawing random cards: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
