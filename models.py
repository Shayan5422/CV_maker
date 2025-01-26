# models.py
from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    resumes = relationship("Resume", back_populates="user")

class Resume(Base):
    __tablename__ = "resumes"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    full_name = Column(String)
    email = Column(String)
    phone = Column(String)
    city = Column(String)
    language = Column(String)
    summary = Column(Text)
    experience = Column(Text)   # Will store JSON string of experience items
    education = Column(Text)    # Will store JSON string of education items
    skills = Column(Text)       # Will store JSON string of skills items
    projects = Column(Text)     # Will store JSON string of project items
    certifications = Column(Text)  # Will store JSON string of certification items
    languages = Column(Text)     # Will store JSON string of language items
    photo = Column(String, nullable=True)
    # Section Titles
    experience_title = Column(String, default="EXPERIENCE")
    education_title = Column(String, default="EDUCATION")
    skills_title = Column(String, default="SKILLS")
    projects_title = Column(String, default="PROJECTS")
    certifications_title = Column(String, default="CERTIFICATIONS")
    languages_title = Column(String, default="LANGUAGES")
    summary_title = Column(String, default="PROFILE")
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="resumes")
