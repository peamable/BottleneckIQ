# W26\_4495\_S2\_PhoebeA

Project Repo for BottleneckIQ



Project Name: BottleneckIQ: An Operations Bottleneck Detection System



Team



|Name| 	Student Id|Email|
|-|-|-|
|Phoebe Elikem Amable|300384324|amablep@student.douglascollege.ca|
|Aye Sandar Maung|300394351|maunga1@student.douglascollege.ca|


# Installation instruction
# Prerequisites

Before running the project, make sure you have:

1. Node.js (includes npm) → https://nodejs.org
2. Python 3.10+ 
3. pip

# Backend setup
# Create venv
## Create a virtual environment named ".venv"
    python -m venv .venv
## Activate the virtual environment
    .venv\Scripts\activate
## Fix the "Scripts Disable" error in PowerShell(if you need to)
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
3. pip install -r requirements.txt
4. docker compose up -d
5. uvicorn app.main:app --reload



# Frontend Installation
## check for node and npm installations
- node -v
- npm -v
- python --version
- pip --version
## navigate to frontend folder
### run the following commands
- npm install
- npm install axios
### Chart libraries
- npm install recharts
- npm install react-plotly.js plotly.js

### for icons
- npm install lucide-react
### finally run the project 
- npm run dev

