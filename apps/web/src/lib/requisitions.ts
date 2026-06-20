import { api } from "@/lib/api";

export type RequisitionStatus =
  | "draft"
  | "submitted"
  | "assigned"
  | "on_hold"
  | "filled"
  | "cancelled";

export type Urgency = "low" | "normal" | "high" | "urgent";

export interface Requisition {
  id: number;
  code: string;
  title: string;
  department_id: number;
  jd_md: string | null;
  headcount: number;
  min_experience_years: number | null;
  max_experience_years: number | null;
  min_budget: number | null;
  max_budget: number | null;
  urgency: Urgency;
  status: RequisitionStatus;
  created_by_id: number;
  assigned_recruiter_id: number | null;
  due_by: string | null;
  created_at: string;
}

export interface RequisitionComment {
  id: number;
  requisition_id: number;
  author_id: number;
  body: string;
  created_at: string;
}

export interface RequisitionSummary {
  total: number;
  submitted: number;
  assigned: number;
  on_hold: number;
  filled: number;
  cancelled: number;
  open_headcount: number;
  by_urgency: Record<string, number>;
}

export const STATUS_LABELS: Record<RequisitionStatus, string> = {
  draft: "Draft",
  submitted: "In triage",
  assigned: "Assigned",
  on_hold: "On hold",
  filled: "Filled",
  cancelled: "Cancelled",
};

export const STATUS_BADGE: Record<RequisitionStatus, string> = {
  draft: "bg-secondary text-secondary-foreground",
  submitted: "bg-amber-500/20 text-amber-300",
  assigned: "bg-primary/20 text-primary",
  on_hold: "bg-orange-500/20 text-orange-300",
  filled: "bg-emerald-500/20 text-emerald-300",
  cancelled: "bg-muted text-muted-foreground",
};

export const URGENCY_LABELS: Record<Urgency, string> = {
  low: "Low",
  normal: "Normal",
  high: "High",
  urgent: "Urgent",
};

// Manual status transitions offered in the UI (mirrors backend ALLOWED_TRANSITIONS).
export const NEXT_STATUSES: Record<RequisitionStatus, RequisitionStatus[]> = {
  draft: ["submitted", "cancelled"],
  submitted: ["on_hold", "cancelled"],
  assigned: ["on_hold", "filled", "cancelled", "submitted"],
  on_hold: ["submitted", "cancelled"],
  filled: [],
  cancelled: [],
};

export async function fetchRequisitions(params?: {
  status?: RequisitionStatus;
  mine?: boolean;
}): Promise<Requisition[]> {
  return (await api.get<Requisition[]>("/requisitions", { params })).data;
}

export async function fetchInbox(): Promise<Requisition[]> {
  return (await api.get<Requisition[]>("/requisitions/inbox")).data;
}

export async function fetchRequisition(id: number): Promise<Requisition> {
  return (await api.get<Requisition>(`/requisitions/${id}`)).data;
}

export async function fetchSummary(): Promise<RequisitionSummary> {
  return (await api.get<RequisitionSummary>("/dashboard/requisitions")).data;
}

export interface DepartmentOption {
  id: number;
  name: string;
}

export interface UserOption {
  id: number;
  name: string;
  role: string;
}

export async function fetchDepartmentOptions(): Promise<DepartmentOption[]> {
  return (await api.get<DepartmentOption[]>("/lookups/departments")).data;
}

export async function fetchUserOptions(): Promise<UserOption[]> {
  return (await api.get<UserOption[]>("/lookups/users")).data;
}

export async function fetchRecruiterOptions(): Promise<UserOption[]> {
  return (await api.get<UserOption[]>("/lookups/recruiters")).data;
}

export function nameById(options: UserOption[] | DepartmentOption[] | undefined, id: number | null): string {
  if (id == null) return "—";
  return options?.find((o) => o.id === id)?.name ?? `#${id}`;
}
