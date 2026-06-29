import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchTemplateOptions, issueAssessment } from "@/lib/assessments";
import { useAuth } from "@/lib/auth";
import {
  type Application,
  SOURCE_LABELS,
  STAGE_LABELS,
  createL1Link,
  fetchCandidate,
  fetchCandidateApplications,
  fetchCandidateConsents,
} from "@/lib/candidates";
import {
  type InterviewRound,
  MODE_LABELS,
  ROUNDS,
  ROUND_LABELS,
  STATUS_LABELS,
  fetchApplicationInterviews,
  fetchInterviewerOptions,
  fetchRubricOptions,
  scheduleInterview,
} from "@/lib/interviews";
import { createOffer } from "@/lib/offers";

const CAN_EDIT = ["hr_head", "ta_tl", "ta_recruiter"];

export function CandidateDetailPage(): JSX.Element {
  const { id } = useParams();
  const candidateId = Number(id);
  const { user } = useAuth();
  const navigate = useNavigate();
  const [link, setLink] = useState<string | null>(null);
  const [tplByApp, setTplByApp] = useState<Record<number, string>>({});

  const cand = useQuery({
    queryKey: ["candidate", candidateId],
    queryFn: () => fetchCandidate(candidateId),
  });
  const apps = useQuery({
    queryKey: ["candidate-apps", candidateId],
    queryFn: () => fetchCandidateApplications(candidateId),
  });
  const templates = useQuery({
    queryKey: ["template-options"],
    queryFn: fetchTemplateOptions,
  });
  const consents = useQuery({
    queryKey: ["candidate-consents", candidateId],
    queryFn: () => fetchCandidateConsents(candidateId),
  });

  const l1 = useMutation({
    mutationFn: (appId: number) => createL1Link(appId),
    onSuccess: (res) => setLink(res.url),
  });
  const assessment = useMutation({
    mutationFn: ({ appId, templateId }: { appId: number; templateId: number }) =>
      issueAssessment(appId, templateId),
    onSuccess: (res) => setLink(res.url),
  });
  const buildOffer = useMutation({
    mutationFn: (appId: number) =>
      createOffer(appId, {
        annual_ctc: cand.data?.expected_ctc ?? 600000,
        joining_date: new Date(Date.now() + 30 * 86_400_000).toISOString().slice(0, 10),
      }),
    onSuccess: (offer) => navigate(`/offers/${offer.id}`),
  });

  if (cand.isLoading) return <p className="text-sm text-muted-foreground">Loading…</p>;
  if (cand.isError || !cand.data)
    return <p className="text-sm text-destructive">Candidate not found.</p>;

  const c = cand.data;
  const canEdit = user != null && CAN_EDIT.includes(user.role);

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">{c.name}</h1>
        <Button variant="outline" size="sm" asChild>
          <Link to={`/candidates/${candidateId}/documents`}>Documents</Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Profile</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-2 gap-y-3 text-sm sm:grid-cols-3">
            <Field label="Email" value={c.email} />
            <Field label="Phone" value={c.phone ?? "—"} />
            <Field label="Location" value={c.location ?? "—"} />
            <Field
              label="Experience"
              value={
                c.is_fresher
                  ? "Fresher"
                  : c.total_experience_years != null
                    ? `${c.total_experience_years} yrs`
                    : "—"
              }
            />
            <Field label="Current company" value={c.current_company ?? "—"} />
            <Field
              label="Expected CTC"
              value={c.expected_ctc != null ? `₹${c.expected_ctc.toLocaleString("en-IN")}` : "—"}
            />
            <Field
              label="Notice period"
              value={c.notice_period_days != null ? `${c.notice_period_days} days` : "—"}
            />
            <Field label="Source" value={SOURCE_LABELS[c.source]} />
            <Field label="Referred by" value={c.referred_by ?? "—"} />
          </dl>
          {c.resume_url && (
            <a
              href={c.resume_url}
              target="_blank"
              rel="noreferrer"
              className="mt-4 inline-block text-sm text-primary hover:underline"
            >
              View résumé ↗
            </a>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Applications</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {apps.data && apps.data.length > 0 ? (
            apps.data.map((a) => (
              <div
                key={a.id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-border/50 p-3 text-sm"
              >
                <div>
                  <Link
                    to={`/requisitions/${a.requisition_id}`}
                    className="font-medium text-primary hover:underline"
                  >
                    Requisition #{a.requisition_id}
                  </Link>
                  <div className="text-xs text-muted-foreground">
                    {STAGE_LABELS[a.stage]}
                    {a.status !== "active" ? ` · ${a.status}` : ""}
                  </div>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <Button variant="outline" size="sm" asChild>
                    <Link to={`/pipeline/${a.requisition_id}`}>Pipeline</Link>
                  </Button>
                  {canEdit && a.status === "active" && (
                    <>
                      <Button size="sm" onClick={() => l1.mutate(a.id)} disabled={l1.isPending}>
                        L1 link
                      </Button>
                      <select
                        className="rounded-md border border-border bg-transparent px-2 py-1 text-xs outline-none focus-visible:ring-2 focus-visible:ring-ring"
                        value={tplByApp[a.id] ?? ""}
                        onChange={(e) => setTplByApp({ ...tplByApp, [a.id]: e.target.value })}
                      >
                        <option value="" className="bg-card">
                          L2 template…
                        </option>
                        {templates.data?.map((t) => (
                          <option key={t.id} value={t.id} className="bg-card">
                            {t.name}
                          </option>
                        ))}
                      </select>
                      <Button
                        size="sm"
                        variant="secondary"
                        disabled={!tplByApp[a.id] || assessment.isPending}
                        onClick={() =>
                          assessment.mutate({ appId: a.id, templateId: Number(tplByApp[a.id]) })
                        }
                      >
                        Send L2
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={buildOffer.isPending}
                        onClick={() => buildOffer.mutate(a.id)}
                      >
                        Build offer
                      </Button>
                    </>
                  )}
                </div>
              </div>
            ))
          ) : (
            <p className="text-sm text-muted-foreground">Not attached to any requisition yet.</p>
          )}

          {link && (
            <div className="rounded-md border border-primary/40 bg-primary/10 p-3 text-sm">
              <div className="mb-1 text-xs text-muted-foreground">
                Share this single-use link with the candidate:
              </div>
              <code className="break-all text-xs">{link}</code>
            </div>
          )}
        </CardContent>
      </Card>

      {consents.data && consents.data.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Consent (DPDPA)</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {consents.data.map((cs) => (
              <div key={cs.id} className="rounded-md border border-border/50 p-3 text-sm">
                <div className="flex items-center justify-between">
                  <span className="font-medium capitalize">{cs.purpose}</span>
                  <span className="text-xs text-muted-foreground">
                    {new Date(cs.given_at).toLocaleString()}
                  </span>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">{cs.text}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {canEdit &&
        apps.data
          ?.filter((a) => a.status === "active")
          .map((a) => <InterviewScheduler key={a.id} application={a} />)}
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-muted-foreground">{label}</dt>
      <dd className="mt-0.5">{value}</dd>
    </div>
  );
}

const schedInput =
  "w-full rounded-md border border-border bg-transparent px-2 py-1.5 text-xs outline-none focus-visible:ring-2 focus-visible:ring-ring";

function InterviewScheduler({ application }: { application: Application }): JSX.Element {
  const qc = useQueryClient();
  const appId = application.id;
  const [form, setForm] = useState<{
    round: InterviewRound;
    interviewer_id: string;
    rubric_template_id: string;
    mode: "online" | "in_person" | "phone";
    when: string;
  }>({ round: "l3_hr", interviewer_id: "", rubric_template_id: "", mode: "online", when: "" });

  const interviews = useQuery({
    queryKey: ["app-interviews", appId],
    queryFn: () => fetchApplicationInterviews(appId),
  });
  const interviewers = useQuery({ queryKey: ["interviewers"], queryFn: fetchInterviewerOptions });
  const rubricOptions = useQuery({ queryKey: ["rubric-options"], queryFn: fetchRubricOptions });

  const schedule = useMutation({
    mutationFn: () =>
      scheduleInterview(appId, {
        round: form.round,
        mode: form.mode,
        scheduled_at: new Date(form.when).toISOString(),
        duration_minutes: 45,
        interviewer_id: Number(form.interviewer_id),
        rubric_template_id: form.rubric_template_id ? Number(form.rubric_template_id) : null,
      }),
    onSuccess: () => {
      setForm({ ...form, when: "", interviewer_id: "", rubric_template_id: "" });
      void qc.invalidateQueries({ queryKey: ["app-interviews", appId] });
      void qc.invalidateQueries({ queryKey: ["candidate-apps"] });
    },
  });

  const rubricsForRound = rubricOptions.data?.filter((r) => r.round === form.round) ?? [];
  const canSubmit = form.interviewer_id !== "" && form.when !== "" && !schedule.isPending;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">
          Interviews · Requisition #{application.requisition_id}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {interviews.data && interviews.data.length > 0 ? (
          <ul className="space-y-1">
            {interviews.data.map((iv) => (
              <li key={iv.id}>
                <Link
                  to={`/interviews/${iv.id}`}
                  className="flex items-center justify-between gap-2 rounded-md border border-border/50 p-2 text-xs hover:text-primary"
                >
                  <span>
                    {ROUND_LABELS[iv.round]} · {iv.interviewer_name}
                  </span>
                  <span className="text-muted-foreground">
                    {new Date(iv.scheduled_at).toLocaleDateString()} · {STATUS_LABELS[iv.status]}
                    {iv.scorecard ? " ✓" : ""}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-xs text-muted-foreground">No interviews scheduled yet.</p>
        )}

        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
          <select
            className={schedInput}
            value={form.round}
            onChange={(e) =>
              setForm({ ...form, round: e.target.value as InterviewRound, rubric_template_id: "" })
            }
          >
            {ROUNDS.map((r) => (
              <option key={r} value={r} className="bg-card">
                {ROUND_LABELS[r]}
              </option>
            ))}
          </select>
          <select
            className={schedInput}
            value={form.interviewer_id}
            onChange={(e) => setForm({ ...form, interviewer_id: e.target.value })}
          >
            <option value="" className="bg-card">
              Interviewer…
            </option>
            {interviewers.data?.map((u) => (
              <option key={u.id} value={u.id} className="bg-card">
                {u.name}
              </option>
            ))}
          </select>
          <select
            className={schedInput}
            value={form.mode}
            onChange={(e) =>
              setForm({ ...form, mode: e.target.value as "online" | "in_person" | "phone" })
            }
          >
            {(["online", "in_person", "phone"] as const).map((m) => (
              <option key={m} value={m} className="bg-card">
                {MODE_LABELS[m]}
              </option>
            ))}
          </select>
          <select
            className={schedInput}
            value={form.rubric_template_id}
            onChange={(e) => setForm({ ...form, rubric_template_id: e.target.value })}
          >
            <option value="" className="bg-card">
              Rubric (optional)…
            </option>
            {rubricsForRound.map((r) => (
              <option key={r.id} value={r.id} className="bg-card">
                {r.name}
              </option>
            ))}
          </select>
          <input
            type="datetime-local"
            className={`${schedInput} col-span-2 sm:col-span-1`}
            value={form.when}
            onChange={(e) => setForm({ ...form, when: e.target.value })}
          />
        </div>
        <Button size="sm" disabled={!canSubmit} onClick={() => schedule.mutate()}>
          Schedule interview
        </Button>
      </CardContent>
    </Card>
  );
}
