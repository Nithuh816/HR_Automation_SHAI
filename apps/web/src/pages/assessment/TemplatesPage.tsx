import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, Navigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/lib/auth";
import { createTemplate, fetchTemplates } from "@/lib/assessments";

const CAN_MANAGE = ["hr_head", "ta_tl"];
const inputClass =
  "w-full rounded-md border border-border bg-transparent px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring";

export function TemplatesPage(): JSX.Element {
  const { user } = useAuth();
  const qc = useQueryClient();
  const templates = useQuery({ queryKey: ["templates"], queryFn: fetchTemplates });
  const [form, setForm] = useState({ name: "", duration_minutes: "30", pass_pct: "60" });
  const [error, setError] = useState<string | null>(null);

  const create = useMutation({
    mutationFn: () =>
      createTemplate({
        name: form.name,
        description: null,
        duration_minutes: Number(form.duration_minutes) || 30,
        pass_pct: Number(form.pass_pct) || 60,
      }),
    onSuccess: () => {
      setForm({ name: "", duration_minutes: "30", pass_pct: "60" });
      setError(null);
      void qc.invalidateQueries({ queryKey: ["templates"] });
    },
    onError: () => setError("Could not create template (duplicate name?)."),
  });

  if (user && !CAN_MANAGE.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Assessment templates</h1>
        <Button variant="outline" asChild>
          <Link to="/assessment/questions">Question bank</Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">New template</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            className="flex flex-wrap items-end gap-3"
            onSubmit={(e) => {
              e.preventDefault();
              create.mutate();
            }}
          >
            <div className="flex-1">
              <label className="mb-1 block text-xs text-muted-foreground">Name</label>
              <input
                className={inputClass}
                required
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
            </div>
            <div className="w-32">
              <label className="mb-1 block text-xs text-muted-foreground">Duration (min)</label>
              <input
                type="number"
                min={1}
                className={inputClass}
                value={form.duration_minutes}
                onChange={(e) => setForm({ ...form, duration_minutes: e.target.value })}
              />
            </div>
            <div className="w-28">
              <label className="mb-1 block text-xs text-muted-foreground">Pass %</label>
              <input
                type="number"
                min={0}
                max={100}
                className={inputClass}
                value={form.pass_pct}
                onChange={(e) => setForm({ ...form, pass_pct: e.target.value })}
              />
            </div>
            <Button type="submit" disabled={create.isPending}>
              Create
            </Button>
          </form>
          {error && <p className="mt-2 text-xs text-destructive">{error}</p>}
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
                <li key={t.id}>
                  <Link
                    to={`/assessment/templates/${t.id}`}
                    className="flex items-center justify-between py-3 hover:text-primary"
                  >
                    <span className="font-medium">{t.name}</span>
                    <span className="text-xs text-muted-foreground">
                      {t.duration_minutes} min · pass {t.pass_pct}%
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
