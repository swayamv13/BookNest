import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/lib/auth-context";

export default function AuthGuard({ children }) {
  const { isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      navigate("/login");
    }
  }, [isLoading, isAuthenticated, navigate]);

  if (isLoading) {
    return (
      <div className="loading-center" style={{ minHeight: "100vh" }}>
        <div className="spinner spinner-lg" />
      </div>
    );
  }

  if (!isAuthenticated) return null;

  return <>{children}</>;
}
