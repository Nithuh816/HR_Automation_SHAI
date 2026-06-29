import { api } from "@/lib/api";

export type OnboardingStatus = "pending" | "pushed" | "failed" | "joined";

export const ONBOARDING_STATUS_LABELS: Record<OnboardingStatus, string> = {
  pending: "Pending",
  pushed: "Pushed to GreytHR",
  failed: "Failed",
  joined: "Joined",
};

export type OfferStatus =
  | "draft"
  | "pending_approval"
  | "approved"
  | "sent"
  | "accepted"
  | "declined"
  | "revoked";

export interface OnboardingQueueItem {
  application_id: number;
  candidate_id: number;
  candidate_name: string;
  requisition_id: number;
  requisition_title: string;
  designation: string;
  joining_date: string;
  offer_status: OfferStatus;
  handoff_id: number | null;
  handoff_status: OnboardingStatus | null;
  greythr_employee_id: string | null;
  documents_required: number;
  documents_verified: number;
}

export interface OnboardingDetail {
  id: number;
  application_id: number;
  status: OnboardingStatus;
  greythr_employee_id: string | null;
  retries: number;
  last_error: string | null;
  pushed_at: string | null;
  joined_at: string | null;
  created_by_id: number;
  candidate_id: number;
  candidate_name: string;
  candidate_email: string;
  requisition_id: number;
  requisition_title: string;
  designation: string;
  annual_ctc: number;
  joining_date: string;
  documents_required: number;
  documents_verified: number;
}

export function formatINR(n: number): string {
  return `₹${n.toLocaleString("en-IN")}`;
}

export async function fetchOnboardingQueue(): Promise<OnboardingQueueItem[]> {
  return (await api.get<OnboardingQueueItem[]>("/onboarding/queue")).data;
}

export async function fetchHandoff(id: number): Promise<OnboardingDetail> {
  return (await api.get<OnboardingDetail>(`/onboarding/${id}`)).data;
}

export async function pushToGreytHR(appId: number): Promise<OnboardingDetail> {
  return (await api.post<OnboardingDetail>(`/onboarding/applications/${appId}/push`)).data;
}

export async function confirmJoining(handoffId: number): Promise<OnboardingDetail> {
  return (await api.post<OnboardingDetail>(`/onboarding/${handoffId}/confirm-joining`)).data;
}
