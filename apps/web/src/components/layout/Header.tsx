import { Bell, Search } from "lucide-react";

import { Button } from "@/components/ui/button";

export function Header(): JSX.Element {
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
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" aria-label="Notifications">
          <Bell className="h-4 w-4" />
        </Button>
        <div className="grid h-8 w-8 place-items-center rounded-full bg-secondary text-xs font-semibold">
          CC
        </div>
      </div>
    </header>
  );
}
