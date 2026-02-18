from sqlalchemy import create_engine
from app.config import settings


# create engine to communicate with fastAPI
engine = create_engine(settings["DATABASE_URL"], pool_pre_ping=True)
