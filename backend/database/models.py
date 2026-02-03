"""
SQLAlchemy models for FSense database.

Contains:
- ImageCache: Generated flower images
- Session: User sessions for conversation continuity
- ConversationHistory: Chat history within sessions
"""

from sqlalchemy import Column, String, DateTime, Integer, Text, Index, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


def generate_uuid() -> str:
    """Generate a new UUID string."""
    return str(uuid.uuid4())


class ImageCache(Base):
    """
    Caches generated flower images with composite key: flower_name + emotion_context

    Status flow: pending → generating → completed/failed
    """
    __tablename__ = "image_cache"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Cache Key Components
    flower_name = Column(String(255), nullable=False)
    emotion_context = Column(String(500), nullable=False)

    # Composite cache key hash (for fast lookups)
    cache_key = Column(String(64), unique=True, nullable=False, index=True)

    # Generation Status
    # Values: "pending", "generating", "completed", "failed"
    status = Column(String(20), nullable=False, default="pending")

    # Image Data
    image_path = Column(String(500), nullable=True)  # relative path: "static/images/{hash}.png"
    image_url = Column(String(500), nullable=True)   # full URL: "/static/images/{hash}.png"

    # Error Tracking
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Metadata
    generation_time_ms = Column(Integer, nullable=True)  # time taken to generate
    prompt_used = Column(Text, nullable=True)  # AI prompt for debugging

    # Indexes
    __table_args__ = (
        Index('idx_status', 'status'),
        Index('idx_flower_emotion', 'flower_name', 'emotion_context'),
        Index('idx_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<ImageCache(cache_key='{self.cache_key}', status='{self.status}')>"


class Session(Base):
    """
    User session for maintaining conversation continuity.

    Sessions allow:
    - Tracking conversation history
    - Persisting user preferences
    - Rate limiting per session
    """
    __tablename__ = "sessions"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Session identifier (sent to iOS)
    session_id = Column(String(36), unique=True, nullable=False, default=generate_uuid, index=True)

    # Client identification
    device_id = Column(String(255), nullable=True)  # iOS device identifier
    client_ip = Column(String(45), nullable=True)   # IPv4 or IPv6

    # Session metadata
    region = Column(String(10), default="US")
    user_agent = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_active_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # Optional session expiration

    # Relationships
    messages = relationship("ConversationHistory", back_populates="session", cascade="all, delete-orphan")

    # Statistics
    message_count = Column(Integer, default=0)

    __table_args__ = (
        Index('idx_session_last_active', 'last_active_at'),
        Index('idx_session_device', 'device_id'),
    )

    def __repr__(self):
        return f"<Session(session_id='{self.session_id}', messages={self.message_count})>"


class ConversationHistory(Base):
    """
    Stores conversation history within a session.

    Each entry represents a user message and the system's response.
    """
    __tablename__ = "conversation_history"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Key to Session
    session_id = Column(String(36), ForeignKey("sessions.session_id", ondelete="CASCADE"), nullable=False, index=True)

    # Request data
    request_id = Column(String(36), nullable=False, index=True)  # Pipeline request ID
    user_message = Column(Text, nullable=False)
    region = Column(String(10), default="US")

    # Response data
    flower_name = Column(String(255), nullable=True)  # Selected flower
    flower_id = Column(String(255), nullable=True)
    response_payload = Column(JSON, nullable=True)    # Full FlowerCardPayload (for history display)

    # Status
    success = Column(Integer, default=1)  # 1 = success, 0 = failed
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationship
    session = relationship("Session", back_populates="messages")

    __table_args__ = (
        Index('idx_history_created', 'created_at'),
    )

    def __repr__(self):
        return f"<ConversationHistory(request_id='{self.request_id}', flower='{self.flower_name}')>"
