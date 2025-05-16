from sqlalchemy import Column, String, ForeignKey, DateTime, Index, text, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, JSONB

from controller.database import Base


class Message(Base):
    """Message model with per-message filter tracking"""
    __tablename__ = 'messages'

    message_id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey('chat_sessions.id', ondelete='CASCADE', onupdate="CASCADE", name="FK_messages_session"), nullable=False)
    role = Column(String(20), nullable=False)  # human/assistant
    timestamp = Column(DateTime(timezone=True), server_default=func.current_timestamp(), index=True)
    content = Column(JSONB, nullable=False)  # Stores message content
    applied_filters = Column(JSONB, default={})  # Filters used for this message
    filter_action = Column(String(10), default="keep")  # keep/update/clear

    session_to_message = relationship("ChatSession", back_populates="session_to_messages")

    # Indices for better query performance
    __table_args__ = (
        Index('idx_messages_session_timestamp', 'session_id', 'timestamp'),
        Index('idx_messages_content_gin', content, postgresql_using='gin'),
        Index('idx_messages_filters_gin', applied_filters, postgresql_using='gin'),
    )
