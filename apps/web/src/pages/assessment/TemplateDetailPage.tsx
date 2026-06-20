import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  addQuestionToTemplate,
  fetchQuestions,
  fetchTemplate,
  removeQuestionFromTemplate,
} from "@/lib/assessments";

export function TemplateDetailPage(): JSX.Element {
  const { id } = useParams();
  const templateId = Number(id);
  const qc = useQueryClient();
  const [pick, setPick] = useState("");

  const template = useQuery({
    queryKey: ["template", templateId],
    queryFn: () => fetchTemplate(templateId),
  });
  const bank = useQuery({ queryKey: ["questions"], queryFn: fetchQuestions });

  const invalidate = () => void qc.invalidateQueries({ queryKey: ["template", templateId] });
  const add = useMutation({
    mutationFn: (qid: number) => addQuestionToTemplate(templateId, qid),
    onSuccess: () => {
      setPick("");
      invalidate();
    },
  });
  const remove = useMutation({
    mutationFn: (qid: number) => removeQuestionFromTemplate(templateId, qid),
    onSuccess: invalidate,
  });

  if (template.isLoading) return <p className="text-sm text-muted-foreground">Loading…</p>;
  if (template.isError || !template.data)
    return <p className="text-sm text-destructive">Template not found.</p>;

  const t = template.data;
  const inTemplate = new Set(t.questions.map((q) => q.id));
  const available = bank.data?.filter((q) => !inTemplate.has(q.id)) ?? [];

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-xl font-semibold">{t.name}</h1>
        <p className="text-sm text-muted-foreground">
          {t.duration_minutes} min · pass {t.pass_pct}% · {t.questions.length} questions
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Add a question</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <select
              className="flex-1 rounded-md border border-border bg-transparent px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
              value={pick}
              onChange={(e) => setPick(e.target.value)}
            >
              <option value="" className="bg-card">
                Select from bank…
              </option>
              {available.map((q) => (
                <option key={q.id} value={q.id} className="bg-card">
                  {q.text.slice(0, 70)}
                </option>
              ))}
            </select>
            <Button disabled={!pick || add.isPending} onClick={() => add.mutate(Number(pick))}>
              Add
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Questions in this template</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {t.questions.length === 0 ? (
            <p className="text-sm text-muted-foreground">None yet — add some from the bank.</p>
          ) : (
            t.questions.map((q, i) => (
              <div
                key={q.id}
                className="flex items-center justify-between gap-3 rounded-md border border-border/50 p-3 text-sm"
              >
                <span>
                  {i + 1}. {q.text}
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => remove.mutate(q.id)}
                  disabled={remove.isPending}
                >
                  Remove
                </Button>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}
