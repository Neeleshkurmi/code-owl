"""link reviews to review runs

Revision ID: 018dba06323e
Revises: 593ff72d6f1e
Create Date: 2026-09-28 21:53:29.519691

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '018dba06323e'
down_revision: Union[str, Sequence[str], None] = '593ff72d6f1e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema.""" 
    # 1. Add the column as nullable initially
    op.add_column('reviews', sa.Column('review_run_id', sa.Integer(), nullable=True))
    
    # 2. Establish the foreign key constraint
    # (We give it an explicit name 'fk_reviews_review_run_id' to prevent downgrade errors)
    op.create_foreign_key('fk_reviews_review_run_id', 'reviews', 'review_runs', ['review_run_id'], ['id'])
    
    # 3. Populate existing reviews with a fallback value.
    # Note: If you don't have an existing row in review_runs with ID 1, you can dynamically 
    # select the first available ID, or create a dummy review run here first.
    op.execute("UPDATE reviews SET review_run_id = 1 WHERE review_run_id IS NULL")
    
    # 4. Now that no rows have NULL values, safely alter the column to NOT NULL
    op.alter_column('reviews', 'review_run_id', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    # 1. Drop the foreign key using the explicit name we assigned
    op.drop_constraint('fk_reviews_review_run_id', 'reviews', type_='foreignkey')
    
    # 2. Drop the column safely
    op.drop_column('reviews', 'review_run_id')
