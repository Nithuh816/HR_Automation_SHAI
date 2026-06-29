import { type ReactNode } from "react";

import { useQuery } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  fetchDropOffs,
  fetchFunnel,
  fetchRecruiterPerformance,
  fetchSources,
  fetchSummary,
  fetchTimeToFill,
} from "@/lib/reports";

// Recharts can't read CSS vars, so the dark-violet tokens are mirrored here.
const chartColors = {
  primary: "hsl(270 91% 65%)",
  border: "hsl(268 40% 28%)",
  axis: "hsl(270 15% 75%)",
  card: "hsl(268 50% 18%)",
  danger: "hsl(0 84% 60%)",
};

const tooltipStyle = {
  background: chartColors.card,
  border: `1px solid ${chartColors.border}`,
  borderRadius: 8,
  fontSize: 12,
};

export function ReportsPage(): JSX.Element {
  const summary = useQuery({ queryKey: ["report-summary"], queryFn: fetchSummary });
  const funnel = useQuery({ queryKey: ["report-funnel"], queryFn: fetchFunnel });
  const sources = useQuery({ queryKey: ["report-sources"], queryFn: fetchSources });
  const dropoffs = useQuery({ queryKey: ["report-dropoffs"], queryFn: fetchDropOffs });
  const ttf = useQuery({ queryKey: ["report-ttf"], queryFn: fetchTimeToFill });
  const perf = useQuery({ queryKey: ["report-perf"], queryFn: fetchRecruiterPerformance });

  if (summary.isError)
    return (
      <p className="text-sm text-destructive">
        Reports are available to the HR Head and TA Team Lead.
      </p>
    );

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Reports</h1>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
        <Kpi label="Open reqs" value={summary.data?.open_requisitions} />
        <Kpi label="Candidates" value={summary.data?.total_candidates} />
        <Kpi label="Active apps" value={summary.data?.active_applications} />
        <Kpi label="Offers out" value={summary.data?.offers_outstanding} />
        <Kpi label="Hires" value={summary.data?.hires} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <ChartCard title="Recruitment funnel">
          {funnel.data && (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={funnel.data.stages} layout="vertical" margin={{ left: 16 }}>
                <CartesianGrid
                  stroke={chartColors.border}
                  strokeDasharray="3 3"
                  horizontal={false}
                />
                <XAxis type="number" stroke={chartColors.axis} fontSize={12} allowDecimals={false} />
                <YAxis
                  type="category"
                  dataKey="label"
                  stroke={chartColors.axis}
                  fontSize={11}
                  width={92}
                />
                <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "transparent" }} />
                <Bar dataKey="count" fill={chartColors.primary} radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        <ChartCard title="Source of candidates">
          {sources.data && (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sources.data}>
                <CartesianGrid stroke={chartColors.border} strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="label" stroke={chartColors.axis} fontSize={11} />
                <YAxis stroke={chartColors.axis} fontSize={12} allowDecimals={false} />
                <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "transparent" }} />
                <Bar dataKey="count" fill={chartColors.primary} radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <ChartCard title="Drop-offs by stage">
          {dropoffs.data && dropoffs.data.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={dropoffs.data}>
                <CartesianGrid stroke={chartColors.border} strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="label" stroke={chartColors.axis} fontSize={11} />
                <YAxis stroke={chartColors.axis} fontSize={12} allowDecimals={false} />
                <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "transparent" }} />
                <Bar dataKey="count" fill={chartColors.danger} radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="grid h-full place-items-center text-sm text-muted-foreground">
              No rejections recorded yet.
            </p>
          )}
        </ChartCard>

        <Card>
          <CardHeader>
            <CardTitle>Recruiter performance</CardTitle>
          </CardHeader>
          <CardContent>
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase tracking-wide text-muted-foreground">
                <tr className="border-b border-border/60">
                  <th className="py-2 pr-4">Recruiter</th>
                  <th className="py-2 pr-4">Candidates</th>
                  <th className="py-2 pr-4">Offers</th>
                  <th className="py-2 pr-4">Hires</th>
                </tr>
              </thead>
              <tbody>
                {perf.data?.map((r) => (
                  <tr key={r.recruiter_id} className="border-b border-border/30">
                    <td className="py-2 pr-4 font-medium">{r.recruiter_name}</td>
                    <td className="py-2 pr-4">{r.candidates}</td>
                    <td className="py-2 pr-4">{r.offers}</td>
                    <td className="py-2 pr-4">{r.hires}</td>
                  </tr>
                ))}
                {perf.data && perf.data.length === 0 && (
                  <tr>
                    <td colSpan={4} className="py-3 text-muted-foreground">
                      No recruiters yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
            {ttf.data?.average_days != null && (
              <p className="mt-4 text-sm text-muted-foreground">
                Average time to fill: <span className="font-medium">{ttf.data.average_days}</span>{" "}
                days
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Kpi({ label, value }: { label: string; value: number | undefined }): JSX.Element {
  return (
    <Card>
      <CardContent className="pt-6">
        <p className="text-2xl font-semibold">{value ?? "—"}</p>
        <p className="text-xs text-muted-foreground">{label}</p>
      </CardContent>
    </Card>
  );
}

function ChartCard({ title, children }: { title: string; children: ReactNode }): JSX.Element {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-72">{children}</div>
      </CardContent>
    </Card>
  );
}
