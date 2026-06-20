import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";

import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

interface PublicQuestion {
  id: number;
  text: string;
  options: string[];
}
interface AssessmentContext {
  template_name: string;
  candidate_name: string;
  duration_minutes: number;
  expires_at: string;
  already_submitted: boolean;
  questions: PublicQuestion[];
}
interface AssessmentResult {
  score_pct: number;
  passed: boolean;
}

function useCountdown(expiresAt: string | undefined): number {
  const [remaining, setRemaining] = useState(0);
  useEffect(() => {
    if (!expiresAt) return;
    const end = new Date(expiresAt).getTime();
    const tick = () => setRemaining(Math.max(0, Math.floor((end - Date.now()) / 1000)));
    tick();
    const t = setInterval(tick, 1000);
    return () => clearInterval(t);
  }, [expiresAt]);
  return remaining;
}

export function L2AssessmentPage(): JSX.Element {
  const { token } = useParams();
  const ctx = useQuery({
    queryKey: ["assessment", token],
    queryFn: async () => (await api.get<AssessmentContext>(`/c/assessment/${token}`)).data,
    retry: false,
  });

  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [result, setResult] = useState<AssessmentResult | null>(null);
  const remaining = useCountdown(ctx.data?.expires_at);
  const submittedRef = useRef(false);

  const submit = useMutation({
    mutationFn: async () => {
      const payload = {
        answers: (ctx.data?.questions ?? []).map((q) => ({
          question_id: q.id,
          selected_index: answers[q.id] ?? null,
        })),
      };
      return (await api.post<AssessmentResult>(`/c/assessment/${token}`, payload)).data;
    },
    onSuccess: (r) => setResult(r),
  });

  // Auto-submit when the timer hits zero.
  useEffect(() => {
    if (
      ctx.data &&
      !ctx.data.already_submitted &&
      !submittedRef.current &&
      ctx.data.expires_at &&
      remaining === 0 &&
      new Date(ctx.data.expires_at).getTime() <= Date.now()
    ) {
      submittedRef.current = true;
      submit.mutate();
    }
  }, [remaining, ctx.data, submit]);

  const mm = String(Math.floor(remaining / 60)).padStart(2, "0");
  const ss = String(remaining % 60).padStart(2, "0");

  return (
    <div className="min-h-screen bg-background p-4">
      <div className="mx-auto max-w-2xl py-8">
        <div className="mb-6 flex items-center gap-2">
          <div className="grid h-9 w-9 place-items-center rounded-md bg-primary text-primary-foreground">
            <span className="text-sm font-bold">HR</span>
          </div>
          <div className="text-sm font-semibold">SHAI Health</div>
        </div>

        {ctx.isLoading ? (
          <Card>
            <CardContent className="pt-6 text-sm text-muted-foreground">Loading…</CardContent>
          </Card>
        ) : ctx.isError ? (
          <Card>
            <CardHeader>
              <CardTitle>Link unavailable</CardTitle>
              <CardDescription>
                This assessment link is invalid, already used, or expired. Please contact your
                recruiter.
              </CardDescription>
            </CardHeader>
          </Card>
        ) : result || ctx.data?.already_submitted ? (
          <Card>
            <CardHeader>
              <CardTitle>Assessment complete 🎉</CardTitle>
              <CardDescription>
                {result
                  ? `You scored ${result.score_pct}%. ${
                      result.passed ? "You've cleared this round." : "Our team will review your result."
                    }`
                  : "You have already completed this assessment."}
              </CardDescription>
            </CardHeader>
          </Card>
        ) : (
          <Card>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle>{ctx.data?.template_name}</CardTitle>
                  <CardDescription>
                    Hi {ctx.data?.candidate_name} — answer all questions before time runs out.
                  </CardDescription>
                </div>
                <div
                  className={`rounded-md px-3 py-1 font-mono text-sm ${
                    remaining < 60 ? "bg-destructive/20 text-destructive" : "bg-secondary"
                  }`}
                >
                  {mm}:{ss}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <form
                className="space-y-6"
                onSubmit={(e) => {
                  e.preventDefault();
                  submittedRef.current = true;
                  submit.mutate();
                }}
              >
                {ctx.data?.questions.map((q, qi) => (
                  <div key={q.id}>
                    <div className="mb-2 text-sm font-medium">
                      {qi + 1}. {q.text}
                    </div>
                    <div className="space-y-1.5">
                      {q.options.map((opt, oi) => (
                        <label key={oi} className="flex items-center gap-2 text-sm">
                          <input
                            type="radio"
                            name={`q-${q.id}`}
                            checked={answers[q.id] === oi}
                            onChange={() => setAnswers({ ...answers, [q.id]: oi })}
                          />
                          {opt}
                        </label>
                      ))}
                    </div>
                  </div>
                ))}
                <Button type="submit" className="w-full" disabled={submit.isPending}>
                  {submit.isPending ? "Submitting…" : "Submit assessment"}
                </Button>
              </form>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
