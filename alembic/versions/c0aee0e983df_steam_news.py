"""Steam News

Revision ID: c0aee0e983df
Revises: b8c50d4e6a0c
Create Date: 2021-04-29 11:35:32.542634

"""
from alembic import op
import sqlalchemy as sa
import core


# revision identifiers, used by Alembic.
revision = 'c0aee0e983df'
down_revision = 'b8c50d4e6a0c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('steamposts',
    sa.Column('uuid', core.database.types.GUID(), nullable=False),
    sa.Column('steam_gid', sa.String(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint('uuid'),
    sa.UniqueConstraint('steam_gid')
    )
    op.create_table('steamposts_subscriptions',
    sa.Column('uuid', core.database.types.GUID(), nullable=False),
    sa.Column('channel_id', sa.String(), nullable=False),
    sa.Column('app_id', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('uuid')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('steamposts_subscriptions')
    op.drop_table('steamposts')
    # ### end Alembic commands ###
