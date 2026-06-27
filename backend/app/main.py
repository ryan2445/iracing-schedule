from datetime import datetime, timezone
import logging
from typing import Any

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
from app.config import settings
from app.mock_data import MOCK_SERIES, MOCK_TRACKS, get_upcoming_sessions
from app.iracing_api import iracing_client, IRacingClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="iRacing Race Tracker API",
    description="Backend API for tracking upcoming iRacing sessions, schedules, and tracks.",
    version="1.0.0",
)

# Enable CORS for the Svelte frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup() -> None:
    logger.info(f"iRacing Race Tracker starting up. Mock Mode: {settings.mock_mode}")
    if not settings.mock_mode:
        success = iracing_client.login()
        if not success:
            logger.warning("Failed to authenticate with iRacing API. Defaulting to Mock Mode.")
            settings.mock_mode = True

@app.get("/api/status")
def get_status() -> dict[str, Any]:
    return {
        "status": "online",
        "mock_mode": settings.mock_mode,
        "username": settings.iracing_username if settings.iracing_username else "None",
        "time_utc": datetime.now(timezone.utc).isoformat(),
    }

@app.get("/api/series")
def get_series() -> list[dict[str, Any]]:
    if settings.mock_mode:
        return MOCK_SERIES
    
    try:
        # Try fetching real series list
        real_series = iracing_client.get_series_list()
        if real_series:
            # Map/format real series to match our structure if needed, or return directly
            # For now, return real series list
            return real_series
        return MOCK_SERIES
    except Exception as e:
        logger.error(f"Error fetching series, falling back to mock: {e}")
        return MOCK_SERIES

@app.get("/api/tracks")
def get_tracks() -> list[dict[str, Any]]:
    return MOCK_TRACKS

@app.get("/api/categories")
def get_categories() -> list[str]:
    # Extract unique categories
    categories = sorted(list(set(series["category"] for series in MOCK_SERIES)))
    return categories

@app.get("/api/licenses")
def get_licenses() -> list[dict[str, Any]]:
    # Gather distinct license groups and sort by id
    seen = set()
    licenses = []
    for series in MOCK_SERIES:
        g = series["license_group"]
        gid = series["license_group_id"]
        if g not in seen:
            seen.add(g)
            licenses.append({"name": g, "id": gid})
    licenses.sort(key=lambda x: x["id"])
    return licenses

@app.get("/api/sessions")
def get_sessions(
    categories: list[str] | None = Query(None, alias="category"),
    licenses: list[str] | None = Query(None, alias="license"),
    fixed: bool | None = Query(None),
    search: str | None = Query(None),
    days: int = Query(7, ge=1, le=14),
    limit: int | None = Query(None, ge=1),
) -> list[dict[str, Any]]:
    """
    Get upcoming race sessions with advanced filtering.
    """
    try:
        # Currently sessions are generated dynamically from mock/schedule data
        # Even in live mode, generating schedule-based upcoming sessions offers better performance
        # than hitting rate-limited iRacing endpoints for every request.
        sessions = get_upcoming_sessions(days=days)
        
        # Apply filters
        filtered_sessions = []
        for session in sessions:
            # Category filter
            if categories and session["category"] not in categories:
                continue
                
            # License group filter
            if licenses and session["license_group"] not in licenses:
                continue
                
            # Fixed setup filter
            if fixed is not None and session["fixed_setup"] != fixed:
                continue
                
            # Search query filter
            if search:
                query = search.lower()
                series_match = query in session["series_name"].lower()
                track_match = query in session["track"]["track_name"].lower() or query in session["track"]["config_name"].lower()
                car_match = any(query in car.lower() for car in session["cars"])
                if not (series_match or track_match or car_match):
                    continue
                    
            filtered_sessions.append(session)
            
        if limit:
            filtered_sessions = filtered_sessions[:limit]
            
        return filtered_sessions
    except Exception as e:
        logger.error(f"Error filtering sessions: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


class ConfigUpdate(BaseModel):
    iracing_username: str | None = None
    iracing_password: str | None = None
    mock_mode: bool = True


@app.post("/api/config")
def update_config(update: ConfigUpdate) -> dict[str, Any]:
    if not update.mock_mode:
        if not update.iracing_username or not update.iracing_password:
            raise HTTPException(status_code=400, detail="Credentials required to disable mock mode.")
        
        # Test credentials
        test_client = IRacingClient()
        # Temporarily override settings for test
        settings.iracing_username = update.iracing_username
        settings.iracing_password = update.iracing_password
        if not test_client.login():
            settings.iracing_username = None
            settings.iracing_password = None
            raise HTTPException(status_code=401, detail="Authentication failed with iRacing API.")
        
        # Set global client
        iracing_client.client = test_client.client
        iracing_client.is_authenticated = True
        settings.mock_mode = False
    else:
        settings.mock_mode = True
        
    # Write to .env
    try:
        env_lines = []
        if update.iracing_username:
            env_lines.append(f"IRACING_USERNAME={update.iracing_username}\n")
        if update.iracing_password:
            env_lines.append(f"IRACING_PASSWORD={update.iracing_password}\n")
        env_lines.append(f"MOCK_MODE={str(update.mock_mode).lower()}\n")
        
        with open(".env", "w") as f:
            f.writelines(env_lines)
            
        logger.info("Successfully updated .env file with new credentials.")
    except Exception as e:
        logger.error(f"Failed to write .env file: {e}")
        
    return {
        "success": True,
        "mock_mode": settings.mock_mode,
        "message": "Configuration updated successfully."
    }
