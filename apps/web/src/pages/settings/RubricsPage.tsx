import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, Navigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/lib/auth";
import {
  type InterviewRound,
  ROUND_LABELS,
  ROUNDS,
  createRubric,
  fetchRubrics,
} from "@/lib/interviews";

const CAN_MANAGE = ["hr_head", "ta_tl"];
const inputClass =
  "w-full rounded-md border border-border bg-transparent px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring";

export function RubricsPage(): JSX.Element {
  const { user } = useAuth();
  const qc = useQueryClient();
  const rubrics = useQuery({ queryKey: ["rubrics"], queryFn: fetchRubrics });
  const [form, setForm] = useState<{ name: string; round: InterviewRound }>({
    name: "",
    round: "l4_tech1",
  });
  const [error, setError] = useState<string | null>(null);

  const create = useMutation({
    mutationFn: () => createRubric({ name: form.name, round: form.round, description: null }),
    onSuccess: () => {
      setForm({ name: "", round: "l4_tech1" });
      setError(null);
      void qc.invalidateQueries({ queryKey: ["rubrics"] });
    },
    onError: () => setError("Could not create rubric (duplicate name?)."),
  });

  if (user && !CAN_MANAGE.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Interview rubrics</h1>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">New rubric</CardTitle>
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
            <div className="w-48">
              <label className="mb-1 block text-xs text-muted-foreground">Round</label>
              <select
                className={inputClass}
                value={form.round}
                onChange={(e) => setForm({ ...form, round: e.target.value as InterviewRound })}
              >
                {ROUNDS.map((r) => (
                  <option key={r} value={r} className="bg-card">
                    {ROUND_LABELS[r]}
                  </option>
                ))}
              </select>
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
          {rubrics.isLoading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : rubrics.data && rubrics.data.length === 0 ? (
            <p className="text-sm text-muted-foreground">No rubrics yet.</p>
          ) : (
            <ul className="divide-y divide-border/40">
              {rubrics.data?.map((r) => (
                <li key={r.id}>
                  <Link
                    to={`/settings/rubrics/${r.id}`}
                    className="flex items-center justify-between py-3 hover:text-primary"
                  >
                    <span className="font-medium">{r.name}</span>
                    <span className="text-xs text-muted-foreground">
                      {ROUND_LABELS[r.round]}
                      {r.is_active ? "" : " · inactive"}
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
