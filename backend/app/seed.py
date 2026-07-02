"""Seed script -- creates 2 users, books, a shared shelf, and an active loan.
Run with: python -m app.seed"""

import asyncio
from datetime import date

from sqlalchemy import select

from app.database import async_session_maker
from app.core.security import hash_password
from app.models.user import User
from app.models.book import Book, BookStatus
from app.models.shelf import Shelf
from app.models.shelf_book import ShelfBook
from app.models.shelf_share import ShelfShare, ShelfRole
from app.models.lending import Lending
from app.models.activity_log import ActivityLog


async def seed():
    async with async_session_maker() as db:
        existing = await db.execute(
            select(User).where(User.email == "demo@booknest.com")
        )
        if existing.scalar_one_or_none() is not None:
            print("Seed skipped — demo user already exists.")
            return

        # ---- Users ----
        demo = User(
            name="Demo User",
            email="demo@booknest.com",
            password_hash=hash_password("Password123"),
        )
        alice = User(
            name="Alice Johnson",
            email="alice@example.com",
            password_hash=hash_password("Password123"),
        )
        bob = User(
            name="Bob Smith",
            email="bob@example.com",
            password_hash=hash_password("Password123"),
        )
        db.add_all([demo, alice, bob])
        await db.flush()

        # ---- Alice's books ----
        books_alice = [
            Book(
                owner_id=alice.id,
                title="The Pragmatic Programmer",
                author="David Thomas & Andrew Hunt",
                status=BookStatus.FINISHED,
                total_pages=352,
                current_page=352,
                rating=5,
                notes="Essential reading for every developer.",
                finished_date=date(2026, 3, 15),
            ),
            Book(
                owner_id=alice.id,
                title="Designing Data-Intensive Applications",
                author="Martin Kleppmann",
                status=BookStatus.READING,
                total_pages=616,
                current_page=340,
                rating=None,
                notes="Deep dive into distributed systems.",
            ),
            Book(
                owner_id=alice.id,
                title="Clean Code",
                author="Robert C. Martin",
                status=BookStatus.FINISHED,
                total_pages=464,
                current_page=464,
                rating=4,
                finished_date=date(2026, 1, 20),
            ),
            Book(
                owner_id=alice.id,
                title="The Art of PostgreSQL",
                author="Dimitri Fontaine",
                status=BookStatus.WANT_TO_READ,
                total_pages=438,
                current_page=0,
            ),
            Book(
                owner_id=alice.id,
                title="Refactoring",
                author="Martin Fowler",
                status=BookStatus.READING,
                total_pages=448,
                current_page=120,
            ),
        ]
        db.add_all(books_alice)
        await db.flush()

        # ---- Bob's books ----
        books_bob = [
            Book(
                owner_id=bob.id,
                title="Python Crash Course",
                author="Eric Matthes",
                status=BookStatus.FINISHED,
                total_pages=544,
                current_page=544,
                rating=4,
                finished_date=date(2026, 5, 10),
            ),
            Book(
                owner_id=bob.id,
                title="Fluent Python",
                author="Luciano Ramalho",
                status=BookStatus.READING,
                total_pages=792,
                current_page=250,
            ),
            Book(
                owner_id=bob.id,
                title="Effective Python",
                author="Brett Slatkin",
                status=BookStatus.WANT_TO_READ,
                total_pages=272,
                current_page=0,
            ),
        ]
        db.add_all(books_bob)
        await db.flush()

        # ---- Alice creates "Favorites" shelf ----
        favorites = Shelf(owner_id=alice.id, name="Favorites")
        db.add(favorites)
        await db.flush()

        # Add some books to the shelf
        db.add_all([
            ShelfBook(shelf_id=favorites.id, book_id=books_alice[0].id),
            ShelfBook(shelf_id=favorites.id, book_id=books_alice[2].id),
        ])

        # ---- Share shelf with Bob as editor ----
        share = ShelfShare(
            shelf_id=favorites.id, user_id=bob.id, role=ShelfRole.EDITOR
        )
        db.add(share)

        # ---- Alice lends "Clean Code" to Bob ----
        loan = Lending(
            book_id=books_alice[2].id,
            owner_id=alice.id,
            borrower_id=bob.id,
        )
        db.add(loan)

        # ---- Activity entries ----
        db.add_all([
            ActivityLog(
                user_id=alice.id,
                event_type="book.created",
                book_id=books_alice[0].id,
                event_metadata={"title": books_alice[0].title},
            ),
            ActivityLog(
                user_id=alice.id,
                event_type="shelf.created",
                shelf_id=favorites.id,
                event_metadata={"name": "Favorites"},
            ),
            ActivityLog(
                user_id=alice.id,
                event_type="shelf.shared",
                shelf_id=favorites.id,
                event_metadata={"shared_with": "bob@example.com", "role": "editor"},
            ),
            ActivityLog(
                user_id=alice.id,
                event_type="book.lent",
                book_id=books_alice[2].id,
                event_metadata={"borrower_email": "bob@example.com"},
            ),
        ])

        await db.commit()

    print("Seed complete!")
    print("   Demo:  demo@booknest.com / Password123")
    print("   Alice: alice@example.com / Password123")
    print("   Bob:   bob@example.com / Password123")
    print("   Shelf 'Favorites' shared with Bob (editor)")
    print("   'Clean Code' lent from Alice to Bob")


if __name__ == "__main__":
    asyncio.run(seed())
