"""Bootstrap schema and add auth/payment columns.

Revision ID: 0001_bootstrap
Revises:
Create Date: 2026-11-10
"""
from alembic import op
import sqlalchemy as sa

from app.database import Base
from app.models import project_models, user_models  # noqa: F401

revision = "0001_bootstrap"
down_revision = None
branch_labels = None
depends_on = None


def _add_column_if_missing(inspector, table_name: str, column_name: str, ddl: str) -> None:
    if table_name not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns(table_name)}
    if column_name not in existing:
        op.execute(sa.text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {ddl}"))


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind, checkfirst=True)
    inspector = sa.inspect(bind)

    for column_name, ddl in {
        "gateway_ref": "VARCHAR",
    }.items():
        _add_column_if_missing(inspector, "transactions", column_name, ddl)

    for column_name, ddl in {
        "is_verified": "BOOLEAN DEFAULT FALSE",
        "reset_token_hash": "VARCHAR",
        "reset_token_expires": "TIMESTAMP",
        "verification_token_hash": "VARCHAR",
        "verification_token_expires": "TIMESTAMP",
    }.items():
        _add_column_if_missing(inspector, "users", column_name, ddl)


def downgrade() -> None:
    pass
