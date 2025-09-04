"use client"

import { CalendarDays, Clock, Users, Check } from "lucide-react"
import type { Meeting } from "@/components/meetings-sidebar"
import type { TimeZone } from "@/lib/timezones"
import { cn } from "@/lib/utils"

export function MeetingCard({ meeting, timeZone }: { meeting: Meeting; timeZone: TimeZone }) {
  const date = new Date(meeting.start_iso)
  const dateText = date.toLocaleString(undefined, {
    timeZone: timeZone.tz,
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  })

  const isScheduled = meeting.status === "scheduled"

  return (
    <div
      className={cn("rounded border p-3", isScheduled ? "border-green-600/30" : "border-border", "flex flex-col gap-2")}
      style={isScheduled ? { borderLeft: "4px solid rgb(22,163,74)" } : undefined}
      aria-label={`Meeting ${meeting.title}`}
    >
      <div className="flex items-center justify-between">
        <h4 className="font-medium text-pretty">{meeting.title}</h4>
        {isScheduled && <Check className="h-4 w-4 text-green-600" aria-label="Scheduled" />}
      </div>

      <div className="flex items-center gap-3 text-sm text-muted-foreground">
        <span className="flex items-center gap-1">
          <CalendarDays className="h-4 w-4" aria-hidden />
          {dateText}
        </span>
      </div>

      <div className="flex items-center gap-4 text-sm text-muted-foreground">
        <span className="flex items-center gap-1">
          <Clock className="h-4 w-4" aria-hidden />
          {meeting.duration_min} min
        </span>
        <span className="flex items-center gap-1">
          <Users className="h-4 w-4" aria-hidden />
          {meeting.participants_count}
        </span>
      </div>
    </div>
  )
}
