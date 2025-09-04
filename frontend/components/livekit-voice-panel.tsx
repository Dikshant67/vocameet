"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import { Button } from "@/components/ui/button"
import { LiveKitRoom, RoomAudioRenderer, ControlBar, useRoomContext } from "@livekit/components-react"
import "@livekit/components-styles"
import type { Room } from "livekit-client"

type Props = {
  roomName: string
  identity: string
  voice: string
}

type TokenResponse = {
  token: string
  url: string
}

export default function LiveKitVoicePanel({ roomName, identity, voice }: Props) {
  const [connecting, setConnecting] = useState(false)
  const [connected, setConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lk, setLk] = useState<TokenResponse | null>(null)
  const [showRoom, setShowRoom] = useState(false)
  const [transcript, setTranscript] = useState<string[]>([])

  const appendTranscript = useCallback((line: string) => {
    setTranscript((prev) => [...prev, line])
  }, [])

  const start = async () => {
    try {
      setError(null)
      setConnecting(true)
      const res = await fetch("/api/livekit/token", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ room: roomName, identity, voice }),
      })
      if (!res.ok) {
        const t = await res.text()
        throw new Error(t || "Failed to fetch token")
      }
      const data: TokenResponse = await res.json()
      setLk(data)
      setShowRoom(true)
    } catch (e: any) {
      setError(e.message || "Error starting voice")
    } finally {
      setConnecting(false)
    }
  }

  // Paste your LiveKit starter voice button here.
  // Example:
  // <YourLiveKitButton onClick={start} onTranscript={(t) => appendTranscript(t)} />

  return (
    <div className="flex flex-col gap-3">
      <div className="flex gap-2">
        {!connected && (
          <Button className="bg-blue-600 hover:bg-blue-700 text-white" disabled={connecting} onClick={start}>
            {connecting ? "Starting…" : "Start voice chat"}
          </Button>
        )}
        {error && <span className="text-sm text-red-600">{error}</span>}
      </div>

      {showRoom && lk && (
        <div className="rounded-md border border-border">
          <LiveKitRoom
            token={lk.token}
            serverUrl={lk.url}
            connect={true}
            audio={true}
            video={false}
            onConnected={() => setConnected(true)}
            onDisconnected={() => setConnected(false)}
          >
            <RoomAudioRenderer />
            <div className="p-3 border-b border-border text-sm">
              Connected to room "{roomName}" as "{identity}" · Voice: {voice}
            </div>

            <DataListener onTranscript={appendTranscript} />

            <div className="p-3">
              <div className="h-40 overflow-y-auto rounded-md border border-border bg-background p-2 text-sm">
                {transcript.length === 0 ? (
                  <div className="text-muted-foreground">Transcription will appear here…</div>
                ) : (
                  <ul className="space-y-1">
                    {transcript.map((t, i) => (
                      <li key={i}>{t}</li>
                    ))}
                  </ul>
                )}
              </div>
            </div>

            <div className="p-3 border-t border-border">
              <ControlBar controls={{ camera: false, screenShare: false }} />
            </div>
          </LiveKitRoom>
        </div>
      )}
    </div>
  )
}

function DataListener({ onTranscript }: { onTranscript: (line: string) => void }) {
  const room = useRoomContext() as Room
  const initialized = useRef(false)

  useEffect(() => {
    if (!room || initialized.current) return
    initialized.current = true

    const onData = (payload: Uint8Array) => {
      try {
        const str = new TextDecoder().decode(payload)
        try {
          const json = JSON.parse(str)
          if (json?.type === "transcript" && typeof json.text === "string") {
            onTranscript(json.text)
          } else if (json?.text) {
            onTranscript(String(json.text))
          } else {
            onTranscript(str)
          }
        } catch {
          onTranscript(str)
        }
      } catch {
        // ignore decode errors
      }
    }

    room.on("dataReceived", onData)
    return () => {
      room.off("dataReceived", onData)
    }
  }, [room, onTranscript])

  return null
}
