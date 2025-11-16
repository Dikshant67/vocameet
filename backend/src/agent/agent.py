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
logging.basicConfig(
    filename="../../logs/assistant.log",
    level=logging.INFO,
    format="%(levelname)s: %(asctime)s - %(message)s",
)
logger = logging.getLogger(__name__)

load_dotenv()
db = AppDatabase()


@dataclass
class UserData:
    """ A class to store user information during the call"""
    session: AgentSession = None
    ctx: Optional[JobContext] = None
    user_id: Optional[int] = None
    session_guid: Optional[str] = None
    user_name: Optional[str] = None
    meeting_date: Optional[str] = None
    meeting_title: Optional[str] = None
    meeting_attendee: Optional[str] = None
    last_conversation_for_reference: Optional[str] = None
    user_email: Optional[str] = None
    user_gender: Optional[str] = None
    user_age: Optional[int] = None
    greeted: Optional[bool]=False

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


RunContext_T = RunContext[UserData]


class AppointmentSchedulingAssistant(Agent):
    def __init__(self, ctx: JobContext) -> None:
        now = datetime.datetime.now(datetime.timezone.utc).astimezone()  # Timezone-aware
        self.transcriptions: List[str] = []
        self.transcription_buffer: str = ""
        self._agent_session: Optional[AgentSession] = None
        self._ctx = ctx

        current_date_str = now.strftime("%A, %B %d, %Y")

        self.base_instructions = f"""You are a friendly and helpful voice AI assistant designed for managing meetings .
            The current date and time is {current_date_str}.
            When you first connect,Greet user with a friendly greeting and offer a friendly welcome.for example if users name is Arun Kumar,Hi Arun 
            **CRITICAL INSTRUCTION: Your responses MUST be in plain text only. NEVER use any special formatting, including asterisks, bolding, italics, or bullet points.**
            Do not accept the dates and time in the past suggest them to use in future dates and times.
            Do not read ,refer asterisk symbol in any context.
            This is a voice conversation — speak naturally, clearly, and concisely. 
            When the user says hello or greets you, don’t just respond with a greeting — use it as an opportunity to move things forward. 
            For example, follow up with a helpful question like: 'Would you like to book a time?' 
            "Always keep the conversation flowing — be proactive, human, and focused on helping the user schedule with ease."
            If you are proccesing a request then just say let me think or proccesing your request or fetching data wait a moment etc
            Dont go completely silent when generating response.
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

    @property
    def agent_session(self) -> Optional[AgentSession]:
        """Safe accessor for the AgentSession created in entrypoint."""
        return self._agent_session

    # all functions annotated with @function_tool will be passed to the LLM when this
    # agent is active

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
        try:
            await self.update_instructions(new_instructions)
            logger.info("Instructions updated for agent.")
        except Exception:
            logger.exception("Failed to update instructions.")
        self.base_instructions = new_instructions  # Keep track for future appends

    @function_tool
    async def lookup_weather(self, context: RunContext_T, location: str):
        logger.info(f"Looking up weather for {location}")
        return "sunny with a temperature of 70 degrees."

    @function_tool
    async def fetch_experts(self, context: RunContext_T, user_requirement: str):
        logger.info(f"Fetching experts for user requirement: {user_requirement}")
        experts_db = db.get_all_experts()
        return experts_db

    @function_tool
    async def get_the_summary_of_user_info(self, context: RunContext_T) -> str:
        name = getattr(context.userdata, "user_name", None) or "Unknown"
        age = getattr(context.userdata, "user_age", None) or "N/A"
        gender = getattr(context.userdata, "user_gender", None) or "Not specified"
        return f"User's Name is {name}, Age is {age}, Gender is {gender}."

    @function_tool
    async def get_current_date(self, context: RunContext_T) -> str:
        now = datetime.datetime.now()
        return now.strftime("%A, %B %d, %Y at %I:%M %p")

    async def save_meeting_in_db(self, event_id: str, user_id: int, expert_id: int, title: str, start_time: str, end_time: str, attendees: list[str]):
        db.create_appointment(event_id, user_id, expert_id, title, start_time, end_time)
        return "meeting saved successfully"

    async def handle_track_subscribed(self, track, publication, participant):
        """
        Handle room track_subscribed events. Uses internal _agent_session backing field.
        This method schedules any heavy async work (DB/IO) using asyncio.create_task to avoid blocking.
        """
        try:
            sess = self.agent_session
            if not sess:
                logger.warning("[handle_track_subscribed] agent_session not set yet; skipping handling.")
                return

            # defensive metadata parsing
            session_guid = None
            if getattr(participant, "metadata", None):
                try:
                    import json
                    metadata = json.loads(participant.metadata)
                    session_guid = metadata.get("sessionGuid")
                except Exception:
                    logger.exception("[handle_track_subscribed] Failed to parse participant.metadata")

            # populate userdata on agent_session
            userdata = sess.userdata
            userdata.user_name = participant.name
            userdata.user_email = participant.identity
            userdata.session_guid = session_guid

            # try lookup in DB only when we have an email/identity
            if userdata.user_email:
                try:
                    user_id = db.get_user_by_email(userdata.user_email)
                    if user_id:
                        userdata.user_id = user_id
                        transcript = db.get_transcription(user_id)
                        userdata.last_conversation_for_reference = transcript
                    else:
                        logger.info(f"[handle_track_subscribed] No user row for email {userdata.user_email}")
                except Exception:
                    logger.exception("[handle_track_subscribed] DB lookup failed")

            # defaults
            if userdata.user_age is None:
                userdata.user_age = 25
            if userdata.user_gender is None:
                userdata.user_gender = "MALE"
                        # proactively greet the user once per session
            try:
                #if not getattr(userdata, "greeted", False):
                #    userdata.greeted = True
                    greeting = (
                        f"Hi {userdata.user_name or 'there'}. "
                        "Welcome back. I can help you schedule meetings — would you like to book a time?"
                    )
                    sess = self.agent_session
                    if sess and hasattr(sess, "generate_reply"):
                        # schedule coroutine so we don't block the handler
                        asyncio.create_task(sess.generate_reply(instructions=greeting))
                    else:
                        logger.debug("[handle_track_subscribed] session not ready or no generate_reply available")
            except Exception:
                logger.exception("[handle_track_subscribed] failed to send proactive greeting")

            # Build short contextual instructions
            instructions = (
                f"You are assisting {userdata.user_name or 'Unknown'}, "
                f"a {userdata.user_age}-year-old {userdata.user_gender}. "
                f"users email is {userdata.user_email or 'Unknown'}. Use this mail only as attendees mail while scheduling meetings. "
            )
            if userdata.last_conversation_for_reference:
                instructions += (
                    "Here is the last conversation for context:\n"
                    "Pick only the key terms from this text and use them as memory "
                    "while talking with the user:\n"
                    f"{userdata.last_conversation_for_reference}\n"
                )

            # schedule append_instructions so the event loop isn't blocked
            asyncio.create_task(self.append_instructions(instructions))
            logger.info(f"[handle_track_subscribed] Appended instructions for {userdata.user_name}")

        except Exception:
            logger.exception("[handle_track_subscribed] Unexpected error")

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
            # parse start
            dt_start_obj = datetime.datetime.fromisoformat(start_time)
            if dt_start_obj.tzinfo is None:
                start_dt = tz.localize(dt_start_obj)
            else:
                start_dt = dt_start_obj.astimezone(tz)
            # parse end
            dt_end_obj = datetime.datetime.fromisoformat(end_time)
            if dt_end_obj.tzinfo is None:
                end_dt = tz.localize(dt_end_obj)
            else:
                end_dt = dt_end_obj.astimezone(tz)
        except Exception as e:
            raise ValueError(f"Invalid datetime format. Could not parse '{start_time}'. Error: {e}")

        start_utc = start_dt.astimezone(pytz.UTC)
        end_utc = end_dt.astimezone(pytz.UTC)

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

        if not expert_id or not desired_start:
            raise ValueError("Missing required arguments: expert_id or desired_start.")

        tz = pytz.timezone(timezone)

        try:
            dt_desired = datetime.datetime.fromisoformat(desired_start)
            if dt_desired.tzinfo is None:
                desired_dt = tz.localize(dt_desired)
            else:
                desired_dt = dt_desired.astimezone(tz)
        except Exception as e:
            raise ValueError(f"Invalid datetime format for desired_start: {e}")

        desired_start_utc = desired_dt.astimezone(pytz.UTC)

        expert = db.get_expert(expert_id)
        if not expert:
            return f"No expert found with id {expert_id}."

        suggested_slots_utc = db.suggest_next_available_slots(
            expert_id,
            desired_start_utc,
            duration_minutes=duration_minutes,
            limit=limit
        )

        if not suggested_slots_utc:
            return f"No available slots found for expert {expert['name']} after {desired_dt.strftime('%I:%M %p on %b %d')}."

        formatted_slots = []
        for start_utc, end_utc in suggested_slots_utc:
            start_local = start_utc.astimezone(tz)
            end_local = end_utc.astimezone(tz)
            formatted_slots.append(
                f"{start_local.strftime('%A, %b %d from %I:%M %p')} to {end_local.strftime('%I:%M %p %Z')}"
            )

        formatted_text = "\n".join(f"- {slot}" for slot in formatted_slots)
        return f"Here are the next available time slots for expert {expert['name']}:\n{formatted_text}"

    @function_tool
    async def list_meetings_by_date(
        self,
        context: "RunContext_T",
        date: str,
        max_results: int = 10
    ) -> List[dict] | str:
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
    """
    Robust prewarm: attempt to load VAD but don't allow exceptions to kill the child process.
    """
    try:
        proc.userdata["vad"] = silero.VAD.load()
        logger.info("silero VAD loaded in prewarm.")
    except Exception:
        logger.exception("prewarm failed; continuing without VAD.")
        proc.userdata["vad"] = None


async def entrypoint(ctx: JobContext):
    # Initialize user data with context
    userdata = UserData(ctx=ctx)

    appointment_scheduling_assistant = AppointmentSchedulingAssistant(ctx)
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession[UserData](
        userdata=userdata,
        llm=openai.LLM.with_azure(
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        ),
        stt=azure.STT(
            speech_key=os.getenv("AZURE_SPEECH_KEY"),
            speech_region=os.getenv("AZURE_SPEECH_REGION"),
            language="en-IN",
        ),
        tts=azure.TTS(
            speech_key=os.getenv("AZURE_SPEECH_KEY"),
            speech_region=os.getenv("AZURE_SPEECH_REGION"),
            voice="en-IN-AartiNeural",
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata.get("vad"),
        preemptive_generation=True,
    )

    # give the agent access to the session via backing field
    appointment_scheduling_assistant._agent_session = session

    # safe room-level handlers
    @ctx.room.on("participant_disconnected")
    def on_participant_disconnected(participant: rtc.RemoteParticipant):
        logger.info(f"User disconnected: {participant}")

    # register track_subscribed to delegate to agent method
    @ctx.room.on("track_subscribed")
    def _room_track_subscribed(track, publication, participant):
        asyncio.create_task(
            appointment_scheduling_assistant.handle_track_subscribed(track, publication, participant)
        )

    # start the agent session
    await session.start(
        agent=appointment_scheduling_assistant,
        room=ctx.room,
        room_input_options=RoomInputOptions(noise_cancellation=noise_cancellation.BVC(),close_on_disconnect=False),
    )
    # convers   ation item handler uses the agent_session accessor
    @session.on("conversation_item_added")
    def conversation_item_added(event: ConversationItemAddedEvent):
        try:
            chat_msg = event.item
            role = getattr(chat_msg, "role", None)
            content_list = getattr(chat_msg, "content", None)

            if not role or not content_list:
                logger.warning("ChatMessage missing role or content, ignoring item.")
                return

            content = " ".join(content_list).strip()
            if not content:
                logger.warning("Empty content received, ignoring item.")
                return

            sess = appointment_scheduling_assistant.agent_session
            if not sess:
                logger.warning("agent_session not yet available; skipping conversation_item_added processing.")
                return

            user_id = sess.userdata.user_id
            session_guid = sess.userdata.session_guid
            if not session_guid:
                logger.warning("No session GUID found for this transcription.")
                return

            role_prefix = "user: " if role == "user" else "agent: "
            new_transcription = f"{role_prefix}{content}"

            logger.info(f"Handling transcription for session: {session_guid}")
            db.add_transcription_with_guid(
                user_id=user_id,
                new_transcription=new_transcription,
                session_guid=session_guid
            )

        except Exception:
            logger.exception("Error processing conversation item")

    if not ctx.room.remote_participants:
        logger.info("No existing participants found - waiting for new connections")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
