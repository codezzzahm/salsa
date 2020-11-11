"""pil

Revision ID: 143a0af52905
Revises: 330603926669
Create Date: 2020-11-06 20:12:33.682766

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '143a0af52905'
down_revision = '330603926669'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('image')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('image',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('img_data', sa.BLOB(), nullable=True),
    sa.Column('user_id', sa.INTEGER(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###
