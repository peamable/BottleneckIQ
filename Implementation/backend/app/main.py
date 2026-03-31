from fastapi import FastAPI, HTTPException
from sqlalchemy import text, inspect
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine
from app.router.upload import router as upload_router
from app.router.metrics import router as metrics_router
from app.router.insights import router as insights_router
from app.router.reports import router as reports_router



app = FastAPI(title="ED Bottleneck API")

# allow request from frontend side
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# test simple API  
@app.get("/test_ed")
def test():
    return {"status": "ok"}


# test db connection is working fine
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


app.include_router(upload_router)
app.include_router(metrics_router)
app.include_router(insights_router)
app.include_router(reports_router)
