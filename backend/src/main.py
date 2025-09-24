# Standard library imports
from datetime import datetime
import logging
import os
from contextlib import asynccontextmanager
import traceback
from livekit import api

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

# --- NEW: Local application imports ---
from AppDatabase import AppDatabase # Assuming your file is named app_database.py
from calendar_service import CalendarService

# --- CONFIG & LOGGING ---
dotenv.load_dotenv()
REDIRECT_URI = "postmessage"
LOGGING_FORMAT = '%(levelname)s:     %(asctime)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=LOGGING_FORMAT)
logger = logging.getLogger(__name__)
CLIENT_SECRETS_FILE = os.path.join(os.path.dirname(__file__), "client_secret.json")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

# ==============================================================================
# --- NEW: DATABASE SETUP (Using AppDatabase Class) ---
# ==============================================================================
# Create a single, global instance of the AppDatabase.
# The __init__ method of your class will handle table creation.
db = AppDatabase()
logger.info("✅ AppDatabase initialized.")

# --- REMOVED: All SQLAlchemy setup (engine, SessionLocal, Base, User model, get_db) ---

# --- MODELS ---
class TokenData(BaseModel):
    token: str
    calendarToken: str | None = None

class AuthCode(BaseModel):
    code: str

# --- LIFESPAN ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("--- Application starting up... ---")
    yield
    logger.info("--- Application shutting down... ---")


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
@app.post("/auth/google")
async def google_auth(auth_code: AuthCode, request: Request):
    try:
        # Step 1: Exchange the authorization code for tokens
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile', 'https://www.googleapis.com/auth/calendar']
        )
        flow.redirect_uri = REDIRECT_URI
        flow.fetch_token(code=auth_code.code)
        
        credentials = flow.credentials
        id_token_jwt = credentials.id_token

        # Step 2: Get user info from the ID token
        id_info = id_token.verify_oauth2_token(id_token_jwt, google_requests.Request(), GOOGLE_CLIENT_ID)
        
        user_email = id_info['email']
        user_name = id_info['name']
        
        # --- NEW DATABASE LOGIC using AppDatabase instance ---
        db_user = db.get_user_by_email(user_email)

        if db_user:
            # User exists, update their last login time and info
            logger.info(f"Existing user '{user_email}' logged in.")
            db.update_user_on_login(user_id=db_user['id'], name=user_name)
        else:
            # New user, create a record
            logger.info(f"New user '{user_email}' created and logged in.")
            db.create_user(name=user_name, email=user_email)
        # --- END OF NEW DATABASE LOGIC ---

        # Step 3: Store credentials and user info in the session
        request.session["user"] = {
            "email": user_email,
            "name": user_name,
            "picture": id_info.get('picture'),
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
        return {"name": user_name, "email": user_email, "picture": id_info.get('picture')}
        
    except Exception as e:
        logger.error(f"Authentication error: {e}", exc_info=True)
        traceback.print_exc()
        raise HTTPException(status_code=401, detail=f"Authentication failed: {e}")

@app.post("/logout")
async def logout(request: Request):
    user_info = request.session.get("user")
    
    # --- NEW DATABASE LOGIC ---
    if user_info and user_info.get("email"):
        user_email = user_info["email"]
        db.record_logout(user_email) # Use the new method
        logger.info(f"User {user_email} logged out and timestamp recorded.")
    # --- END OF NEW DATABASE LOGIC ---

    request.session.clear()
    return {"message": "Logged out"}

# --- PROTECTED ROUTE EXAMPLE ---
@app.get("/calendar/events")
async def get_calendar_events(request: Request, start: str, end: str, timezone: str, user: dict = Depends(get_current_user)):
    creds_dict = request.session.get("credentials")
    if not creds_dict:
        logger.warning(f"No stored credentials found for user {user.get('email')}")
        raise HTTPException(status_code=401, detail="User credentials not found in session.")

    try:
        credentials = Credentials(**creds_dict)
        calendar_service = CalendarService(credentials)
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

@app.get('/getToken')
def getToken():
    token = api.AccessToken("devkey", "secret") \
        .with_identity("identity") \
        .with_name("dikshant") \
        .with_grants(api.VideoGrants(
            room_join=True,
            room="my-room",
        ))
    return token.to_jwt()

# ==============================================================================
# SERVER RUN
# ==============================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000, reload=True)