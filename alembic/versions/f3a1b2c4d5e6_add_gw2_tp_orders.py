"""Add gw2_tp_orders

Revision ID: f3a1b2c4d5e6
Revises: a71060d7ecbb
Create Date: 2026-08-30 18:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
import core.database.types


# revision identifiers, used by Alembic.
revision = 'f3a1b2c4d5e6'
down_revision = 'a71060d7ecbb'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('gw2_tp_orders',
    sa.Column('uuid', core.database.types.GUID(), nullable=False),
    sa.Column('player_uuid', core.database.types.GUID(), nullable=False),
    sa.Column('gw2_item_id', sa.Integer(), nullable=False),
    sa.Column('last_price', sa.Integer(), nullable=True),
    sa.Column('order_type', sa.Enum('Buy', 'Sell', name='tpordertype'), nullable=False),
    sa.Column('done', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['player_uuid'], ['players.uuid'], ),
    sa.PrimaryKeyConstraint('uuid')
    )


def downgrade():
    op.drop_table('gw2_tp_orders')
    op.execute('DROP TYPE IF EXISTS tpordertype')
