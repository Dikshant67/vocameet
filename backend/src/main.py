
# Standard library imports
import logging
import os
from contextlib import asynccontextmanager
import traceback

# Third-party imports
import dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
import google_auth_oauthlib.flow
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware
from google.oauth2.credentials import Credentials
# Local application imports
from calendar_service import CalendarService
REDIRECT_URI = "postmessage"
# from backend.config.config import Config
LOGGING_FORMAT = '%(levelname)s:     %(asctime)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=LOGGING_FORMAT)
logger = logging.getLogger(__name__)
CLIENT_SECRETS_FILE = os.path.join(os.path.dirname(__file__), "client_secret.json")
# --- CONFIG ---
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

# --- MODELS ---
class TokenData(BaseModel):
    token: str
    calendarToken: str | None = None
services = {}

class AuthCode(BaseModel):
    code: str

# --- LIFESPAN ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("--- Application starting up... ---")
    
    # --- THIS IS THE FIX ---
    # We will initialize each service in its own try/except block
    # to get detailed error messages if one fails.
    
    # try:
       
        
    #     # Initialize Calendar Service
    #     try:
    #         # services["calendar"] = CalendarService()
    #         # app.state.calender_service = CalendarService()
    #         # logger.info("✅ CalendarService initialized.")
    #     except Exception as e:
    #         logger.error(f"❌ CalendarService initialization failed: {e}", exc_info=True)
    #         # Don't continue if critical services fail
    #         raise e


    # except Exception as e:
    #     # If any service fails, this will log the critical error.
    # logger.critical(f"FATAL ERROR during service initialization: {e}", exc_info=True)
    # --- END OF FIX ---

    yield
    
    logger.info("--- Application shutting down... ---")
    
    services.clear()


app = FastAPI(lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key="gsdga3t235f655ghi8kuhjhlghlutuu454554jvbnvn")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["root"])
async def read_root():
    return {"message": "🎤 Voice-based Meeting Scheduler API v3.0"}

# --- AUTH HELPERS ---
def get_current_user(request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

# --- AUTH ROUTES ---
# @app.post("/auth/google")
# async def google_auth(data: TokenData, request: Request):
#     try:
#         logger.info(data)
#         # Verify token with Google
#         id_info = google.oauth2.id_token.verify_oauth2_token(
#             data.token,
#             google.auth.transport.requests.Request(),
#             audience=GOOGLE_CLIENT_ID
#         )

#         # Save minimal info in session (what you need later)
#         request.session["user"] = {
#             "email": id_info.get("email"),
#             "name": id_info.get("name"),
#             "picture": id_info.get("picture"),
#              "calendarToken": data.calendarToken,
#         }

#         return {"message": "Authenticated", "user": request.session["user"]}
#     except Exception as e:
#         raise HTTPException(status_code=401, detail=f"Invalid Google token: {e}")
@app.post("/auth/google")
async def google_auth(auth_code: AuthCode, request: Request):
    try:
        # Step 1: Exchange the authorization code for tokens
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile', 'https://www.googleapis.com/auth/calendar']
        )
        flow.redirect_uri = REDIRECT_URI
        logger.info(f"flow created: {flow}")

        # Exchange the code for credentials
        flow.fetch_token(code=auth_code.code)
        
        credentials = flow.credentials
        logger.info(f"credentials object received: {credentials}")

        # Now you have the tokens!
        # --- THIS IS THE FIX ---
        access_token = credentials.token
        # ---------------------
        refresh_token = credentials.refresh_token # This might be None if user has already granted consent
        id_token_jwt = credentials.id_token

        # Step 2: Get user info from the ID token
        id_info = id_token.verify_oauth2_token(id_token_jwt, google_requests.Request(), GOOGLE_CLIENT_ID)
        
        user_email = id_info['email']
        user_name = id_info['name']
        user_picture = id_info['picture']
        
        # Step 3 (Example): Store credentials and user info in the session
        request.session["user"] = {
            "email": user_email,
            "name": user_name,
            "picture": user_picture,
        }
        request.session["credentials"] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }

        logger.info(f"User {user_email} successfully authenticated.")
        # Return the user info to the frontend
        return {"name": user_name, "email": user_email, "picture": user_picture}
        
    except Exception as e:
        # This is the output we need to see!
        print("---!!! AN ERROR OCCURRED !!!---")
        print(f"The actual error is: {e}")
        import traceback
        traceback.print_exc() # This prints the full error stack
@app.post("/logout")
async def logout(request: Request):
    logger.info(f"Logging out user: {request.session}")
    request.session.clear()
    return {"message": "Logged out"}

# --- PROTECTED ROUTE EXAMPLE ---
# @app.get("/calendar/events")
# async def test_availability(start: str, end: str, timezone: str, user: dict = Depends(get_current_user)):
#     calendar_token = user.get("calendarToken")
#     if not calendar_token:
#         logger.warning("No calendar access token found for user.")
#         raise HTTPException(status_code=401, detail="No calendar access token found")
#     logger.info(f"token :- {calendar_token}")
#     calendar_service = CalendarService(calendar_token)
#     if not calendar_service:
#         raise HTTPException(status_code=500, detail="Calendar service not loaded")
#     try:
#         raw_events = calendar_service.list_meetings(max_results=10)
        
#         availability = calendar_service.process_events(raw_events, timezone)
#         return {"availability": availability, "user": user}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail="Error fetching availability.")
@app.get("/calendar/events")
async def get_calendar_events(request: Request, start: str, end: str, timezone: str, user: dict = Depends(get_current_user)):
    # --- THIS IS THE NEW, CORRECT LOGIC ---

    # 1. Get the full credentials dictionary from the session
    creds_dict = request.session.get("credentials")
    if not creds_dict:
        logger.warning(f"No stored credentials found for user {user.get('email')}")
        raise HTTPException(status_code=401, detail="User credentials not found in session.")

    # 2. Recreate a valid Credentials object from the dictionary
    try:
        credentials = Credentials(**creds_dict)
    except Exception as e:
        logger.error(f"Failed to rebuild credentials from session data: {e}")
        raise HTTPException(status_code=500, detail="Could not validate stored credentials.")

    # 3. Initialize the CalendarService with the credentials object
    calendar_service = CalendarService(credentials)
    
    # 4. Fetch and process events as before
    try:
        raw_events = calendar_service.list_meetings(max_results=10)
        availability = calendar_service.process_events(raw_events, timezone)
        return {"availability": availability, "user": user}
    except Exception as e:
        logger.error(f"Error fetching availability: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error fetching availability.")

@app.get("/check")
async def check_user(user: dict = Depends(get_current_user)):
    """Check if a user is authenticated."""
    logger.info(f"User checked: {user}")
    return {"message": f"Hello, {user['name']}! You are logged in."}

# ==============================================================================
# 10. SERVER RUN
# ==============================================================================
if __name__ == "__main__":
    import uvicorn    
    uvicorn.run(app, host="localhost", port=8000 ,reload=True)    