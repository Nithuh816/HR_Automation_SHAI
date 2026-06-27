import { api } from "@/lib/api";

export type ChecklistType = "fresher" | "experienced";

export type DocumentType =
  | "aadhaar"
  | "pan"
  | "resume"
  | "marksheet"
  | "experience_letter"
  | "relieving_letter"
  | "payslip"
  | "photo"
  | "bank_proof"
  | "other";

export type DocumentStatus =
  | "pending"
  | "extracted"
  | "needs_review"
  | "verified"
  | "rejected";

export const DOC_TYPE_LABELS: Record<DocumentType, string> = {
  aadhaar: "Aadhaar",
  pan: "PAN",
  resume: "Résumé",
  marksheet: "Marksheet",
  experience_letter: "Experience letter",
  relieving_letter: "Relieving letter",
  payslip: "Payslip",
  photo: "Photo",
  bank_proof: "Bank proof",
  other: "Other",
};

export const DOC_STATUS_LABELS: Record<DocumentStatus, string> = {
  pending: "Pending",
  extracted: "Auto-extracted",
  needs_review: "Needs review",
  verified: "Verified",
  rejected: "Rejected",
};

export const DOC_TYPES: DocumentType[] = [
  "aadhaar",
  "pan",
  "resume",
  "marksheet",
  "experience_letter",
  "relieving_letter",
  "payslip",
  "photo",
  "bank_proof",
  "other",
];

export interface CandidateDocument {
  id: number;
  candidate_id: number;
  application_id: number | null;
  document_type: DocumentType;
  original_filename: string;
  content_type: string;
  size_bytes: number;
  status: DocumentStatus;
  extracted: Record<string, unknown> | null;
  aadhaar_masked: string | null;
  pan_masked: string | null;
  review_note: string | null;
  uploaded_by_id: number | null;
  reviewed_by_id: number | null;
  reviewed_at: string | null;
  created_at: string;
}

export interface ChecklistItem {
  id: number;
  checklist_type: ChecklistType;
  document_type: DocumentType;
  label: string;
  required: boolean;
  position: number;
}

export interface ChecklistOption {
  id: number;
  document_type: DocumentType;
  label: string;
  required: boolean;
}

export interface ChecklistItemPublic {
  document_type: DocumentType;
  label: string;
  required: boolean;
}

export interface UploadedDocPublic {
  id: number;
  document_type: DocumentType;
  original_filename: string;
  status: DocumentStatus;
}

export interface UploadContext {
  candidate_name: string;
  checklist_type: ChecklistType;
  consent_text: string;
  items: ChecklistItemPublic[];
  uploaded: UploadedDocPublic[];
}

// --- Internal documents ---
export async function fetchCandidateDocuments(candidateId: number): Promise<CandidateDocument[]> {
  return (await api.get<CandidateDocument[]>(`/candidates/${candidateId}/documents`)).data;
}

export async function verifyDocument(id: number): Promise<CandidateDocument> {
  return (await api.post<CandidateDocument>(`/documents/${id}/verify`)).data;
}

export async function rejectDocument(id: number, note: string): Promise<CandidateDocument> {
  return (await api.post<CandidateDocument>(`/documents/${id}/reject`, { note })).data;
}

export async function deleteDocument(id: number): Promise<void> {
  await api.delete(`/documents/${id}`);
}

export async function fetchDocumentBlobUrl(id: number): Promise<string> {
  const res = await api.get(`/documents/${id}/file`, { responseType: "blob" });
  return URL.createObjectURL(res.data as Blob);
}

export async function createUploadLink(
  candidateId: number,
): Promise<{ url: string; expires_at: string }> {
  return (
    await api.post<{ url: string; expires_at: string }>(`/candidates/${candidateId}/upload-link`)
  ).data;
}

export async function fetchChecklistOptions(type: ChecklistType): Promise<ChecklistOption[]> {
  return (await api.get<ChecklistOption[]>(`/lookups/checklist?checklist_type=${type}`)).data;
}

// --- Checklist admin ---
export async function fetchChecklistItems(type?: ChecklistType): Promise<ChecklistItem[]> {
  const q = type ? `?checklist_type=${type}` : "";
  return (await api.get<ChecklistItem[]>(`/checklists${q}`)).data;
}

export async function createChecklistItem(input: {
  checklist_type: ChecklistType;
  document_type: DocumentType;
  label: string;
  required: boolean;
}): Promise<ChecklistItem> {
  return (await api.post<ChecklistItem>("/checklists", input)).data;
}

export async function deleteChecklistItem(id: number): Promise<void> {
  await api.delete(`/checklists/${id}`);
}

// --- Candidate upload portal (token) ---
export async function fetchUploadContext(token: string): Promise<UploadContext> {
  return (await api.get<UploadContext>(`/c/upload/${token}`)).data;
}

export async function uploadDocument(
  token: string,
  documentType: DocumentType,
  file: File,
): Promise<UploadContext> {
  const form = new FormData();
  form.append("document_type", documentType);
  form.append("consent", "true");
  form.append("file", file);
  return (await api.post<UploadContext>(`/c/upload/${token}`, form)).data;
}
