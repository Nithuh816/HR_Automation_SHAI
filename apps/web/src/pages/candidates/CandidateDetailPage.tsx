import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchTemplateOptions, issueAssessment } from "@/lib/assessments";
import { useAuth } from "@/lib/auth";
import {
  SOURCE_LABELS,
  STAGE_LABELS,
  createL1Link,
  fetchCandidate,
  fetchCandidateApplications,
} from "@/lib/candidates";

const CAN_EDIT = ["hr_head", "ta_tl", "ta_recruiter"];

export function CandidateDetailPage(): JSX.Element {
  const { id } = useParams();
  const candidateId = Number(id);
  const { user } = useAuth();
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

  const l1 = useMutation({
    mutationFn: (appId: number) => createL1Link(appId),
    onSuccess: (res) => setLink(res.url),
  });
  const assessment = useMutation({
    mutationFn: ({ appId, templateId }: { appId: number; templateId: number }) =>
      issueAssessment(appId, templateId),
    onSuccess: (res) => setLink(res.url),
  });

  if (cand.isLoading) return <p className="text-sm text-muted-foreground">Loading…</p>;
  if (cand.isError || !cand.data)
    return <p className="text-sm text-destructive">Candidate not found.</p>;

  const c = cand.data;
  const canEdit = user != null && CAN_EDIT.includes(user.role);

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h1 className="text-xl font-semibold">{c.name}</h1>

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
