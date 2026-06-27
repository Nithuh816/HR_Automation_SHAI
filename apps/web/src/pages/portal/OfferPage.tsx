import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  type OfferStatus,
  acceptOffer,
  declineOffer,
  fetchPublicOffer,
  formatINR,
} from "@/lib/offers";

export function OfferPage(): JSX.Element {
  const { token } = useParams();
  const offer = useQuery({
    queryKey: ["public-offer", token],
    queryFn: () => fetchPublicOffer(token as string),
    retry: false,
  });

  const [outcome, setOutcome] = useState<OfferStatus | null>(null);
  const [declining, setDeclining] = useState(false);
  const [reason, setReason] = useState("");

  const accept = useMutation({
    mutationFn: () => acceptOffer(token as string),
    onSuccess: (r) => setOutcome(r.status),
  });
  const decline = useMutation({
    mutationFn: () => declineOffer(token as string, reason),
    onSuccess: (r) => setOutcome(r.status),
  });

  const responded = outcome != null || offer.data?.already_responded;

  return (
    <div className="min-h-screen bg-background p-4">
      <div className="mx-auto max-w-2xl py-8">
        <div className="mb-6 flex items-center gap-2">
          <div className="grid h-9 w-9 place-items-center rounded-md bg-primary text-primary-foreground">
            <span className="text-sm font-bold">HR</span>
          </div>
          <div className="text-sm font-semibold">SHAI Health</div>
        </div>

        {offer.isLoading ? (
          <Card>
            <CardContent className="pt-6 text-sm text-muted-foreground">Loading…</CardContent>
          </Card>
        ) : offer.isError || !offer.data ? (
          <Card>
            <CardHeader>
              <CardTitle>Link unavailable</CardTitle>
              <CardDescription>
                This offer link is invalid, already used, or expired. Please contact your recruiter.
              </CardDescription>
            </CardHeader>
          </Card>
        ) : responded ? (
          <Card>
            <CardHeader>
              <CardTitle>
                {(outcome ?? offer.data.status) === "accepted"
                  ? "Offer accepted 🎉"
                  : "Offer declined"}
              </CardTitle>
              <CardDescription>
                {(outcome ?? offer.data.status) === "accepted"
                  ? "Thank you! Our team will be in touch about onboarding and joining formalities."
                  : "Thank you for letting us know. We wish you the very best."}
              </CardDescription>
            </CardHeader>
          </Card>
        ) : (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>
                  {offer.data.designation} — {formatINR(offer.data.annual_ctc)}/yr
                </CardTitle>
                <CardDescription>
                  Hi {offer.data.candidate_name}, here is your offer from {offer.data.employer}.
                  Proposed joining date: {offer.data.joining_date}.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <iframe
                  title="Offer letter"
                  srcDoc={offer.data.letter_html}
                  className="h-[460px] w-full rounded-md border border-border bg-white"
                />
              </CardContent>
            </Card>

            <Card>
              <CardContent className="space-y-3 pt-6">
                {!declining ? (
                  <div className="flex flex-wrap gap-3">
                    <Button disabled={accept.isPending} onClick={() => accept.mutate()}>
                      Accept offer
                    </Button>
                    <Button variant="outline" onClick={() => setDeclining(true)}>
                      Decline
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <label className="block text-sm text-muted-foreground">
                      We’re sorry to hear that. A brief reason (optional):
                    </label>
                    <textarea
                      className="min-h-[80px] w-full rounded-md border border-border bg-transparent px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      value={reason}
                      onChange={(e) => setReason(e.target.value)}
                    />
                    <div className="flex gap-3">
                      <Button
                        variant="destructive"
                        disabled={decline.isPending}
                        onClick={() => decline.mutate()}
                      >
                        Confirm decline
                      </Button>
                      <Button variant="ghost" onClick={() => setDeclining(false)}>
                        Back
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
