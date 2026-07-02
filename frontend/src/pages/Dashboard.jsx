import { useState, useEffect, useCallback } from "react";
import Navbar from "@/components/layout/Navbar";
import AuthGuard from "@/components/layout/AuthGuard";
import { getDashboard, getActivity } from "@/lib/api-client";
import { wsClient } from "@/lib/websocket-client";
import { useAuth } from "@/lib/auth-context";

function formatTime(dateStr) {
  const d = new Date(dateStr);
  const now = new Date();
  const diff = now.getTime() - d.getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

const eventIcons = {
  "book.created": "📕",
  "book.updated": "✏️",
  "book.deleted": "🗑️",
  "book.finished": "🏆",
  "book.progress_updated": "📈",
  "book.lent": "📤",
  "book.returned": "📥",
  "shelf.created": "📁",
  "shelf.deleted": "🗂️",
  "shelf.shared": "🔗",
  "shelf.book_added": "➕",
  "shelf.book_removed": "➖",
};

function describeEvent(a) {
  const m = a.event_metadata;
  switch (a.event_type) {
    case "book.created": return `Added "${m.title || "a book"}"`;
    case "book.finished": return `Finished "${m.title || "a book"}" 🎉`;
    case "book.lent": return `Lent a book to ${m.borrower_email || "someone"}`;
    case "book.returned": return `Book returned`;
    case "shelf.created": return `Created shelf "${m.name || ""}"`;
    case "shelf.shared": return `Shared "${m.shelf_name || ""}" with ${m.shared_with || "someone"}`;
    case "shelf.book_added": return `Added "${m.book_title || ""}" to "${m.shelf_name || ""}"`;
    case "shelf.book_removed": return `Removed "${m.book_title || ""}" from "${m.shelf_name || ""}"`;
    case "book.progress_updated": return `Updated progress: page ${m.current_page}/${m.total_pages}`;
    default: return a.event_type.replace(/\./g, " ");
  }
}

export default function Dashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    try {
      const [d, a] = await Promise.all([getDashboard(), getActivity(1, 15)]);
      setStats(d);
      setActivities(a.items);
    } catch {} finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    wsClient.connect();
    const handler = () => { loadData(); };
    wsClient.on("*", handler);
    return () => { wsClient.off("*", handler); };
  }, [loadData]);

  return (
    <AuthGuard>
      <Navbar />
      <main className="page fade-in">
        <div className="page-header">
          <h1 className="page-title">
            Welcome back, {user?.name?.split(" ")[0]} 👋
          </h1>
        </div>

        {loading ? (
          <div className="loading-center"><div className="spinner spinner-lg" /></div>
        ) : stats ? (
          <>
            <div className="grid grid-4" style={{ marginBottom: "var(--space-2xl)" }}>
              <div className="stat-card">
                <div className="stat-icon">📚</div>
                <div className="stat-value">{stats.total_books}</div>
                <div className="stat-label">Total Books</div>
              </div>
              <div className="stat-card">
                <div className="stat-icon" style={{ background: "rgba(59,130,246,0.15)" }}>📖</div>
                <div className="stat-value">{stats.reading_count}</div>
                <div className="stat-label">Currently Reading</div>
              </div>
              <div className="stat-card">
                <div className="stat-icon" style={{ background: "var(--success-subtle)" }}>✅</div>
                <div className="stat-value">{stats.finished_count}</div>
                <div className="stat-label">Finished</div>
              </div>
              <div className="stat-card">
                <div className="stat-icon" style={{ background: "var(--accent-glow)" }}>🎯</div>
                <div className="stat-value">{stats.finished_this_year}</div>
                <div className="stat-label">Finished This Year</div>
              </div>
              <div className="stat-card">
                <div className="stat-icon" style={{ background: "rgba(240,180,41,0.15)" }}>⭐</div>
                <div className="stat-value">{stats.average_rating?.toFixed(1) || "—"}</div>
                <div className="stat-label">Avg Rating</div>
              </div>
              <div className="stat-card">
                <div className="stat-icon" style={{ background: "rgba(240,180,41,0.15)" }}>📋</div>
                <div className="stat-value">{stats.want_to_read_count}</div>
                <div className="stat-label">Want to Read</div>
              </div>
              <div className="stat-card">
                <div className="stat-icon" style={{ background: "rgba(59,130,246,0.15)" }}>📤</div>
                <div className="stat-value">{stats.lent_out_count}</div>
                <div className="stat-label">Lent Out</div>
              </div>
              <div className="stat-card">
                <div className="stat-icon" style={{ background: "var(--success-subtle)" }}>🤝</div>
                <div className="stat-value">{stats.shared_with_me_count}</div>
                <div className="stat-label">Shared With Me</div>
              </div>
            </div>

            <div className="glass-card">
              <h3 style={{ marginBottom: "var(--space-lg)" }}>📝 Recent Activity</h3>
              {activities.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-icon">📭</div>
                  <div className="empty-title">No activity yet</div>
                  <p className="text-muted">Start by adding your first book!</p>
                </div>
              ) : (
                <div>
                  {activities.map((a) => (
                    <div key={a.id} className="activity-item">
                      <div className="activity-icon">
                        {eventIcons[a.event_type] || "📌"}
                      </div>
                      <div className="activity-content">
                        <div className="activity-text">{describeEvent(a)}</div>
                        <div className="activity-time">{formatTime(a.created_at)}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        ) : null}
      </main>
    </AuthGuard>
  );
}
