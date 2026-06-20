import { useState } from "react";
import { Navigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useAuth } from "@/lib/auth";

// Convenience identities for dev-login (placeholder seed emails, M1a).
const DEV_USERS = [
  { email: "balaji.p@shaihealth.com", label: "Balaji P — HR Head" },
  { email: "s.muthahir.ahmed@shaihealth.com", label: "Muthahir Ahmed — TA Team Lead" },
  { email: "pavithra.s@shaihealth.com", label: "Pavithra S — TA Recruiter" },
  { email: "sowmya.murugan@shaihealth.com", label: "Sowmya Murugan — Post-Recruitment" },
  { email: "prabhu.v@shaihealth.com", label: "Prabhu V — Dept Head (QA)" },
];

export function LoginPage(): JSX.Element {
  const { user, devLogin, startMicrosoftLogin } = useAuth();
  const [email, setEmail] = useState(DEV_USERS[0].email);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (user) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleDevLogin = async () => {
    setBusy(true);
    setError(null);
    try {
      await devLogin(email);
    } catch {
      setError("Login failed. Is the API running and the user seeded?");
    } finally {
      setBusy(false);
    }
  };

  const handleMicrosoft = async () => {
    setError(null);
    try {
      await startMicrosoftLogin();
    } catch {
      setError("Microsoft SSO is configured in M1b.");
    }
  };

  return (
    <div className="grid min-h-screen place-items-center bg-background p-4">
      <Card className="w-full max-w-sm">
        <CardHeader className="text-center">
          <div className="mx-auto mb-2 grid h-10 w-10 place-items-center rounded-md bg-primary text-primary-foreground">
            <span className="font-bold">HR</span>
          </div>
          <CardTitle>SHAI · HR Automation</CardTitle>
          <CardDescription>Sign in to continue</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button className="w-full" variant="outline" onClick={handleMicrosoft}>
            Continue with Microsoft
          </Button>

          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span className="h-px flex-1 bg-border" />
            dev login
            <span className="h-px flex-1 bg-border" />
          </div>

          <select
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-md border border-border bg-transparent px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            {DEV_USERS.map((u) => (
              <option key={u.email} value={u.email} className="bg-card">
                {u.label}
              </option>
            ))}
          </select>

          <Button className="w-full" onClick={handleDevLogin} disabled={busy}>
            {busy ? "Signing in…" : "Sign in"}
          </Button>

          {error && <p className="text-center text-xs text-destructive">{error}</p>}
        </CardContent>
      </Card>
    </div>
  );
}
