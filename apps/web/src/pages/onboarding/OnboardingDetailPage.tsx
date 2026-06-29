import { type ReactNode } from "react";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/lib/auth";
import {
  ONBOARDING_STATUS_LABELS,
  confirmJoining,
  fetchHandoff,
  formatINR,
} from "@/lib/onboarding";

const CAN_ONBOARD = ["hr_head", "pr"];

export function OnboardingDetailPage(): JSX.Element {
  const { id } = useParams();
  const handoffId = Number(id);
  const { user } = useAuth();
  const qc = useQueryClient();
  const handoff = useQuery({
    queryKey: ["onboarding", handoffId],
    queryFn: () => fetchHandoff(handoffId),
  });
  const join = useMutation({
    mutationFn: () => confirmJoining(handoffId),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["onboarding", handoffId] });
      void qc.invalidateQueries({ queryKey: ["onboarding-queue"] });
    },
  });

  if (handoff.isLoading) return <p className="text-sm text-muted-foreground">Loading…</p>;
  if (handoff.isError || !handoff.data)
    return <p className="text-sm text-destructive">Handoff not found.</p>;

  const h = handoff.data;
  const canOnboard = user != null && CAN_ONBOARD.includes(user.role);

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">{h.candidate_name}</h1>
          <p className="text-sm text-muted-foreground">
            {h.designation} · {h.requisition_title}
          </p>
        </div>
        <Link to="/onboarding/queue" className="text-sm text-primary hover:underline">
          ← Back to queue
        </Link>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>GreytHR handoff</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <Field label="Status">
            <span className="rounded-md bg-secondary px-2 py-1 text-xs">
              {ONBOARDING_STATUS_LABELS[h.status]}
            </span>
          </Field>
          <Field label="GreytHR employee ID">{h.greythr_employee_id ?? "—"}</Field>
          <Field label="Joining date">{h.joining_date}</Field>
          <Field label="Annual CTC">{formatINR(h.annual_ctc)}</Field>
          <Field label="Candidate email">{h.candidate_email}</Field>
          <Field label="Documents">
            {h.documents_verified}/{h.documents_required} verified
          </Field>
          {h.last_error && (
            <Field label="Last error">
              <span className="text-destructive">{h.last_error}</span>
            </Field>
          )}
        </CardContent>
      </Card>

      {canOnboard && h.status === "pushed" && (
        <Card>
          <CardContent className="flex items-center justify-between pt-6">
            <p className="text-sm text-muted-foreground">
              Confirm the candidate has joined to complete the pipeline.
            </p>
            <Button disabled={join.isPending} onClick={() => join.mutate()}>
              {join.isPending ? "Confirming…" : "Confirm joining"}
            </Button>
          </CardContent>
        </Card>
      )}
      {h.status === "joined" && (
        <p className="text-sm text-emerald-400">✓ This candidate has joined.</p>
      )}
      {join.isError && <p className="text-sm text-destructive">Could not confirm joining.</p>}
    </div>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }): JSX.Element {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-border/30 pb-2">
      <span className="text-muted-foreground">{label}</span>
      <span className="text-right font-medium">{children}</span>
    </div>
  );
}
