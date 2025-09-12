// src/components/GoogleSignInButton.tsx (or similar file)
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ChevronDownIcon } from "@heroicons/react/24/solid";
import { useGoogleLogin } from "@react-oauth/google"; // <-- IMPORT THE HOOK
import { useUser } from "@/app/context/UserContext";

// Keep your DecodedJWT interface if you need it, but we'll get user info from the backend now
interface DecodedJWT {
  name: string;
  email: string;
  picture: string;
  [key: string]: any;
}

export default function GoogleSignInButton() {
  const { user, setUser } = useUser();
  const router = useRouter();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  // Use the hook to handle the login flow
  const login = useGoogleLogin({
    // This is the key change: we want an authorization 'code'
    flow: "auth-code",
    // This function will be called with the 'code' after the user consents
    onSuccess: async (codeResponse) => {
      console.log("Authorization Code received:", codeResponse.code);
      try {
        // Send the one-time authorization code to your backend
        const response = await fetch("http://localhost:8000/auth/google", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include", // Important for cookies/sessions
          // The body now contains the code, not an ID token
          body: JSON.stringify({ code: codeResponse.code }),
        });

        if (!response.ok) {
          throw new Error("Failed to authenticate with backend.");
        }

        // Assume your backend returns user info after successful token exchange
        const backendUser = await response.json();

        // Set the user in your context with data from your backend
        setUser({
          name: backendUser.name,
          email: backendUser.email,
          picture: backendUser.picture,
        });
      } catch (error) {
        console.error("Authentication code exchange failed:", error);
      }
    },
    onError: (error) => console.error("❌ Google login error", error),
    // Ensure you request the calendar scope here
    scope: "openid email profile https://www.googleapis.com/auth/calendar",
  });

  const handleLogout = async () => {
    await fetch("http://localhost:8000/logout", {
      method: "POST",
      credentials: "include",
    });
    setUser(null);
    router.push("/");
    setIsMenuOpen(false);
  };

  // The rest of your JSX remains largely the same, but the button now triggers the 'login' function
  return (
    <div>
      {user ? (
        // --- Your existing logged-in user UI (this part is fine) ---
        <div className="relative flex items-center gap-3">
          <img
            src={user.picture}
            alt="Profile"
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
        // --- Replace the <GoogleLogin> component with a simple button ---
        <button
          onClick={() => login()}
          className="flex items-center gap-2 rounded-lg bg-gray-800 px-4 py-2 text-white shadow-md transition hover:bg-gray-700"
        >
          {/* You can add the Google icon here */}
          <svg
            className="h-5 w-5"
            viewBox="0 0 48 48"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              fill="#FFC107"
              d="M43.611,20.083H42V20H24v8h11.303c-1.649,4.657-6.08,8-11.303,8c-6.627,0-12-5.373-12-12s5.373-12,12-12c3.059,0,5.842,1.154,7.961,3.039l5.657-5.657C34.046,6.053,29.268,4,24,4C12.955,4,4,12.955,4,24s8.955,20,20,20s20-8.955,20-20C44,22.659,43.862,21.35,43.611,20.083z"
            />
            <path
              fill="#FF3D00"
              d="M6.306,14.691l6.571,4.819C14.655,15.108,18.961,12,24,12c3.059,0,5.842,1.154,7.961,3.039l5.657-5.657C34.046,6.053,29.268,4,24,4C16.318,4,9.656,8.337,6.306,14.691z"
            />
            <path
              fill="#4CAF50"
              d="M24,44c5.166,0,9.86-1.977,13.409-5.192l-6.19-5.238C29.211,35.091,26.715,36,24,36c-5.223,0-9.657-3.356-11.303-7.962l-6.571,4.819C9.656,39.663,16.318,44,24,44z"
            />
            <path
              fill="#1976D2"
              d="M43.611,20.083H42V20H24v8h11.303c-0.792,2.237-2.231,4.166-4.087,5.574l6.19,5.238C42.012,35.84,44,30.138,44,24C44,22.659,43.862,21.35,43.611,20.083z"
            />
          </svg>
          Sign in with Google
        </button>
      )}
    </div>
  );
}