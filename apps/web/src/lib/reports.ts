import { api } from "@/lib/api";

export interface ReportSummary {
  open_requisitions: number;
  total_candidates: number;
  active_applications: number;
  offers_outstanding: number;
  hires: number;
}

export interface FunnelStage {
  stage: string;
  label: string;
  count: number;
}

export interface FunnelReport {
  stages: FunnelStage[];
  rejected: number;
  total: number;
}

export interface SourceCount {
  source: string;
  label: string;
  count: number;
}

export interface DropOff {
  stage: string;
  label: string;
  count: number;
}

export interface TimeToFillSample {
  requisition_id: number;
  code: string;
  title: string;
  days: number;
}

export interface TimeToFillReport {
  average_days: number | null;
  samples: TimeToFillSample[];
}

export interface RecruiterPerformance {
  recruiter_id: number;
  recruiter_name: string;
  candidates: number;
  offers: number;
  hires: number;
}

export async function fetchSummary(): Promise<ReportSummary> {
  return (await api.get<ReportSummary>("/reports/summary")).data;
}

export async function fetchFunnel(): Promise<FunnelReport> {
  return (await api.get<FunnelReport>("/reports/funnel")).data;
}

export async function fetchSources(): Promise<SourceCount[]> {
  return (await api.get<SourceCount[]>("/reports/sources")).data;
}

export async function fetchDropOffs(): Promise<DropOff[]> {
  return (await api.get<DropOff[]>("/reports/drop-offs")).data;
}

export async function fetchTimeToFill(): Promise<TimeToFillReport> {
  return (await api.get<TimeToFillReport>("/reports/time-to-fill")).data;
}

export async function fetchRecruiterPerformance(): Promise<RecruiterPerformance[]> {
  return (await api.get<RecruiterPerformance[]>("/reports/recruiter-performance")).data;
}
