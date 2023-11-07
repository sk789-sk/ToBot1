"""empty message

Revision ID: 255abd616dd3
Revises: 
Create Date: 2023-11-07 15:48:42.290652

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '255abd616dd3'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_Users'))
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('Users')
    # ### end Alembic commands ###
