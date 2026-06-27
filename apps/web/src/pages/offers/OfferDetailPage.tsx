import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/lib/auth";
import {
  OFFER_STATUS_LABELS,
  approveOffer,
  fetchOffer,
  fetchOfferLetter,
  formatINR,
  revokeOffer,
  sendOffer,
  submitOffer,
  updateOffer,
} from "@/lib/offers";

const CAN_BUILD = ["hr_head", "ta_tl", "ta_recruiter"];
const inputClass =
  "w-full rounded-md border border-border bg-transparent px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring";

export function OfferDetailPage(): JSX.Element {
  const { id } = useParams();
  const offerId = Number(id);
  const { user } = useAuth();
  const qc = useQueryClient();
  const [link, setLink] = useState<string | null>(null);

  const offer = useQuery({ queryKey: ["offer", offerId], queryFn: () => fetchOffer(offerId) });
  const letter = useQuery({
    queryKey: ["offer-letter", offerId],
    queryFn: () => fetchOfferLetter(offerId),
  });

  const [form, setForm] = useState({ annual_ctc: "", joining_date: "" });
  useEffect(() => {
    if (offer.data) {
      setForm({ annual_ctc: String(offer.data.annual_ctc), joining_date: offer.data.joining_date });
    }
  }, [offer.data]);

  const invalidate = () => {
    void qc.invalidateQueries({ queryKey: ["offer", offerId] });
    void qc.invalidateQueries({ queryKey: ["offer-letter", offerId] });
  };
  const save = useMutation({
    mutationFn: () =>
      updateOffer(offerId, {
        annual_ctc: Number(form.annual_ctc),
        joining_date: form.joining_date,
      }),
    onSuccess: invalidate,
  });
  const submit = useMutation({ mutationFn: () => submitOffer(offerId), onSuccess: invalidate });
  const approve = useMutation({ mutationFn: () => approveOffer(offerId), onSuccess: invalidate });
  const send = useMutation({
    mutationFn: () => sendOffer(offerId),
    onSuccess: (res) => {
      setLink(res.url);
      invalidate();
    },
  });
  const revoke = useMutation({ mutationFn: () => revokeOffer(offerId), onSuccess: invalidate });

  if (offer.isLoading) return <p className="text-sm text-muted-foreground">Loading…</p>;
  if (offer.isError || !offer.data)
    return <p className="text-sm text-destructive">Offer not found.</p>;

  const o = offer.data;
  const canBuild = user != null && CAN_BUILD.includes(user.role);
  const isHrHead = user?.role === "hr_head";

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-xl font-semibold">
          Offer · {o.candidate_name}{" "}
          <span className="rounded-md bg-secondary px-2 py-0.5 align-middle text-xs">
            {OFFER_STATUS_LABELS[o.status]}
          </span>
        </h1>
        <p className="text-sm text-muted-foreground">
          <Link to={`/candidates/${o.candidate_id}`} className="text-primary hover:underline">
            {o.candidate_name}
          </Link>{" "}
          · {o.designation} · {o.requisition_title}
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Compensation</CardTitle>
        </CardHeader>
        <CardContent>
          {canBuild && o.status === "draft" ? (
            <div className="mb-4 flex flex-wrap items-end gap-3">
              <div className="w-40">
                <label className="mb-1 block text-xs text-muted-foreground">Annual CTC (₹)</label>
                <input
                  type="number"
                  className={inputClass}
                  value={form.annual_ctc}
                  onChange={(e) => setForm({ ...form, annual_ctc: e.target.value })}
                />
              </div>
              <div className="w-44">
                <label className="mb-1 block text-xs text-muted-foreground">Joining date</label>
                <input
                  type="date"
                  className={inputClass}
                  value={form.joining_date}
                  onChange={(e) => setForm({ ...form, joining_date: e.target.value })}
                />
              </div>
              <Button variant="secondary" disabled={save.isPending} onClick={() => save.mutate()}>
                Recalculate
              </Button>
            </div>
          ) : (
            <p className="mb-4 text-sm text-muted-foreground">
              {formatINR(o.annual_ctc)} / yr · joins {o.joining_date}
            </p>
          )}

          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs uppercase tracking-wide text-muted-foreground">
                <th className="py-1 text-left font-medium">Component</th>
                <th className="py-1 text-right font-medium">Annual</th>
                <th className="py-1 text-right font-medium">Monthly</th>
              </tr>
            </thead>
            <tbody>
              {o.components.map((c) => (
                <tr key={c.label} className="border-t border-border/30 last:font-semibold">
                  <td className="py-1.5">{c.label}</td>
                  <td className="py-1.5 text-right">{formatINR(c.annual)}</td>
                  <td className="py-1.5 text-right">{formatINR(c.monthly)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Workflow</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap items-center gap-3">
          {canBuild && o.status === "draft" && (
            <Button disabled={submit.isPending} onClick={() => submit.mutate()}>
              Submit for approval
            </Button>
          )}
          {o.status === "pending_approval" &&
            (isHrHead ? (
              <Button disabled={approve.isPending} onClick={() => approve.mutate()}>
                Approve
              </Button>
            ) : (
              <p className="text-sm text-muted-foreground">Awaiting HR Head approval.</p>
            ))}
          {canBuild && o.status === "approved" && (
            <Button disabled={send.isPending} onClick={() => send.mutate()}>
              Send to candidate
            </Button>
          )}
          {canBuild && (o.status === "sent" || o.status === "approved") && (
            <Button variant="outline" disabled={revoke.isPending} onClick={() => revoke.mutate()}>
              Revoke
            </Button>
          )}
          {o.status === "accepted" && (
            <p className="text-sm text-emerald-400">Accepted by the candidate. 🎉</p>
          )}
          {o.status === "declined" && (
            <p className="text-sm text-destructive">
              Declined{o.decline_reason ? `: ${o.decline_reason}` : ""}.
            </p>
          )}
        </CardContent>
      </Card>

      {link && (
        <div className="rounded-md border border-primary/40 bg-primary/10 p-3 text-sm">
          <div className="mb-1 text-xs text-muted-foreground">
            Share this single-use offer link with the candidate:
          </div>
          <code className="break-all text-xs">{link}</code>
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Letter preview</CardTitle>
        </CardHeader>
        <CardContent>
          {letter.data ? (
            <iframe
              title="Offer letter"
              srcDoc={letter.data}
              className="h-[480px] w-full rounded-md border border-border bg-white"
            />
          ) : (
            <p className="text-sm text-muted-foreground">Loading letter…</p>
          )}
          <p className="mt-2 text-xs text-muted-foreground">
            Use your browser’s Print → Save as PDF on the candidate’s copy. (Server-side PDF
            activates automatically once WeasyPrint is installed.)
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
