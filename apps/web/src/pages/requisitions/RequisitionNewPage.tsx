import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import {
  URGENCY_LABELS,
  fetchDepartmentOptions,
  type Requisition,
  type Urgency,
} from "@/lib/requisitions";

const CAN_CREATE = ["hr_head", "dept_head", "ta_tl"];
const inputClass =
  "w-full rounded-md border border-border bg-transparent px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring";

export function RequisitionNewPage(): JSX.Element {
  const { user } = useAuth();
  const navigate = useNavigate();
  const depts = useQuery({ queryKey: ["lookup-depts"], queryFn: fetchDepartmentOptions });

  const [form, setForm] = useState({
    title: "",
    department_id: "",
    headcount: "1",
    urgency: "normal" as Urgency,
    min_experience_years: "",
    max_experience_years: "",
    jd_md: "",
    due_by: "",
  });
  const [error, setError] = useState<string | null>(null);

  const create = useMutation({
    mutationFn: async () => {
      const payload = {
        title: form.title,
        department_id: Number(form.department_id),
        headcount: Number(form.headcount),
        urgency: form.urgency,
        min_experience_years: form.min_experience_years
          ? Number(form.min_experience_years)
          : null,
        max_experience_years: form.max_experience_years
          ? Number(form.max_experience_years)
          : null,
        jd_md: form.jd_md || null,
        due_by: form.due_by || null,
      };
      return (await api.post<Requisition>("/requisitions", payload)).data;
    },
    onSuccess: (req) => navigate(`/requisitions/${req.id}`),
    onError: () => setError("Could not create requisition. Check the fields and try again."),
  });

  if (user && !CAN_CREATE.includes(user.role)) {
    return <Navigate to="/requisitions" replace />;
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-xl font-semibold">New requisition</h1>
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Details</CardTitle>
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
              <label className="mb-1 block text-xs text-muted-foreground">Title</label>
              <input
                className={inputClass}
                required
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
              />
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-xs text-muted-foreground">Department</label>
                <select
                  className={inputClass}
                  required
                  value={form.department_id}
                  onChange={(e) => setForm({ ...form, department_id: e.target.value })}
                >
                  <option value="" className="bg-card">
                    Select…
                  </option>
                  {depts.data?.map((d) => (
                    <option key={d.id} value={d.id} className="bg-card">
                      {d.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs text-muted-foreground">Headcount</label>
                <input
                  type="number"
                  min={1}
                  className={inputClass}
                  value={form.headcount}
                  onChange={(e) => setForm({ ...form, headcount: e.target.value })}
                />
              </div>
              <div>
                <label className="mb-1 block text-xs text-muted-foreground">Urgency</label>
                <select
                  className={inputClass}
                  value={form.urgency}
                  onChange={(e) => setForm({ ...form, urgency: e.target.value as Urgency })}
                >
                  {(Object.keys(URGENCY_LABELS) as Urgency[]).map((u) => (
                    <option key={u} value={u} className="bg-card">
                      {URGENCY_LABELS[u]}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs text-muted-foreground">Target date</label>
                <input
                  type="date"
                  className={inputClass}
                  value={form.due_by}
                  onChange={(e) => setForm({ ...form, due_by: e.target.value })}
                />
              </div>
              <div>
                <label className="mb-1 block text-xs text-muted-foreground">Min experience (yrs)</label>
                <input
                  type="number"
                  min={0}
                  className={inputClass}
                  value={form.min_experience_years}
                  onChange={(e) => setForm({ ...form, min_experience_years: e.target.value })}
                />
              </div>
              <div>
                <label className="mb-1 block text-xs text-muted-foreground">Max experience (yrs)</label>
                <input
                  type="number"
                  min={0}
                  className={inputClass}
                  value={form.max_experience_years}
                  onChange={(e) => setForm({ ...form, max_experience_years: e.target.value })}
                />
              </div>
            </div>

            <div>
              <label className="mb-1 block text-xs text-muted-foreground">
                Job description (markdown)
              </label>
              <textarea
                rows={6}
                className={inputClass}
                value={form.jd_md}
                onChange={(e) => setForm({ ...form, jd_md: e.target.value })}
              />
            </div>

            {error && <p className="text-xs text-destructive">{error}</p>}

            <div className="flex justify-end gap-2">
              <Button type="button" variant="ghost" onClick={() => navigate("/requisitions")}>
                Cancel
              </Button>
              <Button type="submit" disabled={create.isPending}>
                {create.isPending ? "Creating…" : "Create"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
