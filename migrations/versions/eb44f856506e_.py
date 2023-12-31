"""empty message

Revision ID: eb44f856506e
Revises: 5368020c1a4f
Create Date: 2023-06-29 15:21:33.098360

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'eb44f856506e'
down_revision = '5368020c1a4f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tariff', sa.Column('channel_id', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('tariff', 'channel_id')
    # ### end Alembic commands ###
