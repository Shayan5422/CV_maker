# schemas.py
from pydantic import BaseModel, EmailStr, constr, field_validator
from typing import Optional, List
from datetime import date
import json

# ----- User Schemas -----
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int

    class Config:
        from_attributes = True

# ----- Component Schemas -----
class ExperienceItem(BaseModel):
    company: str
    position: str
    start_date: str
    end_date: str
    description: str

class EducationItem(BaseModel):
    institution: str
    degree: str
    start_date: str
    end_date: str
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

# ----- Resume Schemas -----
class ResumeBase(BaseModel):
    title: str
    full_name: str
    email: EmailStr
    phone: str  # Validate phone format
    summary: str
    experience: str
    education: str
    skills: str
    projects: str
    certifications: str
    photo: Optional[str] = None

    # Validators to ensure JSON strings are valid
    @field_validator('experience')
    def validate_experience(cls, v):
        try:
            items = json.loads(v)
            [ExperienceItem(**item) for item in items]
            return v
        except Exception as e:
            raise ValueError('Invalid experience format')

    @field_validator('education')
    def validate_education(cls, v):
        try:
            items = json.loads(v)
            [EducationItem(**item) for item in items]
            return v
        except Exception as e:
            raise ValueError('Invalid education format')

    @field_validator('skills')
    def validate_skills(cls, v):
        try:
            items = json.loads(v)
            [SkillItem(**item) for item in items]
            return v
        except Exception as e:
            raise ValueError('Invalid skills format')

    @field_validator('projects')
    def validate_projects(cls, v):
        try:
            items = json.loads(v)
            [ProjectItem(**item) for item in items]
            return v
        except Exception as e:
            raise ValueError('Invalid projects format')

    @field_validator('certifications')
    def validate_certifications(cls, v):
        try:
            items = json.loads(v)
            [CertificationItem(**item) for item in items]
            return v
        except Exception as e:
            raise ValueError('Invalid certifications format')

class ResumeCreate(ResumeBase):
    pass

class Resume(ResumeBase):
    id: int
    user_id: int
    created_at: Optional[date] = None
    updated_at: Optional[date] = None

    class Config:
        from_attributes = True

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