import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Navigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/lib/auth";
import { createQuestion, fetchQuestions } from "@/lib/assessments";

const CAN_MANAGE = ["hr_head", "ta_tl"];
const inputClass =
  "w-full rounded-md border border-border bg-transparent px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring";

const EMPTY = { text: "", options: ["", "", "", ""], correct: 0, category: "", points: "1" };

export function QuestionsPage(): JSX.Element {
  const { user } = useAuth();
  const qc = useQueryClient();
  const questions = useQuery({ queryKey: ["questions"], queryFn: fetchQuestions });
  const [form, setForm] = useState(EMPTY);
  const [error, setError] = useState<string | null>(null);

  const create = useMutation({
    mutationFn: () => {
      const options = form.options.map((o) => o.trim()).filter(Boolean);
      return createQuestion({
        text: form.text,
        options,
        correct_index: form.correct,
        category: form.category || null,
        points: Number(form.points) || 1,
      });
    },
    onSuccess: () => {
      setForm(EMPTY);
      setError(null);
      void qc.invalidateQueries({ queryKey: ["questions"] });
    },
    onError: () => setError("Could not save. Need ≥2 options and a valid correct answer."),
  });

  if (user && !CAN_MANAGE.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Question bank</h1>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">New question</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            className="space-y-4"
            onSubmit={(e) => {
              e.preventDefault();
              create.mutate();
            }}
          >
            <div>
              <label className="mb-1 block text-xs text-muted-foreground">Question</label>
              <textarea
                rows={2}
                required
                className={inputClass}
                value={form.text}
                onChange={(e) => setForm({ ...form, text: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <label className="block text-xs text-muted-foreground">
                Options (select the correct one)
              </label>
              {form.options.map((opt, i) => (
                <div key={i} className="flex items-center gap-2">
                  <input
                    type="radio"
                    name="correct"
                    checked={form.correct === i}
                    onChange={() => setForm({ ...form, correct: i })}
                  />
                  <input
                    className={inputClass}
                    placeholder={`Option ${String.fromCharCode(65 + i)}`}
                    value={opt}
                    onChange={(e) => {
                      const options = [...form.options];
                      options[i] = e.target.value;
                      setForm({ ...form, options });
                    }}
                  />
                </div>
              ))}
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="mb-1 block text-xs text-muted-foreground">Category</label>
                <input
                  className={inputClass}
                  value={form.category}
                  onChange={(e) => setForm({ ...form, category: e.target.value })}
                />
              </div>
              <div>
                <label className="mb-1 block text-xs text-muted-foreground">Points</label>
                <input
                  type="number"
                  min={1}
                  className={inputClass}
                  value={form.points}
                  onChange={(e) => setForm({ ...form, points: e.target.value })}
                />
              </div>
            </div>
            {error && <p className="text-xs text-destructive">{error}</p>}
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? "Saving…" : "Add question"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            All questions {questions.data ? `(${questions.data.length})` : ""}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {questions.isLoading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : questions.data && questions.data.length === 0 ? (
            <p className="text-sm text-muted-foreground">No questions yet.</p>
          ) : (
            questions.data?.map((q) => (
              <div key={q.id} className="rounded-md border border-border/50 p-3 text-sm">
                <div className="font-medium">{q.text}</div>
                <ul className="mt-1 space-y-0.5 text-xs text-muted-foreground">
                  {q.options.map((o, i) => (
                    <li key={i} className={i === q.correct_index ? "text-emerald-400" : ""}>
                      {String.fromCharCode(65 + i)}. {o}
                      {i === q.correct_index ? "  ✓" : ""}
                    </li>
                  ))}
                </ul>
                {q.category && (
                  <span className="mt-1 inline-block text-xs text-muted-foreground">
                    {q.category} · {q.points} pt
                  </span>
                )}
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}
