"""add password_hash to users

Revision ID: f7d1c01871c1
Revises: 872c9c01b184
Create Date: 2025-10-25 12:03:57.821175

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f7d1c01871c1'
down_revision: Union[str, None] = '872c9c01b184'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add password_hash column to users table
    op.add_column('users', sa.Column('password_hash', sa.String(255), nullable=True))


def downgrade() -> None:
    # Remove password_hash column from users table
    op.drop_column('users', 'password_hash')
