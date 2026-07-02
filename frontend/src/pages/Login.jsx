import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/lib/auth-context";
import { ApiError } from "@/lib/api-client";
import { DEMO_EMAIL, DEMO_PASSWORD } from "@/lib/demo-users";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await login(email, password);
      navigate("/dashboard");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Something went wrong. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card slide-up">
        <div className="auth-title">
          <span style={{ marginRight: "8px" }}>📖</span>BookNest
        </div>
        <p className="auth-subtitle">Welcome back! Sign in to continue.</p>

        {error && (
          <div
            className="toast-error"
            style={{
              padding: "0.75rem 1rem",
              borderRadius: "var(--radius-md)",
              marginBottom: "var(--space-lg)",
              fontSize: "0.875rem",
            }}
          >
            ⚠️ {error}
          </div>
        )}

        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="email">
              Email
            </label>
            <input
              id="email"
              type="email"
              className="input"
              placeholder="alice@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              className="input"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              autoComplete="current-password"
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-lg"
            disabled={loading}
            style={{ width: "100%" }}
          >
            {loading ? (
              <>
                <span className="spinner spinner-sm" /> Signing in…
              </>
            ) : (
              "Sign In"
            )}
          </button>
        </form>

        <p className="auth-footer">
          Don&apos;t have an account?{" "}
          <Link to="/signup">Create one</Link>
        </p>

        <p className="auth-demo">
          Demo: {DEMO_EMAIL} / {DEMO_PASSWORD}
        </p>
      </div>
    </div>
  );
}
