# main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List
import jwt
import models
import schemas
from database import SessionLocal, engine, Base
from passlib.context import CryptContext

# Create the database tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS configuration (adjust allowed origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT Configuration
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Dependency: Database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.email == username).first()
    if user is None:
        raise credentials_exception
    return user

# ----- User Endpoints -----
@app.post("/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# ----- Resume Endpoints -----
@app.post("/resumes/", response_model=schemas.Resume)
def create_resume(
    resume: schemas.ResumeCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_resume = models.Resume(**resume.dict(), user_id=current_user.id)
    db.add(db_resume)
    db.commit()
    db.refresh(db_resume)
    return db_resume

@app.get("/resumes/", response_model=List[schemas.Resume])
def get_resumes(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(models.Resume).filter(models.Resume.user_id == current_user.id).all()

@app.get("/resumes/{resume_id}", response_model=schemas.Resume)
def get_resume(
    resume_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    resume = db.query(models.Resume).filter(
        models.Resume.id == resume_id, models.Resume.user_id == current_user.id
    ).first()
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume

@app.put("/resumes/{resume_id}", response_model=schemas.Resume)
def update_resume(
    resume_id: int,
    resume: schemas.ResumeCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_resume = db.query(models.Resume).filter(
        models.Resume.id == resume_id, models.Resume.user_id == current_user.id
    ).first()
    if db_resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    for key, value in resume.dict().items():
        setattr(db_resume, key, value)
    db.commit()
    db.refresh(db_resume)
    return db_resume

@app.delete("/resumes/{resume_id}")
def delete_resume(
    resume_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    resume = db.query(models.Resume).filter(
        models.Resume.id == resume_id, models.Resume.user_id == current_user.id
    ).first()
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    db.delete(resume)
    db.commit()
    return {"message": "Resume deleted"}
