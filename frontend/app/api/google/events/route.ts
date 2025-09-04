import { NextResponse } from "next/server"
import { getServerSession } from "next-auth"
import { authOptions } from "@/lib/auth"

export async function GET() {
  try {
    const session = await getServerSession(authOptions)
    if (!session || !(session as any).accessToken) {
      return NextResponse.json({ error: "Not signed in" }, { status: 401 })
    }

    const accessToken = (session as any).accessToken as string
    const now = new Date().toISOString()

    const url = new URL("https://www.googleapis.com/calendar/v3/calendars/primary/events")
    url.searchParams.set("timeMin", now)
    url.searchParams.set("singleEvents", "true")
    url.searchParams.set("orderBy", "startTime")
    url.searchParams.set("maxResults", "25")
    url.searchParams.set("conferenceDataVersion", "1")

    const res = await fetch(url, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
      cache: "no-store",
    })

    if (!res.ok) {
      const text = await res.text()
      return NextResponse.json({ error: `Google API error: ${text}` }, { status: res.status })
    }

    const data = await res.json()
    const events = Array.isArray(data.items) ? data.items : []

    return NextResponse.json({ events })
  } catch (e: any) {
    return NextResponse.json({ error: e.message || "Unexpected error" }, { status: 500 })
  }
}
