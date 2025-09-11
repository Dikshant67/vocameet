# ==============================================================================
# 5. FASTAPI APP SETUP (LIFESPAN, CORS)
# ==============================================================================
from calendar_service import CalendarService
from fastapi import FastAPI,Request,HTTPException,Depends
import logging
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
import google.auth.transport.requests
import google.oauth2.id_token
import os
import dotenv

# from backend.config.config import Config
log_format = '%(asctime)s - %(levelname)s - [Session:%(session_id)s] - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format)
logger = logging.getLogger(__name__)

# --- CONFIG ---
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

# --- MODELS ---
class TokenData(BaseModel):
    token: str
services = {}



@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("--- Application starting up... ---")
    
    # --- THIS IS THE FIX ---
    # We will initialize each service in its own try/except block
    # to get detailed error messages if one fails.
    
    try:
       
        
        # Initialize Calendar Service
        try:
            services["calendar"] = CalendarService()
            # app.state.calender_service = CalendarService()
            logger.info("✅ CalendarService initialized.")
        except Exception as e:
            logger.error(f"❌ CalendarService initialization failed: {e}", exc_info=True)
            # Don't continue if critical services fail
            raise e


    except Exception as e:
        # If any service fails, this will log the critical error.
        logger.critical(f"FATAL ERROR during service initialization: {e}", exc_info=True)
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
@app.post("/auth/google")
async def google_auth(data: TokenData, request: Request):
    try:
        # Verify token with Google
        id_info = google.oauth2.id_token.verify_oauth2_token(
            data.token,
            google.auth.transport.requests.Request(),
            audience=GOOGLE_CLIENT_ID
        )

        # Save minimal info in session (what you need later)
        request.session["user"] = {
            "email": id_info.get("email"),
            "name": id_info.get("name"),
            "picture": id_info.get("picture"),
        }

        return {"message": "Authenticated", "user": request.session["user"]}
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {e}")

@app.post("/logout")
async def logout(request: Request):
    logger.info(f"Logging out user: {request.session}")
    request.session.clear()
    return {"message": "Logged out"}

# --- PROTECTED ROUTE EXAMPLE ---
@app.get("/calendar/events")
async def test_availability(start: str, end: str, timezone: str, user: dict = Depends(get_current_user)):
    calendar_service = services.get("calendar")
    if not calendar_service:
        raise HTTPException(status_code=500, detail="Calendar service not loaded")
    try:
        raw_events = calendar_service.list_meetings(max_results=10)
        availability = calendar_service.process_events(raw_events, timezone)
        return {"availability": availability, "user": user}
    except Exception as e:
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