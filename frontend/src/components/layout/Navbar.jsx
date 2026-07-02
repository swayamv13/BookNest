import { Link, useLocation } from "react-router-dom";
import { useAuth } from "@/lib/auth-context";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: "📊" },
  { href: "/books", label: "Books", icon: "📚" },
  { href: "/shelves", label: "Shelves", icon: "🗂️" },
  { href: "/borrowed", label: "Lending", icon: "🤝" },
];

export default function Navbar() {
  const { user, isAuthenticated, logout } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) return null;

  return (
    <nav className="nav">
      <div className="nav-inner">
        <Link to="/dashboard" className="nav-brand">
          📖 BookNest
        </Link>

        <ul className="nav-links">
          {navItems.map((item) => (
            <li key={item.href}>
              <Link
                to={item.href}
                className={`nav-link ${
                  location.pathname.startsWith(item.href) ? "active" : ""
                }`}
              >
                <span style={{ marginRight: "4px" }}>{item.icon}</span>
                {item.label}
              </Link>
            </li>
          ))}
        </ul>

        <div className="nav-right">
          <span className="nav-user">{user?.name}</span>
          <button className="btn btn-ghost btn-sm" onClick={logout}>
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
}
