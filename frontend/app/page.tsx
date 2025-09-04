"use client"

import { useSession } from "next-auth/react"
import { useState } from "react"
import { GoogleLoginButton } from "@/components/google-login-button"
import UpcomingEvents from "@/components/upcoming-events"
import LiveKitVoicePanel from "@/components/livekit-voice-panel"
import { cn } from "@/lib/utils"

export default function HomePage() {
  const { data: session } = useSession()
  const [voice, setVoice] = useState("alloy")
  const [roomName, setRoomName] = useState("payjet-room")
  const [identity, setIdentity] = useState("guest")

  return (
    <main className="min-h-dvh bg-background text-foreground">
      <header className="border-b border-border">
        <div className="mx-auto max-w-5xl px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-md bg-blue-600" aria-hidden />
            <div>
              <h1 className="text-lg font-semibold text-balance">VocaMeet</h1>
              <p className="text-xs text-muted-foreground">Manage your meetings with a live voice agent</p>
            </div>
          </div>
          <GoogleLoginButton />
        </div>
      </header>

      <section className="mx-auto max-w-5xl px-4 py-6">
        <div className="grid gap-6 md:grid-cols-2">
        

          <div className="flex flex-col gap-4">
            <h2 className="text-base font-semibold">Voice agent</h2>

            <div className="rounded-lg border border-border bg-card p-4 flex flex-col gap-3">
              <label className="text-sm font-medium" htmlFor="voice">
                Voice
              </label>
              <select
                id="voice"
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-blue-600"
                value={voice}
                onChange={(e) => setVoice(e.target.value)}
              >
                <option value="alloy">Alloy</option>
                <option value="verse">Verse</option>
                <option value="aria">Aria</option>
              </select>

              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-2">
                  <label className="text-sm font-medium" htmlFor="room">
                    Room name
                  </label>
                  <input
                    id="room"
                    className="rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-blue-600"
                    value={roomName}
                    onChange={(e) => setRoomName(e.target.value)}
                    placeholder="payjet-room"
                  />
                </div>
                <div className="flex flex-col gap-2">
                  <label className="text-sm font-medium" htmlFor="identity">
                    Your identity
                  </label>
                  <input
                    id="identity"
                    className="rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-blue-600"
                    value={identity}
                    onChange={(e) => setIdentity(e.target.value)}
                    placeholder="guest"
                  />
                </div>
              </div>

              <LiveKitVoicePanel roomName={roomName} identity={identity} voice={voice} />
              <p className="text-xs text-muted-foreground">
                Paste your LiveKit starter voice button inside this panel (see placeholder) to start voice chat.
                Transcription will display below.
              </p>
            </div>
            
         
          </div>
            <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold">Upcoming meetings</h2>
              <div className="text-xs text-muted-foreground">
                {session ? `Signed in as ${session.user?.email ?? "user"}` : "Not signed in"}
              </div>
            </div>
            <div className={cn("rounded-lg border border-border bg-card")}>
              <UpcomingEvents />
            </div>
          </div>
             <div className="rounded-lg border border-border bg-card p-4">
              <h3 className="text-sm font-semibold mb-2">Timezone</h3>
              <div className="text-sm">Browser timezone: {Intl.DateTimeFormat().resolvedOptions().timeZone}</div>
            </div>
        </div>
        
      </section>
    </main>
  )
}
