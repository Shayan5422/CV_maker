# schemas.py
from pydantic import BaseModel, EmailStr
from typing import List, Optional

# --- User Schemas ---
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int

    class Config:
        from_attributes = True   # Pydantic v2; in v1, use orm_mode = True

# --- Resume Schemas ---
class ResumeBase(BaseModel):
    title: str
    full_name: str
    email: EmailStr
    phone: str
    summary: str
    experience: str   # Expecting a string. If you plan to store structured data, change this type.
    education: str
    skills: str

class ResumeCreate(ResumeBase):
    pass

class Resume(ResumeBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
