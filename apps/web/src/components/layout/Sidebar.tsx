import {
  Building2,
  CalendarClock,
  ClipboardCheck,
  FileText,
  Inbox,
  LayoutDashboard,
  UserCog,
  UserPlus,
  Users,
} from "lucide-react";
import { NavLink } from "react-router-dom";

import { useAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";

const nav = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/requisitions", label: "Requisitions", icon: Inbox },
  { to: "/candidates", label: "Candidates", icon: Users },
  { to: "/pipeline", label: "Pipeline", icon: ClipboardCheck },
  { to: "/interviews/today", label: "Interviews", icon: CalendarClock },
  { to: "/offers", label: "Offers", icon: FileText },
  { to: "/onboarding/queue", label: "Onboarding", icon: UserPlus },
];

// HR Head-only administration.
const adminNav = [
  { to: "/settings/users", label: "Users", icon: UserCog },
  { to: "/settings/departments", label: "Departments", icon: Building2 },
];

const linkClass = ({ isActive }: { isActive: boolean }) =>
  cn(
    "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
    isActive
      ? "bg-primary/15 text-foreground"
      : "text-muted-foreground hover:bg-secondary hover:text-foreground",
  );

export function Sidebar(): JSX.Element {
  const { user } = useAuth();

  return (
    <aside className="hidden w-60 shrink-0 border-r border-border/60 bg-card/40 p-4 md:block">
      <div className="mb-6 flex items-center gap-2 px-2">
        <div className="grid h-8 w-8 place-items-center rounded-md bg-primary text-primary-foreground">
          <span className="text-sm font-bold">HR</span>
        </div>
        <div className="text-sm font-semibold tracking-tight">SHAI · HR</div>
      </div>
      <nav className="space-y-1">
        {nav.map(({ to, label, icon: Icon }) => (
          <NavLink key={to} to={to} className={linkClass}>
            <Icon className="h-4 w-4" />
            <span>{label}</span>
          </NavLink>
        ))}

        {user?.role === "hr_head" && (
          <>
            <div className="px-3 pb-1 pt-4 text-xs font-medium uppercase tracking-wide text-muted-foreground/70">
              Admin
            </div>
            {adminNav.map(({ to, label, icon: Icon }) => (
              <NavLink key={to} to={to} className={linkClass}>
                <Icon className="h-4 w-4" />
                <span>{label}</span>
              </NavLink>
            ))}
          </>
        )}
      </nav>
    </aside>
  );
}
