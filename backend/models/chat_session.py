from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from models import Base
from datetime import datetime

class ChatSession(Base):
    __tablename__ = 'chat_sessions'

    id = Column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False, server_default=func.uuid_generate_v4())
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', name='fk_user_id_session', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    session_to_user = relationship('User', back_populates='user_to_session')
    # token = Column(Text)
    session_name = Column(String(100), nullable=True)
    is_active = Column(Integer, default=1)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), server_onupdate=func.current_timestamp(), index=True)
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), server_onupdate=func.current_timestamp(), index=True)
    session_to_messages = relationship("Message", back_populates="session_to_message")


    def update_activity(self):
        self.updated_at = datetime.now()

    def update_title(self,name:str):
        self.session_name = name
