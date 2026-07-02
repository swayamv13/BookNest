"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-07-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    book_status = ENUM(
        "want_to_read", "reading", "finished", name="book_status", create_type=False
    )
    shelf_role = ENUM("editor", "viewer", name="shelf_role", create_type=False)
    book_status.create(op.get_bind(), checkfirst=True)
    shelf_role.create(op.get_bind(), checkfirst=True)

    # users
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # books
    op.create_table(
        "books",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("owner_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("author", sa.String(300), nullable=False),
        sa.Column("status", book_status, nullable=False, server_default="want_to_read"),
        sa.Column("total_pages", sa.Integer, nullable=True),
        sa.Column("current_page", sa.Integer, nullable=True, server_default="0"),
        sa.Column("rating", sa.Integer, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("finished_date", sa.Date, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.CheckConstraint("rating IS NULL OR (rating BETWEEN 1 AND 5)", name="ck_books_rating_range"),
        sa.CheckConstraint("total_pages IS NULL OR total_pages > 0", name="ck_books_total_pages_positive"),
        sa.CheckConstraint(
            "current_page IS NULL OR (current_page >= 0 AND (total_pages IS NULL OR current_page <= total_pages))",
            name="ck_books_current_page_bounds",
        ),
    )
    op.create_index("ix_books_owner_status", "books", ["owner_id", "status"])
    op.create_index("ix_books_owner_title", "books", ["owner_id", "title"])

    # shelves
    op.create_table(
        "shelves",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("owner_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_shelves_owner", "shelves", ["owner_id"])

    # shelf_books
    op.create_table(
        "shelf_books",
        sa.Column("shelf_id", UUID(as_uuid=True), sa.ForeignKey("shelves.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("book_id", UUID(as_uuid=True), sa.ForeignKey("books.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_shelf_books_book", "shelf_books", ["book_id"])

    # shelf_shares
    op.create_table(
        "shelf_shares",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("shelf_id", UUID(as_uuid=True), sa.ForeignKey("shelves.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", shelf_role, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("shelf_id", "user_id", name="uq_shelf_shares_shelf_user"),
    )
    op.create_index("ix_shelf_shares_user", "shelf_shares", ["user_id"])

    # lending
    op.create_table(
        "lending",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("book_id", UUID(as_uuid=True), sa.ForeignKey("books.id", ondelete="CASCADE"), nullable=False),
        sa.Column("owner_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("borrower_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lent_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("returned_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("owner_id <> borrower_id", name="ck_lending_owner_not_borrower"),
    )
    # THE critical constraint: at most one active loan per book
    op.create_index(
        "one_active_loan_per_book",
        "lending",
        ["book_id"],
        unique=True,
        postgresql_where=sa.text("returned_at IS NULL"),
    )
    op.create_index(
        "ix_lending_borrower_active",
        "lending",
        ["borrower_id"],
        postgresql_where=sa.text("returned_at IS NULL"),
    )

    # activity_log
    op.create_table(
        "activity_log",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(60), nullable=False),
        sa.Column("book_id", UUID(as_uuid=True), sa.ForeignKey("books.id", ondelete="SET NULL"), nullable=True),
        sa.Column("shelf_id", UUID(as_uuid=True), sa.ForeignKey("shelves.id", ondelete="SET NULL"), nullable=True),
        sa.Column("event_metadata", JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_activity_log_user_created", "activity_log", ["user_id", sa.text("created_at DESC")])

    # refresh_tokens
    op.create_table(
        "refresh_tokens",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_refresh_tokens_user", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_hash", "refresh_tokens", ["token_hash"])


def downgrade() -> None:
    op.drop_table("refresh_tokens")
    op.drop_table("activity_log")
    op.drop_table("lending")
    op.drop_table("shelf_shares")
    op.drop_table("shelf_books")
    op.drop_table("shelves")
    op.drop_table("books")
    op.drop_table("users")
    sa.Enum(name="shelf_role").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="book_status").drop(op.get_bind(), checkfirst=True)
