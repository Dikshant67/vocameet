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

  // ✅ Handle Google login success
  const handleSuccess = async (credentialResponse: CredentialResponse) => {
    try {
      const idToken = credentialResponse.credential;
      console.log("ID Token:", idToken);
      if (!idToken) {
        console.error("❌ Login failed: No credential returned");
        return;
      }

      // Decode locally for UI (name, email, pic)
      const decoded: DecodedJWT = jwtDecode(idToken);
      if (decoded.name && decoded.email && decoded.picture) {
        setUser({
          name: decoded.name,
          email: decoded.email,
          picture: decoded.picture,
        });
      }

      // ✅ Send raw ID token to FastAPI for verification
      const res = await fetch("http://localhost:8000/auth/google", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include", // store session cookie
        body: JSON.stringify({ token: idToken }), // send raw string, not decoded object
      });

      if (!res.ok) {
        throw new Error(`Backend Authentication Failed: ${res.status}`);
      }

      const data = await res.json();
      console.log("✅ Logged in via Backend:", data);
    } catch (error) {
      console.error("Google login failed:", error);
    }
  };
  const checkUser = async () => {
    try {
      console.log("Checking user...");
      const response = await fetch("http://localhost:8000/check", {
        method: "GET",
        credentials: "include",
      });
      console.log(response);
    }catch (error) {
      console.error("Error checking user:", error);
    }
  };
  const handleError = () => {
    console.error("❌ Google login error");
  };

  const handleLogout = async () => {
    // Clear backend session
    await fetch("http://localhost:8000/logout", {
      method: "POST",
      credentials: "include",
    });

    setUser(null);
    router.push("/");
    setIsMenuOpen(false);
  };

  const handleProfileClick = () => {
    router.push("/profile");
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
                onClick={handleProfileClick}
                className="block w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100"
              >
                Profile
              </button>
              <button
                onClick={handleLogout}
                className="block w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100"
              >
                Logout
             
            </div>
          )}
        </div>
      ) : (
        <>
        
        <GoogleLogin
          onSuccess={handleSuccess}
          onError={handleError}
          text="signin_with"
          logo_alignment="left"
          useOneTap
          theme="dark"

        />
    
      }
    </div>
  );
}
