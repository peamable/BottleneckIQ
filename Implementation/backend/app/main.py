import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text, inspect


# Load .env from implementation folder 
load_dotenv() 

app = FastAPI(title="ED Bottleneck API")

# connect fastapi and mySQL db on localhost and port
def get_db_url() -> str:
    db_user = os.getenv("DB_USER", "")
    db_pw = os.getenv("DB_PASSWORD", "")
    db_name = os.getenv("DB_NAME", "")
    db_host = os.getenv("DB_HOST", "127.0.0.1")
    db_port = os.getenv("DB_PORT", "3307")

   
   
    if not all([db_user, db_pw, db_name]):
        raise RuntimeError("Missing DB env vars. Check .env (DB_USER, DB_PASSWORD, DB_NAME).")

   
    return f"mysql+pymysql://{db_user}:{db_pw}@{db_host}:{db_port}/{db_name}"

 
# create engine to communicate with fastAPI
engine = create_engine(get_db_url(), pool_pre_ping=True)


# test simple API  
@app.get("/test_ed")
def test():
    return {"status": "ok"}


# test db connection is working file
@app.get("/db-connect")
def db_connect():
    try:
        with engine.connect() as connect:
            result = connect.execute(text("SELECT 1")).scalar()
        return {"db": "ok", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Database not reachable")
    
# get table names from Docker db
# Use the inspector to get schema information
@app.get("/db-tables")
def list_db_tables():
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    return {
        "database": engine.url.database,
        "tables": tables,
        "count": len(tables)
    }


