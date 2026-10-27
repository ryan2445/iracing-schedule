# iRacing Race Tracker

Lists upcoming iRacing races with filtering options and mobile-friendly views.

## Local Development & Build Quickstart

### 1. (Optional) Parse and Export the PDF Schedule

Whenever the source `iracing_season_4_schedule.pdf` changes, or you want to update the parsed database, compile the schedule using the Python parser:

```bash
cd backend
# Run python to parse the PDF and output to the Svelte app's source folder
.venv/bin/python export_schedule.py
```

This updates `frontend/src/lib/schedule.json`.

### 2. Run the Svelte Frontend Locally

Since the frontend computes everything locally, you can develop and run the client-side tracker without any active servers:

```bash
cd frontend
# Install dependencies
npm install

# Start the Vite development server
npm run dev
```
