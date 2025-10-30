"""add llm_usage_logs table

Revision ID: d298ff1ee6ff
Revises: f7d1c01871c1
Create Date: 2025-10-30 09:30:46.601783

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd298ff1ee6ff'
down_revision: Union[str, None] = 'f7d1c01871c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # LLM 사용 기록 테이블 생성
    op.create_table(
        'llm_usage_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('reading_id', sa.UUID(), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('prompt_tokens', sa.Integer(), nullable=False),
        sa.Column('completion_tokens', sa.Integer(), nullable=False),
        sa.Column('total_tokens', sa.Integer(), nullable=False),
        sa.Column('estimated_cost', sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column('latency_seconds', sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column('purpose', sa.String(length=50), nullable=False, server_default='main_reading'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 인덱스 생성
    op.create_index('ix_llm_usage_logs_reading_id', 'llm_usage_logs', ['reading_id'])
    op.create_index('ix_llm_usage_logs_created_at', 'llm_usage_logs', ['created_at'])
    op.create_index('ix_llm_usage_logs_provider', 'llm_usage_logs', ['provider'])

    # 외래 키 제약조건 추가
    op.create_foreign_key(
        'fk_llm_usage_logs_reading_id',
        'llm_usage_logs', 'readings',
        ['reading_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    # 외래 키 제약조건 제거
    op.drop_constraint('fk_llm_usage_logs_reading_id', 'llm_usage_logs', type_='foreignkey')

    # 인덱스 제거
    op.drop_index('ix_llm_usage_logs_provider', 'llm_usage_logs')
    op.drop_index('ix_llm_usage_logs_created_at', 'llm_usage_logs')
    op.drop_index('ix_llm_usage_logs_reading_id', 'llm_usage_logs')

    # 테이블 제거
    op.drop_table('llm_usage_logs')
