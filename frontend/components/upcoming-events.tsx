"use client"

import useSWR from "swr"
import { Button } from "@/components/ui/button"

type GCalEvent = {
  id: string
  summary?: string
  start?: { dateTime?: string; timeZone?: string; date?: string }
  end?: { dateTime?: string; timeZone?: string; date?: string }
  conferenceData?: { entryPoints?: { entryPointType?: string; uri?: string }[] }
  htmlLink?: string
}

type ApiResponse = { events: GCalEvent[] } | { error: string }

const fetcher = (url: string) => fetch(url).then((r) => r.json())

export default function UpcomingEvents() {
  const { data, isLoading, error, mutate } = useSWR<ApiResponse>("/api/google/events", fetcher, {
    revalidateOnFocus: false,
  })

  if (isLoading) {
    return <div className="p-4 text-sm text-muted-foreground">Loading upcoming events…</div>
  }

  if (error || (data && "error" in data)) {
    return (
      <div className="p-4 flex items-center justify-between gap-4">
        <div className="text-sm text-red-600">{error ? "Failed to load events." : (data as any).error}</div>
        <Button variant="outline" onClick={() => mutate()}>
          Retry
        </Button>
      </div>
    )
  }

  const events = (data as { events: GCalEvent[] } | undefined)?.events ?? []

  if (!events.length) {
    return (
      <div className="p-4 text-sm text-muted-foreground">
        No upcoming events found. Sign in and make sure your calendar has upcoming events.
      </div>
    )
  }

  return (
    <div className="max-h-[420px] overflow-y-auto divide-y divide-border">
      {events.map((e) => (
        <EventRow key={e.id} e={e} />
      ))}
    </div>
  )
}

function EventRow({ e }: { e: GCalEvent }) {
  const startIso = e.start?.dateTime || (e.start?.date ? `${e.start.date}T00:00:00` : undefined)
  const tz = e.start?.timeZone || Intl.DateTimeFormat().resolvedOptions().timeZone
  const startFmt = startIso
    ? new Date(startIso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short", timeZone: tz })
    : "—"

  const meet = e.conferenceData?.entryPoints?.find((p) => p.entryPointType === "video")?.uri

  return (
    <div className="p-4 flex items-start justify-between gap-4">
      <div className="min-w-0">
        <div className="text-sm font-medium text-pretty">{e.summary || "Untitled event"}</div>
        <div className="text-xs text-muted-foreground mt-1">
          {startFmt} · TZ: {tz}
        </div>
        {meet && (
          <div className="mt-2">
            <a className="text-xs text-blue-600 hover:underline" href={meet} target="_blank" rel="noopener noreferrer">
              Join meeting
            </a>
          </div>
        )}
      </div>
      {e.htmlLink && (
        <a
          href={e.htmlLink}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs text-muted-foreground hover:text-foreground shrink-0"
          aria-label="Open in Google Calendar"
        >
          Open
        </a>
      )}
    </div>
  )
}
