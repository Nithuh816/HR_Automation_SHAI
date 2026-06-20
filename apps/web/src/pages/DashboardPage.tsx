import { useQuery } from "@tanstack/react-query";
import { Briefcase, CheckCircle2, Inbox, Users } from "lucide-react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/lib/auth";
import { fetchSummary } from "@/lib/requisitions";

// Recharts sets `fill`/`stroke` as SVG presentation attributes, which don't
// resolve CSS variables. Keep these in sync with apps/web/src/styles/index.css.
const chartColors = {
  primary: "hsl(270 91% 65%)",
  border: "hsl(268 40% 28%)",
  axis: "hsl(270 15% 75%)",
  card: "hsl(268 50% 18%)",
};

// Candidate funnel is sample data until M3 wires real candidates.
const sampleFunnel = [
  { stage: "Sourced", count: 47 },
  { stage: "L1", count: 31 },
  { stage: "L2", count: 22 },
  { stage: "L3", count: 14 },
  { stage: "L4", count: 9 },
  { stage: "L5", count: 6 },
  { stage: "L6", count: 4 },
  { stage: "Offer", count: 3 },
  { stage: "Joined", count: 2 },
];

export function DashboardPage(): JSX.Element {
  const { user } = useAuth();
  const summary = useQuery({ queryKey: ["req-summary"], queryFn: fetchSummary });
  const s = summary.data;

  const open = s ? s.submitted + s.assigned + s.on_hold : 0;
  const kpis = [
    { label: "Open requisitions", value: open, icon: Briefcase },
    { label: "In triage", value: s?.submitted ?? 0, icon: Inbox },
    { label: "Open headcount", value: s?.open_headcount ?? 0, icon: Users },
    { label: "Filled", value: s?.filled ?? 0, icon: CheckCircle2 },
  ];

  const statusData = s
    ? [
        { status: "Triage", count: s.submitted },
        { status: "Assigned", count: s.assigned },
        { status: "On hold", count: s.on_hold },
        { status: "Filled", count: s.filled },
        { status: "Cancelled", count: s.cancelled },
      ]
    : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">
          {user ? `Welcome, ${user.name.split(" ")[0]}` : "HR Dashboard"}
        </h1>
        <p className="text-sm text-muted-foreground">SHAI Health · Talent Acquisition overview</p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        {kpis.map(({ label, value, icon: Icon }) => (
          <Card key={label}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
              <Icon className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-semibold">{summary.isLoading ? "…" : value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Requisitions by status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={statusData}>
                <CartesianGrid stroke={chartColors.border} strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="status" stroke={chartColors.axis} fontSize={12} />
                <YAxis stroke={chartColors.axis} fontSize={12} allowDecimals={false} />
                <Tooltip
                  contentStyle={{
                    background: chartColors.card,
                    border: `1px solid ${chartColors.border}`,
                    borderRadius: 8,
                  }}
                />
                <Bar dataKey="count" fill={chartColors.primary} radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Recruitment funnel</CardTitle>
          <p className="text-xs text-muted-foreground">Sample data — candidate pipeline arrives in M3.</p>
        </CardHeader>
        <CardContent>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sampleFunnel}>
                <CartesianGrid stroke={chartColors.border} strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="stage" stroke={chartColors.axis} fontSize={12} />
                <YAxis stroke={chartColors.axis} fontSize={12} />
                <Tooltip
                  contentStyle={{
                    background: chartColors.card,
                    border: `1px solid ${chartColors.border}`,
                    borderRadius: 8,
                  }}
                />
                <Bar dataKey="count" fill={chartColors.primary} radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
