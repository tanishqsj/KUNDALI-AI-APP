"""add_rag_table

Revision ID: ea45fe123d7f
Revises: bd39681e674b
Create Date: 2026-01-11 16:28:35.877280

"""
from alembic import op
import sqlalchemy as sa
import pgvector  # <--- CRITICAL FIX: Added this import

# revision identifiers, used by Alembic.
revision = 'ea45fe123d7f'
down_revision = 'bd39681e674b'
branch_labels = None
depends_on = None


def upgrade():

    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    # 1. Create the new knowledge table
    op.create_table('knowledge_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata_info', sa.String(), nullable=True),
        # Fix: Ensure Vector is used correctly
        sa.Column('embedding', pgvector.sqlalchemy.Vector(1536), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_knowledge_items_id'), 'knowledge_items', ['id'], unique=False)




def downgrade():
    op.drop_index(op.f('ix_knowledge_items_id'), table_name='knowledge_items')
    op.drop_table('knowledge_items')