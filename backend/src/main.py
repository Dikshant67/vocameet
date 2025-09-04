# ==============================================================================
# 5. FASTAPI APP SETUP (LIFESPAN, CORS)
# ==============================================================================
from calendar_service import CalendarService
from fastapi import FastAPI,HTTPException
import logging
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

# from backend.config.config import Config
log_format = '%(asctime)s - %(levelname)s - [Session:%(session_id)s] - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format)
logger = logging.getLogger(__name__)

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

@app.get("/calendar/events")
async def test_availability(start: str, end: str, timezone: str):
    # calendar_service =  _get_state_service(websocket, "calendar") or services.get("calendar")
    calendar_service = services.get("calendar")
    if not calendar_service:
        raise HTTPException(status_code=500, detail="Calendar service not loaded")
    try:
        raw_events = calendar_service.list_meetings(max_results=10)
        availability=calendar_service.process_events(raw_events,timezone)
        logger.info(f"Successfully retrieved {len(availability)} events.")
        return {"availability":availability}
    except Exception as e:
        logger.error(f"Error fetching availability: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error fetching availability.")
# ==============================================================================
# 10. SERVER RUN
# ==============================================================================
if __name__ == "__main__":
    import uvicorn    
    uvicorn.run(app, host="localhost", port=8000)    