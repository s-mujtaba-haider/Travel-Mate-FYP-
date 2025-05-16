from uuid import UUID
import traceback

from fastapi import APIRouter, status, Depends
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session

from controller import deps
from config import settings
from controller import RAGPipeline, RAGError, SearchError, ResponseGenerationError, DatabaseError
from models import User, ChatSession, Message
rag = RAGPipeline(
            csv_path="controller/final_df.csv",
            openai_api_key=settings.OPENAI_API_KEY,
            embeddings_dir="controller/embeddings")

chat_router = APIRouter(
    prefix='/chat',
    tags=['chat']

)

@chat_router.post('/query/{session_id}', status_code=status.HTTP_200_OK, operation_id='authorize_chat_query')
async def add_message(
    session_id: UUID,
    query: str= None,
    max_places: int = 5,
    db: Session = Depends(deps.get_session),
    user: User = Depends(deps.get_current_user)):
    """
    Chat with the assistant

    - **session_id**:UUID = id of the chat session
    - **query**: str = User query 
    - **header**:"Bearer _token_" = Authorization header with Bearer token as "Bearer <token>"

    - **response**:
    Returns the assistant response
    """

    try:
        # Update session activity
        chat_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not chat_session:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content='Session not found')
        chat_session.update_activity()

        # Create new message

        human_message = Message(
            session_id=session_id,
            role="human",
            content={"message": query}
            )
        db.add(human_message)
        db.flush()
        try:
            response = await rag.answer_query(query=query, session_id=session_id, n_places=max_places)
        except SearchError:
            return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content='Cant find any places')
        except RAGError:
            return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content='Failed to initialize System')
        except Exception as e:
            return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content='Some error occured on the server, Please check Account Quota')
        ai_message = Message(
            session_id=session_id,
            role="assistant",
            content={'message':response['message'], 'places':response['places']},
            applied_filters=response['applied_filters'],
            filter_action=response['filter_action']
            )
        db.add(ai_message)
        db.commit()
        db.refresh(ai_message)
        return ai_message
    
    except Exception as e:
        db.rollback()
        print(traceback.format_exc(1))
        raise JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content="Unexpected Error")
    
@chat_router.get('/history/{session_id}', status_code=status.HTTP_200_OK, operation_id='get_chat_history')
async def get_chat_history(session_id: UUID, db: Session = Depends(deps.get_session)):
    """Get complete chat history with filters for a session"""
    try:
        messages = db.query(Message).filter(Message.session_id == session_id).order_by(Message.timestamp).all()
        response = {
            "history": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp
                }
                for msg in messages
            ]
        }
        return response
    except Exception as e:
        print("Error", e)
        print(traceback.format_exc())
        raise JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content="Unexpected Error")