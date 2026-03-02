from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path
import backend.config as config

engine = create_engine(config.DATABASE_URL, connect_args={"check_same_thread": False})

sessionLocal = sessionmaker(bin=engine, autoflush=False, autocommit=False)

Base = declarative_base()
