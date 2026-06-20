import { createBrowserRouter, Navigate } from "react-router-dom";

import { RequireAuth } from "@/components/layout/RequireAuth";
import { DashboardPage } from "@/pages/DashboardPage";
import { HealthPage } from "@/pages/HealthPage";
import { LoginPage } from "@/pages/LoginPage";
import { RequisitionDetailPage } from "@/pages/requisitions/RequisitionDetailPage";
import { RequisitionInboxPage } from "@/pages/requisitions/RequisitionInboxPage";
import { RequisitionNewPage } from "@/pages/requisitions/RequisitionNewPage";
import { RequisitionsListPage } from "@/pages/requisitions/RequisitionsListPage";
import { DepartmentsPage } from "@/pages/settings/DepartmentsPage";
import { UsersPage } from "@/pages/settings/UsersPage";

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  {
    path: "/",
    element: <RequireAuth />,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: "dashboard", element: <DashboardPage /> },
      { path: "health", element: <HealthPage /> },
      { path: "settings/users", element: <UsersPage /> },
      { path: "settings/departments", element: <DepartmentsPage /> },
      { path: "requisitions", element: <RequisitionsListPage /> },
      { path: "requisitions/inbox", element: <RequisitionInboxPage /> },
      { path: "requisitions/new", element: <RequisitionNewPage /> },
      { path: "requisitions/:id", element: <RequisitionDetailPage /> },
      // Stubs — pages added per-milestone.
      { path: "candidates", element: <ComingSoon name="Candidates (M3)" /> },
      { path: "pipeline", element: <ComingSoon name="Pipeline (M3)" /> },
      { path: "interviews/today", element: <ComingSoon name="Interviews (M5)" /> },
      { path: "offers", element: <ComingSoon name="Offers (M6)" /> },
      { path: "onboarding/queue", element: <ComingSoon name="Onboarding queue (M8)" /> },
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
