from controller.database import Base
from sqlalchemy import Column, String, Integer, func, TIMESTAMP, BOOLEAN, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID



class User(Base):
    __tablename__ = 'users'
    user_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4(), index=True)
    email = Column(String(100))
    password = Column(String(250))
    first_name = Column(String(50))
    last_name = Column(String(50))
    dob = Column(Date)
    is_active = Column(BOOLEAN, default=1)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), server_onupdate=func.current_timestamp())
    user_to_session = relationship('ChatSession', back_populates='session_to_user')
