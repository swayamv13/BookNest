import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  login as apiLogin,
  signup as apiSignup,
  logout as apiLogout,
  getMe,
  silentRefresh,
  setAccessToken,
} from "./api-client";

const AuthContext = createContext({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  login: async () => {},
  signup: async () => {},
  logout: async () => {},
});

export function AuthProvider({ children }) {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const ok = await silentRefresh();
      if (ok) {
        try {
          const me = await getMe();
          setUser(me);
        } catch {
          setUser(null);
        }
      }
      setIsLoading(false);
    })();
  }, []);

  const login = useCallback(async (email, password) => {
    const data = await apiLogin(email, password);
    if (data.user) {
      setUser(data.user);
    } else {
      const me = await getMe();
      setUser(me);
    }
  }, []);

  const signup = useCallback(async (name, email, password) => {
    const data = await apiSignup(name, email, password);
    if (data.user) {
      setUser(data.user);
    } else {
      const me = await getMe();
      setUser(me);
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await apiLogout();
    } catch {
      // Always clear local session even if the API call fails
    }
    setAccessToken(null);
    setUser(null);
    navigate("/login", { replace: true });
  }, [navigate]);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        signup,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
