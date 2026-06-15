import { useState } from "react";

import {
  useMarkAllRead,
  useMarkNotificationRead,
  useNotifications,
  useUnreadCount,
} from "../api/hooks";

export default function NotificationBell() {
  const [open, setOpen] = useState(false);
  const unread = useUnreadCount();
  const notifications = useNotifications();
  const markRead = useMarkNotificationRead();
  const markAll = useMarkAllRead();

  const count = unread.data ?? 0;

  return (
    <div className="relative">
      <button
        className="relative rounded-md p-2 text-slate-500 hover:bg-slate-100"
        onClick={() => setOpen((o) => !o)}
        aria-label="Notifications"
      >
        🔔
        {count > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white">
            {count > 9 ? "9+" : count}
          </span>
        )}
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute right-0 z-50 mt-2 w-80 overflow-hidden rounded-lg border border-slate-200 bg-white shadow-lg">
            <div className="flex items-center justify-between border-b border-slate-100 px-4 py-2">
              <span className="text-sm font-semibold text-slate-700">Notifications</span>
              {count > 0 && (
                <button
                  className="text-xs text-brand-600 hover:underline"
                  onClick={() => markAll.mutate()}
                >
                  Mark all read
                </button>
              )}
            </div>
            <div className="max-h-96 overflow-y-auto">
              {notifications.data?.length === 0 && (
                <div className="px-4 py-6 text-center text-sm text-slate-400">
                  You're all caught up.
                </div>
              )}
              {notifications.data?.map((n) => (
                <button
                  key={n.id}
                  onClick={() => !n.is_read && markRead.mutate(n.id)}
                  className={`block w-full px-4 py-3 text-left text-sm hover:bg-slate-50 ${
                    n.is_read ? "text-slate-500" : "bg-brand-50/40 text-slate-800"
                  }`}
                >
                  <div className="flex items-start gap-2">
                    {!n.is_read && (
                      <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-brand-500" />
                    )}
                    <div>
                      <div>{n.message}</div>
                      <div className="mt-0.5 text-xs text-slate-400">
                        {new Date(n.created_at).toLocaleString()}
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
