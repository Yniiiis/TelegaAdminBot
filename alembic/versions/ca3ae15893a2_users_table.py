"""users table

Revision ID: ca3ae15893a2
Revises:
Create Date: 2026-03-29 11:34:41.036475

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ca3ae15893a2"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    tables = insp.get_table_names()

    if "users" not in tables:
        op.create_table(
            "users",
            sa.Column("user_id", sa.BigInteger(), nullable=False),
            sa.Column("get_access_clicked", sa.Boolean(), nullable=False),
            sa.Column("subscription_passed", sa.Boolean(), nullable=False),
            sa.PrimaryKeyConstraint("user_id"),
        )
        return

    cols = {c["name"] for c in insp.get_columns("users")}
    if "subscription_passed" not in cols:
        with op.batch_alter_table("users") as batch_op:
            batch_op.add_column(
                sa.Column(
                    "subscription_passed",
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.text("0"),
                )
            )


def downgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    if "users" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("users")}
    if "subscription_passed" in cols:
        with op.batch_alter_table("users") as batch_op:
            batch_op.drop_column("subscription_passed")
