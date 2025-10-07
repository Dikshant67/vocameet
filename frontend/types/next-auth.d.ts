import NextAuth, { DefaultSession, DefaultUser } from "next-auth";
import { JWT as DefaultJWT } from "next-auth/jwt";

declare module "next-auth" {
  interface Session {
    user: {
      id?: string;
      email?: string;
      name?: string;
      image?: string;
      session_guid?: string;
    } & DefaultSession["user"];
    jwt?: string; // our custom signed JWT
    accessToken?: string;
  }

  interface User extends DefaultUser {
    id?: string;
  }
}

declare module "next-auth/jwt" {
  interface JWT extends DefaultJWT {
    id?: string;
    googleAccessToken?: string;
  }
}
