"""
SQLAlchemy models for FSense database.

Contains image caching model for storing generated flower images.
"""

from sqlalchemy import Column, String, DateTime, Integer, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


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
