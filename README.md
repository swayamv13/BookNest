# BookNest

BookNest is a full-stack reading-tracker app. Users manage their own books, organize them into custom shelves, share shelves with other users under role-based permissions, log reading progress, lend books to other registered users, and see a live activity feed on the dashboard.

**Demo login:** `demo@booknest.com` / `Password123` (shown on the login page)

---

## How to run (clean clone)

### Prerequisites

- Docker Desktop
- Python 3.11+
- Node.js 18+

### 1. Start PostgreSQL

```bash
docker compose up -d
```

Database runs on **localhost:5433** (mapped from container port 5432).

### 2. Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# Mac/Linux
# source venv/bin/activate

pip install -r requirements.txt
copy .env.example .env        # Windows
# cp .env.example .env        # Mac/Linux

alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --port 8000
```

- API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

- App: http://localhost:5173

### Environment variables

Copy `backend/.env.example` → `backend/.env`:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `JWT_SECRET` | Secret for signing access tokens |
| `CORS_ORIGINS` | Allowed frontend origins |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime (default 15) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime (default 14) |

### Seed data

`python -m app.seed` creates:

| User | Email | Password |
|------|-------|----------|
| Demo | `demo@booknest.com` | `Password123` |
| Alice | `alice@example.com` | `Password123` |
| Bob | `bob@example.com` | `Password123` |

Also seeds sample books, a shelf shared with Bob as **editor**, and an active loan (Alice → Bob).

---

## Data model

```
users ─────────────┬──────────── books (owner_id)
                   │
                   ├──────────── shelves (owner_id)
                   │                 │
                   │                 └── shelf_books (M:N junction)
                   │                          │
                   │                          └── books
                   │
                   ├──────────── shelf_shares (user_id, shelf_id, role: editor|viewer)
                   │
                   ├──────────── lendings (book_id, owner_id, borrower_id, returned_at)
                   │
                   └──────────── activity_logs
```

**Key relationships**

- **Books** belong to one user (`owner_id`). Deleting a book removes it from all shelves but does not delete shelves.
- **Shelves** belong to one owner. Books connect via `shelf_books` (many-to-many).
- **Shelf shares** grant `editor` or `viewer` access to a collaborator. Only the shelf owner can share, change roles, or delete the shelf.
- **Lending** tracks one active loan per book (enforced by a partial unique index where `returned_at IS NULL`).

---

## Stack and why

| Layer | Choice | Why |
|-------|--------|-----|
| Frontend | React + Vite | Fast dev experience, component model fits a multi-page SPA |
| Backend | FastAPI (Python) | Async support, automatic OpenAPI docs, Pydantic validation |
| Database | PostgreSQL | Relational data (users, books, shelves, RBAC, lending) with real constraints |
| Auth | JWT + refresh cookie | Stateless API access; refresh token stored httpOnly for security |
| Real-time | Native WebSockets (FastAPI + browser `WebSocket`) | True push updates — no polling |
| Migrations | Alembic | Versioned schema changes |

---

## Password rules

Defined in `backend/app/schemas/auth.py`:

- Minimum **8 characters**, maximum 128
- Name required (1–120 chars)
- Email required; invalid format rejected by API validation
- Passwords hashed with **bcrypt** before storage — never stored in plaintext

---

## Refresh-token flow

| Token | Storage | Lifetime | Purpose |
|-------|---------|----------|---------|
| **Access token** | In-memory on frontend (`api-client.js`) | 15 minutes | Sent as `Authorization: Bearer` on API calls |
| **Refresh token** | httpOnly cookie (`refresh_token`) | 14 days | Rotated on each `/auth/refresh` call; hash stored in DB |

**On login/signup:** API returns access token in JSON body + sets refresh cookie.

**On 401:** Frontend calls `POST /auth/refresh` with cookie, gets new access token, retries the original request transparently.

**On logout:** `POST /auth/logout` revokes refresh token in DB and clears the cookie.

**Why this split:** Access tokens are short-lived and never touch `localStorage` (XSS risk). Refresh tokens are httpOnly (not readable by JS) and rotated server-side.

---

## RBAC enforcement

Shelf permissions are enforced in **one backend dependency**: `require_shelf_access()` in `backend/app/dependencies/shelf_access.py`.

| Role | Can view shelf | Can add/remove books | Can share / delete shelf |
|------|----------------|----------------------|--------------------------|
| Owner | ✅ | ✅ | ✅ |
| Editor | ✅ | ✅ | ❌ |
| Viewer | ✅ | ❌ | ❌ |

A **viewer** calling `POST /shelves/{id}/books/{book_id}` receives **403 Forbidden** — the check runs before any mutation. Unauthorized users get **404** (not 403) so shelf existence is not leaked.

Book endpoints always scope by `owner_id = current_user.id`. Lending endpoints verify book ownership before lend/return.

---

## WebSocket setup

**Library:** Native FastAPI `WebSocket` + browser `WebSocket` API (no Socket.io, no polling).

**Authentication:** Client connects to `ws://localhost:8000/ws?token=<access_token>`. The server validates the JWT on handshake; invalid/expired tokens close with code `4001`.

