# W26\_4495\_S2\_PhoebeA

Project Repo for BottleneckIQ



Project Name: BottleneckIQ: An Operations Bottleneck Detection System



Team



|Name| 	Student Id|Email|
|-|-|-|
|Phoebe Elikem Amable|300384324|amablep@student.douglascollege.ca|
|Aye Sandar Maung|300394351|maunga1@student.douglascollege.ca|


## Installation instruction

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

## Prerequisites

Before running the project, make sure you have:

Node.js (includes npm) → https://nodejs.org
Python 3.10+
pip

## Frontend Installation
# check for node and npm installations
node -v
npm -v
python --version
pip --version
# navigate to frontend folder

npm install

## Chart libraries
npm install recharts
npm install react-plotly.js plotly.js

## for icons
npm install lucide-react

nom run dev

