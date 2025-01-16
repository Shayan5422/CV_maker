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
# Install required package first: pip install reportlab
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from fastapi.responses import FileResponse
import json
import io
import os
from fastapi import BackgroundTasks
from fastapi.responses import FileResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
import io
import os
import json
from datetime import datetime

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


@app.get("/resumes/{resume_id}/pdf")
async def download_resume_pdf(
    resume_id: int,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get resume data
    resume = db.query(models.Resume).filter(
        models.Resume.id == resume_id, 
        models.Resume.user_id == current_user.id
    ).first()
    
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Create unique filename using timestamp
    timestamp = int(datetime.now().timestamp())
    filename = f"temp_resume_{resume_id}_{timestamp}.pdf"
    
    try:
        # Document settings
        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )

        # Define styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1,  # Center alignment
            textColor=colors.HexColor('#2c3e50')
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceBefore=15,
            spaceAfter=10,
            textColor=colors.HexColor('#2980b9')
        )
        
        subheading_style = ParagraphStyle(
            'CustomSubHeading',
            parent=styles['Heading3'],
            fontSize=13,
            spaceBefore=10,
            spaceAfter=5,
            textColor=colors.HexColor('#34495e')
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=8,
            textColor=colors.HexColor('#2c3e50')
        )
        
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#7f8c8d')
        )

        # Build PDF content
        elements = []

        # Header with Title
        elements.append(Paragraph(resume.title, title_style))
        elements.append(Spacer(1, 20))

        # Contact Information
        contact_data = [
            [Paragraph(f"<b>{resume.full_name}</b>", normal_style)],
            [Paragraph(f"Email: {resume.email}", info_style)],
            [Paragraph(f"Phone: {resume.phone}", info_style)]
        ]
        
        contact_table = Table(contact_data, colWidths=[doc.width])
        contact_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(contact_table)
        elements.append(Spacer(1, 20))

        # Professional Summary
        if resume.summary and resume.summary.strip():
            elements.append(Paragraph("Professional Summary", heading_style))
            elements.append(Paragraph(resume.summary, normal_style))
            elements.append(Spacer(1, 20))

        # Experience Section
        if resume.experience:
            elements.append(Paragraph("Professional Experience", heading_style))
            try:
                experience_list = json.loads(resume.experience)
                for exp in experience_list:
                    elements.append(Paragraph(
                        f"<b>{exp['position']}</b> at <b>{exp['company']}</b>", 
                        subheading_style
                    ))
                    elements.append(Paragraph(
                        f"{exp['start_date']} - {exp['end_date']}", 
                        info_style
                    ))
                    elements.append(Paragraph(exp['description'], normal_style))
                    elements.append(Spacer(1, 10))
            except json.JSONDecodeError:
                print(f"Error parsing experience JSON for resume {resume_id}")

        # Education Section
        if resume.education:
            elements.append(Paragraph("Education", heading_style))
            try:
                education_list = json.loads(resume.education)
                for edu in education_list:
                    elements.append(Paragraph(
                        f"<b>{edu['degree']}</b> - {edu['institution']}", 
                        subheading_style
                    ))
                    elements.append(Paragraph(
                        f"{edu['start_date']} - {edu['end_date']}", 
                        info_style
                    ))
                    if edu.get('description'):
                        elements.append(Paragraph(edu['description'], normal_style))
                    elements.append(Spacer(1, 10))
            except json.JSONDecodeError:
                print(f"Error parsing education JSON for resume {resume_id}")

        # Skills Section
        if resume.skills:
            elements.append(Paragraph("Skills", heading_style))
            try:
                skills_list = json.loads(resume.skills)
                skills_data = []
                for skill in skills_list:
                    skills_data.append(
                        Paragraph(
                            f"<b>{skill['skill']}</b> - {skill['proficiency']}", 
                            normal_style
                        )
                    )
                elements.extend(skills_data)
                elements.append(Spacer(1, 15))
            except json.JSONDecodeError:
                print(f"Error parsing skills JSON for resume {resume_id}")

        # Projects Section
        if resume.projects:
            elements.append(Paragraph("Projects", heading_style))
            try:
                projects_list = json.loads(resume.projects)
                for project in projects_list:
                    elements.append(Paragraph(f"<b>{project['name']}</b>", subheading_style))
                    elements.append(Paragraph(project['description'], normal_style))
                    if project.get('link'):
                        elements.append(Paragraph(
                            f"Link: {project['link']}", 
                            info_style
                        ))
                    elements.append(Spacer(1, 10))
            except json.JSONDecodeError:
                print(f"Error parsing projects JSON for resume {resume_id}")

        # Certifications Section
        if resume.certifications:
            elements.append(Paragraph("Certifications", heading_style))
            try:
                certifications_list = json.loads(resume.certifications)
                for cert in certifications_list:
                    elements.append(Paragraph(
                        f"<b>{cert['title']}</b> - {cert['issuer']}", 
                        subheading_style
                    ))
                    elements.append(Paragraph(f"Date: {cert['date']}", info_style))
                    elements.append(Spacer(1, 10))
            except json.JSONDecodeError:
                print(f"Error parsing certifications JSON for resume {resume_id}")

        # Footer
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(
            f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            info_style
        ))

        # Build PDF
        doc.build(elements)

        # Define cleanup function
        def cleanup():
            try:
                if os.path.exists(filename):
                    os.unlink(filename)
            except Exception as e:
                print(f"Error cleaning up file {filename}: {e}")

        # Schedule cleanup
        background_tasks.add_task(cleanup)

        # Return PDF file
        return FileResponse(
            path=filename,
            media_type='application/pdf',
            filename=f"{resume.title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
        )

    except Exception as e:
        # Clean up file if there was an error
        if os.path.exists(filename):
            os.unlink(filename)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating PDF: {str(e)}"
        )