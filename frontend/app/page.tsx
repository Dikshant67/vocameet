"use client";

import { useRouter } from "next/navigation";
import { useUser } from "@/app/context/UserContext";

export default function LandingPage() {
  const router = useRouter();
  const { user } = useUser();

  const handleGetStarted = () => {
    if (user) {
      // Already logged in → go to dashboard
      router.push("/dashboard");
    } else {
      // Not logged in → go to login page
      router.push("/dashboard");
    }
  };

  return (
    <div className="flex h-screen flex-col items-center justify-center bg-gray-50">
      <h1 className="mb-6 text-3xl font-bold">Welcome to Voice Agent</h1>
      <p className="mb-6 text-lg text-gray-600">Meeting Management Platform</p>
      <button
        onClick={handleGetStarted}
        className="rounded-lg bg-blue-600 px-6 py-3 text-white shadow hover:bg-blue-700"
      >
        Get Started
      </button>
    </div>
  );
}
