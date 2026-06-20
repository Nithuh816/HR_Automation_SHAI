import { LogOut, Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ROLE_LABELS, useAuth } from "@/lib/auth";

function initials(name: string): string {
  const parts = name.trim().split(/\s+/);
  const first = parts[0]?.[0] ?? "";
  const last = parts.length > 1 ? parts[parts.length - 1][0] : "";
  return (first + last).toUpperCase() || "?";
}

export function Header(): JSX.Element {
  const { user, logout } = useAuth();

  return (
    <header className="flex h-14 items-center justify-between border-b border-border/60 bg-card/40 px-4">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Search className="h-4 w-4" />
        <input
          type="search"
          placeholder="Search candidates, requisitions…"
          className="w-72 bg-transparent text-sm outline-none placeholder:text-muted-foreground/70"
        />
      </div>
      <div className="flex items-center gap-3">
        {user && (
          <div className="text-right leading-tight">
            <div className="text-sm font-medium">{user.name}</div>
            <div className="text-xs text-muted-foreground">{ROLE_LABELS[user.role]}</div>
          </div>
        )}
        <div className="grid h-8 w-8 place-items-center rounded-full bg-secondary text-xs font-semibold">
          {user ? initials(user.name) : "?"}
        </div>
        <Button variant="ghost" size="icon" aria-label="Sign out" onClick={logout}>
          <LogOut className="h-4 w-4" />
        </Button>
      </div>
    </header>
  );
}
