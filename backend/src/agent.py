from dataclasses import dataclass
import logging
import os
import re
from typing import List, Optional
from AppDatabase import AppDatabase
from livekit.plugins import azure
from livekit import rtc
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

calendar_service = CalendarService()
logger = logging.getLogger("agent")

load_dotenv()
db=AppDatabase()
@dataclass
class UserData:
    user_name: str
    meeting_date : str
    meeting_title : str
    meeting_attendee : str
    transcription : str
    
RunContext_T=RunContext[UserData]
    


class AppointmentSchedulingAssistant(Agent):
    def __init__(self,ctx : JobContext) -> None:
        now = datetime.datetime.now(datetime.timezone.utc).astimezone() # Timezone-aware
        self.transcriptions : List[str] =[] 
        self.transcription_buffer : str = ""
        current_date_str = now.strftime("%A, %B %d, %Y")
        super().__init__(
            instructions=f"""You are a friendly and helpful voice AI assistant designed for managing meetings . 
            The current date and time is {current_date_str}.
            When you first connect,Greet user with a friendly greeting and offer a friendly welcome. 

            **CRITICAL INSTRUCTION: Your responses MUST be in plain text only. NEVER use any special formatting, including asterisks, bolding, italics, or bullet points.**
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
    async def lookup_weather(self, context: RunContext_T, location: str):
        """Use this tool to look up current weather information in the given location.

        If the location is not supported by the weather service, the tool will indicate this. You must tell the user the location's weather is unavailable.

        Args:
            location: The location to look up weather information for (e.g. city name)
        """

        logger.info(f"Looking up weather for {location}")

        return "sunny with a temperature of 70 degrees."
    @function_tool
    async def get_current_date(self,context : RunContext_T) -> str:
        """Used to get the current date and time."""
        now = datetime.datetime.now()
        return now.strftime("%A, %B %d, %Y at %I:%M %p")
    
    async def save_meeting_in_db(self,event_id :str ,title:str,start_time:str,end_time:str,attendees:list[str]):
        db.create_appointment(event_id,1,2,title,start_time,end_time)
        return "meeting saved successfully"
        
    @function_tool
    async def save_user_sentiment(self,context: RunContext_T,sentiment:str)->UserData:
        """ To save the users sentiment in db either Happy,sad,neutral"""
        
        
        
    @function_tool
    async def schedule_meeting(
        self,
        context: RunContext_T,
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
            context (RunContext_T): The current run context (not user-supplied).
            Ask one by one each arg,so that it will be easy for the user to speak the args.
            title (str): The meeting title or subject.
            start_time (str): ISO 8601 formatted start datetime (e.g., "2025-09-03T10:00:00").
            end_time (str): ISO 8601 formatted end datetime.
            attendees (list[str]): List of attendee email addresses.Strictly Do not make any spaces in the input email.
            timezone (str, optional): Time zone for the meeting. Defaults to "Asia/Kolkata" .
    
        Returns:
            str: Confirmation message with meeting title, start time, end time and date
        """
        event_id= calendar_service.create_meeting(title, start_time, end_time, attendees,timezone)
        event_id = event_id[0] if isinstance(event_id, tuple) else event_id
        result= await self.save_meeting_in_db(event_id,title,start_time,end_time,attendees)
        return f"Meeting created:{title} and {result})"
    @function_tool
    async def save_user_data(self,context: RunContext_T,user_name:str)->UserData:
        """Whenever you get the user name , call this function to Save user data in database"""
        user_id=db.create_user(name=user_name)
        db.get_user(user_id)
        return "Data Saved successfully in Database"
    @function_tool
    async def list_meetings_by_date(
        self,
        context: RunContext_T,
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
            context (RunContext_T): The current run context (not user-supplied).
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
        context: RunContext_T,
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
            context (RunContext_T): The current run context (not user-supplied).
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
    context: RunContext_T,
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
            context (RunContext_T): The current run context (not user-supplied).
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
        context: RunContext_T,
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
            context (RunContext_T): The current run context (not user-supplied).
            event_id (str): The unique ID of the meeting to reschedule.
            new_start (str): ISO 8601 formatted new start datetime.
            new_end (str): ISO 8601 formatted new end datetime.

        Returns:
            str: Confirmation message with updated meeting link.
        """
        link = calendar_service.reschedule_meeting(event_id, new_start, new_end)
        return f"Meeting rescheduled:" 
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    
    ctx.log_context_fields = {
        "room": ctx.room.name,
        # "participant": ctx.room.local_participant.identity,
        # "job": ctx.job.id,
        # "userdata": ctx.proc.userdata,
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

        # Handle user joining the room
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
    
    appointment_scheduling_assistant = AppointmentSchedulingAssistant(ctx)
    logger.info(f"{RoomInputOptions.participant_identity}-----------------------$$$$$$$$$$$--------------$$$$$$$$$$")
    logger.info(f"{rtc.participant} : RTC Participant")
  
    # @session.on("user_joined")
    # def save_user_data(user: ctx..RemoteParticipant):
    #     logger.info(f"User joined: {user.identity}")
    #     db.create_user(name=user.identity)
        

          
    await session.start(
        agent=AppointmentSchedulingAssistant(ctx),
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
    @session.on("user_input_transcribed")
    def on_transcript(transcript):
        if appointment_scheduling_assistant.transcription_buffer:
            appointment_scheduling_assistant.transcription_buffer+=" "+ transcript.transcript
        else:
            appointment_scheduling_assistant.transcription_buffer = transcript.transcript
        logger.info(f"Transcription Buffer: {appointment_scheduling_assistant.transcription_buffer}")
        sentence_endings=re.findall(r'[.!?]',appointment_scheduling_assistant.transcription_buffer)
        if len(sentence_endings)>=3:
            sentence_count=0
            last_pos=0
            for match in re.finditer(r'[.!?]',appointment_scheduling_assistant.transcription_buffer):
                sentence_count+=1
                if sentence_count ==3 :
                    last_pos=match.end()
                    break
            two_sentences=appointment_scheduling_assistant.transcription_buffer[:last_pos].strip()# Extract the second sentence
            appointment_scheduling_assistant.transcription_buffer =appointment_scheduling_assistant.transcription_buffer[last_pos:].strip()# Remove the second sentence from the buffer
            appointment_scheduling_assistant.transcriptions.append(two_sentences)# Append the second sentence to the list
            logger.info(f"Processing for notes : {two_sentences}")
            if(len( two_sentences)>5):
             db.add_transcription(1,two_sentences)
    @ctx.room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant):
        """Called when a user joins the room"""
        logger.info(f"User joined: {participant}")
        try:
            # Save user to database
            user_id = db.create_user(name=participant)
            logger.info(f"User saved to database with ID: {user_id}")
        except Exception as e:
            logger.error(f"Error saving user to database: {e}")    
            
       # Alternative approach: Handle when participant metadata is updated
    @ctx.room.on("participant_metadata_changed") 
    def on_participant_metadata_changed(participant: rtc.RemoteParticipant, prev_metadata: str):
        """Called when participant metadata changes - useful if name comes later"""
        logger.info(f"Participant metadata changed for {participant}: {participant}")
        # You can extract additional user info from metadata if needed

        # IMPORTANT: Check for participants that joined before agent was ready
        logger.info(f"Checking for existing participants in room: {ctx.room.name}")
    
    # for participant in ctx.room.remote_participants:
    #     logger.info(f"Found existing participant: {participant.identity}")
    #     try:
    #         # Save user to database
    #         user_id = db.create_user(name=participant)
    #         logger.info(f"Existing user saved to database with ID: {user_id}")
    #     except Exception as e:
    #         logger.error(f"Error saving existing user to database: {e}")
    
    if not ctx.room.remote_participants:
        logger.info("No existing participants found - waiting for new connections")
if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
