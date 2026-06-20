import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { Card, CardContent } from "@/components/ui/card";
import { STATUS_LABELS, fetchRequisitions } from "@/lib/requisitions";

export function PipelineChooserPage(): JSX.Element {
  const reqs = useQuery({ queryKey: ["requisitions", "all"], queryFn: () => fetchRequisitions({}) });

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Pipeline</h1>
      <p className="text-sm text-muted-foreground">Pick a requisition to view its candidate pipeline.</p>
      <Card>
        <CardContent className="pt-6">
          {reqs.isLoading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : reqs.data && reqs.data.length === 0 ? (
            <p className="text-sm text-muted-foreground">No requisitions.</p>
          ) : (
            <ul className="divide-y divide-border/40">
              {reqs.data?.map((r) => (
                <li key={r.id}>
                  <Link
                    to={`/pipeline/${r.id}`}
                    className="flex items-center justify-between py-3 hover:text-primary"
                  >
                    <span>
                      <span className="font-mono text-xs text-muted-foreground">{r.code}</span>{" "}
                      <span className="font-medium">{r.title}</span>
                    </span>
                    <span className="text-xs text-muted-foreground">{STATUS_LABELS[r.status]}</span>
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
