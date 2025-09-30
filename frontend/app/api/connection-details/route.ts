import { NextResponse } from "next/server";
import {
  AccessToken,
  type AccessTokenOptions,
  type VideoGrant,
} from "livekit-server-sdk";
import { RoomConfiguration } from "@livekit/protocol";
import { getServerSession } from "next-auth";
import { authOptions } from "@/app/api/auth/[...nextauth]/route";

// NOTE: environment variables must be defined in `.env.local`
const API_KEY = process.env.LIVEKIT_API_KEY;
const API_SECRET = process.env.LIVEKIT_API_SECRET;
const LIVEKIT_URL = process.env.LIVEKIT_URL;

export const revalidate = 0;

export type ConnectionDetails = {
  serverUrl: string;
  roomName: string;
  participantName: string;
  participantToken: string; 
};

export async function POST(req: Request) {
  try {
    if (!LIVEKIT_URL) throw new Error("LIVEKIT_URL is not defined");
    if (!API_KEY) throw new Error("LIVEKIT_API_KEY is not defined");
    if (!API_SECRET) throw new Error("LIVEKIT_API_SECRET is not defined");

    // ✅ get the user from the NextAuth session
    const session = await getServerSession(authOptions);
    console.log(session);
    if (!session || !session.user) {
      console.log("Unauthorized")
      return new NextResponse("Unauthorized", { status: 401 });
    }

    const { name, email } = session.user;

    // Parse agent configuration from request body
    const body = await req.json();
    console.log(body);
    const agentName: string | undefined =
      body?.room_config?.agents?.[0]?.agent_name;

    // ✅ safer participant naming
    const participantName = name ?? email ?? "Anonymous";
    const participantIdentity = email ?? name ?? "anonymous";
    const roomName = `${participantName.replace(/\s+/g, "_")}_voice_agent_room`;

    const participantToken = await createParticipantToken(
      {
        identity: participantIdentity,
        name: participantName,
        metadata: JSON.stringify({ agentName }),
      },
      roomName,
      agentName
    );

    const data: ConnectionDetails = {
      serverUrl: LIVEKIT_URL,
      roomName,
      participantToken,
      participantName,
    };

    return NextResponse.json(data, {
      headers: { "Cache-Control": "no-store" },
    });
  } catch (error) {
    console.error(error);
    if (error instanceof Error) {
      return new NextResponse(error.message, { status: 500 });
    }
    return new NextResponse("Internal Server Error", { status: 500 });
  }
}

function createParticipantToken(
  userInfo: AccessTokenOptions,
  roomName: string,
  agentName?: string
): Promise<string> {
  const at = new AccessToken(API_KEY, API_SECRET, {
    ...userInfo,
    ttl: "15m",
  });

  const grant: VideoGrant = {
    room: roomName,
    roomJoin: true,
    canPublish: true,
    canPublishData: true,
    canSubscribe: true,
  };
  at.addGrant(grant);

  if (agentName) {
    at.roomConfig = new RoomConfiguration({
      agents: [{ agentName }],
    });
  }

  return at.toJwt();
}
