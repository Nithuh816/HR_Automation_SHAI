import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/lib/auth";
import { fetchCandidate } from "@/lib/candidates";
import {
  type CandidateDocument,
  type DocumentStatus,
  DOC_STATUS_LABELS,
  DOC_TYPE_LABELS,
  createUploadLink,
  fetchCandidateDocuments,
  fetchChecklistOptions,
  fetchDocumentBlobUrl,
  rejectDocument,
  verifyDocument,
} from "@/lib/documents";

const CAN_REVIEW = ["hr_head", "ta_tl", "ta_recruiter", "pr"];

const STATUS_STYLES: Record<DocumentStatus, string> = {
  pending: "bg-secondary text-muted-foreground",
  extracted: "bg-primary/15 text-foreground",
  needs_review: "bg-amber-500/20 text-amber-300",
  verified: "bg-emerald-500/20 text-emerald-300",
  rejected: "bg-destructive/20 text-destructive",
};

export function CandidateDocumentsPage(): JSX.Element {
  const { id } = useParams();
  const candidateId = Number(id);
  const { user } = useAuth();
  const qc = useQueryClient();
  const [link, setLink] = useState<string | null>(null);

  const cand = useQuery({
    queryKey: ["candidate", candidateId],
    queryFn: () => fetchCandidate(candidateId),
  });
  const docs = useQuery({
    queryKey: ["candidate-documents", candidateId],
    queryFn: () => fetchCandidateDocuments(candidateId),
  });
  const checklistType = cand.data?.is_fresher ? "fresher" : "experienced";
  const checklist = useQuery({
    queryKey: ["checklist", checklistType],
    queryFn: () => fetchChecklistOptions(checklistType),
    enabled: cand.data != null,
  });

  const invalidate = () =>
    void qc.invalidateQueries({ queryKey: ["candidate-documents", candidateId] });
  const verify = useMutation({ mutationFn: (docId: number) => verifyDocument(docId), onSuccess: invalidate });
  const reject = useMutation({
    mutationFn: (docId: number) => rejectDocument(docId, "Not legible / incorrect"),
    onSuccess: invalidate,
  });
  const linkMut = useMutation({
    mutationFn: () => createUploadLink(candidateId),
    onSuccess: (res) => setLink(res.url),
  });

  if (cand.isLoading) return <p className="text-sm text-muted-foreground">Loading…</p>;
  if (cand.isError || !cand.data)
    return <p className="text-sm text-destructive">Candidate not found.</p>;

  const canReview = user != null && CAN_REVIEW.includes(user.role);
  const byType = new Map<string, CandidateDocument>();
  for (const d of docs.data ?? []) if (!byType.has(d.document_type)) byType.set(d.document_type, d);

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">{cand.data.name} · Documents</h1>
          <p className="text-sm text-muted-foreground">
            <Link to={`/candidates/${candidateId}`} className="text-primary hover:underline">
              Back to candidate
            </Link>{" "}
            · {checklistType} checklist
          </p>
        </div>
        {canReview && (
          <Button onClick={() => linkMut.mutate()} disabled={linkMut.isPending}>
            Get upload link
          </Button>
        )}
      </div>

      {link && (
        <div className="rounded-md border border-primary/40 bg-primary/10 p-3 text-sm">
          <div className="mb-1 text-xs text-muted-foreground">
            Share this upload link with the candidate (valid 14 days, multi-use):
          </div>
          <code className="break-all text-xs">{link}</code>
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Checklist</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {checklist.data?.map((item) => {
            const doc = byType.get(item.document_type);
            return (
              <div
                key={item.id}
                className="flex items-center justify-between gap-3 border-b border-border/30 py-1.5 text-sm last:border-0"
              >
                <span>
                  {item.label}
                  {item.required && <span className="text-destructive"> *</span>}
                </span>
                {doc ? (
                  <span className={`rounded px-2 py-0.5 text-xs ${STATUS_STYLES[doc.status]}`}>
                    {DOC_STATUS_LABELS[doc.status]}
                  </span>
                ) : (
                  <span className="text-xs text-muted-foreground">Not uploaded</span>
                )}
              </div>
            );
          })}
          {checklist.data && checklist.data.length === 0 && (
            <p className="text-sm text-muted-foreground">No checklist configured.</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Uploaded documents</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {docs.data && docs.data.length > 0 ? (
            docs.data.map((d) => (
              <DocRow
                key={d.id}
                doc={d}
                canReview={canReview}
                onVerify={() => verify.mutate(d.id)}
                onReject={() => reject.mutate(d.id)}
              />
            ))
          ) : (
            <p className="text-sm text-muted-foreground">Nothing uploaded yet.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function DocRow({
  doc,
  canReview,
  onVerify,
  onReject,
}: {
  doc: CandidateDocument;
  canReview: boolean;
  onVerify: () => void;
  onReject: () => void;
}) {
  const view = async () => {
    const url = await fetchDocumentBlobUrl(doc.id);
    window.open(url, "_blank", "noopener");
  };
  const pii = doc.pan_masked ?? doc.aadhaar_masked;
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-border/50 p-3 text-sm">
      <div>
        <div className="font-medium">
          {DOC_TYPE_LABELS[doc.document_type]}{" "}
          <span className="text-xs font-normal text-muted-foreground">
            · {doc.original_filename}
          </span>
        </div>
        <div className="text-xs text-muted-foreground">
          <span className={`rounded px-1.5 py-0.5 ${STATUS_STYLES[doc.status]}`}>
            {DOC_STATUS_LABELS[doc.status]}
          </span>
          {pii && <span className="ml-2 font-mono">{pii}</span>}
        </div>
      </div>
      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm" onClick={() => void view()}>
          View
        </Button>
        {canReview && doc.status !== "verified" && (
          <Button size="sm" onClick={onVerify}>
            Verify
          </Button>
        )}
        {canReview && doc.status !== "rejected" && (
          <Button variant="ghost" size="sm" onClick={onReject}>
            Reject
          </Button>
        )}
      </div>
    </div>
  );
}
