import { useQuery } from "@tanstack/react-query";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";

interface HealthResponse {
  status: string;
  env: string;
  version: string;
}

export function HealthPage(): JSX.Element {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["health"],
    queryFn: async () => {
      const res = await api.get<HealthResponse>("/health".replace(/^\/api\/v1/, ""));
      return res.data;
    },
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>API health</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading && <p className="text-sm text-muted-foreground">Pinging…</p>}
        {isError && (
          <pre className="text-sm text-destructive">
            {error instanceof Error ? error.message : "unknown error"}
          </pre>
        )}
        {data && (
          <dl className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <dt className="text-muted-foreground">Status</dt>
              <dd className="font-mono">{data.status}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Env</dt>
              <dd className="font-mono">{data.env}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Version</dt>
              <dd className="font-mono">{data.version}</dd>
            </div>
          </dl>
        )}
      </CardContent>
    </Card>
  );
}
