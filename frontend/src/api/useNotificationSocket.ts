import { useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";

import { getAuth } from "../auth/storage";

/**
 * Open a WebSocket to the notifications stream (9.2). On each pushed
 * notification, refresh the feed + unread badge instantly (no polling wait).
 * The JWT is passed in the query string because browsers can't set WS headers.
 */
export function useNotificationSocket() {
  const qc = useQueryClient();

  useEffect(() => {
    const auth = getAuth();
    if (!auth) return;

    let socket: WebSocket | null = null;
    let retry: ReturnType<typeof setTimeout> | null = null;
    let closed = false;

    const connect = () => {
      const proto = window.location.protocol === "https:" ? "wss" : "ws";
      socket = new WebSocket(
        `${proto}://${window.location.host}/ws/notifications/?token=${auth.access}`,
      );

      socket.onmessage = () => {
        qc.invalidateQueries({ queryKey: ["notifications"] });
      };
      socket.onclose = () => {
        if (!closed) retry = setTimeout(connect, 5000); // auto-reconnect
      };
    };

    connect();

    return () => {
      closed = true;
      if (retry) clearTimeout(retry);
      socket?.close();
    };
  }, [qc]);
}
