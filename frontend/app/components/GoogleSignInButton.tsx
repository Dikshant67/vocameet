"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { jwtDecode } from "jwt-decode";
import { ChevronDownIcon } from "@heroicons/react/24/solid";
import { CredentialResponse, GoogleLogin } from "@react-oauth/google";
import { useUser } from "@/app/context/UserContext";

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

  const handleSuccess = async (credentialResponse: CredentialResponse) => {
    try {
      const idToken = credentialResponse.credential;
      if (!idToken) return;

      const decoded: DecodedJWT = jwtDecode(idToken);
      if (decoded.name && decoded.email && decoded.picture) {
        setUser({
          name: decoded.name,
          email: decoded.email,
          picture: decoded.picture,
        });
      }

      await fetch("http://localhost:8000/auth/google", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ token: idToken }),
      });
    } catch (error) {
      console.error("Google login failed:", error);
    }
  };

  const handleLogout = async () => {
    await fetch("http://localhost:8000/logout", {
      method: "POST",
      credentials: "include",
    });
    setUser(null);
    router.push("/");
    setIsMenuOpen(false);
  };

  return (
    <div>
      {user ? (
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
        <GoogleLogin
          onSuccess={handleSuccess}
          onError={() => console.error("❌ Google login error")}
          text="signin_with"
          logo_alignment="left"
          useOneTap
          theme="dark"
        />
      )}
    </div>
  );
}
