import { createBrowserRouter, Navigate } from "react-router-dom";

import { AppShell } from "@/components/layout/AppShell";
import { DashboardPage } from "@/pages/DashboardPage";
import { HealthPage } from "@/pages/HealthPage";
import { LoginPage } from "@/pages/LoginPage";

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: "dashboard", element: <DashboardPage /> },
      { path: "health", element: <HealthPage /> },
      // Stubs — pages added per-milestone.
      { path: "requisitions", element: <ComingSoon name="Requisitions (M2)" /> },
      { path: "candidates", element: <ComingSoon name="Candidates (M3)" /> },
      { path: "pipeline", element: <ComingSoon name="Pipeline (M3)" /> },
      { path: "interviews/today", element: <ComingSoon name="Interviews (M5)" /> },
      { path: "offers", element: <ComingSoon name="Offers (M6)" /> },
      { path: "onboarding/queue", element: <ComingSoon name="Onboarding queue (M8)" /> },
      { path: "settings/users", element: <ComingSoon name="Settings (M11)" /> },
    ],
  },
  { path: "*", element: <Navigate to="/dashboard" replace /> },
]);

function ComingSoon({ name }: { name: string }) {
  return (
    <div className="grid h-full place-items-center text-sm text-muted-foreground">
      {name} — coming in a later milestone.
    </div>
  );
}
