import { api } from "@/lib/api";

export type NotificationChannel = "email" | "whatsapp" | "in_app";
export type NotificationStatus = "queued" | "sent" | "failed";

export interface AppNotification {
  id: number;
  kind: string;
  channel: NotificationChannel;
  subject: string | null;
  body: string;
  status: NotificationStatus;
  related_application_id: number | null;
  read_at: string | null;
  created_at: string;
}

export interface NotificationFeed {
  unread: number;
  items: AppNotification[];
}

export async function fetchNotifications(): Promise<NotificationFeed> {
  return (await api.get<NotificationFeed>("/notifications")).data;
}

export async function markNotificationRead(id: number): Promise<AppNotification> {
  return (await api.post<AppNotification>(`/notifications/${id}/read`)).data;
}
