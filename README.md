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
2. Python 3.10+ → https://www.python.org/downloads/
3. pip
4. Download and Install docker desktop and create an account  → https://www.docker.com/products/docker-desktop/

# Backend setup
# Create venv
## Create a virtual environment named ".venv"
    python -m venv .venv
## Activate the virtual environment
    .venv\Scripts\activate
## Fix the "Scripts Disable" error in PowerShell(if you need to)
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
## Run the remaining commands
    pip install -r requirements.txt
## Docker 
    docker compose up -d
## 
<img width="1228" height="167" alt="image" src="https://github.com/user-attachments/assets/f76fcdd8-5204-4bf5-8092-37eed05c262c" />

open the mySQL(adminer) portal from docker and login using the following

<img width="987" height="428" alt="image" src="https://github.com/user-attachments/assets/fd4c7bd3-dae0-4e4f-9399-abe00a41d1ec" />
- password → ed_app_pw
  
<img width="1612" height="457" alt="image" src="https://github.com/user-attachments/assets/a196d41c-8ee8-467d-8084-cd06b69c63ea" />

- find the schema.sql in "\GitHub\W26_4495_S2_PhoebeA\Implementation\init-db\schema.sql"
- Execute the file

## 
    uvicorn app.main:app --reload



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

