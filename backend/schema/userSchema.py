from pydantic import BaseModel, EmailStr
import datetime


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserSignUp(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str | None = None
    dob: datetime.date | None = None

class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    dob: datetime.date | None = None



class UserForget(BaseModel):
    email: EmailStr
    new_password: str

