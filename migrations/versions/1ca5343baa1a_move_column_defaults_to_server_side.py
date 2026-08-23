"""Move column defaults to server-side

Revision ID: 1ca5343baa1a
Revises: 37d21fd38855
Create Date: 2026-08-23 11:28:28.612748

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '1ca5343baa1a'
down_revision = '37d21fd38855'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('categories', schema=None) as batch_op:
        batch_op.alter_column('created_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=True,
               server_default=sa.text('now()'))
        batch_op.alter_column('updated_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=True,
               server_default=sa.text('now()'))

    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.alter_column('created_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=True,
               server_default=sa.text('now()'))
        batch_op.alter_column('updated_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=True,
               server_default=sa.text('now()'))
        batch_op.alter_column('status',
               existing_type=sa.String(length=50),
               existing_nullable=False,
               server_default=sa.text("'pending'"))
        batch_op.alter_column('total_amount',
               existing_type=sa.Numeric(precision=12, scale=2),
               existing_nullable=False,
               server_default=sa.text('0'))

    with op.batch_alter_table('order_items', schema=None) as batch_op:
        batch_op.alter_column('quantity',
               existing_type=sa.Integer(),
               existing_nullable=False,
               server_default=sa.text('1'))

    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.alter_column('created_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=True,
               server_default=sa.text('now()'))
        batch_op.alter_column('updated_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=True,
               server_default=sa.text('now()'))
        batch_op.alter_column('stock',
               existing_type=sa.Integer(),
               existing_nullable=False,
               server_default=sa.text('0'))
        batch_op.alter_column('is_active',
               existing_type=sa.Boolean(),
               existing_nullable=True,
               server_default=sa.text('true'))

    with op.batch_alter_table('token_blocklist', schema=None) as batch_op:
        batch_op.alter_column('created_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=True,
               server_default=sa.text('now()'))

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('created_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=True,
               server_default=sa.text('now()'))
        batch_op.alter_column('updated_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=True,
               server_default=sa.text('now()'))
        batch_op.alter_column('role',
               existing_type=sa.String(length=20),
               existing_nullable=False,
               server_default=sa.text("'customer'"))


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('role',
               existing_type=sa.String(length=20),
               existing_nullable=False,
               server_default=None)
        batch_op.alter_column('updated_at',
               existing_type=sa.DateTime(timezone=True),
               type_=postgresql.TIMESTAMP(),
               existing_nullable=True,
               server_default=None)
        batch_op.alter_column('created_at',
               existing_type=sa.DateTime(timezone=True),
               type_=postgresql.TIMESTAMP(),
               existing_nullable=True,
               server_default=None)

    with op.batch_alter_table('token_blocklist', schema=None) as batch_op:
        batch_op.alter_column('created_at',
               existing_type=sa.DateTime(timezone=True),
               type_=postgresql.TIMESTAMP(),
               existing_nullable=True,
               server_default=None)

    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.alter_column('is_active',
               existing_type=sa.Boolean(),
               existing_nullable=True,
               server_default=None)
        batch_op.alter_column('stock',
               existing_type=sa.Integer(),
               existing_nullable=False,
               server_default=None)
        batch_op.alter_column('updated_at',
               existing_type=sa.DateTime(timezone=True),
               type_=postgresql.TIMESTAMP(),
               existing_nullable=True,
               server_default=None)
        batch_op.alter_column('created_at',
               existing_type=sa.DateTime(timezone=True),
               type_=postgresql.TIMESTAMP(),
               existing_nullable=True,
               server_default=None)

    with op.batch_alter_table('order_items', schema=None) as batch_op:
        batch_op.alter_column('quantity',
               existing_type=sa.Integer(),
               existing_nullable=False,
               server_default=None)

    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.alter_column('total_amount',
               existing_type=sa.Numeric(precision=12, scale=2),
               existing_nullable=False,
               server_default=None)
        batch_op.alter_column('status',
               existing_type=sa.String(length=50),
               existing_nullable=False,
               server_default=None)
        batch_op.alter_column('updated_at',
               existing_type=sa.DateTime(timezone=True),
               type_=postgresql.TIMESTAMP(),
               existing_nullable=True,
               server_default=None)
        batch_op.alter_column('created_at',
               existing_type=sa.DateTime(timezone=True),
               type_=postgresql.TIMESTAMP(),
               existing_nullable=True,
               server_default=None)
