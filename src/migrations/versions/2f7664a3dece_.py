"""empty message

Revision ID: 2f7664a3dece
Revises: 6185268413b3
Create Date: 2023-11-20 17:15:12.614549

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2f7664a3dece'
down_revision = '6185268413b3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Entrants', schema=None) as batch_op:
        batch_op.add_column(sa.Column('SOS', sa.Float(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Entrants', schema=None) as batch_op:
        batch_op.drop_column('SOS')

    # ### end Alembic commands ###
