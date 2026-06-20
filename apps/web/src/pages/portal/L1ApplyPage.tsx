import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useParams } from "react-router-dom";

import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

interface L1Context {
  candidate_name: string;
  requisition_title: string;
  already_submitted: boolean;
  payload: Record<string, unknown> | null;
}

const FIELDS = [
  { key: "father_name", label: "Father's / Guardian's name", type: "text" },
  { key: "date_of_birth", label: "Date of birth", type: "date" },
  { key: "permanent_address", label: "Permanent address", type: "textarea" },
  { key: "highest_qualification", label: "Highest qualification", type: "text" },
  { key: "current_ctc", label: "Current CTC (₹/yr)", type: "number" },
  { key: "expected_ctc", label: "Expected CTC (₹/yr)", type: "number" },
  { key: "notice_period_days", label: "Notice period (days)", type: "number" },
] as const;

const inputClass =
  "w-full rounded-md border border-border bg-transparent px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring";

export function L1ApplyPage(): JSX.Element {
  const { token } = useParams();
  const ctx = useQuery({
    queryKey: ["l1", token],
    queryFn: async () => (await api.get<L1Context>(`/c/l1/${token}`)).data,
    retry: false,
  });

  const [values, setValues] = useState<Record<string, string>>({});
  const [relocate, setRelocate] = useState(false);
  const [done, setDone] = useState(false);

  const submit = useMutation({
    mutationFn: async () => {
      const payload: Record<string, unknown> = { ...values, willing_to_relocate: relocate };
      return (await api.post<L1Context>(`/c/l1/${token}`, { payload })).data;
    },
    onSuccess: () => setDone(true),
  });

  return (
    <div className="min-h-screen bg-background p-4">
      <div className="mx-auto max-w-xl py-8">
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
                This application link is invalid, already used, or expired. Please contact your
                recruiter for a fresh link.
              </CardDescription>
            </CardHeader>
          </Card>
        ) : done || ctx.data?.already_submitted ? (
          <Card>
            <CardHeader>
              <CardTitle>Thank you! 🎉</CardTitle>
              <CardDescription>
                Your application form has been submitted. Our team will be in touch about next
                steps.
              </CardDescription>
            </CardHeader>
          </Card>
        ) : (
          <Card>
            <CardHeader>
              <CardTitle>Application form</CardTitle>
              <CardDescription>
                Hi {ctx.data?.candidate_name} — please complete your application for{" "}
                <strong>{ctx.data?.requisition_title}</strong>.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form
                className="space-y-4"
                onSubmit={(e) => {
                  e.preventDefault();
                  submit.mutate();
                }}
              >
                {FIELDS.map((f) => (
                  <div key={f.key}>
                    <label className="mb-1 block text-xs text-muted-foreground">{f.label}</label>
                    {f.type === "textarea" ? (
                      <textarea
                        rows={3}
                        className={inputClass}
                        value={values[f.key] ?? ""}
                        onChange={(e) => setValues({ ...values, [f.key]: e.target.value })}
                      />
                    ) : (
                      <input
                        type={f.type}
                        className={inputClass}
                        value={values[f.key] ?? ""}
                        onChange={(e) => setValues({ ...values, [f.key]: e.target.value })}
                      />
                    )}
                  </div>
                ))}

                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={relocate}
                    onChange={(e) => setRelocate(e.target.checked)}
                  />
                  I am willing to relocate
                </label>

                {submit.isError && (
                  <p className="text-xs text-destructive">
                    Could not submit. The link may have just expired — please contact your recruiter.
                  </p>
                )}

                <Button type="submit" className="w-full" disabled={submit.isPending}>
                  {submit.isPending ? "Submitting…" : "Submit application"}
                </Button>
              </form>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
