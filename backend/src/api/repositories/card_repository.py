"""
Card Repository - Database access layer for Card model
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from src.models import Card, ArcanaType, Suit


class CardRepository:
    """Repository for Card database operations"""

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[Card]:
        """
        Get all cards with pagination

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Card objects
        """
        return db.query(Card).offset(skip).limit(limit).all()

    @staticmethod
    def get_by_id(db: Session, card_id: int) -> Optional[Card]:
        """
        Get card by ID

        Args:
            db: Database session
            card_id: Card ID

        Returns:
            Card object or None
        """
        return db.query(Card).filter(Card.id == card_id).first()

    @staticmethod
    def get_by_name(db: Session, name: str) -> Optional[Card]:
        """
        Get card by name (case-insensitive)

        Args:
            db: Database session
            name: Card name

        Returns:
            Card object or None
        """
        return db.query(Card).filter(Card.name.ilike(name)).first()

    @staticmethod
    def search_by_name(
        db: Session,
        search_term: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Card]:
        """
        Search cards by name (English or Korean)

        Args:
            db: Database session
            search_term: Search term
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Card objects
        """
        search_pattern = f"%{search_term}%"
        return db.query(Card).filter(
            or_(
                Card.name.ilike(search_pattern),
                Card.name_ko.like(search_pattern)
            )
        ).offset(skip).limit(limit).all()

    @staticmethod
    def get_by_arcana_type(
        db: Session,
        arcana_type: ArcanaType,
        skip: int = 0,
        limit: int = 100
    ) -> List[Card]:
        """
        Get cards by arcana type

        Args:
            db: Database session
            arcana_type: Arcana type (MAJOR or MINOR)
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Card objects
        """
        return db.query(Card).filter(
            Card.arcana_type == arcana_type
        ).offset(skip).limit(limit).all()

    @staticmethod
    def get_by_suit(
        db: Session,
        suit: Suit,
        skip: int = 0,
        limit: int = 100
    ) -> List[Card]:
        """
        Get cards by suit

        Args:
            db: Database session
            suit: Suit (WANDS, CUPS, SWORDS, or PENTACLES)
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Card objects
        """
        return db.query(Card).filter(
            Card.suit == suit
        ).offset(skip).limit(limit).all()

    @staticmethod
    def get_major_arcana(
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[Card]:
        """
        Get all Major Arcana cards

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Card objects
        """
        return CardRepository.get_by_arcana_type(db, ArcanaType.MAJOR, skip, limit)

    @staticmethod
    def get_minor_arcana(
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[Card]:
        """
        Get all Minor Arcana cards

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Card objects
        """
        return CardRepository.get_by_arcana_type(db, ArcanaType.MINOR, skip, limit)

    @staticmethod
    def count_all(db: Session) -> int:
        """
        Count all cards

        Args:
            db: Database session

        Returns:
            Total number of cards
        """
        return db.query(Card).count()

    @staticmethod
    def count_by_arcana_type(db: Session, arcana_type: ArcanaType) -> int:
        """
        Count cards by arcana type

        Args:
            db: Database session
            arcana_type: Arcana type

        Returns:
            Number of cards
        """
        return db.query(Card).filter(Card.arcana_type == arcana_type).count()

    @staticmethod
    def count_by_suit(db: Session, suit: Suit) -> int:
        """
        Count cards by suit

        Args:
            db: Database session
            suit: Suit

        Returns:
            Number of cards
        """
        return db.query(Card).filter(Card.suit == suit).count()

    @staticmethod
    def get_random_cards(
        db: Session,
        count: int = 1,
        arcana_type: Optional[ArcanaType] = None,
        suit: Optional[Suit] = None
    ) -> List[Card]:
        """
        Get random cards with optional filters

        Args:
            db: Database session
            count: Number of random cards to retrieve
            arcana_type: Optional arcana type filter
            suit: Optional suit filter

        Returns:
            List of random Card objects
        """
        from sqlalchemy import func

        query = db.query(Card)

        if arcana_type:
            query = query.filter(Card.arcana_type == arcana_type)

        if suit:
            query = query.filter(Card.suit == suit)

        return query.order_by(func.random()).limit(count).all()
