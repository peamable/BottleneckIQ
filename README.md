# W26\_4495\_S2\_PhoebeA

Project Repo for BottleneckIQ
Project Name: BottleneckIQ: An Operations Bottleneck Detection System
Team

|Name| 	Student Id|Email|
|-|-|-|
|Phoebe Elikem Amable|300384324|amablep@student.douglascollege.ca|
|Aye Sandar Maung|300394351|maunga1@student.douglascollege.ca|

# Installation Instructions

## Prerequisites

Before running the project, install the following:

1. Node.js and npm: https://nodejs.org
2. Python 3.10 or later: https://www.python.org/downloads/
3. Docker Desktop: https://www.docker.com/products/docker-desktop/

## Project Structure Used In Setup

Run setup commands from these folders:

1. `Implementation` for Docker and the shared backend database `.env`
2. `Implementation/backend` for Python backend setup and FastAPI
3. `Implementation/frontend` for Vite frontend setup and React

## 1. Configure Environment Variables

### Backend and Docker

From the `Implementation` folder, copy `.env.example` to `.env` and fill in the database values.

Required keys:

1. `DB_NAME`
2. `DB_USER`
3. `DB_PASSWORD`
4. `DB_ROOT_PASSWORD`

Example:

```powershell
cd Implementation
Copy-Item .env.example .env
```

The backend uses these values to connect to MySQL, and Docker uses the same values to initialize the database container.

### Frontend Firebase Auth

From the `Implementation/frontend` folder, copy `.env.example` to `.env` and fill in your Firebase web app values.

Required keys:

1. `VITE_FIREBASE_API_KEY`
2. `VITE_FIREBASE_AUTH_DOMAIN`
3. `VITE_FIREBASE_PROJECT_ID`
4. `VITE_FIREBASE_STORAGE_BUCKET`
5. `VITE_FIREBASE_MESSAGING_SENDER_ID`
6. `VITE_FIREBASE_APP_ID`

Example:

```powershell
cd Implementation/frontend
Copy-Item .env.example .env
```

## 2. Start Docker Services

From the `Implementation` folder:

```powershell
cd Implementation
docker compose up -d
```

This starts:

1. MySQL on `127.0.0.1:3307`
2. Adminer on `http://localhost:8080`

## 3. Initialize The Database Schema

Open Adminer at `http://localhost:8080` and sign in using the same credentials stored in `Implementation/.env`.

Typical Adminer values:

1. System: `MySQL`
2. Server: `db`
3. Username: value of `DB_USER`
4. Password: value of `DB_PASSWORD`
5. Database: value of `DB_NAME`

Then load and execute:

`Implementation/init-db/schema.sql`

## 4. Set Up And Run The Backend

From the `Implementation/backend` folder:

```powershell
cd Implementation/backend
python -m venv .venv
```

Activate the virtual environment:

```powershell
.venv\Scripts\activate
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```

Install backend dependencies:

```powershell
pip install -r requirements.txt
```

Start the FastAPI server:

```powershell
uvicorn app.main:app --reload
```

The backend will be available at `http://localhost:8000`.

## 5. Set Up And Run The Frontend

From the `Implementation/frontend` folder:

```powershell
cd Implementation/frontend
npm install
npm run dev
```

The frontend uses Vite and will be available at `http://localhost:5173`.

## 6. Recommended Run Order

For a first-time setup, use this order:

1. Configure `Implementation/.env`
2. Configure `Implementation/frontend/.env`
3. Start Docker with `docker compose up -d`
4. Run `schema.sql` in Adminer
5. Start the backend with `uvicorn app.main:app --reload`
6. Start the frontend with `npm run dev`

## 7. Quick Verification Checklist

Before testing the app, confirm that:

1. Docker containers are running
2. Adminer opens at `http://localhost:8080`
3. FastAPI responds at `http://localhost:8000`
4. The frontend opens in the browser
5. Login works with your Firebase configuration
6. CSV upload completes and opens the View Metrics page

## 8. Common Setup Problems

### Missing database environment variables

If the backend fails with a missing DB environment variable error, confirm `Implementation/.env` exists and includes:

1. `DB_NAME`
2. `DB_USER`
3. `DB_PASSWORD`

### Frontend login does not work

If authentication fails before reaching the app flow, confirm `Implementation/frontend/.env` exists and contains the Firebase `VITE_...` variables.

### MySQL connection issues

Confirm Docker is running and that MySQL is exposed on port `3307`.

### Schema not loaded

If uploads or dashboards fail with missing table errors, execute `Implementation/init-db/schema.sql` in Adminer before testing the full workflow.

