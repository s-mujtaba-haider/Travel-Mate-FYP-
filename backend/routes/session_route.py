
import traceback
from fastapi import APIRouter, status, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session

from controller import deps
from models import User, ChatSession


session_router = APIRouter(
    prefix='/session',
    tags=['session']

)


@session_router.get('/', status_code=status.HTTP_200_OK)
async def home():
    return {
        'status_code': status.HTTP_200_OK,
        'detail': 'Welcome to the Session API'
    }


@session_router.post('/create', status_code=status.HTTP_201_CREATED, operation_id='authorize_session_create')
async def create_session(db: Session=Depends(deps.get_session), user: User=Depends(deps.get_current_user)):
    try:
        session = ChatSession(
            # session_id=session_id,
            user_id=user.user_id
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return {
            'status_code': status.HTTP_201_CREATED,
            'detail': 'Session Created',
            'data': {
                'session_id': session.id,
                'user_id': session.user_id,
                'created_at': session.created_at,
                'session_name': session.session_name
            }
        }
    except Exception as e:
        print("Error", e)
        print(traceback.format_exc())
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unexpected Error")

@session_router.get('/get', status_code=status.HTTP_200_OK, operation_id='authorize_session_get')
async def get_session(db: Session=Depends(deps.get_session), user: User=Depends(deps.get_current_user)):
    try:
        session = db.query(ChatSession).filter(ChatSession.user_id == user.user_id).order_by(ChatSession.updated_at.desc()).first()
        if not session:
            return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Session not found')
        return {
            'status_code': status.HTTP_200_OK,
            'detail': 'Session Found',
            'data': {
                'session_id': session.id,
                'user_id': session.user_id,
                'created_at': session.created_at,
                'session_name': session.session_name
                }
        }
    except Exception as e:
        print("Error", e)
        print(traceback.format_exc())
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unexpected Error")

@session_router.delete('/delete/{session_id}', status_code=status.HTTP_200_OK, operation_id='authorize_session_del')
async def delete_session(session_id: str,db: Session=Depends(deps.get_session), user: User=Depends(deps.get_current_user)):
    try:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Session not found')
        db.query(ChatSession).filter(ChatSession.id == session_id).delete()
        db.commit()
        return {
            'status_code': status.HTTP_200_OK,
            'detail': 'Session Deleted'
        }
    except Exception as e:
        print("Error", e)
        print(traceback.format_exc())
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unexpected Error")

@session_router.get('/all', status_code=status.HTTP_200_OK, operation_id='authorize_session_getall')
async def get_all_session(db: Session=Depends(deps.get_session), user: User=Depends(deps.get_current_user)):
    try:
        sessions = db.query(ChatSession).filter(ChatSession.user_id == user.user_id).all()
        if not sessions:
            return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Session not found')
        return {
            'status_code': status.HTTP_200_OK,
            'detail': 'Session Found',
            'data': {
                'sessions': sessions}
        }
    except Exception as e:
        print("Error", e)
        print(traceback.format_exc(1))
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unexpected Error")

# update session name

@session_router.put('/update/{session_id}', status_code=status.HTTP_200_OK, operation_id='authorize_session_update')
async def update_session_name(session_id: str, session_name: str = None, db: Session=Depends(deps.get_session), user: User=Depends(deps.get_current_user)):
    try:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Session not found')
        session.session_name = session_name
        db.commit()
        db.refresh(session)
        return {
            'status_code': status.HTTP_200_OK,
            'detail': 'Session Updated',
            'data': {
                'session_id': session.id,
                'user_id': session.user_id,
                'created_at': session.created_at,
                'session_name': session.session_name
            }
        }
    except Exception as e:
        print("Error", e)
        print(traceback.format_exc(1))
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unexpected Error")