"""Add Recipe model

Revision ID: 659f674ee3cc
Revises: cee8170a04cb
Create Date: 2024-12-20 17:49:19.700052

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '659f674ee3cc'
down_revision = 'cee8170a04cb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('recipes',
    sa.Column('recipe_id', sa.UUID(), nullable=False),
    sa.Column('author_id', sa.UUID(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('content', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['author_id'], ['user.user_id'], ),
    sa.PrimaryKeyConstraint('recipe_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('recipes')
    # ### end Alembic commands ###
