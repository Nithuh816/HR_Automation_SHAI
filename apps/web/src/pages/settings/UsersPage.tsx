import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Navigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { ROLE_LABELS, useAuth, type AuthUser, type Role, type Team } from "@/lib/auth";

interface Department {
  id: number;
  name: string;
}

const ROLES: Role[] = ["hr_head", "ta_tl", "ta_recruiter", "dept_lead", "dept_head", "pr"];
const TEAMS: Team[] = ["ta", "pr", "mgmt", "dept"];

const inputClass =
  "rounded-md border border-border bg-transparent px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring";

export function UsersPage(): JSX.Element {
  const { user } = useAuth();
  const qc = useQueryClient();

  const usersQuery = useQuery({
    queryKey: ["users"],
    queryFn: async () => (await api.get<AuthUser[]>("/users")).data,
  });
  const deptsQuery = useQuery({
    queryKey: ["departments"],
    queryFn: async () => (await api.get<Department[]>("/departments")).data,
  });

  const [form, setForm] = useState({
    email: "",
    name: "",
    role: "ta_recruiter" as Role,
    team: "ta" as Team,
    department_id: "" as string,
  });
  const [error, setError] = useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: async () =>
      (
        await api.post<AuthUser>("/users", {
          email: form.email,
          name: form.name,
          role: form.role,
          team: form.team,
          department_id: form.department_id ? Number(form.department_id) : null,
        })
      ).data,
    onSuccess: () => {
      setForm({ ...form, email: "", name: "" });
      setError(null);
      void qc.invalidateQueries({ queryKey: ["users"] });
    },
    onError: () => setError("Could not create user (duplicate email?)."),
  });

  const deactivateMutation = useMutation({
    mutationFn: async (id: number) => api.post(`/users/${id}/deactivate`),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["users"] }),
  });

  if (user && user.role !== "hr_head") {
    return <Navigate to="/dashboard" replace />;
  }

  const deptName = (id: number | null) =>
    id ? (deptsQuery.data?.find((d) => d.id === id)?.name ?? "—") : "—";

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Users</h1>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Add user</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3"
            onSubmit={(e) => {
              e.preventDefault();
              createMutation.mutate();
            }}
          >
            <input
              className={inputClass}
              placeholder="Email"
              type="email"
              required
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
            />
            <input
              className={inputClass}
              placeholder="Full name"
              required
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
            <select
              className={inputClass}
              value={form.role}
              onChange={(e) => setForm({ ...form, role: e.target.value as Role })}
            >
              {ROLES.map((r) => (
                <option key={r} value={r} className="bg-card">
                  {ROLE_LABELS[r]}
                </option>
              ))}
            </select>
            <select
              className={inputClass}
              value={form.team}
              onChange={(e) => setForm({ ...form, team: e.target.value as Team })}
            >
              {TEAMS.map((t) => (
                <option key={t} value={t} className="bg-card">
                  {t.toUpperCase()}
                </option>
              ))}
            </select>
            <select
              className={inputClass}
              value={form.department_id}
              onChange={(e) => setForm({ ...form, department_id: e.target.value })}
            >
              <option value="" className="bg-card">
                No department
              </option>
              {deptsQuery.data?.map((d) => (
                <option key={d.id} value={d.id} className="bg-card">
                  {d.name}
                </option>
              ))}
            </select>
            <Button type="submit" disabled={createMutation.isPending}>
              {createMutation.isPending ? "Adding…" : "Add user"}
            </Button>
          </form>
          {error && <p className="mt-2 text-xs text-destructive">{error}</p>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            All users {usersQuery.data ? `(${usersQuery.data.length})` : ""}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {usersQuery.isLoading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : usersQuery.isError ? (
            <p className="text-sm text-destructive">Failed to load users.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-xs uppercase tracking-wide text-muted-foreground">
                  <tr className="border-b border-border/60">
                    <th className="py-2 pr-4">Name</th>
                    <th className="py-2 pr-4">Email</th>
                    <th className="py-2 pr-4">Role</th>
                    <th className="py-2 pr-4">Team</th>
                    <th className="py-2 pr-4">Department</th>
                    <th className="py-2 pr-4">Status</th>
                    <th className="py-2" />
                  </tr>
                </thead>
                <tbody>
                  {usersQuery.data?.map((u) => (
                    <tr key={u.id} className="border-b border-border/30">
                      <td className="py-2 pr-4 font-medium">{u.name}</td>
                      <td className="py-2 pr-4 text-muted-foreground">{u.email}</td>
                      <td className="py-2 pr-4">{ROLE_LABELS[u.role]}</td>
                      <td className="py-2 pr-4 uppercase">{u.team}</td>
                      <td className="py-2 pr-4">{deptName(u.department_id)}</td>
                      <td className="py-2 pr-4">
                        {u.is_active ? (
                          <span className="text-emerald-400">active</span>
                        ) : (
                          <span className="text-muted-foreground">inactive</span>
                        )}
                      </td>
                      <td className="py-2 text-right">
                        {u.is_active && u.id !== user?.id && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => deactivateMutation.mutate(u.id)}
                          >
                            Deactivate
                          </Button>
                        )}
                      </td>
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
