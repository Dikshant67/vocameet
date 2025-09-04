import logging
import os
from typing import Dict, Optional
from livekit.plugins import azure

from dotenv import load_dotenv
from livekit.agents import (
    NOT_GIVEN,
    Agent,
    AgentFalseInterruptionEvent,
    AgentSession,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    RoomInputOptions,
    RunContext,
    WorkerOptions,
    cli,
    metrics,
)
import datetime
from livekit.agents.llm import function_tool
from livekit.plugins import cartesia, deepgram, noise_cancellation, openai, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from calendar_service import CalendarService
from livekit.agents import (
    NOT_GIVEN,  # Import NOT_GIVEN
    Agent,
    AgentSession,
    JobContext,
    WorkerOptions,
    cli,
    stt,
    tts,
)
calendar_service = CalendarService()
logger = logging.getLogger("agent")

load_dotenv()

# Define the default language. This will be used if a spoken language is
# not detected or not supported by our configuration.
DEFAULT_LANGUAGE = "en-IN"

# Define all languages you want the agent to be able to understand.
# The STT will try to detect which of these languages the user is speaking.
CANDIDATE_LANGUAGES = ["en-IN", "hi-IN", "mr-IN", "es-ES", "fr-FR"]

# Map the language codes to the specific Azure TTS voice you want to use.
# You can find more voices here: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts
VOICE_MAP = {
    "en-IN": "en-IN-AartiNeural",
    "hi-IN": "hi-IN-MadhurNeural",
    "mr-IN": "mr-IN-AarohiNeural",
    "es-ES": "es-ES-ElviraNeural",
    "fr-FR": "fr-FR-DeniseNeural",
}

# --- 2. DYNAMIC TTS HELPER FUNCTION ---
# def get_tts_for_language(language: str, session: AgentSession) -> tts.TTS:
#     """
#     Retrieves a cached TTS client for the given language or creates a new one.
#     This function includes the authority to fall back to a default language.
#     """
#     # Sanity check: If language is not in our supported VOICE_MAP, use the default.
#     if language not in VOICE_MAP:
#         logger.warning(f"Language '{language}' not supported in VOICE_MAP. Falling back to default.")
#         language = DEFAULT_LANGUAGE

#     voice = VOICE_MAP[language]

#     # Use session.user_data to cache TTS clients. This is efficient as we don't
#     # recreate the client for a language we've already used in this session.
#     if "tts_clients" not in session.user_data:
#         session.user_data["tts_clients"] = {}

#     tts_clients: Dict[str, tts.TTS] = session.user_data["tts_clients"]
    
#     if language in tts_clients:
#         return tts_clients[language]

#     logger.info(f"Creating new TTS client for '{language}' with voice '{voice}'")
#     new_tts_client = azure.TTS(
#         speech_key=os.getenv("AZURE_SPEECH_KEY"),
#         speech_region=os.getenv("AZURE_SPEECH_REGION"),
#         voice=voice,
#     )
#     tts_clients[language] = new_tts_client
#     return new_tts_client

