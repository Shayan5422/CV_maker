# schemas.py
from pydantic import BaseModel
from typing import Optional

class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    
    class Config:
        orm_mode = True

class ResumeBase(BaseModel):
    title: str
    full_name: str
    email: str
    phone: str
    summary: str
    experience: str
    education: str
    skills: str

class ResumeCreate(ResumeBase):
    pass

class Resume(ResumeBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True