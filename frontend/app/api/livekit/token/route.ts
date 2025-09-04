// Issues a LiveKit participant token for the specified room/identity.
// If you prefer your Python starter to issue tokens, set LIVEKIT_TOKEN_ENDPOINT
// and this route will proxy the request.
import { NextResponse } from "next/server"

export async function POST(req: Request) {
  try {
    const { room, identity, voice } = await req.json()

    if (process.env.LIVEKIT_TOKEN_ENDPOINT) {
      const proxied = await fetch(process.env.LIVEKIT_TOKEN_ENDPOINT, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ room, identity, voice }),
      })
      if (!proxied.ok) {
        return NextResponse.json({ error: "Token proxy failed" }, { status: proxied.status })
      }
      const data = await proxied.json()
      return NextResponse.json(data)
    }

    const LIVEKIT_URL = process.env.LIVEKIT_URL
    const LIVEKIT_API_KEY = process.env.LIVEKIT_API_KEY
    const LIVEKIT_API_SECRET = process.env.LIVEKIT_API_SECRET
    if (!LIVEKIT_URL || !LIVEKIT_API_KEY || !LIVEKIT_API_SECRET) {
      return NextResponse.json(
        { error: "Missing LiveKit env vars (LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET)" },
        { status: 500 },
      )
    }

    const { AccessToken } = await import("livekit-server-sdk")
    const at = new AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET, {
      identity: identity || "guest",
      ttl: "1h",
      metadata: voice ? JSON.stringify({ voice }) : undefined,
    })
    at.addGrant({
      room: room || "payjet-room",
      roomJoin: true,
      canPublish: true,
      canSubscribe: true,
      canPublishData: true,
    })
    const jwt = await at.toJwt()

    return NextResponse.json({ token: jwt, url: LIVEKIT_URL })
  } catch (e: any) {
    return NextResponse.json({ error: e.message || "Failed to create token" }, { status: 500 })
  }
}
