import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env from implementation folder 
load_dotenv()

# set up for database URL and upload directory
def get_settings():
    db_user = os.getenv("DB_USER", "")
    db_pw = os.getenv("DB_PASSWORD", "")
    db_name = os.getenv("DB_NAME", "")
    db_host = os.getenv("DB_HOST", "127.0.0.1")
    db_port = os.getenv("DB_PORT", "3307")

    if not all([db_user, db_pw, db_name]):
        raise RuntimeError("Missing DB env vars. Check .env (DB_USER, DB_PASSWORD, DB_NAME).")

    upload_dir_env = os.getenv("UPLOAD_DIR", "./data/input")
    upload_dir = Path(upload_dir_env).resolve()
    upload_dir.mkdir(parents=True, exist_ok=True)

    return {
        "DATABASE_URL": f"mysql+pymysql://{db_user}:{db_pw}@{db_host}:{db_port}/{db_name}",
        "UPLOAD_DIR": upload_dir,
    }

settings = get_settings()