class Assistant(Agent):
    def __init__(self) -> None:
        now = datetime.datetime.now(datetime.timezone.utc).astimezone() # Timezone-aware
        current_date_str = now.strftime("%A, %B %d, %Y")
        super().__init__(
            instructions=f"""You are a friendly and helpful voice AI assistant designed for managing meetings . 
            The current date and time is {current_date_str}.
            Do not accept the dates and time in the past suggest them to use in future dates and times.
            Do not read ,refer asterisk symbol in any context.
            You always ask questions one at a time.
            You warmly greet users, offer a friendly welcome, and are ready to assist with scheduling. 
            You ask details to the user one at a time.
            Your responses are clear, concise, and to the point, without complex formatting or punctuation. You are curious, friendly, 
            and have a sense of humor. Your goal is to provide a smooth and efficient user experience for all meeting scheduling needs""",
        )

    # all functions annotated with @function_tool will be passed to the LLM when this
    # agent is active
    
    @function_tool
    async def lookup_weather(self, context: RunContext, location: str):
        """Use this tool to look up current weather information in the given location.

        If the location is not supported by the weather service, the tool will indicate this. You must tell the user the location's weather is unavailable.

        Args:
            location: The location to look up weather information for (e.g. city name)
        """

        logger.info(f"Looking up weather for {location}")

        return "sunny with a temperature of 70 degrees."
    @function_tool
    async def get_current_date(self,context : RunContext) -> str:
        """Used to get the current date and time."""
        now = datetime.datetime.now()
        return now.strftime("%A, %B %d, %Y at %I:%M %p")
    @function_tool
    async def schedule_meeting(
        self,
        context: RunContext,
        title: str,
        start_time: str,
        end_time: str,
        attendees: list[str],
        timezone: str = "Asia/Kolkata"
    ):
        """
        Schedule a meeting in Google Calendar.
    
        Guidance for LLM:
        - Always request all arguments: `title`, `start_time`, `end_time`, and `attendees` one by one.
        - If any argument is missing, politely ask the user for the missing detail.
          Example: "Could you please tell me the meeting title?" 
                   "What time should the meeting start and end?"
        - If the user request is ambiguous (e.g., "set up a meeting tomorrow" without a time),
          clarify before calling the tool.Confirm all the details before scheduling.
    
        Args:
            context (RunContext): The current run context (not user-supplied).
            Ask one by one each arg,so that it will be easy for the user to speak the args.
            title (str): The meeting title or subject.
            start_time (str): ISO 8601 formatted start datetime (e.g., "2025-09-03T10:00:00").
            end_time (str): ISO 8601 formatted end datetime.
            attendees (list[str]): List of attendee email addresses.
            timezone (str, optional): Time zone for the meeting. Defaults to "Asia/Kolkata" .
    
        Returns:
            str: Confirmation message with meeting title, start time, end time and date
        """
        event_id, link = calendar_service.create_meeting(title, start_time, end_time, attendees,timezone)
        return f"Meeting created:{title})"
    
    @function_tool
    async def list_meetings_by_date(
        self,
        context: RunContext,
        date: str,
        max_results: int = 10
    ):
        """
        List meetings scheduled on a specific date from Google Calendar.
    
        Guidance for LLM:
        - Always ask the user for the date (format: YYYY-MM-DD).
        - If the user says "today" or "tomorrow", resolve it to an actual date using current timezone.
        - If no meetings are found on that date, politely inform the user.
        - This tool is especially useful when the user wants to cancel/reschedule a meeting 
          but does not remember the event ID.
    
        Args:
            context (RunContext): The current run context (not user-supplied).
            date (str): The date to search for meetings (format YYYY-MM-DD).
            max_results (int, optional): Maximum number of meetings to list. Defaults to 10.
    
        Returns:
            list[dict] | str: A list of meeting summaries with ID, title, start, and end times,
                              or a message saying no meetings are found.
        """
        events = calendar_service.list_meetings(max_results)
    
        # Filter events by date
        filtered_events = []
        for event in events:
            start_time = event["start"].get("dateTime", event["start"].get("date"))
            if start_time.startswith(date):  # Compare with YYYY-MM-DD
                filtered_events.append({
                    "id": event["id"],
                    "summary": event.get("summary", "No title"),
                    "start": start_time,
                    "end": event["end"].get("dateTime", event["end"].get("date")),
                })
    
        if not filtered_events:
            return f"No meetings found on {date}."
    
        return filtered_events
    @function_tool
    async def list_meetings(
        self,
        context: RunContext,
        max_results: int = 10
    ):
        """
        List upcoming meetings from Google Calendar.

        Guidance for LLM:
        - This tool does not require user-provided arguments (except optional `max_results`).
        - If the meetings found just mention titles,dates and time to the user.
        - If the user does not specify a limit, default to 10.
        - If no meetings are found, politely inform the user.

        Args:
            context (RunContext): The current run context (not user-supplied).
            max_results (int, optional): Maximum number of meetings to list. Defaults to 10.

        Returns:
            list[dict] | str: A list of meeting summaries with ID, title, start, and end times,
                            or a message saying no meetings are found.
        """
        events = calendar_service.list_meetings(max_results)
        if not events:
            return "No upcoming meetings found."
        return [
            {
                "id": event["id"],
                "summary": event.get("summary", "No title"),
                "start": event["start"].get("dateTime", event["start"].get("date")),
                "end": event["end"].get("dateTime", event["end"].get("date")),
            }
            for event in events
        ]


    @function_tool
    async def cancel_meeting(
    self,
    context: RunContext,
    event_id: Optional[str] = None,
    date: Optional[str] = None,
    ordinal: Optional[int] = None
    ):
        """
        Cancel a meeting in Google Calendar.

        Guidance for LLM:
        - If `event_id` is provided, the tool will cancel the meeting directly.
        - If `date` is provided without an `event_id`, the tool will list all meetings on that day and ask for confirmation.
        - If the user then specifies an ordinal number (e.g., "the first one", "the 3rd one"), the LLM should call this tool again with both `date` and `ordinal` to cancel the specific meeting.
        - If neither `event_id` nor `date` are provided, the tool will ask the user for more information.

        Args:
            context (RunContext): The current run context (not user-supplied).
            event_id (str, optional): The unique ID of the meeting to cancel.
            date (str, optional): The date (YYYY-MM-DD) to search for meetings to cancel.
            ordinal (int, optional): The ordinal number of the meeting to cancel from the list of meetings on the given date (1-based index).

        Returns:
            str | dict:
                - A confirmation message if the meeting was cancelled.
                - A dictionary with a message and a list of meetings if a date was provided but no ordinal.
                - An error message if no meetings are found or the ordinal is invalid.
                - A message asking for more information if no arguments are provided.
        """
        if event_id:
            success = calendar_service.cancel_meeting(event_id)
            return f"✅ Meeting {event_id} cancelled." if success else f"❌ Failed to cancel meeting."

        if date:
            # First, get the list of meetings for the given date.
            events = calendar_service.list_meetings(max_results=100) # Get a good number of events to filter
            meetings_on_date = [
                {
                    "id": event["id"],
                    "summary": event.get("summary", "No title"),
                    "start": event["start"].get("dateTime", event["start"].get("date")),
                    "end": event["end"].get("dateTime", event["end"].get("date")),
                }
                for event in events
                if event["start"].get("dateTime", event["start"].get("date")).startswith(date)
            ]

            if not meetings_on_date:
                return f"No meetings found on {date}."

            if ordinal:
                if 1 <= ordinal <= len(meetings_on_date):
                    event_to_cancel = meetings_on_date[ordinal - 1]
                    event_id_to_cancel = event_to_cancel['id']
                    summary = event_to_cancel['summary']
                    success = calendar_service.cancel_meeting(event_id_to_cancel)
                    return f"✅ Meeting '{summary}' with ID {event_id_to_cancel} cancelled." if success else f"❌ Failed to cancel meeting with ID {event_id_to_cancel}."
                else:
                    return f"Invalid choice. Please provide a number between 1 and {len(meetings_on_date)}."

            return {
                "message": f"I found {len(meetings_on_date)} meetings on {date}. Please tell me which one to cancel by providing its number.",
                "meetings": meetings_on_date
            }

        return "Could you please provide the meeting ID or the date of the meeting you'd like to cancel?"   
    @function_tool
    async def reschedule_meeting(
        self,
        context: RunContext,
        event_id: str,
        new_start: str,
        new_end: str
    ):
        """
        Reschedule a meeting in Google Calendar.

        Guidance for LLM:
        - Always provide the `event_id`, `new_start`, and `new_end`.
        - If any argument is missing, ask politely before calling the tool.
            Example: "Could you please provide the new start and end time for the meeting?"
        - If the user says "reschedule my next meeting" without specifying which one,
            list upcoming meetings and confirm which meeting to move.

        Args:
            context (RunContext): The current run context (not user-supplied).
            event_id (str): The unique ID of the meeting to reschedule.
            new_start (str): ISO 8601 formatted new start datetime.
            new_end (str): ISO 8601 formatted new end datetime.

        Returns:
            str: Confirmation message with updated meeting link.
        """
        link = calendar_service.reschedule_meeting(event_id, new_start, new_end)
        return f"Meeting rescheduled:" 
