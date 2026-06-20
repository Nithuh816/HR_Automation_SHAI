import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { api } from "@/lib/api";

export type Role =
  | "hr_head"
  | "ta_tl"
  | "ta_recruiter"
  | "dept_lead"
  | "dept_head"
  | "pr";

export type Team = "ta" | "pr" | "mgmt" | "dept";

export interface AuthUser {
  id: number;
  email: string;
  name: string;
  role: Role;
  team: Team;
  department_id: number | null;
  manager_id: number | null;
  is_active: boolean;
}

export const ROLE_LABELS: Record<Role, string> = {
  hr_head: "HR Head",
  ta_tl: "TA Team Lead",
  ta_recruiter: "TA Recruiter",
  dept_lead: "Dept Team Lead",
  dept_head: "Dept Head",
  pr: "Post-Recruitment",
};

const TOKEN_KEY = "hr.access_token";

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  devLogin: (email: string) => Promise<void>;
  startMicrosoftLogin: () => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }): JSX.Element {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  const loadMe = useCallback(async () => {
    if (!sessionStorage.getItem(TOKEN_KEY)) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const { data } = await api.get<AuthUser>("/auth/me");
      setUser(data);
    } catch {
      sessionStorage.removeItem(TOKEN_KEY);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadMe();
  }, [loadMe]);

  const devLogin = useCallback(
    async (email: string) => {
      const { data } = await api.post<{ access_token: string }>("/auth/dev-login", {
        email,
      });
      sessionStorage.setItem(TOKEN_KEY, data.access_token);
      await loadMe();
    },
    [loadMe],
  );

  const startMicrosoftLogin = useCallback(async () => {
    const { data } = await api.get<{ authorization_url: string }>("/auth/login");
    window.location.href = data.authorization_url;
  }, []);

  const logout = useCallback(() => {
    sessionStorage.removeItem(TOKEN_KEY);
    setUser(null);
    window.location.href = "/login";
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ user, loading, devLogin, startMicrosoftLogin, logout }),
    [user, loading, devLogin, startMicrosoftLogin, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
