"use client"

import useSWR from "swr"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { MeetingCard } from "@/components/meeting-card"
import type { TimeZone } from "@/lib/timezones"

export type Meeting = {
  id: string
  title: string
  start_iso: string
  duration_min: number
  participants_count: number
  status: "scheduled" | "pending" | "canceled"
}

const fetcher = (url: string) => fetch(url).then((r) => r.json())

export function MeetingsSidebar({ timeZone }: { timeZone: TimeZone }) {
  const { data, isLoading } = useSWR<Meeting[]>(`/api/meetings`, fetcher)

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="text-balance">Upcoming Meetings</CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[540px]">
          <div className="flex flex-col gap-3">
            {isLoading ? (
              <p className="text-sm text-muted-foreground">Loading meetings...</p>
            ) : data?.length ? (
              data.map((m) => <MeetingCard key={m.id} meeting={m} timeZone={timeZone} />)
            ) : (
              <p className="text-sm text-muted-foreground">No meetings scheduled.</p>
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  )
}
