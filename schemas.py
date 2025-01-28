# schemas.py
from typing import Optional, List
from pydantic import BaseModel, EmailStr, constr, validator
from datetime import date
import json

# ----- User Schemas -----
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

    @validator('password')
    def password_validation(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class User(UserBase):
    id: int
    is_active: bool = True

    class Config:
        orm_mode = True

# ----- Component Schemas -----
class ExperienceItem(BaseModel):
    company: str
    position: str
    start_date: str
    end_date: Optional[str] = None
    is_current: bool = False
    description: str

class EducationItem(BaseModel):
    institution: str
    degree: str
    start_date: str
    end_date: Optional[str] = None
    is_current: bool = False
    description: Optional[str] = None

class SkillItem(BaseModel):
    skill: str
    proficiency: str

class ProjectItem(BaseModel):
    name: str
    description: str
    link: Optional[str] = None

class CertificationItem(BaseModel):
    title: str
    issuer: str
    date: str

class LanguageItem(BaseModel):
    language: str
    proficiency: str

# ----- Resume Schemas -----
class ResumeBase(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    city: Optional[str] = None
    summary: Optional[str] = None
    experience: Optional[str] = None
    education: Optional[str] = None
    skills: Optional[str] = None
    projects: Optional[str] = None
    certifications: Optional[str] = None
    languages: Optional[str] = None
    photo: Optional[str] = None

class ResumeCreate(ResumeBase):
    pass

class Resume(ResumeBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True

    # Helper methods for PDF generation
    def get_experience_list(self) -> List[ExperienceItem]:
        return [ExperienceItem(**item) for item in json.loads(self.experience)]

    def get_education_list(self) -> List[EducationItem]:
        return [EducationItem(**item) for item in json.loads(self.education)]

    def get_skills_list(self) -> List[SkillItem]:
        return [SkillItem(**item) for item in json.loads(self.skills)]

    def get_projects_list(self) -> List[ProjectItem]:
        return [ProjectItem(**item) for item in json.loads(self.projects)]

    def get_certifications_list(self) -> List[CertificationItem]:
        return [CertificationItem(**item) for item in json.loads(self.certifications)]

    def get_languages_list(self) -> List[LanguageItem]:
        return [LanguageItem(**item) for item in json.loads(self.languages)]