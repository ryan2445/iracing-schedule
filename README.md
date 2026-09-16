# iRacing Race Tracker

Lists upcoming iRacing races with extensive filtering options and multiple mobile-friendly views. Features a gorgeous high-fidelity dark mode, dynamic linear timeline schedules, and an interactive weekly calendar planner.

## Architecture

This project is built as a **100% serverless static website** that can be hosted on AWS (via S3 + CloudFront or AWS Amplify) for $0/month.

- **Frontend**: Svelte 5 (Vite, TypeScript, Lucide Icons, custom CSS variables, and a dark sim-racing theme). All session-generation logic, search queries, category filtering, and sorting are computed entirely on the client side in the browser.
- **Backend (Build-Time Parser)**: A Python 3.12+ command-line tool that parses the official static iRacing Season Schedule PDF and pre-compiles the recurrence rules, track associations, and session schedules into a bundled JSON database.

---

## Features

- **Linear Timeline**: Displays active race sessions in chronological order with live browser-based countdowns.
- **Calendar Planner**: Interactive 7-day linear day selector that highlights daily races with timeline tracks.
- **Comprehensive Filters**: Zero-latency search and filter options by category (Sports Car, Formula, Oval, etc.), license class, setup constraints, or custom search query.
- **Static & Offline Capable**: Because all schedule computations are written in TypeScript, the site does not need a running backend API server and runs entirely offline after loading.

---

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

---

## Static Production Build & AWS Deployment

### 1. Build the Static Files

To compile the Svelte application into highly optimized, minified static files:

```bash
cd frontend
npm run build
aws s3 sync dist/ s3://<bucket>/tracker --delete
```
