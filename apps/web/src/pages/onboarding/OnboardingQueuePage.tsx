import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useAuth } from "@/lib/auth";
import {
  ONBOARDING_STATUS_LABELS,
  fetchOnboardingQueue,
  pushToGreytHR,
  type OnboardingQueueItem,
} from "@/lib/onboarding";

const CAN_ONBOARD = ["hr_head", "pr"];

export function OnboardingQueuePage(): JSX.Element {
  const { user } = useAuth();
  const qc = useQueryClient();
  const queue = useQuery({ queryKey: ["onboarding-queue"], queryFn: fetchOnboardingQueue });
  const push = useMutation({
    mutationFn: (appId: number) => pushToGreytHR(appId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["onboarding-queue"] }),
  });

  const canOnboard = user != null && CAN_ONBOARD.includes(user.role);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Onboarding</h1>
        <p className="text-sm text-muted-foreground">
          Candidates who accepted their offer — push them to GreytHR, then confirm joining.
        </p>
      </div>

      <Card>
        <CardContent className="pt-6">
          {queue.isLoading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : queue.isError ? (
            <p className="text-sm text-destructive">
              Could not load the queue.{" "}
              {!canOnboard && "Onboarding is restricted to the Post-Recruitment team."}
            </p>
          ) : queue.data && queue.data.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No candidates are awaiting onboarding yet.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-xs uppercase tracking-wide text-muted-foreground">
                  <tr className="border-b border-border/60">
                    <th className="py-2 pr-4">Candidate</th>
                    <th className="py-2 pr-4">Role</th>
                    <th className="py-2 pr-4">Joining</th>
                    <th className="py-2 pr-4">Documents</th>
                    <th className="py-2 pr-4">Status</th>
                    <th className="py-2 pr-4" />
                  </tr>
                </thead>
                <tbody>
                  {queue.data?.map((row) => (
                    <Row
                      key={row.application_id}
                      row={row}
                      canOnboard={canOnboard}
                      pushing={push.isPending}
                      onPush={() => push.mutate(row.application_id)}
                    />
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {push.isError && (
            <p className="mt-3 text-sm text-destructive">Push to GreytHR failed. Please retry.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function Row({
  row,
  canOnboard,
  pushing,
  onPush,
}: {
  row: OnboardingQueueItem;
  canOnboard: boolean;
  pushing: boolean;
  onPush: () => void;
}): JSX.Element {
  return (
    <tr className="border-b border-border/30 hover:bg-secondary/40">
      <td className="py-2 pr-4 font-medium">
        {row.handoff_id ? (
          <Link to={`/onboarding/${row.handoff_id}`} className="text-primary hover:underline">
            {row.candidate_name}
          </Link>
        ) : (
          row.candidate_name
        )}
      </td>
      <td className="py-2 pr-4">{row.designation}</td>
      <td className="py-2 pr-4">{row.joining_date}</td>
      <td className="py-2 pr-4">
        {row.documents_verified}/{row.documents_required} verified
      </td>
      <td className="py-2 pr-4">
        <span className="rounded-md bg-secondary px-2 py-1 text-xs">
          {row.handoff_status ? ONBOARDING_STATUS_LABELS[row.handoff_status] : "Ready"}
        </span>
      </td>
      <td className="py-2 pr-4 text-right">
        {row.handoff_id ? (
          <Link to={`/onboarding/${row.handoff_id}`} className="text-primary hover:underline">
            View
          </Link>
        ) : canOnboard ? (
          <Button size="sm" disabled={pushing} onClick={onPush}>
            {pushing ? "Pushing…" : "Push to GreytHR"}
          </Button>
        ) : null}
      </td>
    </tr>
  );
}
