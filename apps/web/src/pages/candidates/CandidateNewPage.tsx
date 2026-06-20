import { useMutation, useQuery } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";
import { Navigate, useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { SOURCE_LABELS, type Candidate, type CandidateSource } from "@/lib/candidates";
import { fetchRequisitions } from "@/lib/requisitions";

const CAN_EDIT = ["hr_head", "ta_tl", "ta_recruiter"];
const inputClass =
  "w-full rounded-md border border-border bg-transparent px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring";

export function CandidateNewPage(): JSX.Element {
  const { user } = useAuth();
  const navigate = useNavigate();
  const reqs = useQuery({ queryKey: ["requisitions", "all"], queryFn: () => fetchRequisitions({}) });

  const [form, setForm] = useState({
    name: "",
    email: "",
    phone: "",
    location: "",
    is_fresher: false,
    total_experience_years: "",
    expected_ctc: "",
    notice_period_days: "",
    source: "linkedin" as CandidateSource,
    referred_by: "",
    resume_url: "",
    requisition_id: "",
  });
  const [error, setError] = useState<string | null>(null);

  const create = useMutation({
    mutationFn: async () => {
      const payload = {
        name: form.name,
        email: form.email,
        phone: form.phone || null,
        location: form.location || null,
        is_fresher: form.is_fresher,
        total_experience_years: form.total_experience_years
          ? Number(form.total_experience_years)
          : null,
        expected_ctc: form.expected_ctc ? Number(form.expected_ctc) : null,
        notice_period_days: form.notice_period_days ? Number(form.notice_period_days) : null,
        source: form.source,
        referred_by: form.referred_by || null,
        resume_url: form.resume_url || null,
        requisition_id: form.requisition_id ? Number(form.requisition_id) : null,
      };
      return (await api.post<Candidate>("/candidates", payload)).data;
    },
    onSuccess: (c) => navigate(`/candidates/${c.id}`),
    onError: () => setError("Could not create candidate. Check the fields and try again."),
  });

  if (user && !CAN_EDIT.includes(user.role)) {
    return <Navigate to="/candidates" replace />;
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-xl font-semibold">New candidate</h1>
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Details</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            className="space-y-4"
            onSubmit={(e) => {
              e.preventDefault();
              create.mutate();
            }}
          >
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Labeled label="Full name">
                <input
                  className={inputClass}
                  required
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                />
              </Labeled>
              <Labeled label="Email">
                <input
                  type="email"
                  className={inputClass}
                  required
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                />
              </Labeled>
              <Labeled label="Phone">
                <input
                  className={inputClass}
                  value={form.phone}
                  onChange={(e) => setForm({ ...form, phone: e.target.value })}
                />
              </Labeled>
              <Labeled label="Location">
                <input
                  className={inputClass}
                  value={form.location}
                  onChange={(e) => setForm({ ...form, location: e.target.value })}
                />
              </Labeled>
              <Labeled label="Source">
                <select
                  className={inputClass}
                  value={form.source}
                  onChange={(e) => setForm({ ...form, source: e.target.value as CandidateSource })}
                >
                  {(Object.keys(SOURCE_LABELS) as CandidateSource[]).map((s) => (
                    <option key={s} value={s} className="bg-card">
                      {SOURCE_LABELS[s]}
                    </option>
                  ))}
                </select>
              </Labeled>
              <Labeled label="Referred by">
                <input
                  className={inputClass}
                  value={form.referred_by}
                  onChange={(e) => setForm({ ...form, referred_by: e.target.value })}
                />
              </Labeled>
              <Labeled label="Total experience (yrs)">
                <input
                  type="number"
                  min={0}
                  step="0.5"
                  className={inputClass}
                  disabled={form.is_fresher}
                  value={form.total_experience_years}
                  onChange={(e) => setForm({ ...form, total_experience_years: e.target.value })}
                />
              </Labeled>
              <Labeled label="Expected CTC (₹/yr)">
                <input
                  type="number"
                  min={0}
                  className={inputClass}
                  value={form.expected_ctc}
                  onChange={(e) => setForm({ ...form, expected_ctc: e.target.value })}
                />
              </Labeled>
              <Labeled label="Notice period (days)">
                <input
                  type="number"
                  min={0}
                  className={inputClass}
                  value={form.notice_period_days}
                  onChange={(e) => setForm({ ...form, notice_period_days: e.target.value })}
                />
              </Labeled>
              <Labeled label="Attach to requisition">
                <select
                  className={inputClass}
                  value={form.requisition_id}
                  onChange={(e) => setForm({ ...form, requisition_id: e.target.value })}
                >
                  <option value="" className="bg-card">
                    None
                  </option>
                  {reqs.data?.map((r) => (
                    <option key={r.id} value={r.id} className="bg-card">
                      {r.code} · {r.title}
                    </option>
                  ))}
                </select>
              </Labeled>
            </div>

            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={form.is_fresher}
                onChange={(e) => setForm({ ...form, is_fresher: e.target.checked })}
              />
              Fresher (no prior experience)
            </label>

            <Labeled label="Resume URL">
              <input
                className={inputClass}
                placeholder="Link to resume (Drive, LinkedIn, …)"
                value={form.resume_url}
                onChange={(e) => setForm({ ...form, resume_url: e.target.value })}
              />
            </Labeled>

            {error && <p className="text-xs text-destructive">{error}</p>}

            <div className="flex justify-end gap-2">
              <Button type="button" variant="ghost" onClick={() => navigate("/candidates")}>
                Cancel
              </Button>
              <Button type="submit" disabled={create.isPending}>
                {create.isPending ? "Creating…" : "Create"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

function Labeled({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <label className="mb-1 block text-xs text-muted-foreground">{label}</label>
      {children}
    </div>
  );
}
