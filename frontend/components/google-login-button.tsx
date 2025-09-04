"use client"

import { signIn, signOut, useSession } from "next-auth/react"
import { Button } from "@/components/ui/button"

export function GoogleLoginButton() {
  const { data: session, status } = useSession()
  const loading = status === "loading"

  if (loading) {
    return (
      <Button disabled variant="outline" className="min-w-32 bg-transparent">
        Loading…
      </Button>
    )
  }

  if (session) {
    return (
      <div className="flex items-center gap-2">
        <Button variant="outline" onClick={() => signOut()} className="min-w-32">
          Sign out
        </Button>
      </div>
    )
  }

  return (
    <Button className="bg-blue-600 hover:bg-blue-700 text-white" onClick={() => signIn("google", { callbackUrl: "/" })}>
      Sign in with Google
    </Button>
  )
}
