import { useEffect, useRef, useState } from "react";

import { Navigate, useSearchParams } from "react-router-dom";

import { useAuth } from "@/lib/auth";

// Microsoft Entra redirects here with ?code=... after SSO. We exchange it for an
// app token via the backend, then land on the dashboard. (Active once MS_* env
// is configured; until then the dev-login on /login is used instead.)
export function AuthCallbackPage(): JSX.Element {
  const [params] = useSearchParams();
  const { user, completeMicrosoftLogin } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const ran = useRef(false);

  useEffect(() => {
    if (ran.current) return;
    ran.current = true;
    const code = params.get("code");
    if (!code) {
      setError("Missing authorization code.");
      return;
    }
    completeMicrosoftLogin(code).catch(() =>
      setError("Sign-in failed — this account may not be provisioned for the app."),
    );
  }, [params, completeMicrosoftLogin]);

  if (user) return <Navigate to="/dashboard" replace />;

  return (
    <div className="grid min-h-screen place-items-center bg-background p-4 text-sm">
      {error ? (
        <div className="text-center">
          <p className="text-destructive">{error}</p>
          <a href="/login" className="mt-2 inline-block text-primary hover:underline">
            Back to sign in
          </a>
        </div>
      ) : (
        <p className="text-muted-foreground">Completing Microsoft sign-in…</p>
      )}
    </div>
  );
}
