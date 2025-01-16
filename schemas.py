# schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional

# ----- User Schemas -----
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int

    class Config:
        from_attributes = True

# ----- Resume Schemas -----
class ResumeBase(BaseModel):
    title: str
    full_name: str
    email: EmailStr
    phone: str
    summary: str
    experience: str       # JSON string, representing an array of experience items
    education: str        # JSON string, representing an array of education items
    skills: str           # JSON string, representing an array of skills entries
    projects: str         # JSON string, representing an array of project items
    certifications: str   # JSON string, representing an array of certification items

class ResumeCreate(ResumeBase):
    pass

class Resume(ResumeBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
