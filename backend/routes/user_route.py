import os
import traceback
from datetime import datetime, date
from uuid import uuid4

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, status, Depends, Request, Response, File, UploadFile, Form
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException
from fastapi.responses import FileResponse
from fastapi_another_jwt_auth import AuthJWT
# from google.auth.transport import requests
# from google.oauth2 import id_token
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash, check_password_hash

from controller import deps
from models.user import User
from schema import UserLogin, UserSignUp, UserForget, UserUpdate

auth_router = APIRouter(
    prefix='/user',
    tags=['user']

)

@auth_router.get('/', status_code=status.HTTP_200_OK)
async def home():
    return {
        'status_code': status.HTTP_200_OK,
        'detail': 'Welcome to the User API'
    }

@auth_router.post('/signup', status_code=status.HTTP_201_CREATED)
async def signup(user: UserSignUp, res: Response, session: Session = Depends(deps.get_session),
                 Authorize: AuthJWT = Depends()):
    """
        ## Create a user
        This requires the following
        ```
            -email: str
            -password: str
            -dob: str
            -first_name: str
            -last_name: str
        ```

    """
    response = {}
    try:
        db_email = session.query(User).filter(User.email == user.email).first()
        if db_email is not None:
            res.status_code = status.HTTP_400_BAD_REQUEST
            return HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                 detail="User with the email already exists")

        # u_id = str(uuid4())
        new_user = User(
            # user_id=u_id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            dob=user.dob,
            password=generate_password_hash(user.password) if user.password else None,
            is_active=True,
        )

        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        # access_token = Authorize.create_access_token(subject=new_user.user_id, expires_time=False)
        response = {
            'status_code': status.HTTP_201_CREATED,
            'detail': 'User created successfully',
            'data': {
                'email': new_user.email,
                'first_name': new_user.first_name,
                'last_name': new_user.last_name,
                'dob': new_user.dob,
                'user_id': new_user.user_id
            }
        }
        return jsonable_encoder(response)
    except Exception as e:
        print("Error", e)
        print(traceback.format_exc())
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unexpected Error")


@auth_router.post('/login', status_code=status.HTTP_201_CREATED)
async def login(user: UserLogin, req: Request, response: Response, session: Session = Depends(deps.get_session),
                Authorize: AuthJWT = Depends()):
    """
        ## Login a user
        This requires
            ```
                username:str
                password:str
            ```
        and returns a token pair `access`
    """
    try:
        db_user = session.query(User).filter(User.email == user.email).first()
        if db_user and check_password_hash(db_user.password, user.password):
            access_token = Authorize.create_access_token(subject=str(db_user.user_id), expires_time=False)
            res = {
                'status_code': status.HTTP_201_CREATED,
                'detail': 'Login Successfully',
                'data': {
                    'email': db_user.email,
                    'token': access_token,
                    'first_name': db_user.first_name,
                    'last_name': db_user.last_name,
                    'dob': db_user.dob,
                    'user_id': db_user.user_id,
                    'is_active': db_user.is_active,
                }
            }
            return res
        response.status_code = status.HTTP_400_BAD_REQUEST
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                             detail="Invalid Username Or Password")
    except Exception as e:
        print("Error", e)
        print(traceback.format_exc())
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unexpected Error")


@auth_router.post("/forget", status_code=status.HTTP_201_CREATED)
async def forget(info: UserForget, response: Response, session: Session = Depends(deps.get_session)):
    try:
        user = session.query(User).filter(User.email == info.email).first()
        if user:
            user.password = generate_password_hash(info.new_password)
            session.commit()
            return {
                'status_code': status.HTTP_201_CREATED,
                'detail': 'Password updated successfully'
            }

        response.status_code = status.HTTP_400_BAD_REQUEST
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                             detail="User Not found with this email")
    except Exception as e:
        print("Error", e)
        print(traceback.format_exc())
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unexpected Error")


# update user

@auth_router.put('/update', status_code=status.HTTP_201_CREATED, operation_id="authorize_user_update")
async def update_user( data: UserUpdate, response: Response, session: Session = Depends(deps.get_session), user: User = Depends(deps.get_current_user)):
    try:
        db_user = session.query(User).filter(User.user_id == user.user_id).first()
        if not db_user:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                               detail="User Not found with this user_id")
        
        # Convert the Pydantic model to dictionary
        update_data = data.model_dump()
        
        # Only update fields that are not None
        for field, value in update_data.items():
            if value is not None:
                setattr(db_user, field, value)
        
        session.commit()
        session.refresh(db_user)
        return {
            'status_code': status.HTTP_200_OK,
            'detail': 'User updated successfully',
            'data': {
                'email': db_user.email,
                'first_name': db_user.first_name,
                'last_name': db_user.last_name,
                'dob': db_user.dob,
                'user_id': db_user.user_id
            }
        }
        
    except Exception as e:
        print("Error", e)
        print(traceback.format_exc())
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unexpected Error")
    

@auth_router.get('/guest', status_code=status.HTTP_201_CREATED)
async def guest_login(session: Session = Depends(deps.get_session),
                Authorize: AuthJWT = Depends()):
    """
        ## Guest user
       
        and returns a token pair `access`
    """
    try:

        GUEST_USERNAME_PREFIX = "guest_"
        GUEST_EMAIL_DOMAIN = "@guest.temporary"

        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        guest_username = f"{GUEST_USERNAME_PREFIX}{timestamp}"
        guest_email = f"{guest_username}{GUEST_EMAIL_DOMAIN}"

        new_user = User(
            # user_id=u_id,
            email=guest_email,
            first_name=guest_username,
            last_name=None,
            dob=None,
            password=None,
            is_active=True,
        )

        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        access_token = Authorize.create_access_token(subject=str(new_user.user_id), expires_time=False)
        res = {
            'status_code': status.HTTP_201_CREATED,
            'detail': 'Login Successfully',
            'data': {
                'email': new_user.email,
                'token': access_token,
                'first_name': new_user.first_name,
                'last_name': new_user.last_name,
                'dob': new_user.dob,
                'user_id': new_user.user_id,
                'is_active': new_user.is_active,
            }
        }
        return res
    except Exception as e:
        print("Error", e)
        print(traceback.format_exc())
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unexpected Error")
