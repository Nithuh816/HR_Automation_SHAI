import { Briefcase, TrendingUp, UserCheck, Users } from "lucide-react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

// Recharts sets `fill`/`stroke` as SVG presentation attributes, which don't
// resolve CSS variables. Keep these in sync with apps/web/src/styles/index.css.
const chartColors = {
  primary: "hsl(270 91% 65%)",
  border: "hsl(268 40% 28%)",
  axis: "hsl(270 15% 75%)",
  card: "hsl(268 50% 18%)",
};

const stageData = [
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

const kpis = [
  { label: "Open requisitions", value: 12, icon: Briefcase, delta: "+2 this week" },
  { label: "Active candidates", value: 138, icon: Users, delta: "+18 this week" },
  { label: "Joined (MTD)", value: 7, icon: UserCheck, delta: "+3 vs last month" },
  { label: "Avg. time-to-fill", value: "24d", icon: TrendingUp, delta: "−4d vs last month" },
];

export function DashboardPage(): JSX.Element {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">HR Dashboard</h1>
        <p className="text-sm text-muted-foreground">SHAI Health · Talent Acquisition overview</p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        {kpis.map(({ label, value, icon: Icon, delta }) => (
          <Card key={label}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
              <Icon className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-semibold">{value}</div>
              <div className="mt-1 text-xs text-muted-foreground">{delta}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recruitment funnel</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stageData}>
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
