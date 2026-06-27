import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { Card, CardContent } from "@/components/ui/card";
import {
  MODE_LABELS,
  ROUND_LABELS,
  STATUS_LABELS,
  fetchTodaysInterviews,
} from "@/lib/interviews";

function formatWhen(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function InterviewsTodayPage(): JSX.Element {
  const interviews = useQuery({
    queryKey: ["interviews-today"],
    queryFn: fetchTodaysInterviews,
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Upcoming interviews</h1>
        <p className="text-sm text-muted-foreground">
          From the start of today onward. Interviewers see their own; TA staff see all.
        </p>
      </div>

      <Card>
        <CardContent className="pt-6">
          {interviews.isLoading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : interviews.data && interviews.data.length === 0 ? (
            <p className="text-sm text-muted-foreground">Nothing scheduled.</p>
          ) : (
            <ul className="divide-y divide-border/40">
              {interviews.data?.map((i) => (
                <li key={i.id}>
                  <Link
                    to={`/interviews/${i.id}`}
                    className="flex flex-wrap items-center justify-between gap-3 py-3 hover:text-primary"
                  >
                    <div>
                      <div className="font-medium">{i.candidate_name}</div>
                      <div className="text-xs text-muted-foreground">
                        {ROUND_LABELS[i.round]} · {i.requisition_title} · {i.interviewer_name}
                      </div>
                    </div>
                    <div className="text-right text-xs text-muted-foreground">
                      <div>{formatWhen(i.scheduled_at)}</div>
                      <div>
                        {MODE_LABELS[i.mode]} · {STATUS_LABELS[i.status]}
                      </div>
                    </div>
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
