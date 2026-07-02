import { useState, useEffect, useCallback } from "react";
import Navbar from "@/components/layout/Navbar";
import AuthGuard from "@/components/layout/AuthGuard";
import {
  getBooks, createBook, updateBook, deleteBook, updateProgress, lendBook,
} from "@/lib/api-client";

function StatusBadge({ status }) {
  const cls = status === "reading" ? "badge-reading"
    : status === "finished" ? "badge-finished" : "badge-want-to-read";
  const label = status.replace(/_/g, " ");
  return <span className={`badge ${cls}`}>{label}</span>;
}

function StarDisplay({ rating }) {
  if (!rating) return <span className="text-muted text-sm">No rating</span>;
  return (
    <div className="stars stars-readonly">
      {[1, 2, 3, 4, 5].map((i) => (
        <span key={i} className={`star ${i <= rating ? "star-filled" : "star-empty"}`}>★</span>
      ))}
    </div>
  );
}

function ProgressDisplay({ current, total }) {
  if (!total) return null;
  const pct = Math.round(((current || 0) / total) * 100);
  return (
    <div style={{ flex: 1, minWidth: 120 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
        <span className="text-xs text-muted">{current || 0} / {total} pages</span>
        <span className="text-xs text-muted">{pct}%</span>
      </div>
      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export default function Books() {
  const [books, setBooks] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState({ page: 1, page_size: 12, sort_by: "created_at", sort_dir: "desc" });
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingBook, setEditingBook] = useState(null);
  const [showLendModal, setShowLendModal] = useState(null);
  const [showProgressModal, setShowProgressModal] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [searchTimeout, setSearchTimeout] = useState(null);

  const loadBooks = useCallback(async (f) => {
    setLoading(true);
    try {
      const data = await getBooks(f);
      setBooks(data.items);
      setTotal(data.total);
    } catch {} finally { setLoading(false); }
  }, []);

  useEffect(() => { loadBooks(filters); }, [filters, loadBooks]);

  function handleSearch(value) {
    setSearchTerm(value);
    if (searchTimeout) clearTimeout(searchTimeout);
    setSearchTimeout(setTimeout(() => {
      setFilters(f => ({ ...f, search: value || undefined, page: 1 }));
    }, 300));
  }

  const totalPages = Math.ceil(total / (filters.page_size || 12));

  return (
    <AuthGuard>
      <Navbar />
      <main className="page fade-in">
        <div className="page-header">
          <h1 className="page-title">📚 My Books</h1>
          <button className="btn btn-primary" onClick={() => { setEditingBook(null); setShowForm(true); }}>
            + Add Book
          </button>
        </div>

        <div className="filters-bar">
          <input
            className="input search-input"
            placeholder="Search by title or author…"
            value={searchTerm}
            onChange={e => handleSearch(e.target.value)}
          />
          <select className="select" style={{ width: 160 }} value={filters.status || ""}
            onChange={e => setFilters(f => ({ ...f, status: e.target.value || undefined, page: 1 }))}>
            <option value="">All Status</option>
            <option value="want_to_read">Want to Read</option>
            <option value="reading">Reading</option>
            <option value="finished">Finished</option>
          </select>
          <select className="select" style={{ width: 140 }} value={filters.sort_by || "created_at"}
            onChange={e => setFilters(f => ({ ...f, sort_by: e.target.value }))}>
            <option value="created_at">Date Added</option>
            <option value="title">Title</option>
            <option value="author">Author</option>
            <option value="rating">Rating</option>
          </select>
          <button className="btn btn-ghost btn-sm"
            onClick={() => setFilters(f => ({ ...f, sort_dir: f.sort_dir === "asc" ? "desc" : "asc" }))}>
            {filters.sort_dir === "asc" ? "↑ Asc" : "↓ Desc"}
          </button>
        </div>

        {loading ? (
          <div className="loading-center"><div className="spinner spinner-lg" /></div>
        ) : books.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📚</div>
            <div className="empty-title">No books found</div>
            <p className="text-muted">Add your first book to get started!</p>
          </div>
        ) : (
          <>
            <div className="grid grid-3">
              {books.map(book => (
                <div key={book.id} className="book-card">
                  <div className="book-card-header">
                    <div>
                      <div className="book-title">{book.title}</div>
                      <div className="book-author">{book.author}</div>
                    </div>
                    <StatusBadge status={book.status} />
                  </div>
                  <div className="book-meta">
                    <StarDisplay rating={book.rating} />
                    <ProgressDisplay current={book.current_page} total={book.total_pages} />
                  </div>
                  {book.notes && (
                    <p className="text-sm text-muted" style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {book.notes}
                    </p>
                  )}
                  <div className="book-actions">
                    <button className="btn btn-ghost btn-sm" onClick={() => { setEditingBook(book); setShowForm(true); }}>✏️ Edit</button>
                    {book.total_pages && book.status !== "finished" && (
                      <button className="btn btn-ghost btn-sm" onClick={() => setShowProgressModal(book)}>📈 Progress</button>
                    )}
                    <button className="btn btn-ghost btn-sm" onClick={() => setShowLendModal(book.id)}>📤 Lend</button>
                    <button className="btn btn-danger btn-sm" onClick={async () => {
                      if (confirm("Delete this book?")) {
                        await deleteBook(book.id);
                        loadBooks(filters);
                      }
                    }}>🗑️</button>
                  </div>
                </div>
              ))}
            </div>

            {totalPages > 1 && (
              <div className="pagination">
                <button className="btn btn-ghost btn-sm" disabled={page <= 1}
                  onClick={() => { const p = page - 1; setPage(p); setFilters(f => ({ ...f, page: p })); }}>← Prev</button>
                <span className="text-sm text-muted">Page {page} of {totalPages}</span>
                <button className="btn btn-ghost btn-sm" disabled={page >= totalPages}
                  onClick={() => { const p = page + 1; setPage(p); setFilters(f => ({ ...f, page: p })); }}>Next →</button>
              </div>
            )}
          </>
        )}

        {showForm && (
          <BookFormModal
            book={editingBook}
            onClose={() => setShowForm(false)}
            onSaved={() => { setShowForm(false); loadBooks(filters); }}
          />
        )}

        {showLendModal && (
          <LendModal
            bookId={showLendModal}
            onClose={() => setShowLendModal(null)}
            onLent={() => { setShowLendModal(null); loadBooks(filters); }}
          />
        )}

        {showProgressModal && (
          <ProgressModal
            book={showProgressModal}
            onClose={() => setShowProgressModal(null)}
            onUpdated={() => { setShowProgressModal(null); loadBooks(filters); }}
          />
        )}
      </main>
    </AuthGuard>
  );
}

function BookFormModal({ book, onClose, onSaved }) {
  const [title, setTitle] = useState(book?.title || "");
  const [author, setAuthor] = useState(book?.author || "");
  const [status, setStatus] = useState(book?.status || "want_to_read");
  const [totalPgs, setTotalPgs] = useState(book?.total_pages?.toString() || "");
  const [currentPg, setCurrentPg] = useState(book?.current_page?.toString() || "0");
  const [rating, setRating] = useState(book?.rating || 0);
  const [notes, setNotes] = useState(book?.notes || "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data = { title, author, status, notes: notes || null };
      if (totalPgs) data.total_pages = parseInt(totalPgs);
      if (!book) data.current_page = parseInt(currentPg) || 0;
      if (rating > 0) data.rating = rating;
      if (book) {
        await updateBook(book.id, data);
      } else {
        await createBook(data);
      }
      onSaved();
    } catch (err) {
      setError(err.message || "Failed to save");
    } finally { setLoading(false); }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content slide-up" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title">{book ? "Edit Book" : "Add New Book"}</h3>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        {error && <div className="form-error" style={{ marginBottom: "var(--space-md)", color: "var(--danger)" }}>⚠️ {error}</div>}
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "var(--space-md)" }}>
          <div className="form-group">
            <label className="form-label">Title</label>
            <input className="input" value={title} onChange={e => setTitle(e.target.value)} required />
          </div>
          <div className="form-group">
            <label className="form-label">Author</label>
            <input className="input" value={author} onChange={e => setAuthor(e.target.value)} required />
          </div>
          <div style={{ display: "flex", gap: "var(--space-md)" }}>
            <div className="form-group" style={{ flex: 1 }}>
              <label className="form-label">Status</label>
              <select className="select" value={status} onChange={e => setStatus(e.target.value)}>
                <option value="want_to_read">Want to Read</option>
                <option value="reading">Reading</option>
                <option value="finished">Finished</option>
              </select>
            </div>
            <div className="form-group" style={{ flex: 1 }}>
              <label className="form-label">Total Pages</label>
              <input className="input" type="number" min="1" value={totalPgs} onChange={e => setTotalPgs(e.target.value)} placeholder="Optional" />
            </div>
          </div>
          {!book && (
            <div className="form-group">
              <label className="form-label">Current Page</label>
              <input className="input" type="number" min="0" value={currentPg} onChange={e => setCurrentPg(e.target.value)} />
            </div>
          )}
          <div className="form-group">
            <label className="form-label">Rating</label>
            <div className="stars">
              {[1, 2, 3, 4, 5].map(i => (
                <button type="button" key={i} className={`star ${i <= rating ? "star-filled" : "star-empty"}`}
                  onClick={() => setRating(i === rating ? 0 : i)}>★</button>
              ))}
            </div>
          </div>
          <div className="form-group">
            <label className="form-label">Notes</label>
            <textarea className="textarea" value={notes} onChange={e => setNotes(e.target.value)} placeholder="Your thoughts…" />
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? <><span className="spinner spinner-sm" /> Saving…</> : (book ? "Update" : "Add Book")}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function LendModal({ bookId, onClose, onLent }) {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await lendBook(bookId, email);
      onLent();
    } catch (err) {
      setError(err.message || "Failed to lend");
    } finally { setLoading(false); }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content slide-up" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title">📤 Lend Book</h3>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        {error && <div className="form-error" style={{ marginBottom: "var(--space-md)", color: "var(--danger)" }}>⚠️ {error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Borrower&apos;s Email</label>
            <input className="input" type="email" value={email} onChange={e => setEmail(e.target.value)}
              placeholder="bob@example.com" required />
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? <><span className="spinner spinner-sm" /> Lending…</> : "Lend Book"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function ProgressModal({ book, onClose, onUpdated }) {
  const [currentPg, setCurrentPg] = useState(book.current_page?.toString() || "0");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await updateProgress(book.id, parseInt(currentPg));
      onUpdated();
    } catch (err) {
      setError(err.message || "Failed to update progress");
    } finally { setLoading(false); }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content slide-up" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title">📈 Update Progress</h3>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        <p className="text-muted text-sm" style={{ marginBottom: "var(--space-md)" }}>
          Update page progress for <strong>{book.title}</strong> (Total pages: {book.total_pages})
        </p>
        {error && <div className="form-error" style={{ marginBottom: "var(--space-md)", color: "var(--danger)" }}>⚠️ {error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Current Page</label>
            <input className="input" type="number" min="0" max={book.total_pages || undefined} value={currentPg} onChange={e => setCurrentPg(e.target.value)} required />
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? <><span className="spinner spinner-sm" /> Saving…</> : "Save Progress"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
