// Placeholder for Microsoft 365 SSO. Wired up in M1 using @azure/msal-browser.
export type Role = "HR_HEAD" | "TA_TL" | "TA_RECRUITER" | "DEPT_LEAD" | "DEPT_HEAD" | "PR_MEMBER" | "ADMIN";

export interface AuthUser {
  id: string;
  email: string;
  name: string;
  role: Role;
}

export function getCurrentUser(): AuthUser | null {
  const raw = sessionStorage.getItem("hr.user");
  return raw ? (JSON.parse(raw) as AuthUser) : null;
}

export function signOut(): void {
  sessionStorage.removeItem("hr.user");
  sessionStorage.removeItem("hr.access_token");
  window.location.href = "/login";
}
