import { createBrowserRouter, Navigate } from "react-router-dom";

import { RequireAuth } from "@/components/layout/RequireAuth";
import { QuestionsPage } from "@/pages/assessment/QuestionsPage";
import { TemplateDetailPage } from "@/pages/assessment/TemplateDetailPage";
import { TemplatesPage } from "@/pages/assessment/TemplatesPage";
import { CandidateDetailPage } from "@/pages/candidates/CandidateDetailPage";
import { CandidateNewPage } from "@/pages/candidates/CandidateNewPage";
import { CandidatesListPage } from "@/pages/candidates/CandidatesListPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { HealthPage } from "@/pages/HealthPage";
import { LoginPage } from "@/pages/LoginPage";
import { PipelineBoardPage } from "@/pages/pipeline/PipelineBoardPage";
import { PipelineChooserPage } from "@/pages/pipeline/PipelineChooserPage";
import { L1ApplyPage } from "@/pages/portal/L1ApplyPage";
import { L2AssessmentPage } from "@/pages/portal/L2AssessmentPage";
import { RequisitionDetailPage } from "@/pages/requisitions/RequisitionDetailPage";
import { RequisitionInboxPage } from "@/pages/requisitions/RequisitionInboxPage";
import { RequisitionNewPage } from "@/pages/requisitions/RequisitionNewPage";
import { RequisitionsListPage } from "@/pages/requisitions/RequisitionsListPage";
import { DepartmentsPage } from "@/pages/settings/DepartmentsPage";
import { UsersPage } from "@/pages/settings/UsersPage";

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  // Candidate-facing, no auth.
  { path: "/c/apply/:token", element: <L1ApplyPage /> },
  { path: "/c/assessment/:token", element: <L2AssessmentPage /> },
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
      { path: "candidates", element: <CandidatesListPage /> },
      { path: "candidates/new", element: <CandidateNewPage /> },
      { path: "candidates/:id", element: <CandidateDetailPage /> },
      { path: "pipeline", element: <PipelineChooserPage /> },
      { path: "pipeline/:reqId", element: <PipelineBoardPage /> },
      { path: "assessment/templates", element: <TemplatesPage /> },
      { path: "assessment/templates/:id", element: <TemplateDetailPage /> },
      { path: "assessment/questions", element: <QuestionsPage /> },
      // Stubs — pages added per-milestone.
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
