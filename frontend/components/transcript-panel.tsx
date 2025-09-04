"use client"

import { useEffect, useRef, useState } from "react"
import { ScrollArea } from "@/components/ui/scroll-area"

type TranscriptItem = {
  id: string
  text: string
  timestamp?: string
  speaker?: "user" | "assistant"
}

export function TranscriptPanel() {
  const [items, setItems] = useState<TranscriptItem[]>([])
  const areaRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const base = process.env.NEXT_PUBLIC_FASTAPI_WS_URL
    if (!base) return
    const url = new URL(base)
    url.pathname = url.pathname.replace(/\/?$/, "/transcript")

    const ws = new WebSocket(url.toString())
    ws.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data)
        setItems((prev) => [...prev, data])
      } catch {
        setItems((prev) => [
          ...prev,
          { id: String(Date.now()), text: typeof evt.data === "string" ? evt.data : "[unparseable]" },
        ])
      }
    }
    ws.onerror = () => {
      console.warn("[v0] Transcript WS error")
    }
    return () => {
      ws.close()
    }
  }, [])

  useEffect(() => {
    areaRef.current?.scrollTo({ top: areaRef.current.scrollHeight, behavior: "smooth" })
  }, [items])

  return (
    <div className="space-y-2">
      <h3 className="font-medium">Live Transcript</h3>
      <ScrollArea className="h-64 rounded border" ref={areaRef as any}>
        <div className="p-3 flex flex-col gap-2">
          {items.length === 0 ? (
            <p className="text-sm text-muted-foreground">Your transcription will appear here.</p>
          ) : (
            items.map((it) => (
              <div key={it.id} className="text-sm leading-relaxed">
                {it.speaker ? (
                  <span className="font-medium mr-1">{it.speaker === "user" ? "You:" : "Assistant:"}</span>
                ) : null}
                <span>{it.text}</span>
              </div>
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  )
}
