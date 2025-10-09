# main.py
import os
import logging
from typing import Dict, Optional
from fastapi import FastAPI, Request, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from grpc import Status
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from jose import jwt, JWTError
from services.calendar_service import CalendarService
from db.AppDatabase import AppDatabase  # Your SQLite helper
import dotenv 
from dotenv import load_dotenv

# -------------------------------
# CONFIG & LOGGING
# -------------------------------
logging.basicConfig(filename="../logs/assistant.log",level=logging.INFO, format="%(levelname)s: %(asctime)s - %(message)s")
logger = logging.getLogger(__name__)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
NEXTAUTH_SECRET = os.environ.get("NEXTAUTH_SECRET")
logger.info("NEXTAUTH_SECRET:",os.environ.get("NEXTAUTH_SECRET"))

NEXTAUTH_ALGO = "HS256"  # NextAuth uses HS256 by default

# -------------------------------
# DATABASE
# -------------------------------
db = AppDatabase()
logger.info("✅ AppDatabase initialized.")

# -------------------------------
# FASTAPI APP
# -------------------------------
app = FastAPI()

# Session middleware (optional)
app.add_middleware(SessionMiddleware, secret_key=NEXTAUTH_SECRET)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001"
    ],  # adjust for frontend URLs
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
# def get_current_user(authorization: str = Header(...)):
#     """
#     Verify NextAuth JWT from frontend.
#     Expect header: Authorization: Bearer <jwt>
#     """
#     if not authorization:
#         raise HTTPException(status_code=401, detail="Missing Authorization header")
    
#     parts = authorization.split()
#     if len(parts) != 2 or parts[0].lower() != "bearer":
#         raise HTTPException(status_code=401, detail="Invalid Authorization header format")
    
#     token = parts[1]
#     try:
#         payload = jwt.decode(token, NEXTAUTH_SECRET, algorithms=[NEXTAUTH_ALGO])
#         email = payload.get("email")
#         name = payload.get("name")
#         picture = payload.get("picture") or payload.get("image")
        
#         if not email:
#             raise HTTPException(status_code=401, detail="Invalid token payload")
#         existing_user = db.get_user_by_email(email)
#         if not existing_user :
#                 db.create_user(
#                 name=name,
#                 email=email,

#                 )
#                 logger.info(f"Created new user for the First Request {email}")
#         return {"email": email, "name": name, "picture": picture}
#     except JWTError as e:
#         logger.error(f"JWT verification failed: {e}")
#         raise HTTPException(status_code=401, detail="Invalid or expired token")
def get_current_user(
    authorization: str = Header(...),

) -> Dict[str, Optional[str]]:
    """
    Verify NextAuth JWT from frontend and ensure user exists in DB.

    Expected header:
        Authorization: Bearer <jwt>

    Returns:
        dict: Contains user's email, name, and picture.
    """
    if not authorization:
        logger.warning("Missing Authorization header.")
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        logger.warning("Invalid Authorization header format.")
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")

    token = parts[1]

    try:
        # Decode the JWT
        payload = jwt.decode(token, NEXTAUTH_SECRET, algorithms=[NEXTAUTH_ALGO])
        email: Optional[str] = payload.get("email")
        name: Optional[str] = payload.get("name")
        picture: Optional[str] = payload.get("picture") or payload.get("image")

        if not email:
            logger.warning("Token payload missing 'email'.")
            raise HTTPException(status_code=401, detail="Invalid token payload")

        # Check and create user if not present
        existing_user = db.get_user_by_email(email)
        if not existing_user:
            db.create_user(name=name or "Unknown", email=email)
            logger.info(f"Created new user record on first login: {email}")

        logger.info(f"Authenticated user: {email}")
        return {"email": email, "name": name, "picture": picture}

    except JWTError as e:
        logger.error(f"JWT verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    except Exception as e:
        logger.exception(f"Unexpected error in get_current_user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
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

@app.post("/logout", response_model=Dict[str, str])
async def logout(user: Dict = Depends(get_current_user)):
    """
    Log out the current authenticated user.

    - Requires a valid JWT in the Authorization header.
    - Records the logout timestamp in the database.
    """
    try:
        email = user.get("email")

        if not email:
            logger.warning("Logout attempted without a valid user email.")
            raise HTTPException(status_code=400, detail="Invalid user information")

        db.record_logout(email)
        logger.info(f"User '{email}' logged out successfully and timestamp recorded.")

        return {"message": f"User {email} logged out successfully."}

    except HTTPException:
        raise  # Re-raise to preserve intended HTTP codes

    except Exception as e:
        logger.exception(f"Unexpected error during logout for user {user}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/calendar/events")
async def get_calendar_events(start: str, end: str, timezone: str, user: dict = Depends(get_current_user)):
    try:  
        calendar_service = CalendarService()
        raw_events = calendar_service.list_meetings(max_results=10)
        availability = calendar_service.process_events(raw_events, timezone)
        return {"availability": availability, "user": user}
    except Exception as e:
        logger.error(f"Error fetching availability: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error fetching availability.")



# -------------------------------
# RUN
# -------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000, reload=True)
