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
    summary = Column(Text)
    experience = Column(Text)   # Will store JSON string of experience items
    education = Column(Text)    # Will store JSON string of education items
    skills = Column(Text)       # Will store JSON string of skills items
    projects = Column(Text)     # Will store JSON string of project items
    certifications = Column(Text)  # Will store JSON string of certification items
    photo = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="resumes")
