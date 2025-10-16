// app/components/UpcomingMeetings.tsx
"use client";

import { useMeetings } from "@/hooks/useMeetings";

function formatDateTime(iso: string) {
  try {
    const d = new Date(iso);
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(d);
  } catch {
    return iso;
  }
}

export default function UpcomingMeetings({ enabled }: { enabled: boolean }) {
  const { meetings, loading, error } = useMeetings(enabled);

  if (!enabled) return null;

  return (
    <div className="bg-background/95 border-bg2 fixed top-[3cm] right-50 z-40 mr-3 max-h-[70vh] w-80 rounded-xl border p-3 shadow-md backdrop-blur">
      <h3 className="mb-2 text-sm font-semibold">Upcoming Meetings</h3>
      {loading && <p className="text-muted-foreground text-xs">Loading…</p>}
      {error && <p className="text-destructive-foreground text-xs">{error}</p>}
      {!loading && !error && meetings.length === 0 && (
        <p className="text-muted-foreground text-xs">No upcoming meetings</p>
      )}
      <div className="max-h-[60vh] space-y-2 overflow-y-auto pr-1">
        {meetings.map((m) => {
          const participantCount = m.attendees?.length ?? 0;
          return (
            <div key={m.id} className="border-bg2 rounded-lg border p-2">
              <div className="truncate text-sm font-medium" title={m.title}>
                {m.title || "(No title)"}
              </div>
              <div className="text-muted-foreground text-[11px]">
                {formatDateTime(m.start)}
              </div>
              <div className="text-muted-foreground text-[11px]">
                Participants: {participantCount}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
