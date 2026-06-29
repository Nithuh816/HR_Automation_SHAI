import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { fetchNotifications, markNotificationRead } from "@/lib/notifications";

export function NotificationsPage(): JSX.Element {
  const qc = useQueryClient();
  const feed = useQuery({ queryKey: ["notifications"], queryFn: fetchNotifications });
  const read = useMutation({
    mutationFn: (id: number) => markNotificationRead(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Notifications</h1>
        {feed.data && feed.data.unread > 0 && (
          <span className="rounded-md bg-primary/15 px-2 py-1 text-xs text-primary">
            {feed.data.unread} unread
          </span>
        )}
      </div>

      <Card>
        <CardContent className="pt-6">
          {feed.isLoading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : feed.data && feed.data.items.length === 0 ? (
            <p className="text-sm text-muted-foreground">You have no notifications.</p>
          ) : (
            <ul className="divide-y divide-border/40">
              {feed.data?.items.map((n) => (
                <li key={n.id} className="flex items-start justify-between gap-4 py-3">
                  <div>
                    <p
                      className={
                        n.read_at ? "text-sm text-muted-foreground" : "text-sm font-medium"
                      }
                    >
                      {n.body}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(n.created_at).toLocaleString()}
                    </p>
                  </div>
                  {!n.read_at && (
                    <Button
                      size="sm"
                      variant="ghost"
                      disabled={read.isPending}
                      onClick={() => read.mutate(n.id)}
                    >
                      Mark read
                    </Button>
                  )}
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
