import { api } from "@/lib/api";

export type InterviewRound = "l3_hr" | "l4_tech1" | "l5_tech2" | "l6_salary";
export type InterviewMode = "online" | "in_person" | "phone";
export type InterviewStatus =
  | "scheduled"
  | "rescheduled"
  | "completed"
  | "cancelled"
  | "no_show";
export type ScorecardDecision = "strong_yes" | "yes" | "no" | "strong_no";

export const ROUND_LABELS: Record<InterviewRound, string> = {
  l3_hr: "L3 · HR",
  l4_tech1: "L4 · Technical 1",
  l5_tech2: "L5 · Technical 2",
  l6_salary: "L6 · Salary",
};

export const MODE_LABELS: Record<InterviewMode, string> = {
  online: "Online (Teams)",
  in_person: "In person",
  phone: "Phone",
};

export const STATUS_LABELS: Record<InterviewStatus, string> = {
  scheduled: "Scheduled",
  rescheduled: "Rescheduled",
  completed: "Completed",
  cancelled: "Cancelled",
  no_show: "No show",
};

export const DECISION_LABELS: Record<ScorecardDecision, string> = {
  strong_yes: "Strong yes",
  yes: "Yes",
  no: "No",
  strong_no: "Strong no",
};

export const ROUNDS: InterviewRound[] = ["l3_hr", "l4_tech1", "l5_tech2", "l6_salary"];
export const DECISIONS: ScorecardDecision[] = ["strong_yes", "yes", "no", "strong_no"];

export interface ScorecardScore {
  criterion_id: number | null;
  label: string;
  score: number;
  weight: number;
  comment: string | null;
}

export interface Scorecard {
  id: number;
  interview_id: number;
  overall_score: number | null;
  decision: ScorecardDecision;
  strengths: string | null;
  concerns: string | null;
  recommendation: string | null;
  submitted_by_id: number;
  submitted_at: string;
  scores: ScorecardScore[];
}

export interface Interview {
  id: number;
  application_id: number;
  round: InterviewRound;
  mode: InterviewMode;
  scheduled_at: string;
  duration_minutes: number;
  interviewer_id: number;
  rubric_template_id: number | null;
  teams_join_url: string | null;
  location: string | null;
  status: InterviewStatus;
  notes: string | null;
  candidate_id: number;
  candidate_name: string;
  requisition_id: number;
  requisition_title: string;
  interviewer_name: string;
  scorecard: Scorecard | null;
}

export interface RubricCriterion {
  id: number;
  label: string;
  weight: number;
  max_score: number;
  position: number;
}

export interface Rubric {
  id: number;
  name: string;
  round: InterviewRound;
  description: string | null;
  is_active: boolean;
}

export interface RubricDetail extends Rubric {
  criteria: RubricCriterion[];
}

export interface RubricOption {
  id: number;
  name: string;
  round: InterviewRound;
}

export interface UserOption {
  id: number;
  name: string;
  role: string;
}

export interface ScheduleInput {
  round: InterviewRound;
  mode: InterviewMode;
  scheduled_at: string;
  duration_minutes: number;
  interviewer_id: number;
  rubric_template_id: number | null;
  location?: string | null;
  notes?: string | null;
}

export interface ScorecardInput {
  decision: ScorecardDecision;
  strengths: string | null;
  concerns: string | null;
  recommendation: string | null;
  scores: {
    criterion_id: number | null;
    label: string;
    score: number;
    weight: number;
    comment: string | null;
  }[];
}

// --- Interviews ---
export async function fetchTodaysInterviews(): Promise<Interview[]> {
  return (await api.get<Interview[]>("/interviews/today")).data;
}

export async function fetchInterview(id: number): Promise<Interview> {
  return (await api.get<Interview>(`/interviews/${id}`)).data;
}

export async function fetchApplicationInterviews(appId: number): Promise<Interview[]> {
  return (await api.get<Interview[]>(`/applications/${appId}/interviews`)).data;
}

export async function scheduleInterview(
  appId: number,
  input: ScheduleInput,
): Promise<Interview> {
  return (await api.post<Interview>(`/applications/${appId}/interviews`, input)).data;
}

export async function rescheduleInterview(
  id: number,
  scheduledAt: string,
): Promise<Interview> {
  return (await api.post<Interview>(`/interviews/${id}/reschedule`, { scheduled_at: scheduledAt }))
    .data;
}

export async function cancelInterview(id: number): Promise<Interview> {
  return (await api.post<Interview>(`/interviews/${id}/cancel`)).data;
}

export async function submitScorecard(id: number, input: ScorecardInput): Promise<Interview> {
  return (await api.post<Interview>(`/interviews/${id}/scorecard`, input)).data;
}

// --- Rubrics (admin) ---
export async function fetchRubrics(): Promise<Rubric[]> {
  return (await api.get<Rubric[]>("/rubrics")).data;
}

export async function fetchRubric(id: number): Promise<RubricDetail> {
  return (await api.get<RubricDetail>(`/rubrics/${id}`)).data;
}

export async function createRubric(input: {
  name: string;
  round: InterviewRound;
  description: string | null;
}): Promise<Rubric> {
  return (await api.post<Rubric>("/rubrics", input)).data;
}

export async function addCriterion(
  rubricId: number,
  input: { label: string; weight: number; max_score: number },
): Promise<RubricCriterion> {
  return (await api.post<RubricCriterion>(`/rubrics/${rubricId}/criteria`, input)).data;
}

export async function removeCriterion(rubricId: number, criterionId: number): Promise<void> {
  await api.delete(`/rubrics/${rubricId}/criteria/${criterionId}`);
}

// --- Lookups ---
export async function fetchRubricOptions(): Promise<RubricOption[]> {
  return (await api.get<RubricOption[]>("/lookups/rubrics")).data;
}

export async function fetchInterviewerOptions(): Promise<UserOption[]> {
  return (await api.get<UserOption[]>("/lookups/users")).data;
}
