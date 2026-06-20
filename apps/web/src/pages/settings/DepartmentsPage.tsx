import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Navigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { useAuth, type AuthUser } from "@/lib/auth";

interface Department {
  id: number;
  name: string;
  head_user_id: number | null;
}

const inputClass =
  "rounded-md border border-border bg-transparent px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring";

export function DepartmentsPage(): JSX.Element {
  const { user } = useAuth();
  const qc = useQueryClient();

  const deptsQuery = useQuery({
    queryKey: ["departments"],
    queryFn: async () => (await api.get<Department[]>("/departments")).data,
  });
  const usersQuery = useQuery({
    queryKey: ["users"],
    queryFn: async () => (await api.get<AuthUser[]>("/users")).data,
  });

  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: async () => (await api.post<Department>("/departments", { name })).data,
    onSuccess: () => {
      setName("");
      setError(null);
      void qc.invalidateQueries({ queryKey: ["departments"] });
    },
    onError: () => setError("Could not create department (duplicate name?)."),
  });

  const setHeadMutation = useMutation({
    mutationFn: async ({ id, headId }: { id: number; headId: number | null }) =>
      api.patch(`/departments/${id}`, { head_user_id: headId }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["departments"] }),
  });

  if (user && user.role !== "hr_head") {
    return <Navigate to="/dashboard" replace />;
  }

  const userName = (id: number | null) =>
    id ? (usersQuery.data?.find((u) => u.id === id)?.name ?? "—") : "—";

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Departments</h1>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Add department</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            className="flex gap-3"
            onSubmit={(e) => {
              e.preventDefault();
              createMutation.mutate();
            }}
          >
            <input
              className={`${inputClass} flex-1`}
              placeholder="Department name"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
            <Button type="submit" disabled={createMutation.isPending}>
              {createMutation.isPending ? "Adding…" : "Add"}
            </Button>
          </form>
          {error && <p className="mt-2 text-xs text-destructive">{error}</p>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            All departments {deptsQuery.data ? `(${deptsQuery.data.length})` : ""}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {deptsQuery.isLoading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : deptsQuery.isError ? (
            <p className="text-sm text-destructive">Failed to load departments.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-xs uppercase tracking-wide text-muted-foreground">
                  <tr className="border-b border-border/60">
                    <th className="py-2 pr-4">Name</th>
                    <th className="py-2 pr-4">Head</th>
                    <th className="py-2">Assign head</th>
                  </tr>
                </thead>
                <tbody>
                  {deptsQuery.data?.map((d) => (
                    <tr key={d.id} className="border-b border-border/30">
                      <td className="py-2 pr-4 font-medium">{d.name}</td>
                      <td className="py-2 pr-4 text-muted-foreground">
                        {userName(d.head_user_id)}
                      </td>
                      <td className="py-2">
                        <select
                          className={inputClass}
                          value={d.head_user_id ?? ""}
                          onChange={(e) =>
                            setHeadMutation.mutate({
                              id: d.id,
                              headId: e.target.value ? Number(e.target.value) : null,
                            })
                          }
                        >
                          <option value="" className="bg-card">
                            No head
                          </option>
                          {usersQuery.data?.map((u) => (
                            <option key={u.id} value={u.id} className="bg-card">
                              {u.name}
                            </option>
                          ))}
                        </select>
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
