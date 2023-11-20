"""empty message

Revision ID: 30158a68c0ac
Revises: 56af5d84b8c3
Create Date: 2023-11-20 14:25:10.392672

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '30158a68c0ac'
down_revision = '56af5d84b8c3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Entrants', schema=None) as batch_op:
        batch_op.alter_column('point_total',
               existing_type=sa.BLOB(),
               type_=sa.Integer(),
               existing_nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Entrants', schema=None) as batch_op:
        batch_op.alter_column('point_total',
               existing_type=sa.Integer(),
               type_=sa.BLOB(),
               existing_nullable=True)

    # ### end Alembic commands ###
