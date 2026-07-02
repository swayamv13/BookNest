import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "@/components/layout/Navbar";
import AuthGuard from "@/components/layout/AuthGuard";
import { getShelves, getSharedShelves, createShelf } from "@/lib/api-client";

export default function Shelves() {
  const navigate = useNavigate();
  const [ownShelves, setOwnShelves] = useState([]);
  const [sharedShelves, setSharedShelves] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [creating, setCreating] = useState(false);

  const loadShelves = useCallback(async () => {
    try {
      const [own, shared] = await Promise.all([getShelves(), getSharedShelves()]);
      setOwnShelves(own);
      setSharedShelves(shared);
    } catch {} finally { setLoading(false); }
  }, []);

  useEffect(() => { loadShelves(); }, [loadShelves]);

  async function handleCreate(e) {
    e.preventDefault();
    setCreating(true);
    try {
      await createShelf(newName);
      setNewName("");
      setShowCreate(false);
      loadShelves();
    } catch {} finally { setCreating(false); }
  }

  function RoleBadge({ role }) {
    const cls = role === "owner" ? "badge-owner" : role === "editor" ? "badge-editor" : "badge-viewer";
    return <span className={`badge ${cls}`}>{role}</span>;
  }

  return (
    <AuthGuard>
      <Navbar />
      <main className="page fade-in">
        <div className="page-header">
          <h1 className="page-title">🗂️ Shelves</h1>
          <button className="btn btn-primary" onClick={() => setShowCreate(true)}>+ New Shelf</button>
        </div>

        {loading ? (
          <div className="loading-center"><div className="spinner spinner-lg" /></div>
        ) : (
          <>
            <h3 className="section-title">📁 My Shelves</h3>
            {ownShelves.length === 0 ? (
              <div className="empty-state" style={{ padding: "var(--space-xl)" }}>
                <div className="empty-icon">📁</div>
                <div className="empty-title">No shelves yet</div>
                <p className="text-muted">Create a shelf to organize your books!</p>
              </div>
            ) : (
              <div className="grid grid-3" style={{ marginBottom: "var(--space-2xl)" }}>
                {ownShelves.map(shelf => (
                  <div key={shelf.id} className="shelf-card" onClick={() => navigate(`/shelves/${shelf.id}`)}>
                    <div className="shelf-card-header">
                      <h4>{shelf.name}</h4>
                      <RoleBadge role="owner" />
                    </div>
                    <div className="text-sm text-muted">{shelf.book_count} book{shelf.book_count !== 1 ? "s" : ""}</div>
                  </div>
                ))}
              </div>
            )}

            <hr className="section-divider" />
            <h3 className="section-title">🤝 Shared With Me</h3>
            {sharedShelves.length === 0 ? (
              <div className="empty-state" style={{ padding: "var(--space-xl)" }}>
                <div className="empty-icon">🔗</div>
                <div className="empty-title">No shared shelves</div>
                <p className="text-muted">When someone shares a shelf with you, it will appear here.</p>
              </div>
            ) : (
              <div className="grid grid-3">
                {sharedShelves.map(shelf => (
                  <div key={shelf.id} className="shelf-card" onClick={() => navigate(`/shelves/${shelf.id}`)}>
                    <div className="shelf-card-header">
                      <h4>{shelf.name}</h4>
                      <RoleBadge role={shelf.role} />
                    </div>
                    <div className="text-sm text-muted">{shelf.book_count} book{shelf.book_count !== 1 ? "s" : ""}</div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {showCreate && (
          <div className="modal-overlay" onClick={() => setShowCreate(false)}>
            <div className="modal-content slide-up" onClick={e => e.stopPropagation()}>
              <div className="modal-header">
                <h3 className="modal-title">Create New Shelf</h3>
                <button className="modal-close" onClick={() => setShowCreate(false)}>✕</button>
              </div>
              <form onSubmit={handleCreate}>
                <div className="form-group">
                  <label className="form-label">Shelf Name</label>
                  <input className="input" value={newName} onChange={e => setNewName(e.target.value)}
                    placeholder="e.g. Favorites, Sci-Fi, Work Reading" required />
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-secondary" onClick={() => setShowCreate(false)}>Cancel</button>
                  <button type="submit" className="btn btn-primary" disabled={creating}>
                    {creating ? <><span className="spinner spinner-sm" /> Creating…</> : "Create Shelf"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>
    </AuthGuard>
  );
}
