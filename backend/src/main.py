
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

# --- NEW DATABASE IMPORTS ---
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, Session
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
# ==============================================================================
# 3. --- NEW --- DATABASE SETUP (SQLAlchemy with SQLite)
# ==============================================================================
# The database file will be named 'vocameet.db' in the same directory
DATABASE_URL = "sqlite:///./vocameet.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} # Required for SQLite
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- NEW --- Database Model for User
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String)
    picture = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login_time = Column(DateTime)
    last_logout_time = Column(DateTime, nullable=True)

# Create the database tables
Base.metadata.create_all(bind=engine)

# --- NEW --- Dependency to get a DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



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

# -------------------------------
# MODELS
# -------------------------------
class SaveUserPayload(BaseModel):
    name: str
    email: str
    picture: str | None = None
    accessToken: str | None = None  # Google OAuth token if needed
    refreshToken: str | None = None
    userMetadata: dict | None = None

# -------------------------------
# HELPERS
# -------------------------------
def get_current_user(authorization: str = Header(...)):
    """
    Verify NextAuth JWT from frontend.
    Expect header: Authorization: Bearer <jwt>
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")
    
    token = parts[1]
    try:
        payload = jwt.decode(token, NEXTAUTH_SECRET, algorithms=[NEXTAUTH_ALGO])
        email = payload.get("email")
        name = payload.get("name")
        picture = payload.get("picture") or payload.get("image")
        
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        existing_user = db.get_user_by_email(email)
        if not existing_user :
                db.create_user(
                name=name,
                email=email,

                )
                logger.info(f"Created new user for the First Request {email}")
        return {"email": email, "name": name, "picture": picture}
    except JWTError as e:
        logger.error(f"JWT verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")
# -------------------------------
# ROUTES
# -------------------------------
@app.get("/", tags=["root"])
async def read_root():
    return {"message": "🎤 Voice-based Meeting Scheduler API v3.0"}

# @app.post("/api/save-user")
# async def save_user(payload: SaveUserPayload, user: dict = Depends(get_current_user)):
#     """
#     Save or update user info securely in SQLite.
#     Requires valid JWT from NextAuth.
#     """
#     email = payload.email or user["email"]
#     name = payload.name or user["name"]
#     picture = payload.picture or user.get("picture")
#     access_token = payload.accessToken
#     refresh_token = payload.refreshToken
#     user_metadata = payload.userMetadata

#     existing_user = db.get_user_by_email(email)
#     if existing_user:
#         db.update_user(
#             email=email,
#             name=name,
#             picture=picture,
#             access_token=access_token,
#             refresh_token=refresh_token,
#             user_metadata=user_metadata,
#         )
#         logger.info(f"Updated existing user: {email}")
#     else:
#         db.create_user(
#             name=name,
#             email=email,
#             picture=picture,
#             access_token=access_token,
#             refresh_token=refresh_token,
#             user_metadata=user_metadata,
#         )
#         logger.info(f"Created new user: {email}")

#     return {"message": "User saved successfully"}

@app.post("/logout")
async def logout(request: Request, db: Session = Depends(get_db)):
    user_info = request.session.get("user")
    
    # --- NEW DATABASE LOGIC ---
    if user_info and user_info.get("email"):
        user_email = user_info["email"]
        db_user = db.query(User).filter(User.email == user_email).first()
        if db_user:
            db_user.last_logout_time = datetime.utcnow()
            db.commit()
            logger.info(f"User {user_email} logged out and timestamp recorded.")
    # --- END OF NEW DATABASE LOGIC ---
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
# 10. SERVER RUN
# ==============================================================================
if __name__ == "__main__":
    import uvicorn    
    uvicorn.run(app, host="localhost", port=8000 ,reload=True)    