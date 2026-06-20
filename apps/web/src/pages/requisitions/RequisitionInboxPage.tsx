import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Navigate, Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import {
  URGENCY_LABELS,
  fetchDepartmentOptions,
  fetchInbox,
  fetchRecruiterOptions,
  nameById,
} from "@/lib/requisitions";

const CAN_TRIAGE = ["hr_head", "ta_tl"];
const selectClass =
  "rounded-md border border-border bg-transparent px-2 py-1 text-xs outline-none focus-visible:ring-2 focus-visible:ring-ring";

export function RequisitionInboxPage(): JSX.Element {
  const { user } = useAuth();
  const qc = useQueryClient();
  const [pick, setPick] = useState<Record<number, string>>({});

  const inbox = useQuery({ queryKey: ["req-inbox"], queryFn: fetchInbox });
  const depts = useQuery({ queryKey: ["lookup-depts"], queryFn: fetchDepartmentOptions });
  const recruiters = useQuery({ queryKey: ["lookup-recruiters"], queryFn: fetchRecruiterOptions });

  const assign = useMutation({
    mutationFn: ({ id, recruiterId }: { id: number; recruiterId: number }) =>
      api.post(`/requisitions/${id}/assign`, { recruiter_id: recruiterId }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["req-inbox"] });
      void qc.invalidateQueries({ queryKey: ["requisitions"] });
      void qc.invalidateQueries({ queryKey: ["req-summary"] });
    },
  });

  if (user && !CAN_TRIAGE.includes(user.role)) {
    return <Navigate to="/requisitions" replace />;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Triage inbox</h1>
        <Button variant="outline" asChild>
          <Link to="/requisitions">All requisitions</Link>
        </Button>
      </div>

      <Card>
        <CardContent className="pt-6">
          {inbox.isLoading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : inbox.data && inbox.data.length === 0 ? (
            <p className="text-sm text-muted-foreground">Nothing to triage. 🎉</p>
          ) : (
            <div className="space-y-3">
              {inbox.data?.map((r) => (
                <div
                  key={r.id}
                  className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-border/50 p-3"
                >
                  <div className="min-w-0">
                    <Link
                      to={`/requisitions/${r.id}`}
                      className="font-medium text-foreground hover:underline"
                    >
                      {r.title}
                    </Link>
                    <div className="text-xs text-muted-foreground">
                      {r.code} · {nameById(depts.data, r.department_id)} · {r.headcount} head(s) ·{" "}
                      {URGENCY_LABELS[r.urgency]}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <select
                      className={selectClass}
                      value={pick[r.id] ?? ""}
                      onChange={(e) => setPick({ ...pick, [r.id]: e.target.value })}
                    >
                      <option value="" className="bg-card">
                        Assign to…
                      </option>
                      {recruiters.data?.map((u) => (
                        <option key={u.id} value={u.id} className="bg-card">
                          {u.name}
                        </option>
                      ))}
                    </select>
                    <Button
                      size="sm"
                      disabled={!pick[r.id] || assign.isPending}
                      onClick={() =>
                        assign.mutate({ id: r.id, recruiterId: Number(pick[r.id]) })
                      }
                    >
                      Assign
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
