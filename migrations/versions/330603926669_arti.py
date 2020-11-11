"""arti

Revision ID: 330603926669
Revises: dc64f9b992b4
Create Date: 2020-11-06 15:48:22.883050

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '330603926669'
down_revision = 'dc64f9b992b4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('article1',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('body', sa.String(length=140), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_article1_timestamp'), 'article1', ['timestamp'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_article1_timestamp'), table_name='article1')
    op.drop_table('article1')
    # ### end Alembic commands ###
