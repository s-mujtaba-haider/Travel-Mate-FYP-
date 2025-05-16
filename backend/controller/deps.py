from typing import List, Generator
import json
from fastapi import Depends, HTTPException, status
from fastapi_another_jwt_auth import AuthJWT
from sqlalchemy.orm import Session

from controller.database import Session as db_session
from models.user import User


def get_session() -> Generator:
    db = db_session()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(session: Session = Depends(get_session), Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
        current_user = Authorize.get_jwt_subject()
        user = session.query(User).filter(User.user_id == current_user).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Token"
        )

# class RoleChecker:
#     def __init__(self, allowed_roles: List):
#         self.allowed_roles = allowed_roles
#
#     def __call__(self, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
#         # roles = session.query(User).filter(User.user_id == user).all()
#         if user.roles.role_name.lower() not in self.allowed_roles:
#             raise HTTPException(status_code=403, detail="Operation not permitted")
#         return user
# raise HTTPException(status_code=403, detail="Operation not permitted")
# # if user.role not in self.allowed_roles:
# #     logger.debug(f"User with role {user.role} not in {self.allowed_roles}")
# #
