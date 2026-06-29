import { useState } from "react";

import { useQuery } from "@tanstack/react-query";

import { Card, CardContent } from "@/components/ui/card";
import { fetchAuditLog } from "@/lib/audit";

const ENTITY_TYPES = [
  "",
  "application",
  "offer",
  "interview",
  "document",
  "requisition",
  "user",
];

export function AuditLogPage(): JSX.Element {
  const [entityType, setEntityType] = useState("");
  const log = useQuery({
    queryKey: ["audit-log", entityType],
    queryFn: () => fetchAuditLog({ entity_type: entityType || undefined, limit: 200 }),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Audit log</h1>
        <select
          value={entityType}
          onChange={(e) => setEntityType(e.target.value)}
          className="rounded-md border border-border bg-transparent px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          {ENTITY_TYPES.map((t) => (
            <option key={t} value={t} className="bg-card">
              {t || "All entities"}
            </option>
          ))}
        </select>
      </div>

      <Card>
        <CardContent className="pt-6">
          {log.isLoading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : log.isError ? (
            <p className="text-sm text-destructive">The audit log is HR Head only.</p>
          ) : log.data && log.data.length === 0 ? (
            <p className="text-sm text-muted-foreground">No audit entries yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-xs uppercase tracking-wide text-muted-foreground">
                  <tr className="border-b border-border/60">
                    <th className="py-2 pr-4">When</th>
                    <th className="py-2 pr-4">Actor</th>
                    <th className="py-2 pr-4">Action</th>
                    <th className="py-2 pr-4">Entity</th>
                    <th className="py-2 pr-4">Detail</th>
                  </tr>
                </thead>
                <tbody>
                  {log.data?.map((e) => (
                    <tr key={e.id} className="border-b border-border/30 hover:bg-secondary/30">
                      <td className="whitespace-nowrap py-2 pr-4 text-muted-foreground">
                        {new Date(e.created_at).toLocaleString()}
                      </td>
                      <td className="py-2 pr-4">{e.actor_label}</td>
                      <td className="py-2 pr-4">
                        <span className="rounded-md bg-secondary px-2 py-1 font-mono text-xs">
                          {e.action}
                        </span>
                      </td>
                      <td className="py-2 pr-4 text-muted-foreground">
                        {e.entity_type}
                        {e.entity_id != null ? ` #${e.entity_id}` : ""}
                      </td>
                      <td className="py-2 pr-4">{e.summary ?? "—"}</td>
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
