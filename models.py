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
    experience = Column(Text)   # If you want to store structured data, consider using JSON
    education = Column(Text)    # Same as above
    skills = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="resumes")
