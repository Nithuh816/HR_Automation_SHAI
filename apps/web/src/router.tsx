import { createBrowserRouter, Navigate } from "react-router-dom";

import { RequireAuth } from "@/components/layout/RequireAuth";
import { QuestionsPage } from "@/pages/assessment/QuestionsPage";
import { TemplateDetailPage } from "@/pages/assessment/TemplateDetailPage";
import { TemplatesPage } from "@/pages/assessment/TemplatesPage";
import { CandidateDetailPage } from "@/pages/candidates/CandidateDetailPage";
import { CandidateDocumentsPage } from "@/pages/candidates/CandidateDocumentsPage";
import { CandidateNewPage } from "@/pages/candidates/CandidateNewPage";
import { CandidatesListPage } from "@/pages/candidates/CandidatesListPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { HealthPage } from "@/pages/HealthPage";
import { InterviewDetailPage } from "@/pages/interviews/InterviewDetailPage";
import { InterviewsTodayPage } from "@/pages/interviews/InterviewsTodayPage";
import { AuthCallbackPage } from "@/pages/AuthCallbackPage";
import { LoginPage } from "@/pages/LoginPage";
import { PipelineBoardPage } from "@/pages/pipeline/PipelineBoardPage";
import { PipelineChooserPage } from "@/pages/pipeline/PipelineChooserPage";
import { OffersListPage } from "@/pages/offers/OffersListPage";
import { OfferDetailPage } from "@/pages/offers/OfferDetailPage";
import { NotificationsPage } from "@/pages/notifications/NotificationsPage";
import { OnboardingDetailPage } from "@/pages/onboarding/OnboardingDetailPage";
import { OnboardingQueuePage } from "@/pages/onboarding/OnboardingQueuePage";
import { ReportsPage } from "@/pages/reports/ReportsPage";
import { DocUploadPage } from "@/pages/portal/DocUploadPage";
import { L1ApplyPage } from "@/pages/portal/L1ApplyPage";
import { L2AssessmentPage } from "@/pages/portal/L2AssessmentPage";
import { OfferPage } from "@/pages/portal/OfferPage";
import { RequisitionDetailPage } from "@/pages/requisitions/RequisitionDetailPage";
import { RequisitionInboxPage } from "@/pages/requisitions/RequisitionInboxPage";
import { RequisitionNewPage } from "@/pages/requisitions/RequisitionNewPage";
import { RequisitionsListPage } from "@/pages/requisitions/RequisitionsListPage";
import { ChecklistsPage } from "@/pages/settings/ChecklistsPage";
import { DepartmentsPage } from "@/pages/settings/DepartmentsPage";
import { OfferTemplatesPage } from "@/pages/settings/OfferTemplatesPage";
import { RubricDetailPage } from "@/pages/settings/RubricDetailPage";
import { RubricsPage } from "@/pages/settings/RubricsPage";
import { UsersPage } from "@/pages/settings/UsersPage";

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  { path: "/auth/callback", element: <AuthCallbackPage /> },
  // Candidate-facing, no auth.
  { path: "/c/apply/:token", element: <L1ApplyPage /> },
  { path: "/c/assessment/:token", element: <L2AssessmentPage /> },
  { path: "/c/offer/:token", element: <OfferPage /> },
  { path: "/c/upload/:token", element: <DocUploadPage /> },
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
      { path: "candidates/:id/documents", element: <CandidateDocumentsPage /> },
      { path: "pipeline", element: <PipelineChooserPage /> },
      { path: "pipeline/:reqId", element: <PipelineBoardPage /> },
      { path: "assessment/templates", element: <TemplatesPage /> },
      { path: "assessment/templates/:id", element: <TemplateDetailPage /> },
      { path: "assessment/questions", element: <QuestionsPage /> },
      { path: "interviews/today", element: <InterviewsTodayPage /> },
      { path: "interviews/:id", element: <InterviewDetailPage /> },
      { path: "settings/rubrics", element: <RubricsPage /> },
      { path: "settings/rubrics/:id", element: <RubricDetailPage /> },
      { path: "offers", element: <OffersListPage /> },
      { path: "offers/:id", element: <OfferDetailPage /> },
      { path: "settings/offer-templates", element: <OfferTemplatesPage /> },
      { path: "settings/checklists", element: <ChecklistsPage /> },
      { path: "onboarding/queue", element: <OnboardingQueuePage /> },
      { path: "onboarding/:id", element: <OnboardingDetailPage /> },
      { path: "notifications", element: <NotificationsPage /> },
      { path: "reports", element: <ReportsPage /> },
    ],
  },
  { path: "*", element: <Navigate to="/dashboard" replace /> },
]);
