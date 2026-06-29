import { api } from "@/lib/api";

export interface AuditEntry {
  id: number;
  actor_user_id: number | null;
  actor_label: string;
  action: string;
  entity_type: string;
  entity_id: number | null;
  summary: string | null;
  meta: Record<string, unknown> | null;
  created_at: string;
}

export async function fetchAuditLog(params?: {
  entity_type?: string;
  action?: string;
  limit?: number;
}): Promise<AuditEntry[]> {
  return (await api.get<AuditEntry[]>("/audit-log", { params })).data;
}
