import { api } from "@/lib/api";

export type Stage =
  | "sourced"
  | "l1_application"
  | "l2_assessment"
  | "l3_hr"
  | "l4_tech1"
  | "l5_tech2"
  | "l6_salary"
  | "offer"
  | "joined";

export type ApplicationStatus = "active" | "rejected" | "withdrawn";

export type CandidateSource =
  | "linkedin"
  | "naukri"
  | "referral"
  | "institution"
  | "cold_call"
  | "other";

export const STAGE_ORDER: Stage[] = [
  "sourced",
  "l1_application",
  "l2_assessment",
  "l3_hr",
  "l4_tech1",
  "l5_tech2",
  "l6_salary",
  "offer",
  "joined",
];

export const STAGE_LABELS: Record<Stage, string> = {
  sourced: "Sourced",
  l1_application: "L1 Application",
  l2_assessment: "L2 Assessment",
  l3_hr: "L3 HR",
  l4_tech1: "L4 Tech 1",
  l5_tech2: "L5 Tech 2",
  l6_salary: "L6 Salary",
  offer: "Offer",
  joined: "Joined",
};

export const SOURCE_LABELS: Record<CandidateSource, string> = {
  linkedin: "LinkedIn",
  naukri: "Naukri",
  referral: "Referral",
  institution: "Institution",
  cold_call: "Cold call",
  other: "Other",
};

export interface Candidate {
  id: number;
  name: string;
  email: string;
  phone: string | null;
  location: string | null;
  is_fresher: boolean;
  total_experience_years: number | null;
  relevant_experience_years: number | null;
  current_company: string | null;
  current_ctc: number | null;
  expected_ctc: number | null;
  notice_period_days: number | null;
  source: CandidateSource;
  referred_by: string | null;
  resume_url: string | null;
  created_by_id: number;
  created_at: string;
}

export interface Application {
  id: number;
  candidate_id: number;
  requisition_id: number;
  stage: Stage;
  status: ApplicationStatus;
  stage_entered_at: string;
  rejection_stage: Stage | null;
  rejection_reason: string | null;
}

export interface PipelineCard {
  application_id: number;
  candidate_id: number;
  candidate_name: string;
  stage: Stage;
  status: ApplicationStatus;
}

export async function fetchCandidates(): Promise<Candidate[]> {
  return (await api.get<Candidate[]>("/candidates")).data;
}

export async function fetchCandidate(id: number): Promise<Candidate> {
  return (await api.get<Candidate>(`/candidates/${id}`)).data;
}

export async function fetchCandidateApplications(id: number): Promise<Application[]> {
  return (await api.get<Application[]>(`/candidates/${id}/applications`)).data;
}

export async function fetchPipeline(reqId: number): Promise<PipelineCard[]> {
  return (await api.get<PipelineCard[]>(`/pipeline/${reqId}`)).data;
}

export async function moveStage(appId: number, stage: Stage): Promise<Application> {
  return (await api.post<Application>(`/applications/${appId}/stage`, { stage })).data;
}

export async function rejectApplication(appId: number, reason: string): Promise<Application> {
  return (await api.post<Application>(`/applications/${appId}/reject`, { reason })).data;
}

export async function createL1Link(appId: number): Promise<{ url: string; expires_at: string }> {
  return (await api.post<{ url: string; expires_at: string }>(`/applications/${appId}/l1-link`)).data;
}