**Event scoping** (in `backend/app/websocket/events.py`):

| Event | Recipients |
|-------|------------|
| `book.lent` / `book.returned` | Book owner + borrower only |
| `shelf.book_added` / `shelf.book_removed` | Shelf owner + all collaborators |
| `activity.new` | The user who owns the activity |

No global broadcast — each event targets a computed audience.

**Frontend reconnect:** `websocket-client.js` uses exponential backoff (1s → 30s max). On disconnect, pages still work via manual refresh / API calls.

**Pages using WebSockets:** Dashboard (activity reload), Lending (borrowed/lent-out reload).

---

## Features implemented

- Sign up / login / logout with JWT refresh
- Books CRUD with filter, search, pagination, sorting
- Custom shelves (many-to-many with books)
- Share shelves by email (editor / viewer)
- Reading progress with validation and auto-finish
- Lend / return books between registered users
- Activity log and dashboard stats
- Real-time updates via WebSockets
- Loading states, error messages, disabled buttons during requests

---

## What was hard

1. **Route ordering for lending** — `GET /books/borrowed` was caught by `GET /books/{book_id}`. Fixed by registering static routes before the dynamic route.

2. **bcrypt + passlib compatibility** — bcrypt 5.x broke passlib. Switched to direct `bcrypt` calls in `security.py`.

3. **WebSocket auth in browsers** — Browsers cannot set custom headers on WebSocket handshakes, so the access token is passed as a query parameter instead.

4. **Shelf RBAC in one place** — Centralized all permission checks in `require_shelf_access()` so every shelf route uses the same logic.

---

## Known issues / incomplete

- Seed creates an **editor** share but not a separate **viewer** share (viewer role is implemented in code).
- Shelf detail page does not yet subscribe to WebSocket events (refresh manually or navigate back).
- `docker-compose.yml` runs only Postgres — frontend and backend are started separately.

---

## What I would improve with more time

- Add automated tests for auth, RBAC, and lending edge cases
- Wire WebSocket listeners on `ShelfDetail` for live collaborator updates
- Full docker-compose with backend + frontend + DB in one command
- Email notification when a book is lent

---

## Project structure

```
BookNest/
├── backend/
│   ├── app/              # FastAPI application
│   ├── alembic/          # Database migrations
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   └── src/              # React SPA
├── docker-compose.yml    # PostgreSQL
└── README.md
```

---

## Demo video guide (4–6 minutes)

Record **locally** with two browser windows side by side (Chrome normal + Chrome Incognito, or Chrome + Edge).

### Before recording

1. Run backend + frontend + Docker (see steps above).
2. Run `python -m app.seed` so Alice and Bob exist.
3. Close extra tabs. Zoom both windows to ~80% so they fit on screen.

### Suggested script (~5 min)

| Time | Window A (Alice) | Window B (Bob) | What to say |
|------|------------------|----------------|-------------|
| 0:00 | Open `localhost:5173`, login `alice@example.com` | — | Intro: "BookNest — reading tracker with shelves, sharing, lending, and live updates." |
| 0:30 | Show **Books** page — list, filter, search | — | "Users manage their own books with status, search, and pagination." |
| 1:00 | **Shelves** → open "Favorites" | Login `bob@example.com` | "Shelves are many-to-many — books stay when a shelf is deleted." |
| 1:30 | Share shelf with Bob as **editor** | Bob opens **Shared with me** → Favorites | "Owner shares by email with editor or viewer roles." |
| 2:00 | — | Bob adds a book to shared shelf | "Editor can add books — enforced on the backend." |
| 2:30 | Shelf updates live (or refresh) | — | "WebSocket pushes shelf changes to collaborators." |
| 3:00 | **Books** → set progress to total pages on a "Reading" book | — | "Progress auto-finishes when current page equals total pages." |
| 3:30 | **Lend** a book to `bob@example.com` | Bob opens **Lending** → Borrowed | "Lending is one active loan per book; borrower sees it read-only." |
| 4:15 | Mark book **Returned** | Borrowed list updates | "Return clears the loan for both users." |
| 4:45 | **Dashboard** — stats + activity feed | — | "Dashboard shows counts, finished-this-year, lent-out, and recent activity." |
| 5:15 | — | — | Wrap up: mention JWT refresh, bcrypt, RBAC on backend, PostgreSQL data model. |

### Recording tips

- Use **OBS Studio** or **Windows Game Bar** (`Win + G`) — free and simple.
- Record at **1920×1080** or **1280×720**.
- Speak while clicking — explain *why*, not just *what*.
- If live WebSocket is slow to show, say "it updates via WebSocket" and refresh once.
- Upload to **YouTube (Unlisted)** or **Google Drive** and paste the link in your submission.

### Minimum scenes (must show)

1. Two users logged in
2. Books + shelves
3. Shared shelf (editor vs viewer permission)
4. Reading progress → auto-finish
5. Lend → borrower view → return
6. Dashboard + activity feed

---

## License

MIT
