"""
Database repository layer.

Provides CRUD operations for:
- ImageCache
- Session
- ConversationHistory
"""

from typing import Optional, List
from sqlalchemy.orm import Session as DbSession
from datetime import datetime, timedelta
import logging
import uuid

from backend.database.models import ImageCache, Session, ConversationHistory

logger = logging.getLogger(__name__)


class ImageCacheRepository:
    """Data access layer for image cache"""

    def __init__(self, db: DbSession):
        self.db = db

    def get_by_cache_key(self, cache_key: str) -> Optional[ImageCache]:
        """Get cached image by cache key"""
        return self.db.query(ImageCache).filter(
            ImageCache.cache_key == cache_key
        ).first()

    def create(
        self,
        flower_name: str,
        emotion_context: str,
        cache_key: str,
    ) -> ImageCache:
        """Create new cache entry"""
        entry = ImageCache(
            flower_name=flower_name,
            emotion_context=emotion_context,
            cache_key=cache_key,
            status="pending",
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        logger.info(f"Created cache entry: {cache_key}")
        return entry

    def update_status(
        self,
        cache_key: str,
        status: str,
        image_path: Optional[str] = None,
        image_url: Optional[str] = None,
        error_message: Optional[str] = None,
        generation_time_ms: Optional[int] = None,
        prompt_used: Optional[str] = None,
    ) -> Optional[ImageCache]:
        """Update cache entry status"""
        entry = self.get_by_cache_key(cache_key)
        if not entry:
            logger.warning(f"Cache entry not found: {cache_key}")
            return None

        entry.status = status
        entry.updated_at = datetime.utcnow()

        if image_path:
            entry.image_path = image_path
        if image_url:
            entry.image_url = image_url
        if error_message:
            entry.error_message = error_message
        if generation_time_ms:
            entry.generation_time_ms = generation_time_ms
        if prompt_used:
            entry.prompt_used = prompt_used

        if status == "completed":
            entry.completed_at = datetime.utcnow()
        elif status == "failed":
            entry.retry_count += 1

        self.db.commit()
        self.db.refresh(entry)
        logger.info(f"Updated cache entry {cache_key}: status={status}")
        return entry

    def get_stale_pending_entries(self, timeout_minutes: int = 10) -> list[ImageCache]:
        """Get entries stuck in 'pending' or 'generating' status (for cleanup)"""
        threshold = datetime.utcnow() - timedelta(minutes=timeout_minutes)
        return self.db.query(ImageCache).filter(
            ImageCache.status.in_(["pending", "generating"]),
            ImageCache.updated_at < threshold,
        ).all()


# ═══════════════════════════════════════════════════════════════════════════════
# SESSION REPOSITORY
# ═══════════════════════════════════════════════════════════════════════════════

class SessionRepository:
    """Data access layer for user sessions"""

    def __init__(self, db: DbSession):
        self.db = db

    def get_by_session_id(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        return self.db.query(Session).filter(
            Session.session_id == session_id
        ).first()

    def create(
        self,
        device_id: Optional[str] = None,
        client_ip: Optional[str] = None,
        region: str = "US",
        user_agent: Optional[str] = None,
    ) -> Session:
        """Create a new session"""
        session = Session(
            session_id=str(uuid.uuid4()),
            device_id=device_id,
            client_ip=client_ip,
            region=region,
            user_agent=user_agent,
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        logger.info(f"Created session: {session.session_id}")
        return session

    def update_last_active(self, session_id: str) -> Optional[Session]:
        """Update session's last active timestamp"""
        session = self.get_by_session_id(session_id)
        if not session:
            return None

        session.last_active_at = datetime.utcnow()
        self.db.commit()
        return session

    def increment_message_count(self, session_id: str) -> Optional[Session]:
        """Increment session's message count"""
        session = self.get_by_session_id(session_id)
        if not session:
            return None

        session.message_count += 1
        session.last_active_at = datetime.utcnow()
        self.db.commit()
        return session

    def get_expired_sessions(self, inactive_hours: int = 24) -> List[Session]:
        """Get sessions that have been inactive for specified hours"""
        threshold = datetime.utcnow() - timedelta(hours=inactive_hours)
        return self.db.query(Session).filter(
            Session.last_active_at < threshold
        ).all()

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and its history"""
        session = self.get_by_session_id(session_id)
        if not session:
            return False

        self.db.delete(session)
        self.db.commit()
        logger.info(f"Deleted session: {session_id}")
        return True


# ═══════════════════════════════════════════════════════════════════════════════
# CONVERSATION HISTORY REPOSITORY
# ═══════════════════════════════════════════════════════════════════════════════

class ConversationHistoryRepository:
    """Data access layer for conversation history"""

    def __init__(self, db: DbSession):
        self.db = db

    def add_message(
        self,
        session_id: str,
        request_id: str,
        user_message: str,
        region: str = "US",
        flower_name: Optional[str] = None,
        flower_id: Optional[str] = None,
        response_payload: Optional[dict] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> ConversationHistory:
        """Add a new message to conversation history"""
        entry = ConversationHistory(
            session_id=session_id,
            request_id=request_id,
            user_message=user_message,
            region=region,
            flower_name=flower_name,
            flower_id=flower_id,
            response_payload=response_payload,
            success=1 if success else 0,
            error_message=error_message,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        logger.debug(f"Added conversation entry: {request_id}")
        return entry

    def get_session_history(
        self,
        session_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ConversationHistory]:
        """Get conversation history for a session (most recent first)"""
        return self.db.query(ConversationHistory).filter(
            ConversationHistory.session_id == session_id
        ).order_by(
            ConversationHistory.created_at.desc()
        ).offset(offset).limit(limit).all()

    def get_session_history_for_context(
        self,
        session_id: str,
        limit: int = 5,
    ) -> List[dict]:
        """
        Get recent conversation history formatted for AI context.

        Returns list of {role, content} dicts for conversation context.
        """
        entries = self.db.query(ConversationHistory).filter(
            ConversationHistory.session_id == session_id,
            ConversationHistory.success == 1,
        ).order_by(
            ConversationHistory.created_at.desc()
        ).limit(limit).all()

        # Reverse to get chronological order
        entries = list(reversed(entries))

        context = []
        for entry in entries:
            context.append({
                "role": "user",
                "content": entry.user_message,
            })
            if entry.flower_name:
                context.append({
                    "role": "assistant",
                    "content": f"Recommended: {entry.flower_name}",
                })

        return context

    def count_session_messages(self, session_id: str) -> int:
        """Count total messages in a session"""
        return self.db.query(ConversationHistory).filter(
            ConversationHistory.session_id == session_id
        ).count()
