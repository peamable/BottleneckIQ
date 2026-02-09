## Backend setup

1. Install Python 3.13.11
2. Create venv
# 2.1. Create a virtual environment named ".venv"
    python -m venv .venv
# 2.2. Activate the virtual environment
    .venv\Scripts\activate
# 2.3. Fix the "Scripts Disable" error in PowerShell
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
3. pip install -r requirements.txt
4. docker compose up -d
5. uvicorn app.main:app --reload
