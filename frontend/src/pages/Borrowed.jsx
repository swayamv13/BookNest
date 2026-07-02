import { useState, useEffect, useCallback } from "react";
import Navbar from "@/components/layout/Navbar";
import AuthGuard from "@/components/layout/AuthGuard";
import {
  getBorrowedBooks, getLentOutBooks, returnBook,
} from "@/lib/api-client";
import { wsClient } from "@/lib/websocket-client";

function formatDate(dateStr) {
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short", day: "numeric", year: "numeric",
  });
}

export default function Borrowed() {
  const [borrowed, setBorrowed] = useState([]);
  const [lentOut, setLentOut] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [returning, setReturning] = useState(null);

  const loadData = useCallback(async () => {
    setError("");
    try {
      const [b, l] = await Promise.all([getBorrowedBooks(), getLentOutBooks()]);
      setBorrowed(b);
      setLentOut(l);
    } catch (err) {
      setError(err.message || "Failed to load lending data");
    } finally { setLoading(false); }
  }, []);

  useEffect(() => {
    loadData();
    wsClient.connect();
    const handler = () => { loadData(); };
    wsClient.on("book.lent", handler);
    wsClient.on("book.returned", handler);
    return () => {
      wsClient.off("book.lent", handler);
      wsClient.off("book.returned", handler);
    };
  }, [loadData]);

  async function handleReturn(bookId) {
    setReturning(bookId);
    try {
      await returnBook(bookId);
      loadData();
    } catch {} finally { setReturning(null); }
  }

  return (
    <AuthGuard>
      <Navbar />
      <main className="page fade-in">
        <div className="page-header">
          <h1 className="page-title">🤝 Lending</h1>
        </div>

        {error && (
          <div className="toast-error" style={{ padding: "0.75rem 1rem", borderRadius: "var(--radius-md)", marginBottom: "var(--space-lg)", fontSize: "0.875rem" }}>
            ⚠️ {error}
          </div>
        )}

        {loading ? (
          <div className="loading-center"><div className="spinner spinner-lg" /></div>
        ) : (
          <>
            <h3 className="section-title">📥 Books I&apos;ve Borrowed</h3>
            {borrowed.length === 0 ? (
              <div className="empty-state" style={{ padding: "var(--space-xl)" }}>
                <div className="empty-icon">📥</div>
                <div className="empty-title">No borrowed books</div>
                <p className="text-muted">When someone lends you a book, it will appear here.</p>
              </div>
            ) : (
              <div className="grid grid-3" style={{ marginBottom: "var(--space-2xl)" }}>
                {borrowed.map(b => (
                  <div key={b.id} className="book-card">
                    <div>
                      <div className="book-title">{b.book_title}</div>
                      <div className="book-author">{b.book_author}</div>
                    </div>
                    <div className="text-sm text-muted">
                      Lent by <strong style={{ color: "var(--text-primary)" }}>{b.owner_name}</strong>
                    </div>
                    <div className="text-xs text-muted">
                      Since {formatDate(b.lent_at)}
                    </div>
                  </div>
                ))}
              </div>
            )}

            <hr className="section-divider" />

            <h3 className="section-title">📤 Books I&apos;ve Lent Out</h3>
            {lentOut.length === 0 ? (
              <div className="empty-state" style={{ padding: "var(--space-xl)" }}>
                <div className="empty-icon">📤</div>
                <div className="empty-title">No lent-out books</div>
                <p className="text-muted">Lend a book from your collection to see it here.</p>
              </div>
            ) : (
              <div className="grid grid-3">
                {lentOut.map(l => (
                  <div key={l.id} className="book-card">
                    <div>
                      <div className="book-title">{l.book_title}</div>
                    </div>
                    <div className="text-sm text-muted">
                      Borrowed by <strong style={{ color: "var(--text-primary)" }}>{l.borrower_name}</strong>
                    </div>
                    <div className="text-xs text-muted">
                      {l.borrower_email} · Since {formatDate(l.lent_at)}
                    </div>
                    <div className="book-actions">
                      <button
                        className="btn btn-primary btn-sm"
                        disabled={returning === l.book_id}
                        onClick={() => handleReturn(l.book_id)}
                      >
                        {returning === l.book_id ? (
                          <><span className="spinner spinner-sm" /> Returning…</>
                        ) : (
                          "📥 Mark Returned"
                        )}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </main>
    </AuthGuard>
  );
}
