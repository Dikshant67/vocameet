// app/api/auth/[...nextauth]/route.ts
import NextAuth, { NextAuthOptions } from "next-auth";
import GoogleProvider from "next-auth/providers/google";
import jwt from "jsonwebtoken";
import { v4 as uuidv4 } from 'uuid';

export const authOptions: NextAuthOptions = {
  providers: [
    GoogleProvider({
      clientId: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID!,
      clientSecret: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_SECRET!,
    }),
  ],

  secret: process.env.NEXTAUTH_SECRET,

  session: {
    strategy: "jwt", // store session in JWT, not database
  },

  callbacks: {
    async jwt({ token, account, user }) {
      // First time user logs in
      if (account && user) {
        token.email = user.email;
        token.name = user.name;
        token.picture = user.image;
        token.session_guid = token.session_guid || uuidv4();
      }
      return token;
    },

    async session({ session, token }) {
      // 🔑 Sign a custom JWT that FastAPI can validate
      const signedJwt = jwt.sign(
        {
          email: token.email,
          name: token.name,
          picture: token.picture,
          session_guid: token.session_guid, 
        },
        process.env.NEXTAUTH_SECRET!, // must match FastAPI NEXTAUTH_SECRET
        {
          algorithm: "HS256",
          expiresIn: "1h",
        }
      );

      session.jwt = signedJwt; // ✅ real string token
      session.user = {
        ...session.user,
        id: token.sub as string,
        email: token.email as string,
        name: token.name as string,
        image: token.picture as string,
        session_guid: token.session_guid as string, 
      };

      return session;
    },
  },
};

const handler = NextAuth(authOptions);
export { handler as GET, handler as POST };
