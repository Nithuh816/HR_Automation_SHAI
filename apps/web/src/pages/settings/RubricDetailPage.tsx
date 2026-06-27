import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Navigate, useParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/lib/auth";
import { ROUND_LABELS, addCriterion, fetchRubric, removeCriterion } from "@/lib/interviews";

const CAN_MANAGE = ["hr_head", "ta_tl"];
const inputClass =
  "w-full rounded-md border border-border bg-transparent px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring";

export function RubricDetailPage(): JSX.Element {
  const { id } = useParams();
  const rubricId = Number(id);
  const { user } = useAuth();
  const qc = useQueryClient();
  const [form, setForm] = useState({ label: "", weight: "1", max_score: "5" });

  const rubric = useQuery({
    queryKey: ["rubric", rubricId],
    queryFn: () => fetchRubric(rubricId),
  });

  const invalidate = () => void qc.invalidateQueries({ queryKey: ["rubric", rubricId] });
  const add = useMutation({
    mutationFn: () =>
      addCriterion(rubricId, {
        label: form.label,
        weight: Number(form.weight) || 1,
        max_score: Number(form.max_score) || 5,
      }),
    onSuccess: () => {
      setForm({ label: "", weight: "1", max_score: "5" });
      invalidate();
    },
  });
  const remove = useMutation({
    mutationFn: (cid: number) => removeCriterion(rubricId, cid),
    onSuccess: invalidate,
  });

  if (user && !CAN_MANAGE.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }
  if (rubric.isLoading) return <p className="text-sm text-muted-foreground">Loading…</p>;
  if (rubric.isError || !rubric.data)
    return <p className="text-sm text-destructive">Rubric not found.</p>;

  const r = rubric.data;
  const totalWeight = r.criteria.reduce((sum, c) => sum + c.weight, 0);

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-xl font-semibold">{r.name}</h1>
        <p className="text-sm text-muted-foreground">
          {ROUND_LABELS[r.round]} · {r.criteria.length} criteria · total weight {totalWeight}
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Add a criterion</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            className="flex flex-wrap items-end gap-3"
            onSubmit={(e) => {
              e.preventDefault();
              add.mutate();
            }}
          >
            <div className="flex-1">
              <label className="mb-1 block text-xs text-muted-foreground">Label</label>
              <input
                className={inputClass}
                required
                value={form.label}
                onChange={(e) => setForm({ ...form, label: e.target.value })}
              />
            </div>
            <div className="w-24">
              <label className="mb-1 block text-xs text-muted-foreground">Weight</label>
              <input
                type="number"
                min={1}
                className={inputClass}
                value={form.weight}
                onChange={(e) => setForm({ ...form, weight: e.target.value })}
              />
            </div>
            <div className="w-28">
              <label className="mb-1 block text-xs text-muted-foreground">Max score</label>
              <input
                type="number"
                min={1}
                className={inputClass}
                value={form.max_score}
                onChange={(e) => setForm({ ...form, max_score: e.target.value })}
              />
            </div>
            <Button type="submit" disabled={!form.label || add.isPending}>
              Add
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Criteria</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {r.criteria.length === 0 ? (
            <p className="text-sm text-muted-foreground">None yet — add the first one above.</p>
          ) : (
            r.criteria.map((c, i) => (
              <div
                key={c.id}
                className="flex items-center justify-between gap-3 rounded-md border border-border/50 p-3 text-sm"
              >
                <span>
                  {i + 1}. {c.label}
                </span>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-muted-foreground">
                    weight {c.weight} · /{c.max_score}
                  </span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => remove.mutate(c.id)}
                    disabled={remove.isPending}
                  >
                    Remove
                  </Button>
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}
