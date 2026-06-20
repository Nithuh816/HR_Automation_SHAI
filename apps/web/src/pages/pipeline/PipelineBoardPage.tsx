import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth";
import {
  STAGE_LABELS,
  STAGE_ORDER,
  fetchPipeline,
  moveStage,
  rejectApplication,
  type PipelineCard,
  type Stage,
} from "@/lib/candidates";

const CAN_MOVE = ["hr_head", "ta_tl", "ta_recruiter"];

export function PipelineBoardPage(): JSX.Element {
  const { reqId } = useParams();
  const requisitionId = Number(reqId);
  const { user } = useAuth();
  const qc = useQueryClient();

  const board = useQuery({
    queryKey: ["pipeline", requisitionId],
    queryFn: () => fetchPipeline(requisitionId),
  });

  const invalidate = () => void qc.invalidateQueries({ queryKey: ["pipeline", requisitionId] });
  const move = useMutation({
    mutationFn: ({ appId, stage }: { appId: number; stage: Stage }) => moveStage(appId, stage),
    onSuccess: invalidate,
  });
  const reject = useMutation({
    mutationFn: (appId: number) => rejectApplication(appId, "Rejected from pipeline"),
    onSuccess: invalidate,
  });

  const canMove = user != null && CAN_MOVE.includes(user.role);
  const cards = board.data ?? [];
  const active = cards.filter((c) => c.status === "active");
  const closed = cards.filter((c) => c.status !== "active");
  const byStage = (stage: Stage) => active.filter((c) => c.stage === stage);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Pipeline · Requisition #{requisitionId}</h1>
        <Button variant="outline" asChild>
          <Link to={`/requisitions/${requisitionId}`}>Requisition</Link>
        </Button>
      </div>

      {board.isLoading ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : (
        <div className="flex gap-3 overflow-x-auto pb-4">
          {STAGE_ORDER.map((stage) => (
            <div key={stage} className="w-60 shrink-0">
              <div className="mb-2 flex items-center justify-between px-1 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                <span>{STAGE_LABELS[stage]}</span>
                <span>{byStage(stage).length}</span>
              </div>
              <div className="space-y-2">
                {byStage(stage).map((card) => (
                  <PipelineCardView
                    key={card.application_id}
                    card={card}
                    canMove={canMove}
                    onMove={(s) => move.mutate({ appId: card.application_id, stage: s })}
                    onReject={() => reject.mutate(card.application_id)}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {closed.length > 0 && (
        <div>
          <h2 className="mb-2 text-sm font-medium text-muted-foreground">Closed</h2>
          <div className="flex flex-wrap gap-2">
            {closed.map((c) => (
              <Link
                key={c.application_id}
                to={`/candidates/${c.candidate_id}`}
                className="rounded-md border border-border/40 bg-secondary/40 px-3 py-1.5 text-xs text-muted-foreground line-through"
              >
                {c.candidate_name} · {c.status}
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function PipelineCardView({
  card,
  canMove,
  onMove,
  onReject,
}: {
  card: PipelineCard;
  canMove: boolean;
  onMove: (stage: Stage) => void;
  onReject: () => void;
}) {
  return (
    <div className="rounded-md border border-border/50 bg-card p-3 text-sm">
      <Link
        to={`/candidates/${card.candidate_id}`}
        className="font-medium hover:text-primary"
      >
        {card.candidate_name}
      </Link>
      {canMove && (
        <div className="mt-2 flex items-center gap-1">
          <select
            className="flex-1 rounded border border-border bg-transparent px-1 py-1 text-xs outline-none focus-visible:ring-2 focus-visible:ring-ring"
            value={card.stage}
            onChange={(e) => onMove(e.target.value as Stage)}
          >
            {STAGE_ORDER.map((s) => (
              <option key={s} value={s} className="bg-card">
                {STAGE_LABELS[s]}
              </option>
            ))}
          </select>
          <Button variant="ghost" size="sm" className="h-7 px-2 text-xs" onClick={onReject}>
            Reject
          </Button>
        </div>
      )}
    </div>
  );
}
