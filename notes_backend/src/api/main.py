import os
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, func
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Database setup
# Read DATABASE_URL from environment, fallback to local postgres default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5001/postgres",
)

# SQLAlchemy engine and session
engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


class Note(Base):
    """SQLAlchemy Note model representing the notes table."""
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


# Create tables if they don't exist
Base.metadata.create_all(bind=engine)


# FastAPI app with metadata and tags
app = FastAPI(
    title="Notes API",
    description="Simple Notes CRUD API built with FastAPI and PostgreSQL.",
    version="1.0.0",
    openapi_tags=[
        {"name": "health", "description": "Service health and status"},
        {"name": "notes", "description": "Operations on notes (CRUD)"},
    ],
)

# CORS configuration: allow frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    """Dependency to provide a database session and ensure it is closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Pydantic Schemas
class NoteBase(BaseModel):
    title: str = Field(..., description="Title of the note", min_length=1, max_length=255)
    content: str = Field(..., description="Content of the note")


class NoteCreate(NoteBase):
    """Schema for creating a new note."""
    pass


class NoteUpdate(BaseModel):
    title: Optional[str] = Field(None, description="Updated title of the note", min_length=1, max_length=255)
    content: Optional[str] = Field(None, description="Updated content of the note")


class NoteRead(NoteBase):
    id: int = Field(..., description="Unique identifier of the note")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


# Routes

# PUBLIC_INTERFACE
@app.get("/", tags=["health"], summary="Health Check", description="Returns a simple message indicating the service is healthy.")
def health_check():
    """Health endpoint to verify service status."""
    return {"message": "Healthy"}


# PUBLIC_INTERFACE
@app.get(
    "/notes",
    response_model=List[NoteRead],
    tags=["notes"],
    summary="List notes",
    description="Retrieve all notes ordered by most recently updated first.",
)
def list_notes(db: Session = Depends(get_db)):
    """List all notes sorted by updated_at descending."""
    notes = db.query(Note).order_by(Note.updated_at.desc()).all()
    return notes


# PUBLIC_INTERFACE
@app.get(
    "/notes/{note_id}",
    response_model=NoteRead,
    tags=["notes"],
    summary="Get note by ID",
    description="Retrieve a single note by its unique identifier.",
)
def get_note(note_id: int, db: Session = Depends(get_db)):
    """Fetch a single note by ID."""
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


# PUBLIC_INTERFACE
@app.post(
    "/notes",
    response_model=NoteRead,
    status_code=201,
    tags=["notes"],
    summary="Create note",
    description="Create a new note with a title and content.",
)
def create_note(payload: NoteCreate, db: Session = Depends(get_db)):
    """Create a new note."""
    note = Note(title=payload.title, content=payload.content)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


# PUBLIC_INTERFACE
@app.put(
    "/notes/{note_id}",
    response_model=NoteRead,
    tags=["notes"],
    summary="Update note",
    description="Update an existing note's title and/or content.",
)
def update_note(note_id: int, payload: NoteUpdate, db: Session = Depends(get_db)):
    """Update a note by ID."""
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    if payload.title is not None:
        note.title = payload.title
    if payload.content is not None:
        note.content = payload.content

    db.add(note)
    db.commit()
    db.refresh(note)
    return note


# PUBLIC_INTERFACE
@app.delete(
    "/notes/{note_id}",
    status_code=204,
    tags=["notes"],
    summary="Delete note",
    description="Delete a note by its unique identifier.",
)
def delete_note(note_id: int, db: Session = Depends(get_db)):
    """Delete a note by ID."""
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()
    return None
