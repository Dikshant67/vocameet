"use client";

import { ReactNode } from "react";
import { SessionProvider } from "next-auth/react";
import { GoogleOAuthProvider } from "@react-oauth/google";
import { UserProvider } from "./context/UserContext";

interface ProvidersProps {
  children: ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  return (
    <SessionProvider   refetchInterval={1 * 60} // fetch session every 5 mins
  refetchOnWindowFocus={false}>
      <GoogleOAuthProvider clientId={process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID!}>
        <UserProvider>{children}</UserProvider>
      </GoogleOAuthProvider>
    </SessionProvider>
  );
}
