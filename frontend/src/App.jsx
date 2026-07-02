import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./lib/auth-context";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Dashboard from "./pages/Dashboard";
import Books from "./pages/Books";
import Shelves from "./pages/Shelves";
import ShelfDetail from "./pages/ShelfDetail";
import Borrowed from "./pages/Borrowed";

function HomeRedirect() {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) return null;
  return <Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/books" element={<Books />} />
          <Route path="/shelves" element={<Shelves />} />
          <Route path="/shelves/:id" element={<ShelfDetail />} />
          <Route path="/borrowed" element={<Borrowed />} />
          <Route path="*" element={<HomeRedirect />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
