from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base
from config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


def create_app(_engine=None) -> FastAPI:
    from app.routes import router

    if _engine is not None:
        global engine, SessionLocal
        engine = _engine
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    app = FastAPI(
        title="Game Collection Tracker API",
        description="REST API for tracking video game collections, playtime, and achievements",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    init_db()
    app.include_router(router, prefix="/api")

    return app
