import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useAuth } from "@/lib/auth";
import {
  STATUS_BADGE,
  STATUS_LABELS,
  URGENCY_LABELS,
  fetchDepartmentOptions,
  fetchRequisitions,
  fetchUserOptions,
  nameById,
  type RequisitionStatus,
} from "@/lib/requisitions";

const CAN_CREATE = ["hr_head", "dept_head", "ta_tl"];
const CAN_TRIAGE = ["hr_head", "ta_tl"];
const STATUS_FILTERS: (RequisitionStatus | "all")[] = [
  "all",
  "submitted",
  "assigned",
  "on_hold",
  "filled",
  "cancelled",
];

export function RequisitionsListPage(): JSX.Element {
  const { user } = useAuth();
  const [filter, setFilter] = useState<RequisitionStatus | "all">("all");

  const reqs = useQuery({
    queryKey: ["requisitions", filter],
    queryFn: () => fetchRequisitions(filter === "all" ? {} : { status: filter }),
  });
  const depts = useQuery({ queryKey: ["lookup-depts"], queryFn: fetchDepartmentOptions });
  const users = useQuery({ queryKey: ["lookup-users"], queryFn: fetchUserOptions });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Requisitions</h1>
        <div className="flex gap-2">
          {user && CAN_TRIAGE.includes(user.role) && (
            <Button variant="outline" asChild>
              <Link to="/requisitions/inbox">Triage inbox</Link>
            </Button>
          )}
          {user && CAN_CREATE.includes(user.role) && (
            <Button asChild>
              <Link to="/requisitions/new">New requisition</Link>
            </Button>
          )}
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {STATUS_FILTERS.map((s) => (
          <button
            key={s}
            onClick={() => setFilter(s)}
            className={`rounded-full px-3 py-1 text-xs ${
              filter === s
                ? "bg-primary text-primary-foreground"
                : "bg-secondary text-muted-foreground hover:text-foreground"
            }`}
          >
            {s === "all" ? "All" : STATUS_LABELS[s]}
          </button>
        ))}
      </div>

      <Card>
        <CardContent className="pt-6">
          {reqs.isLoading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : reqs.data && reqs.data.length === 0 ? (
            <p className="text-sm text-muted-foreground">No requisitions.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-xs uppercase tracking-wide text-muted-foreground">
                  <tr className="border-b border-border/60">
                    <th className="py-2 pr-4">Code</th>
                    <th className="py-2 pr-4">Title</th>
                    <th className="py-2 pr-4">Department</th>
                    <th className="py-2 pr-4">Heads</th>
                    <th className="py-2 pr-4">Urgency</th>
                    <th className="py-2 pr-4">Status</th>
                    <th className="py-2 pr-4">Recruiter</th>
                  </tr>
                </thead>
                <tbody>
                  {reqs.data?.map((r) => (
                    <tr key={r.id} className="border-b border-border/30 hover:bg-secondary/40">
                      <td className="py-2 pr-4 font-mono text-xs">
                        <Link to={`/requisitions/${r.id}`} className="text-primary hover:underline">
                          {r.code}
                        </Link>
                      </td>
                      <td className="py-2 pr-4 font-medium">{r.title}</td>
                      <td className="py-2 pr-4 text-muted-foreground">
                        {nameById(depts.data, r.department_id)}
                      </td>
                      <td className="py-2 pr-4">{r.headcount}</td>
                      <td className="py-2 pr-4">{URGENCY_LABELS[r.urgency]}</td>
                      <td className="py-2 pr-4">
                        <span className={`rounded-full px-2 py-0.5 text-xs ${STATUS_BADGE[r.status]}`}>
                          {STATUS_LABELS[r.status]}
                        </span>
                      </td>
                      <td className="py-2 pr-4 text-muted-foreground">
                        {nameById(users.data, r.assigned_recruiter_id)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
