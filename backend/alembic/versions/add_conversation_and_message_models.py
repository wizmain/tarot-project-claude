"""add conversation and message models

Revision ID: add_conversation_message
Revises: f7d1c01871c1
Create Date: 2025-01-27 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'add_conversation_message'
down_revision: Union[str, None] = 'f7d1c01871c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create conversations table
    op.create_table('conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='대화 고유 ID (UUID)'),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, comment='사용자 ID'),
        sa.Column('title', sa.String(length=255), nullable=False, comment='대화 제목'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='대화 생성 시간'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='마지막 업데이트 시간'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_conversation_user_created', 'conversations', ['user_id', 'created_at'], unique=False)
    op.create_index(op.f('ix_conversations_id'), 'conversations', ['id'], unique=False)
    op.create_index(op.f('ix_conversations_user_id'), 'conversations', ['user_id'], unique=False)
    op.create_index(op.f('ix_conversations_created_at'), 'conversations', ['created_at'], unique=False)
    op.create_foreign_key(None, 'conversations', 'users', ['user_id'], ['id'], ondelete='CASCADE')

    # Create messages table
    op.create_table('messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='메시지 고유 ID (UUID)'),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False, comment='대화 ID'),
        sa.Column('role', sa.Enum('user', 'assistant', 'system', name='messagerole'), nullable=False, comment='메시지 역할 (user, assistant, system)'),
        sa.Column('content', sa.Text(), nullable=False, comment='메시지 내용'),
        sa.Column('message_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='추가 메타데이터 (JSON)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='메시지 생성 시간'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_message_conversation_created', 'messages', ['conversation_id', 'created_at'], unique=False)
    op.create_index(op.f('ix_messages_id'), 'messages', ['id'], unique=False)
    op.create_index(op.f('ix_messages_conversation_id'), 'messages', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_messages_created_at'), 'messages', ['created_at'], unique=False)
    op.create_foreign_key(None, 'messages', 'conversations', ['conversation_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    # Drop messages table
    op.drop_constraint(None, 'messages', type_='foreignkey')
    op.drop_index(op.f('ix_messages_created_at'), table_name='messages')
    op.drop_index(op.f('ix_messages_conversation_id'), table_name='messages')
    op.drop_index(op.f('ix_messages_id'), table_name='messages')
    op.drop_index('idx_message_conversation_created', table_name='messages')
    op.drop_table('messages')
    op.execute('DROP TYPE messagerole')

    # Drop conversations table
    op.drop_constraint(None, 'conversations', type_='foreignkey')
    op.drop_index(op.f('ix_conversations_created_at'), table_name='conversations')
    op.drop_index(op.f('ix_conversations_user_id'), table_name='conversations')
    op.drop_index(op.f('ix_conversations_id'), table_name='conversations')
    op.drop_index('idx_conversation_user_created', table_name='conversations')
    op.drop_table('conversations')

