import NextAuth, { NextAuthOptions } from "next-auth";
import GoogleProvider from "next-auth/providers/google";
import jwt from "jsonwebtoken";
import { v4 as uuidv4 } from "uuid";

export const authOptions: NextAuthOptions = {
  providers: [
    GoogleProvider({
      clientId: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID!,
      clientSecret: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_SECRET!,
      profile(profile) {
        console.log(profile)
        // 👇 This ensures Google profile info is correctly mapped
        return {
          id: profile.sub,
          name: profile.name,
          email: profile.email,
          image: profile.picture,
        };
      },
    }),
  ],

  secret: process.env.NEXTAUTH_SECRET,

  session: {
    strategy: "jwt",
  },

  callbacks: {
    async jwt({ token, account, user }) {
      console.log("user image"+token?.name)
      if (account && user) {
        token.email = user.email;
        token.name = user.name;
        token.picture = user.image || token.picture || "/user.png"; // ✅ image will now exist
        token.session_guid = token.session_guid || uuidv4();
      }
      return token;
    },

    async session({ session, token }) {
      const signedJwt = jwt.sign(
        {
          email: token.email,
          name: token.name,
          picture: token.picture,
          session_guid: token.session_guid,
        },
        process.env.NEXTAUTH_SECRET!,
        { algorithm: "HS256", expiresIn: "1h" }
      );

      session.jwt = signedJwt;
      console.log("picture"+token.picture);
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
