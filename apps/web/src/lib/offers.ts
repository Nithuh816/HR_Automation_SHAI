import { api } from "@/lib/api";

export type OfferStatus =
  | "draft"
  | "pending_approval"
  | "approved"
  | "sent"
  | "accepted"
  | "declined"
  | "revoked";

export const OFFER_STATUS_LABELS: Record<OfferStatus, string> = {
  draft: "Draft",
  pending_approval: "Pending approval",
  approved: "Approved",
  sent: "Sent",
  accepted: "Accepted",
  declined: "Declined",
  revoked: "Revoked",
};

export interface SalaryComponent {
  label: string;
  annual: number;
  monthly: number;
}

export interface Offer {
  id: number;
  application_id: number;
  template_id: number | null;
  designation: string;
  annual_ctc: number;
  joining_date: string;
  notes: string | null;
  status: OfferStatus;
  created_by_id: number;
  approved_by_id: number | null;
  approved_at: string | null;
  sent_at: string | null;
  responded_at: string | null;
  decline_reason: string | null;
  candidate_id: number;
  candidate_name: string;
  requisition_id: number;
  requisition_title: string;
  components: SalaryComponent[];
}

export interface OfferTemplate {
  id: number;
  name: string;
  subject: string;
  body_md: string;
  is_active: boolean;
}

export interface TemplateOption {
  id: number;
  name: string;
}

export interface SendResult {
  url: string;
  expires_at: string;
  offer: Offer;
}

export interface PublicOffer {
  candidate_name: string;
  designation: string;
  employer: string;
  annual_ctc: number;
  joining_date: string;
  components: SalaryComponent[];
  subject: string;
  letter_html: string;
  status: OfferStatus;
  already_responded: boolean;
}

export function formatINR(n: number): string {
  return `₹${n.toLocaleString("en-IN")}`;
}

// --- Offers (internal) ---
export async function fetchOffers(): Promise<Offer[]> {
  return (await api.get<Offer[]>("/offers")).data;
}

export async function fetchOffer(id: number): Promise<Offer> {
  return (await api.get<Offer>(`/offers/${id}`)).data;
}

export async function fetchApplicationOffers(appId: number): Promise<Offer[]> {
  return (await api.get<Offer[]>(`/applications/${appId}/offers`)).data;
}

export async function createOffer(
  appId: number,
  input: { annual_ctc: number; joining_date: string; designation?: string; template_id?: number | null },
): Promise<Offer> {
  return (await api.post<Offer>(`/applications/${appId}/offers`, input)).data;
}

export async function updateOffer(
  id: number,
  input: Partial<{ annual_ctc: number; joining_date: string; designation: string; template_id: number | null; notes: string | null }>,
): Promise<Offer> {
  return (await api.patch<Offer>(`/offers/${id}`, input)).data;
}

export async function submitOffer(id: number): Promise<Offer> {
  return (await api.post<Offer>(`/offers/${id}/submit`)).data;
}

export async function approveOffer(id: number): Promise<Offer> {
  return (await api.post<Offer>(`/offers/${id}/approve`)).data;
}

export async function sendOffer(id: number): Promise<SendResult> {
  return (await api.post<SendResult>(`/offers/${id}/send`)).data;
}

export async function revokeOffer(id: number): Promise<Offer> {
  return (await api.post<Offer>(`/offers/${id}/revoke`)).data;
}

export async function fetchOfferLetter(id: number): Promise<string> {
  return (await api.get<string>(`/offers/${id}/letter`, { responseType: "text" })).data;
}

// --- Offer templates (admin) ---
export async function fetchOfferTemplates(): Promise<OfferTemplate[]> {
  return (await api.get<OfferTemplate[]>("/offer-templates")).data;
}

export async function createOfferTemplate(input: {
  name: string;
  subject: string;
  body_md: string;
}): Promise<OfferTemplate> {
  return (await api.post<OfferTemplate>("/offer-templates", input)).data;
}

export async function fetchOfferTemplateOptions(): Promise<TemplateOption[]> {
  return (await api.get<TemplateOption[]>("/lookups/offer-templates")).data;
}

// --- Candidate-facing (token, no account) ---
export async function fetchPublicOffer(token: string): Promise<PublicOffer> {
  return (await api.get<PublicOffer>(`/c/offer/${token}`)).data;
}

export async function acceptOffer(token: string): Promise<{ status: OfferStatus }> {
  return (await api.post<{ status: OfferStatus }>(`/c/offer/${token}/accept`)).data;
}

export async function declineOffer(
  token: string,
  reason: string,
): Promise<{ status: OfferStatus }> {
  return (await api.post<{ status: OfferStatus }>(`/c/offer/${token}/decline`, { reason })).data;
}
