from datetime import datetime
import json
from typing import Dict, List
from uuid import UUID
from sqlalchemy.orm import Session
from models import ChatSession, Message
from controller.deps import get_session
from langchain_core.messages import HumanMessage, AIMessage

class PlacesRAGDatabase:
    def __init__(self):
        self.db_manager: Session = get_session()

    async def get_or_create_session(self, user_id: UUID) -> ChatSession:
        """Get active session or create new one"""
        try:
            # Find active session
            session = await self.db_manager.query(ChatSession)\
                .filter(ChatSession.user_id == user_id, ChatSession.is_active == True)\
                .order_by(ChatSession.updated_at.desc())\
                .first()
            
            if not session:
                raise Exception("No active session found")
            
            return session
        except Exception as e:
            await self.db_manager.rollback()
            return None
            # raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    async def get_chat_history(self, session_id: UUID, limit: int = 10) -> List[Dict]:
        """Get recent chat history for a session"""
        try:
            messages = await self.db_manager.query(Message)\
                .filter(Message.session_id == session_id)\
                .order_by(Message.timestamp.desc())\
                .limit(limit)\
                .all()
            
            history = []
            for msg in messages:
                if msg.role == "human":
                    history.append(HumanMessage(content=msg.content["query"]))
                else:
                    history.append(AIMessage(content=json.dumps(msg.content)))
            
            return list(reversed(history))
        except Exception as e:
            await self.db_manager.rollback()
            return []
            # raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    # async def add_message(self, session_id: UUID, role: str, content: Dict):
    #     """Add a new message to the chat history"""
    #     async with self.db_manager.get_session() as db:
    #         message = Message(
    #             session_id=session_id,
    #             role=role,
    #             content=content
    #         )
    #         db.add(message)
            
    #         # Update session last_activity
    #         session = await db.get(ChatSession, session_id)
    #         session.last_activity = datetime.utcnow()
            
    #         await db.commit()
    #         return message