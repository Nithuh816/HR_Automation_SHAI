import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { Card, CardContent } from "@/components/ui/card";
import { OFFER_STATUS_LABELS, formatINR, fetchOffers } from "@/lib/offers";

export function OffersListPage(): JSX.Element {
  const offers = useQuery({ queryKey: ["offers"], queryFn: fetchOffers });

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Offers</h1>

      <Card>
        <CardContent className="pt-6">
          {offers.isLoading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : offers.data && offers.data.length === 0 ? (
            <p className="text-sm text-muted-foreground">No offers yet.</p>
          ) : (
            <ul className="divide-y divide-border/40">
              {offers.data?.map((o) => (
                <li key={o.id}>
                  <Link
                    to={`/offers/${o.id}`}
                    className="flex flex-wrap items-center justify-between gap-3 py-3 hover:text-primary"
                  >
                    <div>
                      <div className="font-medium">{o.candidate_name}</div>
                      <div className="text-xs text-muted-foreground">
                        {o.designation} · {formatINR(o.annual_ctc)}/yr · joins {o.joining_date}
                      </div>
                    </div>
                    <span className="rounded-md bg-secondary px-2 py-1 text-xs">
                      {OFFER_STATUS_LABELS[o.status]}
                    </span>
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
