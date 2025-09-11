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

  const handleSuccess = (credentialResponse: CredentialResponse) => {
    if (credentialResponse.credential) {
   const decoded: DecodedJWT = jwtDecode(credentialResponse.credential);
      console.log("🔍 Decoded JWT:", decoded);
      if (decoded.name && decoded.email && decoded.picture) {
        const userData = {
          name: decoded.name,
          email: decoded.email,
          picture: decoded.picture,
        };
        setUser(userData);
        // router.push("/dashboard");
        console.log("✅ User Info:", userData);
      } else {
        console.error("❌ Invalid user data in JWT");
      }
    } else {
      console.error("❌ Login failed: No credential returned");
    }
  };

  const handleError = () => {
    console.error("❌ Google login error");
  };

  const handleLogout = () => {
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
              aria-label={isMenuOpen ? "Close menu" : "Open menu"}
            >
              <ChevronDownIcon className="h-4 w-4" />
            </button>
          </div>
          <div
            className={`absolute top-full right-0 mt-2 overflow-hidden rounded-md bg-white shadow-lg transition-all duration-300 ease-in-out ${
              isMenuOpen ? "max-h-40 opacity-100" : "max-h-0 opacity-0"
            }`}
          >
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
            </button>
          </div>
        </div>
      ) : (
        <GoogleLogin
          onSuccess={handleSuccess}
          onError={handleError}
          text="signin_with"
          logo_alignment="left"
          useOneTap
          theme="dark"
         
        />
      )}
    </div>
  );
}
