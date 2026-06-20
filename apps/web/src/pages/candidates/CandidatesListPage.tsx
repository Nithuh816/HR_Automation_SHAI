import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useAuth } from "@/lib/auth";
import { SOURCE_LABELS, fetchCandidates } from "@/lib/candidates";

const CAN_EDIT = ["hr_head", "ta_tl", "ta_recruiter"];

export function CandidatesListPage(): JSX.Element {
  const { user } = useAuth();
  const candidates = useQuery({ queryKey: ["candidates"], queryFn: fetchCandidates });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Candidates</h1>
        {user && CAN_EDIT.includes(user.role) && (
          <Button asChild>
            <Link to="/candidates/new">New candidate</Link>
          </Button>
        )}
      </div>

      <Card>
        <CardContent className="pt-6">
          {candidates.isLoading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : candidates.data && candidates.data.length === 0 ? (
            <p className="text-sm text-muted-foreground">No candidates yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-xs uppercase tracking-wide text-muted-foreground">
                  <tr className="border-b border-border/60">
                    <th className="py-2 pr-4">Name</th>
                    <th className="py-2 pr-4">Email</th>
                    <th className="py-2 pr-4">Experience</th>
                    <th className="py-2 pr-4">Location</th>
                    <th className="py-2 pr-4">Source</th>
                  </tr>
                </thead>
                <tbody>
                  {candidates.data?.map((c) => (
                    <tr key={c.id} className="border-b border-border/30 hover:bg-secondary/40">
                      <td className="py-2 pr-4 font-medium">
                        <Link to={`/candidates/${c.id}`} className="text-primary hover:underline">
                          {c.name}
                        </Link>
                      </td>
                      <td className="py-2 pr-4 text-muted-foreground">{c.email}</td>
                      <td className="py-2 pr-4">
                        {c.is_fresher
                          ? "Fresher"
                          : c.total_experience_years != null
                            ? `${c.total_experience_years} yrs`
                            : "—"}
                      </td>
                      <td className="py-2 pr-4 text-muted-foreground">{c.location ?? "—"}</td>
                      <td className="py-2 pr-4">{SOURCE_LABELS[c.source]}</td>
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
