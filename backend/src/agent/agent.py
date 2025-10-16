# agent.py
from dataclasses import dataclass
import logging
import os
import re
import asyncio

from typing import AsyncIterable, List, Optional
from db.AppDatabase import AppDatabase
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
    ModelSettings,
    ConversationItemAddedEvent
    
    
)
import datetime
from livekit.agents.llm import function_tool
from livekit.plugins import cartesia, deepgram, noise_cancellation, openai, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel
import pytz
from services.calendar_service import CalendarService

calendar_service = CalendarService()
# -------------------------------
# CONFIG & LOGGING
# -------------------------------
logging.basicConfig(filename="../../logs/assistant.log",level=logging.INFO, format="%(levelname)s: %(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()
db=AppDatabase()
@dataclass
class UserData:
    """ A class to store user information during the call"""
    session : AgentSession =None
    ctx: Optional[JobContext] = None
    user_id : Optional[int]=None
    session_guid : Optional[str]=None
    user_name: Optional[str]=None
    meeting_date : Optional[str]=None
    meeting_title : Optional[str]=None
    meeting_attendee : Optional[str]=None
    last_conversation_for_reference : Optional[str]=None
    user_email : Optional[str]=None
    user_gender: Optional[str]=None 
    user_age:Optional[int]=None
    def is_identified(self) -> bool:
        """Check if the user is identified."""
        return self.user_name is not None 

    def reset(self) -> None:
        """Reset customer information."""
        self.user_name = None
     

    def summarize(self) -> str:
        """Return a summary of the user data."""
        if self.is_identified():
            return f"User: {self.user_name}  Email: {self.user_email} Age : {self.user_age} Gender : {self.user_gender}"
        else:
            return "User not yet identified."
        
RunContext_T=RunContext[UserData]
    


class AppointmentSchedulingAssistant(Agent):
    def __init__(self,ctx : JobContext) -> None:
        now = datetime.datetime.now(datetime.timezone.utc).astimezone() # Timezone-aware
        self.transcriptions : List[str] =[] 
        self.transcription_buffer : str = ""

        current_date_str = now.strftime("%A, %B %d, %Y")
       
        self.base_instructions=f"""You are a friendly and helpful voice AI assistant designed for managing meetings . 
            The current date and time is {current_date_str}.
            When you first connect,Greet user with a friendly greeting and offer a friendly welcome.for example if users name is Arun Kumar,Hi Arun 
            **CRITICAL INSTRUCTION: Your responses MUST be in plain text only. NEVER use any special formatting, including asterisks, bolding, italics, or bullet points.**
            Do not accept the dates and time in the past suggest them to use in future dates and times.
            Do not read ,refer asterisk symbol in any context.
            You always ask questions one at a time.
            You warmly greet users, offer a friendly welcome, and are ready to assist with scheduling. 
            You ask details to the user one at a time
            When a user requests a meeting, fetch relevant experts from the database based on the user's requirements. Compare the expert's speciality with the user's needs.
            Check the expert's availability and detect any scheduling conflicts. If conflicts exist, suggest alternative available time slots.
            Once a suitable slot is found, schedule the meeting with the expert.
            Your responses should be clear, concise, and to the point, without complex formatting. You are curious, friendly, and have a sense of humor. Your goal is to provide a smooth and efficient user experience for scheduling meetings with experts.
            Your responses are clear, concise, and to the point, without complex formatting or punctuation or emojis . You are curious, friendly, 
            and have a sense of humor. Your goal is to provide a smooth and efficient user experience for all meeting scheduling needs"""
        super().__init__(instructions=self.base_instructions)

    # all functions annotated with @function_tool will be passed to the LLM when this
    # agent is active
    # def run_agent_with_user(user_id: str):
    # # Your logic here
    #     print(f"Running agent for user: {user_id}")
    #     # Simulate fetching or processing user data
    #     user_data = {
    #         "user_id": user_id,
    #         "preferences": ["AI", "Python", "FastAPI"]
    #     }
    
    #     # Do something with user_data...
    #     return f"Processed data for user {user_data['user_id']}"
    async def tts_node(self, text: AsyncIterable[str], model_settings: ModelSettings):  
        async def process_text():  
            async for chunk in text:  
            # Remove markdown formatting  
                modified_chunk = chunk.replace("*", "").replace("_", "").replace("#", "")  
                yield modified_chunk  
  
        return Agent.default.tts_node(self, process_text(), model_settings)
    async def append_instructions(self, additional_instructions: str):  
        """Append new instructions to existing ones."""  
        current_instructions = self.base_instructions  
        new_instructions = f"{current_instructions}\n\nAdditional instructions: {additional_instructions}"  
        await self.update_instructions(new_instructions)  
        logger.info(new_instructions)
        self.base_instructions = new_instructions  # Keep track for future appends
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
    async def fetch_experts(self, context: RunContext_T, user_requirement: str):
        """Use this tool to fetch experts from the database based on the user's requirements.

        The tool compares the user's requirement with the speciality of experts and returns a list of matching experts along with their availability. 
        If no experts match the requirement, the tool should indicate that no suitable expert is available.

        Args:
            user_requirement: The specific need or topic the user wants expert assistance for (e.g. data engineering, SAP testing)
        """

        logger.info(f"Fetching experts for user requirement: {user_requirement}")
        experts_db=db.get_all_experts()
        
        # Pseudo code to simulate database lookup
        # In real implementation, replace with actual DB query
   
        # matching_experts = [expert for expert in experts_db if user_requirement.lower() in expert["speciality"].lower()]

        # if not matching_experts:
        #     return f"No experts available for {user_requirement} at the moment."

        # Return experts id and their availability
        return experts_db
    
    @function_tool
    async def get_the_summary_of_user_info(self,context: RunContext_T)-> str:
        """Used to get the summary of the user Details such as Name, Age, Gender"""
        # safely extract values with defaults
        name = getattr(context.userdata, "user_name", None) or "Unknown"
        age = getattr(context.userdata, "user_age", None) or "N/A"
        gender = getattr(context.userdata, "user_gender", None) or "Not specified"

        return f"User's Name is {name}, Age is {age}, Gender is {gender}."
    @function_tool
    async def get_current_date(self,context : RunContext_T) -> str:
        """Used to get the current date and time."""
        now = datetime.datetime.now()
        return now.strftime("%A, %B %d, %Y at %I:%M %p")
    
    async def save_meeting_in_db(self,event_id :str ,user_id:int,expert_id:int,title:str,start_time:str,end_time:str,attendees:list[str]):
        db.create_appointment(event_id,user_id,expert_id,title,start_time,end_time)
        return "meeting saved successfully"
   
    @function_tool
    async def schedule_meeting(
        self,
        context: "RunContext_T",
        title: str,
        expert_id: int,
        start_time: str,
        end_time: str,
        timezone: str = "Asia/Kolkata"
    ) -> str:
        import pytz
        import datetime

        if context.userdata.user_email:
            attendees = [context.userdata.user_email]
        else:
            attendees = []

        if not all([title, start_time, end_time, attendees]):
            raise ValueError("Missing one or more required arguments.")

        tz = pytz.timezone(timezone)
        try:
            # FIX: Robustly handle both naive and aware datetime strings.
            
            # --- Handle Start Time ---
            dt_start_obj = datetime.datetime.fromisoformat(start_time)
            if dt_start_obj.tzinfo is None:
                # It's a naive datetime, so we localize it.
                start_dt = tz.localize(dt_start_obj)
            else:
                # It's already an aware datetime, so we just ensure it's in the correct timezone.
                start_dt = dt_start_obj.astimezone(tz)

            # --- Handle End Time ---
            dt_end_obj = datetime.datetime.fromisoformat(end_time)
            if dt_end_obj.tzinfo is None:
                end_dt = tz.localize(dt_end_obj)
            else:
                end_dt = dt_end_obj.astimezone(tz)

        except Exception as e:
            # This will catch parsing errors or other issues.
            raise ValueError(f"Invalid datetime format. Could not parse '{start_time}'. Error: {e}")

        # Convert to UTC for all internal logic and database storage
        start_utc = start_dt.astimezone(pytz.UTC)
        end_utc = end_dt.astimezone(pytz.UTC)

        # ... the rest of your function remains the same ...
        
        expert = db.get_expert(expert_id)
        if not expert:
            return f"No expert found with id {expert_id}."

        if not db.is_within_availability(expert_id, start_utc, end_utc) or db.has_conflict(expert_id, start_utc, end_utc):
            suggested_slots_utc = db.suggest_next_available_slots(expert_id, start_utc)
            if suggested_slots_utc:
                slots_text_parts = []
                for start, end in suggested_slots_utc:
                    local_start = start.astimezone(tz)
                    slots_text_parts.append(f"from {local_start.strftime('%I:%M %p')} to {end.astimezone(tz).strftime('%I:%M %p on %b %d')}")
                slots_text = ", ".join(slots_text_parts)
                return f"Expert {expert['name']} is not available at the requested time. Here are some other options: {slots_text}"
            else:
                return f"Expert {expert['name']} is not available at the requested time, and no other suitable slots could be found nearby."

        try:
            event_id = calendar_service.create_meeting(
                summary=title,
                start_time=start_dt.isoformat(),
                end_time=end_dt.isoformat(),
                attendees=attendees,
                timezone=timezone,
            )

            if isinstance(event_id, tuple):
                event_id = event_id[0]

            save_result = db.create_appointment(
                event_id=event_id,
                user_id=context.userdata.user_id,
                expert_id=expert_id,
                title=title,
                start_time=start_utc.isoformat(),
                end_time=end_utc.isoformat(),
            )
            

            confirmation_message = (
                f"Meeting '{title}' successfully created with {expert['name']}.\n"
                f"Time: {start_dt.strftime('%A, %B %d at %I:%M %p %Z')}\n"
                f"Attendees: {', '.join(attendees)}"
            )
            return confirmation_message

        except Exception as exc:
            # logger.exception("Failed to schedule meeting: %s", exc) 
            raise RuntimeError("An unexpected error occurred while scheduling the meeting.") from exc
    @function_tool
    async def suggest_slots_for_expert(
        self,
        context: "RunContext_T",
        expert_id: int,
        desired_start: str,
        timezone: str = "Asia/Kolkata",
        duration_minutes: int = 30,
        limit: int = 3
    ) -> str:
        import pytz
        import datetime

        # --- Step 1: Validate input ---
        if not expert_id or not desired_start:
            raise ValueError("Missing required arguments: expert_id or desired_start.")

        tz = pytz.timezone(timezone)

        try:
            # --- Step 2: Parse desired_start string into aware datetime ---
            dt_desired = datetime.datetime.fromisoformat(desired_start)
            if dt_desired.tzinfo is None:
                desired_dt = tz.localize(dt_desired)
            else:
                desired_dt = dt_desired.astimezone(tz)
        except Exception as e:
            raise ValueError(f"Invalid datetime format for desired_start: {e}")

        # --- Step 3: Convert to UTC for internal use ---
        desired_start_utc = desired_dt.astimezone(pytz.UTC)

        # --- Step 4: Check if expert exists ---
        expert = db.get_expert(expert_id)
        if not expert:
            return f"No expert found with id {expert_id}."

        # --- Step 5: Fetch next available slots from DB ---
        suggested_slots_utc = db.suggest_next_available_slots(
            expert_id,
            desired_start_utc,
            duration_minutes=duration_minutes,
            limit=limit
        )

        # --- Step 6: Handle case when no slots are found ---
        if not suggested_slots_utc:
            return f"No available slots found for expert {expert['name']} after {desired_dt.strftime('%I:%M %p on %b %d')}."

        # --- Step 7: Format output slots in expert's timezone ---
        formatted_slots = []
        for start_utc, end_utc in suggested_slots_utc:
            start_local = start_utc.astimezone(tz)
            end_local = end_utc.astimezone(tz)
            formatted_slots.append(
                f"{start_local.strftime('%A, %b %d from %I:%M %p')} to {end_local.strftime('%I:%M %p %Z')}"
            )

        # --- Step 8: Construct final message ---
        formatted_text = "\n".join(f"- {slot}" for slot in formatted_slots)
        return f"Here are the next available time slots for expert {expert['name']}:\n{formatted_text}"
    @function_tool
    async def list_meetings_by_date(
        self,
        context: "RunContext_T",
        date: str,
        max_results: int = 10
    ) -> List[dict] | str:
        """
        List meetings scheduled on a specific date from Google Calendar.

        Guidance for LLM:
            - Always ask the user for the date (format: YYYY-MM-DD).
            - If the user says "today" or "tomorrow", resolve it to an actual date
            using the current timezone.
            - If no meetings are found on that date, politely inform the user.
            - This tool is especially useful when the user wants to cancel or
            reschedule a meeting but does not remember the event ID.

        Args:
            context (RunContext_T): The current run context (not user-supplied).
            date (str): The date to search for meetings (format YYYY-MM-DD).
            max_results (int, optional): Maximum number of meetings to list.
                Defaults to 10.

        Returns:
            List[dict] | str: A list of meetings with ID, title, start, and end
                times, or a message if no meetings are found.

        Raises:
            ValueError: If `date` is empty or not in a valid format.
            RuntimeError: If there is an unexpected error during retrieval.
        """
        if not date or not isinstance(date, str):
            raise ValueError("A valid date string (YYYY-MM-DD) must be provided.")

        try:
            events = calendar_service.list_meetings(max_results=max_results)
            if not events:
                logger.info("No events returned from calendar service.")
                return f"No meetings found on {date}."

            filtered_events: List[dict[str, str]] = []
            for event in events:
                start_info = event.get("start", {})
                end_info = event.get("end", {})

                start_time = start_info.get("dateTime") or start_info.get("date")
                end_time = end_info.get("dateTime") or end_info.get("date")

                if not start_time:
                    logger.warning("Skipping event with missing start time: %s", event)
                    continue

                if start_time.startswith(date):
                    filtered_events.append({
                        "id": event.get("id", "Unknown ID"),
                        "summary": event.get("summary", "No title"),
                        "start": start_time,
                        "end": end_time or "Unknown end time",
                    })

            if not filtered_events:
                logger.info("No meetings found for date: %s", date)
                return f"No meetings found on {date}."

            logger.info("Found %d meetings for date %s", len(filtered_events), date)
            return filtered_events

        except ValueError as exc:
            logger.error("Invalid date input for list_meetings_by_date: %s", exc)
            raise

        except Exception as exc:
            logger.exception("Error listing meetings for date %s: %s", date, exc)
            raise RuntimeError(
                "An unexpected error occurred while fetching meetings."
            ) from exc    
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
        - If meetings are found, mention their titles, start dates, and times to the user.
        - If no meetings are found, politely inform the user.
        - The default maximum number of results is 10 unless the user specifies otherwise.

        Args:
            context (RunContext_T): The current run context (not user-supplied).
            max_results (int, optional): Maximum number of meetings to list. Defaults to 10.

        Returns:
            list[dict] | str: A list of meeting summaries with ID, title, start, and end times,
                            or a message saying no meetings are found.
        """
        try:
            logger.info(f"[list_meetings] Fetching up to {max_results} upcoming meetings from Google Calendar.")

            events = calendar_service.list_meetings(max_results)
            logger.debug(f"[list_meetings] Raw events received: {events}")

            if not events or len(events) == 0:
                logger.info("[list_meetings] No upcoming meetings found.")
                return "No upcoming meetings found."

            formatted_meetings = []
            for event in events:
                start_time = event["start"].get("dateTime", event["start"].get("date"))
                end_time = event["end"].get("dateTime", event["end"].get("date"))

                formatted_meetings.append({
                    "id": event["id"],
                    "summary": event.get("summary", "No title"),
                    "start": start_time,
                    "end": end_time,
                })

            logger.info(f"[list_meetings] Successfully fetched {len(formatted_meetings)} upcoming meetings.")
            return formatted_meetings

        except Exception as e:
            logger.error(f"[list_meetings] Error fetching meetings: {str(e)}", exc_info=True)
            return f"An error occurred while fetching meetings: {str(e)}"

    @function_tool
    async def cancel_meeting(
        self,
        context: RunContext_T,
        event_id: Optional[str] = None,
        date: Optional[str] = None,
        ordinal: Optional[int] = None
    ) -> str | dict:
        """
        Cancel a meeting in Google Calendar.

        Guidance for LLM:
            - If `event_id` is provided, cancel the meeting directly.
            - If `date` is provided without an `event_id`, list meetings on that day
            and ask for confirmation.
            - If the user specifies an ordinal (e.g., "the 1st" or "3rd"), cancel
            the specific meeting.
            - If neither `event_id` nor `date` are provided, ask the user for
            more information.

        Args:
            context (RunContext_T): The current run context (not user-supplied).
            event_id (str, optional): The unique ID of the meeting to cancel.
            date (str, optional): The date (YYYY-MM-DD) to search for meetings to cancel.
            ordinal (int, optional): The ordinal number (1-based) of the meeting to cancel
                                    from the list on the given date.

        Returns:
            str | dict:
                - Confirmation message if a meeting was cancelled.
                - A dictionary with a message and a list of meetings if date is provided but no ordinal.
                - Error message if no meetings are found or ordinal is invalid.
                - Message asking for more information if no arguments are provided.
        """
        try:
            if event_id:
                logger.info(f"[cancel_meeting] Cancelling meeting with ID: {event_id}")
                success = calendar_service.cancel_meeting(event_id)
                if success:
                    logger.info(f"[cancel_meeting] Meeting {event_id} successfully cancelled.")
                    return f"✅ Meeting {event_id} cancelled."
                else:
                    logger.warning(f"[cancel_meeting] Failed to cancel meeting {event_id}.")
                    return f"❌ Failed to cancel meeting {event_id}."

            if date:
                logger.info(f"[cancel_meeting] Listing meetings on date: {date}")
                events = calendar_service.list_meetings(max_results=100)
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
                    logger.info(f"[cancel_meeting] No meetings found on {date}.")
                    return f"No meetings found on {date}."

                if ordinal:
                    if 1 <= ordinal <= len(meetings_on_date):
                        event_to_cancel = meetings_on_date[ordinal - 1]
                        event_id_to_cancel = event_to_cancel['id']
                        summary = event_to_cancel['summary']
                        logger.info(f"[cancel_meeting] Cancelling meeting '{summary}' with ID {event_id_to_cancel}")
                        success = calendar_service.cancel_meeting(event_id_to_cancel)
                        if success:
                            logger.info(f"[cancel_meeting] Meeting '{summary}' cancelled successfully.")
                            return f"✅ Meeting '{summary}' with ID {event_id_to_cancel} cancelled."
                        else:
                            logger.warning(f"[cancel_meeting] Failed to cancel meeting '{summary}' with ID {event_id_to_cancel}.")
                            return f"❌ Failed to cancel meeting with ID {event_id_to_cancel}."
                    else:
                        logger.warning(f"[cancel_meeting] Invalid ordinal {ordinal} provided.")
                        return f"Invalid choice. Please provide a number between 1 and {len(meetings_on_date)}."

                logger.info(f"[cancel_meeting] Found {len(meetings_on_date)} meetings on {date}, awaiting user choice.")
                return {
                    "message": f"I found {len(meetings_on_date)} meetings on {date}. "
                            "Please tell me which one to cancel by providing its number.",
                    "meetings": meetings_on_date
                }

            logger.info("[cancel_meeting] No event_id or date provided; requesting more info from user.")
            return "Could you please provide the meeting ID or the date of the meeting you'd like to cancel?"

        except Exception as e:
            logger.error(f"[cancel_meeting] Error cancelling meeting: {str(e)}", exc_info=True)
            return f"An error occurred while cancelling the meeting: {str(e)}"

    @function_tool
    async def reschedule_meeting(
        self,
        context: RunContext_T,
        event_id: str,
        new_start: str,
        new_end: str
    ) -> str:
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
            str: Confirmation message with updated meeting link or error message.
        """
        try:
            logger.info(f"[reschedule_meeting] Attempting to reschedule meeting ID: {event_id}")
            
            if not event_id or not new_start or not new_end:
                logger.warning("[reschedule_meeting] Missing required arguments.")
                return "Please provide the meeting ID, new start time, and new end time."

            link = calendar_service.reschedule_meeting(event_id, new_start, new_end)

            if link:
                logger.info(f"[reschedule_meeting] Meeting {event_id} successfully rescheduled.")
                return f"✅ Meeting successfully rescheduled. Updated link: {link}"
            else:
                logger.warning(f"[reschedule_meeting] Failed to reschedule meeting {event_id}.")
                return f"❌ Failed to reschedule meeting {event_id}."

        except Exception as e:
            logger.error(f"[reschedule_meeting] Error rescheduling meeting {event_id}: {str(e)}", exc_info=True)
            return f"An error occurred while rescheduling the meeting: {str(e)}"
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    # Initialize user data with context
    userdata = UserData(ctx=ctx)
    
    appointment_scheduling_assistant = AppointmentSchedulingAssistant(ctx)
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }
    session = AgentSession[UserData](
        userdata=userdata,
        llm=openai.LLM.with_azure(
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"), 
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"), 
    ),
        stt = azure.STT(speech_key=os.getenv("AZURE_SPEECH_KEY"), speech_region=os.getenv("AZURE_SPEECH_REGION"),language="en-IN"),
        tts = azure.TTS(speech_key=os.getenv("AZURE_SPEECH_KEY"), speech_region=os.getenv("AZURE_SPEECH_REGION"),voice="en-IN-AartiNeural"),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )
    
    # @session.on("agent_false_interruption")
    # def _on_agent_false_interruption(ev: AgentFalseInterruptionEvent):
    #     logger.info("false positive interruption, resuming")
    #     session.generate_reply(instructions=ev.extra_instructions or NOT_GIVEN)
    # usage_collector = metrics.UsageCollector()
    # @session.on("metrics_collected")
    # def _on_metrics_collected(ev: MetricsCollectedEvent):
    #     metrics.log_metrics(ev.metrics)
    #     logger.info("metrics printed on console -----------------------")
    #     usage_collector.collect(ev.metrics)
    @ctx.room.on("participant_disconnected")
    def on_participant_disconnected(participant: rtc.RemoteParticipant):
        """Called when a user leaves the room"""
        logger.info(f"User disconnected: {participant}")
    @ctx.room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant):
        """Called when a user enters the room"""
        logger.info(f"User Connected: {participant}" )  

    @ctx.room.on("track_subscribed")
    def on_track_subscribed(
        track: rtc.Track,
        publication: rtc.RemoteTrackPublication,
        participant: rtc.RemoteParticipant,
    ) -> None:
        """
        Event handler triggered when a remote participant's track is subscribed.

        Responsibilities:
            - Extract and log session metadata (session GUID).
            - Populate appointment assistant user context (name, email, etc.).
            - Retrieve and set user-related information from the database.
            - Generate and append contextual instructions asynchronously.

        Args:
            track (rtc.Track): The subscribed media track.
            publication (rtc.RemoteTrackPublication): Publication details.
            participant (rtc.RemoteParticipant): Remote participant whose track was subscribed.
        """
        try:
            if not appointment_scheduling_assistant:
                logger.warning("[on_track_subscribed] Appointment scheduling assistant is not initialized.")
                return

            # Extract session GUID from participant metadata
            if participant.metadata:
                import json
                metadata = json.loads(participant.metadata)
                session_guid = metadata.get("sessionGuid")
                if session_guid:
                    logger.info(f"[on_track_subscribed] Session GUID: {session_guid}")
                else:
                    logger.debug("[on_track_subscribed] No session GUID found in metadata.")

            # Update user information in the assistant session
            user_data = appointment_scheduling_assistant.session.userdata
            user_data.user_name = participant.name
            user_data.user_email = participant.identity
            user_data.session_guid = session_guid

            # Check if the user can be identified
            if not user_data.is_identified():
                logger.info(f"[on_track_subscribed] Participant {participant.name} is not yet identified.")
                return

            # Retrieve user details from the database
            user_id = db.get_user_by_email(participant.identity)
            if user_id:
                user_data.user_id = user_id
                logger.info(f"[on_track_subscribed] User found: ID={user_id}")

                transcript = db.get_transcription(user_id)
                user_data.last_conversation_for_reference = transcript
            else:
                logger.warning(f"[on_track_subscribed] No user found for email: {participant.identity}")
                return

            # Assign default user details (could be dynamic later)
            user_data.user_age = 25
            user_data.user_gender = "MALE"

            # Build context instructions
            instructions = (
                f"You are assisting {user_data.user_name}, "
                f"a {user_data.user_age}-year-old {user_data.user_gender}. "
                f"users email is {user_data.user_email}. Use this mail only as attendees mail while scheduling meetings. "
            )

            if user_data.last_conversation_for_reference:
                instructions += (
                    "Here is the last conversation for context:\n"
                    "Pick only the key terms from this text and use them as memory "
                    "while talking with the user:\n"
                    f"{user_data.last_conversation_for_reference}\n"
                )

            # Append contextual instructions asynchronously
            asyncio.create_task(
                appointment_scheduling_assistant.append_instructions(instructions)
            )
            logger.info(f"[on_track_subscribed] Instructions appended for user {user_data.user_name}.")

        except Exception as e:
            logger.error(f"[on_track_subscribed] Error processing subscription: {str(e)}", exc_info=True)
                 
    await session.start(
        agent=appointment_scheduling_assistant,
        room=ctx.room,
        room_input_options=RoomInputOptions(noise_cancellation=noise_cancellation.BVC(),),
    )
    # await ctx.connect()
    @session.on("conversation_item_added")
    def conversation_item_added(event: ConversationItemAddedEvent):
        """
        Handles conversation_item_added events and stores role-based messages
        (user/assistant) in a single row per session using add_transcription_with_guid.
        """
        try:
            # The actual ChatMessage object is inside `event.item`
            chat_msg = event.item  

            role = getattr(chat_msg, "role", None)
            content_list = getattr(chat_msg, "content", None)

            if not role or not content_list:
                logger.warning("ChatMessage missing role or content, ignoring item.")
                return

            # Join content list to single string
            content = " ".join(content_list).strip()
            if not content:
                logger.warning("Empty content received, ignoring item.")
                return

            # Get session info
            user_id = appointment_scheduling_assistant.session.userdata.user_id
            session_guid = appointment_scheduling_assistant.session.userdata.session_guid
            if not session_guid:
                logger.warning("No session GUID found for this transcription.")
                return

            # Prefix message with role
            role_prefix = "user: " if role == "user" else "agent: "
            new_transcription = f"{role_prefix}{content}"

            logger.info(f"Handling transcription for session: {session_guid}")
            # Save to DB using existing method
            db.add_transcription_with_guid(
                user_id=user_id,
                new_transcription=new_transcription,
                session_guid=session_guid
            )

        except Exception as e:
            logger.error(f"Error processing conversation item: {e}", exc_info=True)


        
    # @session.on("user_input_transcribed")
    # def on_transcript(transcript):
    #     """
    #     Handles incremental transcription updates from user speech input.

    #     This method:
    #     - Buffers partial speech segments until a sentence is complete.
    #     - Deduplicates processed text fragments.
    #     - Stores new transcriptions in DB (tagged by user_id and session GUID).
    #     - Logs all major steps for observability and debugging.

    #     Args:
    #         transcript: The transcribed text object with .transcript attribute.
    #     """

    #     try:
    #         text = transcript.transcript.strip()
    #         if not text:
    #             logger.debug("Received empty transcript — ignoring.")
    #             return

    #         session_guid = appointment_scheduling_assistant.session.userdata.session_guid
    #         if not session_guid:
    #             logger.warning("No session GUID found for this transcription.")
    #         else:
    #             logger.info(f"Handling transcription for session: {session_guid}")

    #         # --- Manage transcription buffer ---
    #         buffer = appointment_scheduling_assistant.transcription_buffer
    #         text_lower = text.lower()

    #         if buffer and text_lower.startswith(buffer.lower()):
    #             # Incremental update (overwrite)
    #             appointment_scheduling_assistant.transcription_buffer = text
    #         else:
    #             # New text (append)
    #             appointment_scheduling_assistant.transcription_buffer = f"{buffer} {text}".strip()

    #         logger.debug(
    #             f"Updated transcription buffer: "
    #             f"{appointment_scheduling_assistant.transcription_buffer[:100]}..."
    #         )

    #         # --- Sentence segmentation ---
    #         sentences = re.split(
    #             r'(?<=[.!?])\s+',
    #             appointment_scheduling_assistant.transcription_buffer.strip()
    #         )

    #         # Retain last incomplete fragment in buffer
    #         complete_sentences = sentences[:-1]
    #         appointment_scheduling_assistant.transcription_buffer = (
    #             sentences[-1] if sentences else ""
    #         )

    #         # --- Deduplication setup ---
    #         processed_transcriptions = getattr(
    #             appointment_scheduling_assistant, "transcriptions", []
    #         )

    #         # --- Process each complete sentence ---
    #         for sentence in complete_sentences:
    #             clean_sentence = sentence.strip()
    #             if not clean_sentence:
    #                 continue

    #             normalized = re.sub(r'\s+', ' ', clean_sentence.lower())

    #             if len(normalized) <= 5:
    #                 continue  # Skip very short noise fragments

    #             if normalized in processed_transcriptions:
    #                 logger.debug(f"Duplicate sentence ignored: {clean_sentence}")
    #                 continue

    #             # New valid transcription
    #             processed_transcriptions.append(normalized)
    #             logger.info(f"Processing new transcription: {clean_sentence}")

    #             user_id = getattr(appointment_scheduling_assistant.session.userdata, "user_id", None)
    #             if not user_id:
    #                 logger.warning("User ID not found — skipping DB write.")
    #                 continue

    #             # --- Save to DB (with session GUID) ---
    #             try:
    #                 db.add_transcription_with_guid(user_id, clean_sentence, session_guid)
    #                 logger.info(f"Saved transcription to DB (user_id={user_id}, session_guid={session_guid}).")
    #             except Exception as db_error:
    #                 logger.error(f"DB error while saving transcription: {db_error}")

    #     except Exception as e:
    #         logger.exception(f"Error in on_transcript handler: {e}")

    if not ctx.room.remote_participants:
        logger.info("No existing participants found - waiting for new connections")
if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm ,drain_timeout=60,initialize_process_timeout=60))
