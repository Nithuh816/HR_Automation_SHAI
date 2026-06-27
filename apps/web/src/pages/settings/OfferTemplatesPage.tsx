import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Navigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/lib/auth";
import { createOfferTemplate, fetchOfferTemplates } from "@/lib/offers";

const CAN_MANAGE = ["hr_head", "ta_tl"];
const inputClass =
  "w-full rounded-md border border-border bg-transparent px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring";

const PLACEHOLDER_HELP =
  "Placeholders: {{ candidate_name }}, {{ designation }}, {{ annual_ctc }}, {{ joining_date }}, {{ employer }}";

export function OfferTemplatesPage(): JSX.Element {
  const { user } = useAuth();
  const qc = useQueryClient();
  const templates = useQuery({ queryKey: ["offer-templates"], queryFn: fetchOfferTemplates });
  const [form, setForm] = useState({ name: "", subject: "", body_md: "" });
  const [error, setError] = useState<string | null>(null);

  const create = useMutation({
    mutationFn: () => createOfferTemplate(form),
    onSuccess: () => {
      setForm({ name: "", subject: "", body_md: "" });
      setError(null);
      void qc.invalidateQueries({ queryKey: ["offer-templates"] });
    },
    onError: () => setError("Could not create template (duplicate name?)."),
  });

  if (user && !CAN_MANAGE.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Offer letter templates</h1>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">New template</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            className="space-y-3"
            onSubmit={(e) => {
              e.preventDefault();
              create.mutate();
            }}
          >
            <div className="flex flex-wrap gap-3">
              <div className="flex-1">
                <label className="mb-1 block text-xs text-muted-foreground">Name</label>
                <input
                  className={inputClass}
                  required
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                />
              </div>
              <div className="flex-1">
                <label className="mb-1 block text-xs text-muted-foreground">Subject</label>
                <input
                  className={inputClass}
                  required
                  value={form.subject}
                  onChange={(e) => setForm({ ...form, subject: e.target.value })}
                />
              </div>
            </div>
            <div>
              <label className="mb-1 block text-xs text-muted-foreground">Letter body</label>
              <textarea
                className={`${inputClass} min-h-[160px] font-mono`}
                required
                value={form.body_md}
                onChange={(e) => setForm({ ...form, body_md: e.target.value })}
              />
              <p className="mt-1 text-xs text-muted-foreground">{PLACEHOLDER_HELP}</p>
            </div>
            <Button type="submit" disabled={create.isPending}>
              Create
            </Button>
            {error && <p className="text-xs text-destructive">{error}</p>}
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-6">
          {templates.isLoading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : templates.data && templates.data.length === 0 ? (
            <p className="text-sm text-muted-foreground">No templates yet.</p>
          ) : (
            <ul className="divide-y divide-border/40">
              {templates.data?.map((t) => (
                <li key={t.id} className="py-3">
                  <div className="font-medium">{t.name}</div>
                  <div className="text-xs text-muted-foreground">{t.subject}</div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
