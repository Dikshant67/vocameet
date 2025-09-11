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
 <div className="bg-slate-50 font-sans text-gray-800 leading-relaxed">
      {/* Header */}
      {/* <header
        role="banner"
        className="bg-blue-900 text-white px-8 py-4 flex items-center justify-between flex-wrap"
      >
        <div
          className="logo font-bold text-2xl tracking-wide"
          aria-label="Meeting Voice Agent Logo"
        >
          🔊 Meeting Voice Agent
        </div>
        <nav aria-label="Primary navigation" className="flex space-x-4">
          <a href="#getting-started" className="font-semibold text-white no-underline hover:underline focus:underline">
            Get Started
          </a>
          <a href="#features" className="font-semibold text-white no-underline hover:underline focus:underline">
            Features
          </a>
          <a href="#contact" className="font-semibold text-white no-underline hover:underline focus:underline">
            Contact
          </a>
        </nav>
      </header> */}

      {/* Main Content */}
      <main className="max-w-4xl mx-auto my-8 mb-16 px-4">
        {/* Hero Section */}
        <section
          className="bg-blue-100 px-8 py-12 rounded-lg text-center mb-12 shadow-lg"
          role="region"
          aria-labelledby="hero-title"
        >
          <h1 id="hero-title" className="text-4xl font-bold mb-2 text-blue-950">
            Manage Your Meetings Effortlessly with Voice
          </h1>
          <p className="text-xl mb-8 text-blue-900">
            The smart voice agent that schedules, reminds, and organizes your
            meetings — simply by talking.
          </p>
          <a
         
            className="btn-primary inline-block bg-blue-600 text-white px-7 py-3 rounded-md text-lg no-underline transition-colors duration-300 ease-in-out hover:bg-blue-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            role="button"
            onClick={handleGetStarted}
          >
            Get Started
          </a>
        </section>

        {/* Getting Started Section */}
        <section
          id="getting-started"
          className="mb-12"
          role="region"
          aria-labelledby="get-started-title"
        >
          <h2 id="get-started-title" className="text-center text-3xl font-bold mb-8 text-blue-950">
            Getting Started in 3 Easy Steps
          </h2>
          <div className="steps grid grid-cols-1 sm:grid-cols-3 gap-8">
            <article
              className="step bg-white border border-blue-200 rounded-lg px-6 py-8 shadow-md text-center transition-shadow duration-300 ease-in-out hover:shadow-2xl focus-within:shadow-2xl"
              tabIndex={0}
              aria-labelledby="step1-title"
              role="group"
              aria-describedby="step1-desc"
            >
              <div className="step-number text-5xl font-bold text-blue-600 mb-4 select-none" aria-hidden="true">
                1
              </div>
              <h3 id="step1-title" className="text-xl font-semibold mb-3 text-blue-900">
                Create Your Account
              </h3>
              <p id="step1-desc" className="text-base text-gray-600">
                Sign up quickly with your email or social login to personalize
                your meeting experience.
              </p>
            </article>

            <article
              className="step bg-white border border-blue-200 rounded-lg px-6 py-8 shadow-md text-center transition-shadow duration-300 ease-in-out hover:shadow-2xl focus-within:shadow-2xl"
              tabIndex={0}
              aria-labelledby="step2-title"
              role="group"
              aria-describedby="step2-desc"
            >
              <div className="step-number text-5xl font-bold text-blue-600 mb-4 select-none" aria-hidden="true">
                2
              </div>
              <h3 id="step2-title" className="text-xl font-semibold mb-3 text-blue-900">
                Link Your Calendar
              </h3>
              <p id="step2-desc" className="text-base text-gray-600">
                Connect Google Calendar, Outlook, or other calendars for
                seamless meeting coordination.
              </p>
            </article>

            <article
              className="step bg-white border border-blue-200 rounded-lg px-6 py-8 shadow-md text-center transition-shadow duration-300 ease-in-out hover:shadow-2xl focus-within:shadow-2xl"
              tabIndex={0}
              aria-labelledby="step3-title"
              role="group"
              aria-describedby="step3-desc"
            >
              <div className="step-number text-5xl font-bold text-blue-600 mb-4 select-none" aria-hidden="true">
                3
              </div>
              <h3 id="step3-title" className="text-xl font-semibold mb-3 text-blue-900">
                Start Using Voice Commands
              </h3>
              <p id="step3-desc" className="text-base text-gray-600">
                Use natural voice commands to schedule, reschedule, join, or
                cancel meetings instantly.
              </p>
            </article>
          </div>
        </section>

        {/* Features Section */}
        <section
          id="features"
          className="bg-blue-50 px-4 py-8 rounded-lg shadow-md"
          role="region"
          aria-labelledby="features-title"
        >
          <h2 id="features-title" className="text-center text-3xl font-bold mb-8 text-blue-950">
            Why Choose Our Voice Agent?
          </h2>
          <div className="features-list grid grid-cols-1 sm:grid-cols-2 gap-6 max-w-3xl mx-auto">
            <div
              className="feature-item bg-white px-6 py-5 rounded-md shadow-sm border-l-4 border-blue-600 transition-colors duration-300 ease-in-out hover:bg-blue-100"
              tabIndex={0}
            >
              <h3 className="feature-title font-semibold text-blue-900 mb-2 text-lg">
                Hands-Free Scheduling
              </h3>
              <p className="feature-desc text-gray-800 text-base leading-snug">
                Schedule meetings without lifting a finger—just speak and your
                meeting is set.
              </p>
            </div>
            <div
              className="feature-item bg-white px-6 py-5 rounded-md shadow-sm border-l-4 border-blue-600 transition-colors duration-300 ease-in-out hover:bg-blue-100"
              tabIndex={0}
            >
              <h3 className="feature-title font-semibold text-blue-900 mb-2 text-lg">
                Automatic Reminders
              </h3>
              <p className="feature-desc text-gray-800 text-base leading-snug">
                Never miss a meeting with automated reminders sent via email,
                SMS, or notifications.
              </p>
            </div>
        <div
            className="feature-item bg-white px-6 py-5 rounded-md shadow-sm border-l-4 border-blue-600 transition-colors duration-300 ease-in-out hover:bg-blue-100"
            tabIndex={0}
            >
            <h3 className="feature-title font-semibold text-blue-900 mb-2 text-lg">
                Seamless Calendar Sync
            </h3>
            <p className="feature-desc text-gray-800 text-base leading-snug">
                Connects with your existing calendar (Google, Outlook, etc.) to find available slots and prevent any scheduling conflicts.
            </p>
            </div>
                <div
            className="feature-item bg-white px-6 py-5 rounded-md shadow-sm border-l-4 border-blue-600 transition-colors duration-300 ease-in-out hover:bg-blue-100"
            tabIndex={0}
            >
            <h3 className="feature-title font-semibold text-blue-900 mb-2 text-lg">
                Natural Language Understanding
            </h3>
            <p className="feature-desc text-gray-800 text-base leading-snug">
                No rigid commands. Just speak naturally—"Schedule a call with Jane for sometime next week"—and our agent understands.
            </p>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer
        id="contact"
        role="contentinfo"
        aria-label="Contact information"
        className="text-center p-6 bg-slate-100 text-gray-500 text-sm border-t border-gray-200"
      >
        <p>
          Contact us:{" "}
          <a href="mailto:support@meetingvoiceagent.com" className="text-blue-700 no-underline hover:underline">
            support@meetingvoiceagent.com
          </a>
        </p>
        <p>© 2025 Meeting Voice Agent. All rights reserved.</p>
      </footer>
    </div>
  );
}
