import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Navigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/lib/auth";
import {
  type ChecklistType,
  type DocumentType,
  DOC_TYPES,
  DOC_TYPE_LABELS,
  createChecklistItem,
  deleteChecklistItem,
  fetchChecklistItems,
} from "@/lib/documents";

const CAN_MANAGE = ["hr_head", "ta_tl"];
const inputClass =
  "w-full rounded-md border border-border bg-transparent px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring";
const TYPES: ChecklistType[] = ["fresher", "experienced"];

export function ChecklistsPage(): JSX.Element {
  const { user } = useAuth();
  const qc = useQueryClient();
  const items = useQuery({ queryKey: ["checklist-items"], queryFn: () => fetchChecklistItems() });
  const [form, setForm] = useState<{
    checklist_type: ChecklistType;
    document_type: DocumentType;
    label: string;
    required: boolean;
  }>({ checklist_type: "fresher", document_type: "aadhaar", label: "", required: true });

  const invalidate = () => void qc.invalidateQueries({ queryKey: ["checklist-items"] });
  const create = useMutation({ mutationFn: () => createChecklistItem(form), onSuccess: () => {
    setForm({ ...form, label: "" });
    invalidate();
  } });
  const remove = useMutation({ mutationFn: (id: number) => deleteChecklistItem(id), onSuccess: invalidate });

  if (user && !CAN_MANAGE.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Document checklists</h1>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Add required document</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            className="flex flex-wrap items-end gap-3"
            onSubmit={(e) => {
              e.preventDefault();
              create.mutate();
            }}
          >
            <div className="w-40">
              <label className="mb-1 block text-xs text-muted-foreground">Checklist</label>
              <select
                className={inputClass}
                value={form.checklist_type}
                onChange={(e) =>
                  setForm({ ...form, checklist_type: e.target.value as ChecklistType })
                }
              >
                {TYPES.map((t) => (
                  <option key={t} value={t} className="bg-card">
                    {t}
                  </option>
                ))}
              </select>
            </div>
            <div className="w-44">
              <label className="mb-1 block text-xs text-muted-foreground">Type</label>
              <select
                className={inputClass}
                value={form.document_type}
                onChange={(e) =>
                  setForm({ ...form, document_type: e.target.value as DocumentType })
                }
              >
                {DOC_TYPES.map((t) => (
                  <option key={t} value={t} className="bg-card">
                    {DOC_TYPE_LABELS[t]}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex-1">
              <label className="mb-1 block text-xs text-muted-foreground">Label</label>
              <input
                className={inputClass}
                required
                value={form.label}
                onChange={(e) => setForm({ ...form, label: e.target.value })}
              />
            </div>
            <label className="flex items-center gap-2 pb-2 text-sm">
              <input
                type="checkbox"
                checked={form.required}
                onChange={(e) => setForm({ ...form, required: e.target.checked })}
              />
              Required
            </label>
            <Button type="submit" disabled={create.isPending}>
              Add
            </Button>
          </form>
        </CardContent>
      </Card>

      {TYPES.map((t) => (
        <Card key={t}>
          <CardHeader>
            <CardTitle className="text-base capitalize">{t}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {items.data?.filter((i) => i.checklist_type === t).length === 0 && (
              <p className="text-sm text-muted-foreground">No items.</p>
            )}
            {items.data
              ?.filter((i) => i.checklist_type === t)
              .map((i) => (
                <div
                  key={i.id}
                  className="flex items-center justify-between gap-3 rounded-md border border-border/50 p-2 text-sm"
                >
                  <span>
                    {i.label}{" "}
                    <span className="text-xs text-muted-foreground">
                      ({DOC_TYPE_LABELS[i.document_type]}
                      {i.required ? ", required" : ", optional"})
                    </span>
                  </span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => remove.mutate(i.id)}
                    disabled={remove.isPending}
                  >
                    Remove
                  </Button>
                </div>
              ))}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
