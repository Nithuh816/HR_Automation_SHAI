import { useMutation, useQuery } from "@tanstack/react-query";
import { useRef, useState } from "react";
import { useParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  type DocumentType,
  DOC_STATUS_LABELS,
  DOC_TYPE_LABELS,
  fetchUploadContext,
  uploadDocument,
} from "@/lib/documents";

export function DocUploadPage(): JSX.Element {
  const { token } = useParams();
  const ctx = useQuery({
    queryKey: ["upload-context", token],
    queryFn: () => fetchUploadContext(token as string),
    retry: false,
  });

  const [consent, setConsent] = useState(false);
  const [pick, setPick] = useState<DocumentType>("aadhaar");
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const upload = useMutation({
    mutationFn: (file: File) => uploadDocument(token as string, pick, file),
    onSuccess: (data) => {
      setError(null);
      if (fileRef.current) fileRef.current.value = "";
      ctx.refetch();
      void data;
    },
    onError: () => setError("Upload failed. Please check the file and try again."),
  });

  const submit = () => {
    const file = fileRef.current?.files?.[0];
    if (!file) {
      setError("Please choose a file.");
      return;
    }
    if (!consent) {
      setError("Please tick the consent box before uploading.");
      return;
    }
    upload.mutate(file);
  };

  const uploadedTypes = new Set((ctx.data?.uploaded ?? []).map((u) => u.document_type));

  return (
    <div className="min-h-screen bg-background p-4">
      <div className="mx-auto max-w-2xl py-8">
        <div className="mb-6 flex items-center gap-2">
          <div className="grid h-9 w-9 place-items-center rounded-md bg-primary text-primary-foreground">
            <span className="text-sm font-bold">HR</span>
          </div>
          <div className="text-sm font-semibold">SHAI Health</div>
        </div>

        {ctx.isLoading ? (
          <Card>
            <CardContent className="pt-6 text-sm text-muted-foreground">Loading…</CardContent>
          </Card>
        ) : ctx.isError || !ctx.data ? (
          <Card>
            <CardHeader>
              <CardTitle>Link unavailable</CardTitle>
              <CardDescription>
                This upload link is invalid or expired. Please contact your recruiter.
              </CardDescription>
            </CardHeader>
          </Card>
        ) : (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Upload your documents</CardTitle>
                <CardDescription>
                  Hi {ctx.data.candidate_name} — please upload the documents below for onboarding.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {ctx.data.items.map((item) => (
                  <div
                    key={item.document_type}
                    className="flex items-center justify-between border-b border-border/30 py-1.5 text-sm last:border-0"
                  >
                    <span>
                      {item.label}
                      {item.required && <span className="text-destructive"> *</span>}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {uploadedTypes.has(item.document_type) ? "✓ uploaded" : "pending"}
                    </span>
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Add a document</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex flex-wrap items-center gap-3">
                  <select
                    className="rounded-md border border-border bg-transparent px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    value={pick}
                    onChange={(e) => setPick(e.target.value as DocumentType)}
                  >
                    {ctx.data.items.map((item) => (
                      <option key={item.document_type} value={item.document_type} className="bg-card">
                        {DOC_TYPE_LABELS[item.document_type]}
                      </option>
                    ))}
                  </select>
                  <input ref={fileRef} type="file" className="text-sm" />
                </div>
                <label className="flex items-start gap-2 text-xs text-muted-foreground">
                  <input
                    type="checkbox"
                    className="mt-0.5"
                    checked={consent}
                    onChange={(e) => setConsent(e.target.checked)}
                  />
                  {ctx.data.consent_text}
                </label>
                <Button disabled={upload.isPending} onClick={submit}>
                  Upload
                </Button>
                {error && <p className="text-xs text-destructive">{error}</p>}
              </CardContent>
            </Card>

            {ctx.data.uploaded.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Your uploads</CardTitle>
                </CardHeader>
                <CardContent className="space-y-1">
                  {ctx.data.uploaded.map((u) => (
                    <div
                      key={u.id}
                      className="flex justify-between border-b border-border/30 py-1 text-sm last:border-0"
                    >
                      <span>
                        {DOC_TYPE_LABELS[u.document_type]} · {u.original_filename}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {DOC_STATUS_LABELS[u.status]}
                      </span>
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
