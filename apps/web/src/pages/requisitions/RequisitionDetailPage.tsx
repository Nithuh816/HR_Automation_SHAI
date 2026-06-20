import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import {
  NEXT_STATUSES,
  STATUS_BADGE,
  STATUS_LABELS,
  URGENCY_LABELS,
  fetchDepartmentOptions,
  fetchRecruiterOptions,
  fetchRequisition,
  fetchUserOptions,
  nameById,
  type RequisitionComment,
  type RequisitionStatus,
} from "@/lib/requisitions";

const CAN_TRIAGE = ["hr_head", "ta_tl"];

export function RequisitionDetailPage(): JSX.Element {
  const { id } = useParams();
  const reqId = Number(id);
  const { user } = useAuth();
  const qc = useQueryClient();
  const [pick, setPick] = useState("");
  const [comment, setComment] = useState("");

  const req = useQuery({
    queryKey: ["requisition", reqId],
    queryFn: () => fetchRequisition(reqId),
  });
  const depts = useQuery({ queryKey: ["lookup-depts"], queryFn: fetchDepartmentOptions });
  const users = useQuery({ queryKey: ["lookup-users"], queryFn: fetchUserOptions });
  const recruiters = useQuery({ queryKey: ["lookup-recruiters"], queryFn: fetchRecruiterOptions });
  const comments = useQuery({
    queryKey: ["req-comments", reqId],
    queryFn: async () =>
      (await api.get<RequisitionComment[]>(`/requisitions/${reqId}/comments`)).data,
  });

  const invalidate = () => {
    void qc.invalidateQueries({ queryKey: ["requisition", reqId] });
    void qc.invalidateQueries({ queryKey: ["requisitions"] });
    void qc.invalidateQueries({ queryKey: ["req-summary"] });
  };

  const assign = useMutation({
    mutationFn: (recruiterId: number) =>
      api.post(`/requisitions/${reqId}/assign`, { recruiter_id: recruiterId }),
    onSuccess: invalidate,
  });
  const changeStatus = useMutation({
    mutationFn: (s: RequisitionStatus) => api.post(`/requisitions/${reqId}/status`, { status: s }),
    onSuccess: invalidate,
  });
  const addComment = useMutation({
    mutationFn: (body: string) => api.post(`/requisitions/${reqId}/comments`, { body }),
    onSuccess: () => {
      setComment("");
      void qc.invalidateQueries({ queryKey: ["req-comments", reqId] });
    },
  });

  if (req.isLoading) return <p className="text-sm text-muted-foreground">Loading…</p>;
  if (req.isError || !req.data)
    return <p className="text-sm text-destructive">Requisition not found.</p>;

  const r = req.data;
  const isTriage = user != null && CAN_TRIAGE.includes(user.role);
  const isOwner = user?.id === r.assigned_recruiter_id;
  const canChangeStatus = isTriage || isOwner;
  const closed = r.status === "filled" || r.status === "cancelled";

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="font-mono text-xs text-muted-foreground">{r.code}</div>
          <h1 className="text-xl font-semibold">{r.title}</h1>
        </div>
        <span className={`rounded-full px-3 py-1 text-xs ${STATUS_BADGE[r.status]}`}>
          {STATUS_LABELS[r.status]}
        </span>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Details</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-2 gap-y-3 text-sm sm:grid-cols-3">
            <Field label="Department" value={nameById(depts.data, r.department_id)} />
            <Field label="Headcount" value={String(r.headcount)} />
            <Field label="Urgency" value={URGENCY_LABELS[r.urgency]} />
            <Field
              label="Experience"
              value={
                r.min_experience_years != null || r.max_experience_years != null
                  ? `${r.min_experience_years ?? 0}–${r.max_experience_years ?? "?"} yrs`
                  : "—"
              }
            />
            <Field label="Target date" value={r.due_by ?? "—"} />
            <Field label="Created by" value={nameById(users.data, r.created_by_id)} />
            <Field label="Recruiter" value={nameById(users.data, r.assigned_recruiter_id)} />
          </dl>
          {r.jd_md && (
            <div className="mt-4">
              <div className="mb-1 text-xs uppercase tracking-wide text-muted-foreground">
                Job description
              </div>
              <p className="whitespace-pre-wrap text-sm">{r.jd_md}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {(isTriage || canChangeStatus) && !closed && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {isTriage && (
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-sm text-muted-foreground">Assign recruiter:</span>
                <select
                  className="rounded-md border border-border bg-transparent px-2 py-1 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  value={pick}
                  onChange={(e) => setPick(e.target.value)}
                >
                  <option value="" className="bg-card">
                    Select…
                  </option>
                  {recruiters.data?.map((u) => (
                    <option key={u.id} value={u.id} className="bg-card">
                      {u.name}
                    </option>
                  ))}
                </select>
                <Button size="sm" disabled={!pick} onClick={() => assign.mutate(Number(pick))}>
                  Assign
                </Button>
              </div>
            )}
            {canChangeStatus && NEXT_STATUSES[r.status].length > 0 && (
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-sm text-muted-foreground">Change status:</span>
                {NEXT_STATUSES[r.status].map((s) => (
                  <Button
                    key={s}
                    size="sm"
                    variant="outline"
                    onClick={() => changeStatus.mutate(s)}
                  >
                    {STATUS_LABELS[s]}
                  </Button>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Comments</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {comments.data && comments.data.length > 0 ? (
            <ul className="space-y-3">
              {comments.data.map((c) => (
                <li key={c.id} className="rounded-md border border-border/40 p-3 text-sm">
                  <div className="mb-1 text-xs text-muted-foreground">
                    {nameById(users.data, c.author_id)} · {new Date(c.created_at).toLocaleString()}
                  </div>
                  <p className="whitespace-pre-wrap">{c.body}</p>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">No comments yet.</p>
          )}
          <form
            className="flex gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              if (comment.trim()) addComment.mutate(comment.trim());
            }}
          >
            <input
              className="flex-1 rounded-md border border-border bg-transparent px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder="Add a comment…"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
            />
            <Button type="submit" disabled={addComment.isPending || !comment.trim()}>
              Post
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-muted-foreground">{label}</dt>
      <dd className="mt-0.5">{value}</dd>
    </div>
  );
}
