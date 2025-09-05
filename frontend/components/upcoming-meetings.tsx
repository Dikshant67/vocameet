

import React, { useEffect, useMemo, useState } from "react";

interface MeetingItem {
  id: string;
  title: string;
  start: string; // ISO string
  end: string;   // ISO string
  attendees?: { email?: string; responseStatus?: string }[];
  
}

interface ApiResponse {
  availability: MeetingItem[];
}
interface UpcomingMeetings{
  disabled: boolean;
  startButtonText: string;
  onStartCall: () => void;
}
function formatDateTime(iso: string) {
  try {
    const d = new Date(iso);
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(d);
  } catch (e) {
    return iso;
  }
}

export default function UpcomingMeetings({disabled}) {
  const [meetings, setMeetings] = useState<MeetingItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const backendBaseUrl = useMemo(() => {
    return process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
        const start = new Date().toISOString();
        const end = new Date(Date.now() + 1000 * 60 * 60 * 24 * 30).toISOString(); // +30 days
        const url = new URL("/calendar/events", backendBaseUrl);
        url.searchParams.set("start", start);
        url.searchParams.set("end", end);
        url.searchParams.set("timezone", tz);
        const res = await fetch(url.toString(), { signal: controller.signal });
        if (!res.ok) {
          throw new Error(`Failed to fetch meetings: ${res.status}`);
        }
        const data: ApiResponse = await res.json();
        setMeetings(data?.availability ?? []);
      } catch (e: any) {
        if (e.name !== "AbortError") {
          setError(e.message || "Failed to load meetings");
        }
      } finally {
        setLoading(false);
      }
    }

    load();
    return () => controller.abort();
  }, [backendBaseUrl]);
  if (disabled) {
    return null;
  }
  return (

<div  className="bg-background/95 border-bg2 fixed right-50 top-[3cm] z-40 mr-3 w-80 max-h-[70vh] rounded-xl border p-3 shadow-md backdrop-blur">
      <h3 className="text-sm font-semibold mb-2">Upcoming Meetings</h3>
      {loading && <p className="text-xs text-muted-foreground">Loading…</p>}
      {error && <p className="text-xs text-destructive-foreground">{error}</p>}
      {!loading && !error && meetings.length === 0 && (
        <p className="text-xs text-muted-foreground">No upcoming meetings</p>
      )}
      <div className="overflow-y-auto pr-1 space-y-2 max-h-[60vh]">
        {meetings.map((m) => {
          const participantCount = m.attendees?.length ?? 0;
          return (
            <div key={m.id} className="border border-bg2 rounded-lg p-2">
              <div className="text-sm font-medium truncate" title={m.title}>{m.title || "(No title)"}</div>
              <div className="text-[11px] text-muted-foreground">{formatDateTime(m.start)}</div>
              <div className="text-[11px] text-muted-foreground">Participants: {participantCount}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}