#     @function_tool
#     async def get_tts_for_language(language: str, session: AgentSession) -> tts.TTS:
#         """
#         Get the language from the user when he speaks the language and returns the corresponding TTS client.
#         Retrieves a cached TTS client for the given language or creates a new one.
    
#         """
#     # Default to English if language or voice is not supported
#         VOICE_MAP = {
#     "en-IN": "en-IN-AartiNeural",
#     "hi-IN": "hi-IN-MadhurNeural",
#     "mr-IN": "mr-IN-AarohiNeural",
#     "es-ES": "es-ES-ElviraNeural",
#     "fr-FR": "fr-FR-DeniseNeural",
# }
#         voice = VOICE_MAP.get(language)
#         if not voice:
#             logging.warning(f"No voice found for language '{language}', defaulting to en-IN.")
#             language = "en-IN"
#             voice = VOICE_MAP[language]

#         # session.user_data is a dictionary for storing custom state
#         if "tts_clients" not in session.user_data:
#             session.user_data["tts_clients"] = {}

#         tts_clients: Dict[str, tts.TTS] = session.user_data["tts_clients"]
        
#         if language in tts_clients:
#             return tts_clients[language]

#         logging.info(f"Creating new TTS client for {language} with voice {voice}")
#         new_tts_client = azure.TTS(
#             speech_key=os.getenv("AZURE_SPEECH_KEY"),
#             speech_region=os.getenv("AZURE_SPEECH_REGION"),
#             voice=voice,
#         )
#         tts_clients[language] = new_tts_client
#         return new_tts_client
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using OpenAI, Cartesia, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all providers at https://docs.livekit.io/agents/integrations/llm/
        llm=openai.LLM.with_azure(
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"), # or AZURE_OPENAI_ENDPOINT
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"), # or OPENAI_API_VERSION
    ),
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all providers at https://docs.livekit.io/agents/integrations/stt/
        
        #  stt=deepgram.STT(model="nova-3", language="multi"),
        stt = azure.STT(speech_key=os.getenv("AZURE_SPEECH_KEY"), speech_region=os.getenv("AZURE_SPEECH_REGION"),language="en-IN"),
        
        tts = azure.TTS(speech_key=os.getenv("AZURE_SPEECH_KEY"), speech_region=os.getenv("AZURE_SPEECH_REGION"),voice="en-IN-AartiNeural"),

        #voice="mr-IN-AarohiNeural"
        #language="mr-IN"
                        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all providers at https://docs.livekit.io/agents/integrations/tts/
        # tts=cartesia.TTS(voice="6f84f4b8-58a2-430c-8c79-688dad597532"),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
    )

    # To use a realtime model instead of a voice pipeline, use the following session setup instead:
    # session = AgentSession(
    #     # See all providers at https://docs.livekit.io/agents/integrations/realtime/
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # sometimes background noise could interrupt the agent session, these are considered false positive interruptions
    # when it's detected, you may resume the agent's speech
    
    @session.on("agent_false_interruption")
    def _on_agent_false_interruption(ev: AgentFalseInterruptionEvent):
        logger.info("false positive interruption, resuming")
        session.generate_reply(instructions=ev.extra_instructions or NOT_GIVEN)

    # Metrics collection, to measure pipeline performance
    # For more information, see https://docs.livekit.io/agents/build/metrics/
    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/integrations/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/integrations/avatar/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            # LiveKit Cloud enhanced noise cancellation
            # - If self-hosting, omit this parameter
            # - For telephony applications, use `BVCTelephony` for best results
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    # Join the room and connect to the user
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
