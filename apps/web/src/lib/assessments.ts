import { api } from "@/lib/api";

export interface Question {
  id: number;
  text: string;
  options: string[];
  correct_index: number;
  category: string | null;
  points: number;
  is_active: boolean;
}

export interface Template {
  id: number;
  name: string;
  description: string | null;
  duration_minutes: number;
  pass_pct: number;
  is_active: boolean;
}

export interface TemplateDetail extends Template {
  questions: Question[];
}

export interface Attempt {
  id: number;
  application_id: number;
  template_id: number;
  status: "not_started" | "in_progress" | "submitted" | "expired";
  started_at: string | null;
  submitted_at: string | null;
  expires_at: string | null;
  score_pct: number | null;
  passed: boolean | null;
}

export async function fetchQuestions(): Promise<Question[]> {
  return (await api.get<Question[]>("/assessment/questions")).data;
}

export async function createQuestion(input: {
  text: string;
  options: string[];
  correct_index: number;
  category: string | null;
  points: number;
}): Promise<Question> {
  return (await api.post<Question>("/assessment/questions", input)).data;
}

export async function fetchTemplates(): Promise<Template[]> {
  return (await api.get<Template[]>("/assessment/templates")).data;
}

export async function fetchTemplate(id: number): Promise<TemplateDetail> {
  return (await api.get<TemplateDetail>(`/assessment/templates/${id}`)).data;
}

export async function createTemplate(input: {
  name: string;
  description: string | null;
  duration_minutes: number;
  pass_pct: number;
}): Promise<Template> {
  return (await api.post<Template>("/assessment/templates", input)).data;
}

export async function addQuestionToTemplate(templateId: number, questionId: number): Promise<void> {
  await api.post(`/assessment/templates/${templateId}/questions`, { question_id: questionId });
}

export async function removeQuestionFromTemplate(
  templateId: number,
  questionId: number,
): Promise<void> {
  await api.delete(`/assessment/templates/${templateId}/questions/${questionId}`);
}

export async function issueAssessment(
  appId: number,
  templateId: number,
): Promise<{ url: string; expires_at: string }> {
  return (
    await api.post<{ url: string; expires_at: string }>(`/applications/${appId}/assessment`, {
      template_id: templateId,
    })
  ).data;
}

export async function fetchAttempts(appId: number): Promise<Attempt[]> {
  return (await api.get<Attempt[]>(`/applications/${appId}/attempts`)).data;
}
