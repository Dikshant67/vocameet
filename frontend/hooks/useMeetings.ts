"use client";
import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";

interface MeetingItem {
  id: string;
  title: string;
  start: string;
  end: string;
  attendees?: { email?: string; responseStatus?: string }[];
}

interface ApiResponse {
  availability: MeetingItem[];
}

export function useMeetings(enabled: boolean) {
  const [meetings, setMeetings] = useState<MeetingItem[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const { data: session } = useSession();

  useEffect(() => {
  
    if (!enabled || !session?.jwt) return; // ✅ use JWT, not Google accessToken

    const controller = new AbortController();

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
        const start = new Date().toISOString();
        const end = new Date(Date.now() + 1000 * 60 * 60 * 24 * 30).toISOString();

        const url = new URL(
                         "/calendar/events",
                        process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"
                              );

        url.searchParams.set("start", start);
        url.searchParams.set("end", end);
        url.searchParams.set("timezone", tz);

        const res = await fetch(url.toString(), {
          signal: controller.signal,
          headers: {
            Authorization: `Bearer ${session.jwt}`, // ✅ signed NextAuth token
            "Content-Type": "application/json",
          },
          credentials: "include",
        });
        
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
  }, [enabled, session?.jwt]); // ✅ depend on JWT

  return { meetings, loading, error };
}
