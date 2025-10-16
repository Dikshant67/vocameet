import { NextResponse } from "next/server";
import {
  AccessToken,
  type AccessTokenOptions,
  type VideoGrant,
} from "livekit-server-sdk";
import { RoomConfiguration } from "@livekit/protocol";
import { getServerSession } from "next-auth";
import { authOptions } from "@/app/api/auth/[...nextauth]/route";
import { getSessionGuid } from '@/lib/session';



// NOTE: environment variables must be defined in `.env.local`
const API_KEY = process.env.LIVEKIT_API_KEY;
const API_SECRET = process.env.LIVEKIT_API_SECRET;
const LIVEKIT_URL = process.env.LIVEKIT_URL;

// don't cache the results
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
    const sessionGuid = getSessionGuid();
    // ✅ get the user from the NextAuth session
    const session = await getServerSession(authOptions);
    // console.log(session);
    
    if (!session || !session.user) {
      console.log("Unauthorized")
      return new NextResponse("Unauthorized", { status: 401 });
    }

    const { name, email , session_guid} = session.user;

    // Parse agent configuration from request body
    const body = await req.json();
    const agentName: string = body?.room_config?.agents?.[0]?.agent_name;

    // Generate participant token
    const participantName = 'user';
    const participantIdentity = `voice_assistant_user_${Math.floor(Math.random() * 10_000)}`;
    const roomName = `voice_assistant_room_${Math.floor(Math.random() * 10_000)}`;

    const participantToken = await createParticipantToken(
      {
        identity: participantIdentity,
        name: participantName, 
    
        metadata: JSON.stringify({ agentName,sessionGuid }),
      },
      roomName,
      agentName
    );

    // Return connection details
    const data: ConnectionDetails = {
      serverUrl: LIVEKIT_URL,
      roomName,
      participantToken: participantToken,
      participantName,
    };
    const headers = new Headers({
      'Cache-Control': 'no-store',
    });
    return NextResponse.json(data, { headers });
  } catch (error) {
    if (error instanceof Error) {
      console.error(error);
      return new NextResponse(error.message, { status: 500 });
    }
  }
}

function createParticipantToken(
  userInfo: AccessTokenOptions,
  roomName: string,
  agentName?: string
): Promise<string> {
  const at = new AccessToken(API_KEY, API_SECRET, {
    ...userInfo,
    ttl: '15m',
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
