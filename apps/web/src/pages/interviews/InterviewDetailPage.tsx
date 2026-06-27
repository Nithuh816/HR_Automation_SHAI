import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/lib/auth";
import {
  DECISIONS,
  DECISION_LABELS,
  MODE_LABELS,
  ROUND_LABELS,
  STATUS_LABELS,
  type ScorecardDecision,
  cancelInterview,
  fetchInterview,
  fetchRubric,
  rescheduleInterview,
  submitScorecard,
} from "@/lib/interviews";

const CAN_SCHEDULE = ["hr_head", "ta_tl", "ta_recruiter"];
const inputClass =
  "w-full rounded-md border border-border bg-transparent px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring";

interface ScoreRow {
  criterion_id: number | null;
  label: string;
  weight: number;
  max_score: number;
  score: number;
  comment: string;
}

function formatWhen(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function InterviewDetailPage(): JSX.Element {
  const { id } = useParams();
  const interviewId = Number(id);
  const { user } = useAuth();
  const qc = useQueryClient();

  const interview = useQuery({
    queryKey: ["interview", interviewId],
    queryFn: () => fetchInterview(interviewId),
  });

  const rubricId = interview.data?.rubric_template_id ?? null;
  const rubric = useQuery({
    queryKey: ["rubric", rubricId],
    queryFn: () => fetchRubric(rubricId as number),
    enabled: rubricId != null,
  });

  const invalidate = () => void qc.invalidateQueries({ queryKey: ["interview", interviewId] });
  const reschedule = useMutation({
    mutationFn: (whenLocal: string) =>
      rescheduleInterview(interviewId, new Date(whenLocal).toISOString()),
    onSuccess: invalidate,
  });
  const cancel = useMutation({ mutationFn: () => cancelInterview(interviewId), onSuccess: invalidate });

  const [when, setWhen] = useState("");
  const [decision, setDecision] = useState<ScorecardDecision>("yes");
  const [strengths, setStrengths] = useState("");
  const [concerns, setConcerns] = useState("");
  const [recommendation, setRecommendation] = useState("");
  const [rows, setRows] = useState<ScoreRow[]>([]);

  // Seed the score rows from the rubric once it loads.
  const seededRows = useMemo<ScoreRow[]>(
    () =>
      (rubric.data?.criteria ?? []).map((c) => ({
        criterion_id: c.id,
        label: c.label,
        weight: c.weight,
        max_score: c.max_score,
        score: 0,
        comment: "",
      })),
    [rubric.data],
  );
  const effectiveRows = rows.length > 0 || seededRows.length === 0 ? rows : seededRows;

  const submit = useMutation({
    mutationFn: () =>
      submitScorecard(interviewId, {
        decision,
        strengths: strengths || null,
        concerns: concerns || null,
        recommendation: recommendation || null,
        scores: effectiveRows.map((r) => ({
          criterion_id: r.criterion_id,
          label: r.label,
          score: r.score,
          weight: r.weight,
          comment: r.comment || null,
        })),
      }),
    onSuccess: invalidate,
  });

  if (interview.isLoading) return <p className="text-sm text-muted-foreground">Loading…</p>;
  if (interview.isError || !interview.data)
    return <p className="text-sm text-destructive">Interview not found.</p>;

  const iv = interview.data;
  const canSchedule = user != null && CAN_SCHEDULE.includes(user.role);
  const isInterviewer = user != null && (user.id === iv.interviewer_id || user.role === "hr_head");
  const live = iv.status === "scheduled" || iv.status === "rescheduled";
  const setRow = (idx: number, patch: Partial<ScoreRow>) =>
    setRows(effectiveRows.map((r, i) => (i === idx ? { ...r, ...patch } : r)));

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-xl font-semibold">
          {ROUND_LABELS[iv.round]} — {iv.candidate_name}
        </h1>
        <p className="text-sm text-muted-foreground">
          <Link to={`/candidates/${iv.candidate_id}`} className="text-primary hover:underline">
            {iv.candidate_name}
          </Link>{" "}
          · {iv.requisition_title} · {STATUS_LABELS[iv.status]}
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Details</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-2 gap-y-3 text-sm sm:grid-cols-3">
            <Field label="When" value={formatWhen(iv.scheduled_at)} />
            <Field label="Duration" value={`${iv.duration_minutes} min`} />
            <Field label="Mode" value={MODE_LABELS[iv.mode]} />
            <Field label="Interviewer" value={iv.interviewer_name} />
            <Field label="Location" value={iv.location ?? "—"} />
          </dl>
          {iv.teams_join_url && (
            <a
              href={iv.teams_join_url}
              target="_blank"
              rel="noreferrer"
              className="mt-4 inline-block text-sm text-primary hover:underline"
            >
              Join Teams meeting ↗
            </a>
          )}
        </CardContent>
      </Card>

      {canSchedule && live && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Manage</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap items-end gap-3">
            <div>
              <label className="mb-1 block text-xs text-muted-foreground">Reschedule to</label>
              <input
                type="datetime-local"
                className={inputClass}
                value={when}
                onChange={(e) => setWhen(e.target.value)}
              />
            </div>
            <Button
              variant="secondary"
              disabled={!when || reschedule.isPending}
              onClick={() => reschedule.mutate(when)}
            >
              Reschedule
            </Button>
            <Button variant="outline" disabled={cancel.isPending} onClick={() => cancel.mutate()}>
              Cancel interview
            </Button>
          </CardContent>
        </Card>
      )}

      {iv.scorecard ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Scorecard</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="flex items-center gap-4">
              <span className="rounded-md bg-primary/15 px-2 py-1 text-xs font-medium">
                {DECISION_LABELS[iv.scorecard.decision]}
              </span>
              {iv.scorecard.overall_score != null && (
                <span className="text-muted-foreground">
                  Overall {iv.scorecard.overall_score.toFixed(2)}
                </span>
              )}
            </div>
            {iv.scorecard.scores.length > 0 && (
              <ul className="space-y-1">
                {iv.scorecard.scores.map((s, i) => (
                  <li key={i} className="flex justify-between border-b border-border/30 py-1">
                    <span>{s.label}</span>
                    <span className="text-muted-foreground">
                      {s.score} (×{s.weight})
                    </span>
                  </li>
                ))}
              </ul>
            )}
            {iv.scorecard.strengths && <Para label="Strengths" value={iv.scorecard.strengths} />}
            {iv.scorecard.concerns && <Para label="Concerns" value={iv.scorecard.concerns} />}
            {iv.scorecard.recommendation && (
              <Para label="Recommendation" value={iv.scorecard.recommendation} />
            )}
          </CardContent>
        </Card>
      ) : (
        isInterviewer &&
        iv.status !== "cancelled" && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Submit scorecard</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {effectiveRows.length > 0 && (
                <div className="space-y-2">
                  {effectiveRows.map((r, i) => (
                    <div
                      key={r.criterion_id ?? i}
                      className="flex flex-wrap items-end gap-3 rounded-md border border-border/50 p-3"
                    >
                      <div className="flex-1 text-sm">
                        <div className="font-medium">{r.label}</div>
                        <div className="text-xs text-muted-foreground">
                          weight {r.weight} · max {r.max_score}
                        </div>
                      </div>
                      <div className="w-24">
                        <label className="mb-1 block text-xs text-muted-foreground">Score</label>
                        <input
                          type="number"
                          min={0}
                          max={r.max_score}
                          className={inputClass}
                          value={r.score}
                          onChange={(e) => setRow(i, { score: Number(e.target.value) })}
                        />
                      </div>
                      <input
                        className={`${inputClass} flex-1`}
                        placeholder="Comment (optional)"
                        value={r.comment}
                        onChange={(e) => setRow(i, { comment: e.target.value })}
                      />
                    </div>
                  ))}
                </div>
              )}

              <div className="w-56">
                <label className="mb-1 block text-xs text-muted-foreground">Decision</label>
                <select
                  className={inputClass}
                  value={decision}
                  onChange={(e) => setDecision(e.target.value as ScorecardDecision)}
                >
                  {DECISIONS.map((d) => (
                    <option key={d} value={d} className="bg-card">
                      {DECISION_LABELS[d]}
                    </option>
                  ))}
                </select>
              </div>

              <Textarea label="Strengths" value={strengths} onChange={setStrengths} />
              <Textarea label="Concerns" value={concerns} onChange={setConcerns} />
              <Textarea
                label="Recommendation"
                value={recommendation}
                onChange={setRecommendation}
              />

              <Button disabled={submit.isPending} onClick={() => submit.mutate()}>
                Submit scorecard
              </Button>
              <p className="text-xs text-muted-foreground">
                A “{DECISION_LABELS.yes}” or “{DECISION_LABELS.strong_yes}” advances the candidate;
                a “no” rejects the application.
              </p>
            </CardContent>
          </Card>
        )
      )}
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

function Para({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs uppercase tracking-wide text-muted-foreground">{label}</div>
      <p className="mt-0.5 whitespace-pre-wrap">{value}</p>
    </div>
  );
}

function Textarea({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div>
      <label className="mb-1 block text-xs text-muted-foreground">{label}</label>
      <textarea
        className={`${inputClass} min-h-[64px]`}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}
