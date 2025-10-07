"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { signIn, signOut, useSession } from "next-auth/react";
import { ChevronDownIcon } from "@heroicons/react/24/solid";
import { useUser } from "@/app/context/UserContext";
import Image from "next/image";

export default function GoogleSignInButton() {
  const { user, setUser } = useUser();
  const router = useRouter();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const { data: session, status } = useSession();

useEffect(() => {
  // Step 1: On mount — try loading user from localStorage (instant preload)
  const storedUser = localStorage.getItem("user");
  if (!user && storedUser) {
    setUser(JSON.parse(storedUser));
  }

  // Step 2: When session updates
  if (status === "authenticated" && session?.user) {
       {console.log(user?.image)}
    const newUser = {
      name: session.user.name || "",
      email: session.user.email || "",
      image: session.user.image || "/user.png",
    };

    // Update only if changed
    if (
      !user ||
      user.email !== newUser.email ||
      user.image !== newUser.image ||
      user.name !== newUser.name
    ) {
      setUser(newUser);
      localStorage.setItem("user", JSON.stringify(newUser)); // ✅ Save to localStorage
    }
  }

  // Step 3: Clear localStorage when logged out
  if (status === "unauthenticated") {
    setUser(null);
    localStorage.removeItem("user");
  }
}, [status, session]);


  const handleLogin = async () => {
    try {

      await signIn("google", { callbackUrl: "/" });
    } catch (error) {
      console.error("NextAuth login error:", error);
    }
  };

  const handleLogout = async () => {
    try {
      await signOut({ callbackUrl: "/" });
      setIsMenuOpen(false);
    } catch (error) {
      console.error("NextAuth logout error:", error);
    }
  };

  return (
     <div>
    {status === "loading" ? (
      // While NextAuth is verifying session, show a small placeholder
      <div className="flex items-center gap-2">
        <div className="h-8 w-8 animate-pulse rounded-full bg-gray-300" />
        <span className="text-gray-500 text-sm">Loading...</span>
      </div>
    ) : user ? (
   
      // Authenticated state
      <div className="relative flex items-center gap-3">
        <Image
          src={user?.image || "./user.png"}
          alt="Profile"
          width={32} // 👈 Must provide width
        height={32} // 👈 Must provide height
          className="h-8 w-8 cursor-pointer rounded-full"
        
        />
        <div className="flex items-center gap-1">
          <span className="font-medium">{user.name}</span>
          <button
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="text-sm text-gray-600 hover:text-gray-800 focus:outline-none"
          >
            <ChevronDownIcon className="h-4 w-4" />
          </button>
        </div>
        {isMenuOpen && (
          <div className="absolute top-full right-0 mt-2 rounded-md bg-white shadow-lg">
            <button
              onClick={() => router.push("/profile")}
              className="block w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100"
            >
              Profile
            </button>
            <button
              onClick={handleLogout}
              className="block w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100"
            >
              Logout
            </button>
          </div>
        )}
      </div>
    ) : (
      // Unauthenticated state
      <button
        onClick={handleLogin}
        className="flex items-center gap-2 rounded-lg bg-gray-800 px-4 py-2 text-white shadow-md transition hover:bg-gray-700"
      >
        <svg className="h-5 w-5" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
          <path
            fill="#FFC107"
            d="M43.611,20.083H42V20H24v8h11.303c-1.649,4.657-6.08,8-11.303,8c-6.627,0-12-5.373-12-12s5.373-12,12-12
            c3.059,0,5.842,1.154,7.961,3.039l5.657-5.657C34.046,6.053,29.268,4,24,4C12.955,4,4,12.955,4,24s8.955,20,20,20
            s20-8.955,20-20C44,22.659,43.862,21.35,43.611,20.083z"
          />
        </svg>
        Sign in with Google
      </button>
    )}
  </div>
);
  
}
