import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Navbar from "@/components/layout/Navbar";
import AuthGuard from "@/components/layout/AuthGuard";
import {
  getShelfDetail, updateShelf, deleteShelf, addBookToShelf,
  removeBookFromShelf, shareShelf, updateShare, removeShare,
  getBooks,
} from "@/lib/api-client";

export default function ShelfDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const shelfId = id;

  const [shelf, setShelf] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showShare, setShowShare] = useState(false);
  const [showAddBook, setShowAddBook] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editName, setEditName] = useState("");

  const loadShelf = useCallback(async () => {
    try {
      const data = await getShelfDetail(shelfId);
      setShelf(data);
      setEditName(data.name);
    } catch {} finally { setLoading(false); }
  }, [shelfId]);

  useEffect(() => { loadShelf(); }, [loadShelf]);

  const isOwner = shelf?.role === "owner";
  const canEdit = shelf?.role === "owner" || shelf?.role === "editor";

  async function handleRename(e) {
    e.preventDefault();
    await updateShelf(shelfId, editName);
    setEditing(false);
    loadShelf();
  }

  async function handleDelete() {
    if (confirm("Delete this shelf? Books will not be affected.")) {
      await deleteShelf(shelfId);
      navigate("/shelves");
    }
  }

  async function handleRemoveBook(bookId) {
    await removeBookFromShelf(shelfId, bookId);
    loadShelf();
  }

  return (
    <AuthGuard>
      <Navbar />
      <main className="page fade-in">
        {loading ? (
          <div className="loading-center"><div className="spinner spinner-lg" /></div>
        ) : shelf ? (
          <>
            <div className="page-header">
              <div>
                {editing ? (
                  <form onSubmit={handleRename} style={{ display: "flex", gap: "var(--space-sm)" }}>
                    <input className="input" value={editName} onChange={e => setEditName(e.target.value)} autoFocus />
                    <button type="submit" className="btn btn-primary btn-sm">Save</button>
                    <button type="button" className="btn btn-ghost btn-sm" onClick={() => setEditing(false)}>Cancel</button>
                  </form>
                ) : (
                  <h1 className="page-title">
                    🗂️ {shelf.name}
                    <span className={`badge ${shelf.role === "owner" ? "badge-owner" : shelf.role === "editor" ? "badge-editor" : "badge-viewer"}`}
                      style={{ marginLeft: "var(--space-sm)", fontSize: "0.75rem", verticalAlign: "middle" }}>
                      {shelf.role}
                    </span>
                  </h1>
                )}
                <p className="text-sm text-muted" style={{ marginTop: "var(--space-xs)" }}>
                  Owned by {shelf.owner_name} · {shelf.books.length} book{shelf.books.length !== 1 ? "s" : ""}
                </p>
              </div>
              <div style={{ display: "flex", gap: "var(--space-sm)" }}>
                {canEdit && (
                  <button className="btn btn-secondary btn-sm" onClick={() => setShowAddBook(true)}>
                    + Add Book
                  </button>
                )}
                {isOwner && (
                  <>
                    <button className="btn btn-secondary btn-sm" onClick={() => setEditing(true)}>✏️ Rename</button>
                    <button className="btn btn-primary btn-sm" onClick={() => setShowShare(true)}>🔗 Share</button>
                    <button className="btn btn-danger btn-sm" onClick={handleDelete}>🗑️</button>
                  </>
                )}
              </div>
            </div>

            <h3 className="section-title">📚 Books on this shelf</h3>
            {shelf.books.length === 0 ? (
              <div className="empty-state" style={{ padding: "var(--space-xl)" }}>
                <div className="empty-icon">📚</div>
                <div className="empty-title">No books on this shelf</div>
              </div>
            ) : (
              <div className="grid grid-3" style={{ marginBottom: "var(--space-2xl)" }}>
                {shelf.books.map(book => (
                  <div key={book.id} className="book-card">
                    <div className="book-card-header">
                      <div>
                        <div className="book-title">{book.title}</div>
                        <div className="book-author">{book.author}</div>
                      </div>
                      <span className={`badge ${book.status === "reading" ? "badge-reading" : book.status === "finished" ? "badge-finished" : "badge-want-to-read"}`}>
                        {book.status.replace(/_/g, " ")}
                      </span>
                    </div>
                    {canEdit && (
                      <div className="book-actions">
                        <button className="btn btn-danger btn-sm" onClick={() => handleRemoveBook(book.id)}>
                          Remove
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {isOwner && (
              <>
                <hr className="section-divider" />
                <h3 className="section-title">👥 Collaborators</h3>
                {shelf.collaborators.length === 0 ? (
                  <p className="text-muted" style={{ padding: "var(--space-md) 0" }}>
                    No collaborators yet. Share this shelf to collaborate!
                  </p>
                ) : (
                  <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-xs)" }}>
                    {shelf.collaborators.map(c => (
                      <div key={c.id} className="collab-row">
                        <div className="collab-info">
                          <span className="collab-name">{c.user_name}</span>
                          <span className="collab-email">{c.user_email}</span>
                        </div>
                        <div className="collab-actions">
                          <select className="select" style={{ width: 100, padding: "0.375rem 0.5rem", fontSize: "0.8125rem" }}
                            value={c.role} onChange={async e => {
                              await updateShare(shelfId, c.user_id, e.target.value);
                              loadShelf();
                            }}>
                            <option value="editor">Editor</option>
                            <option value="viewer">Viewer</option>
                          </select>
                          <button className="btn btn-danger btn-sm" onClick={async () => {
                            await removeShare(shelfId, c.user_id);
                            loadShelf();
                          }}>Remove</button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}

            {showShare && <ShareModal shelfId={shelfId} onClose={() => setShowShare(false)} onShared={loadShelf} />}
            {showAddBook && <AddBookModal shelfId={shelfId} existingBookIds={shelf.books.map(b => b.id)} onClose={() => setShowAddBook(false)} onAdded={loadShelf} />}
          </>
        ) : (
          <div className="error-state">
            <h3>Shelf not found</h3>
            <button className="btn btn-primary" onClick={() => navigate("/shelves")} style={{ marginTop: "var(--space-md)" }}>Back to Shelves</button>
          </div>
        )}
      </main>
    </AuthGuard>
  );
}

function ShareModal({ shelfId, onClose, onShared }) {
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("viewer");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await shareShelf(shelfId, email, role);
      onShared();
      onClose();
    } catch (err) {
      setError(err.message || "Failed to share");
    } finally { setLoading(false); }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content slide-up" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title">🔗 Share Shelf</h3>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        {error && <div className="form-error" style={{ marginBottom: "var(--space-md)", color: "var(--danger)" }}>⚠️ {error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-group" style={{ marginBottom: "var(--space-md)" }}>
            <label className="form-label">Email</label>
            <input className="input" type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="collaborator@example.com" required />
          </div>
          <div className="form-group">
            <label className="form-label">Role</label>
            <select className="select" value={role} onChange={e => setRole(e.target.value)}>
              <option value="viewer">Viewer — can view books</option>
              <option value="editor">Editor — can add/remove books</option>
            </select>
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? <><span className="spinner spinner-sm" /> Sharing…</> : "Share"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function AddBookModal({ shelfId, existingBookIds, onClose, onAdded }) {
  const [myBooks, setMyBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const data = await getBooks({ page_size: 100 });
        setMyBooks(data.items.filter(b => !existingBookIds.includes(b.id)));
      } catch {} finally { setLoading(false); }
    })();
  }, [existingBookIds]);

  async function handleAdd(bookId) {
    setAdding(bookId);
    try {
      await addBookToShelf(shelfId, bookId);
      onAdded();
      onClose();
    } catch {} finally { setAdding(null); }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content slide-up" onClick={e => e.stopPropagation()} style={{ maxHeight: "80vh" }}>
        <div className="modal-header">
          <h3 className="modal-title">Add Book to Shelf</h3>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        {loading ? (
          <div className="loading-center"><div className="spinner" /></div>
        ) : myBooks.length === 0 ? (
          <p className="text-muted">No more books to add.</p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-sm)" }}>
            {myBooks.map(book => (
              <div key={book.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "var(--space-sm) var(--space-md)", borderRadius: "var(--radius-md)", background: "var(--bg-card)" }}>
                <div>
                  <div style={{ fontWeight: 500 }}>{book.title}</div>
                  <div className="text-sm text-muted">{book.author}</div>
                </div>
                <button className="btn btn-primary btn-sm" disabled={adding === book.id} onClick={() => handleAdd(book.id)}>
                  {adding === book.id ? <span className="spinner spinner-sm" /> : "Add"}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
