# iRacing Race Tracker

Lists upcoming iRacing races with extensive filtering options and multiple mobile-friendly views. Features a gorgeous high-fidelity dark mode, dynamic linear timeline schedules, and an interactive weekly calendar planner.

## Project Structure

- `frontend/`: Svelte 5 (Vite, TypeScript, Lucide Icons, Custom CSS variables, Dark Sim-Racing Theme)
- `backend/`: Python 3.14 (FastAPI, uvicorn, uv, static typing, mypy & ruff clean)

## Features

- **Linear Timeline**: Displays active race sessions in chronological order with live countdowns.
- **Calendar Planner**: Interactive 7-day linear day selector that highlights daily races with timeline tracks.
- **Comprehensive Filters**: Filters by category (Sports Car, Formula, Oval, etc.), license class, setup constraints, or custom search query.
- **Connection Switcher**: Syncs live data directly from members-ng.iracing.com when logging in, or defaults to realistic simulated mock schedules.

## Local Development Quickstart

### 1. Run the Python Backend

```bash
cd backend
# Install dependencies and launch the server using uv
uv run python main.py
```

The FastAPI API server will be available at `http://localhost:8000`. You can explore the interactive OpenAPI documentation at `http://localhost:8000/docs`.

### 2. Run the Svelte Frontend

```bash
cd frontend
# Install dependencies and start the Vite dev server
npm install
npm run dev
```

The frontend will start at `http://localhost:5173`. Open it in your browser and enjoy the ultimate sim-racing tracker!
