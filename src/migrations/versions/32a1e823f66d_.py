"""empty message

Revision ID: 32a1e823f66d
Revises: e8255e9fbf04
Create Date: 2023-12-08 01:04:42.793131

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '32a1e823f66d'
down_revision = 'e8255e9fbf04'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('discord_id', sa.Integer(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Users', schema=None) as batch_op:
        batch_op.drop_column('discord_id')

    # ### end Alembic commands ###
