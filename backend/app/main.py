from datetime import datetime, timezone, timedelta
import logging
import os
from typing import Any

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.schedule import schedule_engine, PDF_PATH

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="iRacing Race Tracker API",
    description="Backend API for tracking upcoming iRacing sessions, schedules, and tracks from parsed PDF schedule.",
    version="2.0.0",
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
    logger.info("iRacing Race Tracker starting up with Static PDF Schedule Engine.")


@app.get("/api/status")
def get_status() -> dict[str, Any]:
    return {
        "status": "online",
        "mock_mode": False,
        "username": "Static PDF Schedule",
        "time_utc": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/cache/status")
def get_cache_status() -> dict[str, Any]:
    """
    Exposes PDF Schedule parser diagnostic information to the Svelte dashboard.
    We return the status representing in-memory parsing (no disk cache).
    """
    pdf_size = os.path.exists(PDF_PATH) and os.path.getsize(PDF_PATH) or 0

    return {
        "db_path": "iracing_season_3_schedule.pdf",
        "db_size_bytes": pdf_size,
        "total_snapshots": len(schedule_engine.series_list),
        "endpoints": [
            {
                "endpoint": "PDF Parser Engine",
                "count": len(schedule_engine.series_list),
                "last_fetched": datetime.now(timezone.utc).isoformat(),
                "total_bytes": 0,
            }
        ],
        "recent_history": [
            {
                "id": 1,
                "endpoint": "Parsed PDF successfully",
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "size_bytes": 0,
            }
        ],
    }


@app.get("/api/series")
def get_series() -> list[dict[str, Any]]:
    return schedule_engine.series_list


@app.get("/api/tracks")
def get_tracks() -> list[dict[str, Any]]:
    return schedule_engine.tracks_list


@app.get("/api/categories")
def get_categories() -> list[str]:
    return schedule_engine.categories_list


@app.get("/api/licenses")
def get_licenses() -> list[dict[str, Any]]:
    return schedule_engine.licenses_list


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
    Get upcoming race sessions with advanced filtering from the parsed schedule PDF.
    """
    try:
        now = datetime.now(timezone.utc)
        end = now + timedelta(days=days)
        sessions = schedule_engine.generate_sessions_for_range(now, end)

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
                track_match = (
                    query in session["track"]["track_name"].lower()
                    or query in session["track"]["config_name"].lower()
                )
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


@app.post("/api/config")
def update_config() -> dict[str, Any]:
    """
    Configuration update endpoint. Stubbed out as the PDF Schedule is active.
    """
    return {
        "success": True,
        "mock_mode": False,
        "message": "PDF Schedule Engine is active and running.",
    }
