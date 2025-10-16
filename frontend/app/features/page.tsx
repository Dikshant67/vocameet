export default function Features(){
    return(
        <div>
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
        </div>
    )   
}