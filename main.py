# main.py
from fastapi import FastAPI, Depends, HTTPException, Query, status
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
    theme: str = Query(None, description="Theme ID for the PDF"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    resume = db.query(models.Resume).filter(
        models.Resume.id == resume_id, 
        models.Resume.user_id == current_user.id
    ).first()
    
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")

    # تعریف تم‌ها
    themes = {
        "modern-blue": {
            "colors": {
                "primary": "#2563eb",
                "secondary": "#1d4ed8",
                "background": "#f8fafc",
                "text": "#1e293b",
                "accent": "#60a5fa"
            },
            "fonts": {
                "title": "Helvetica-Bold",
                "heading": "Helvetica-Bold",
                "normal": "Helvetica"
            }
        },
        "elegant-dark": {
            "colors": {
                "primary": "#334155",
                "secondary": "#1e293b",
                "background": "#f1f5f9",
                "text": "#0f172a",
                "accent": "#94a3b8"
            },
            "fonts": {
                "title": "Times-Bold",
                "heading": "Times-Bold",
                "normal": "Times-Roman"
            }
        },
        "creative-purple": {
            "colors": {
                "primary": "#7c3aed",
                "secondary": "#6d28d9",
                "background": "#faf5ff",
                "text": "#2e1065",
                "accent": "#a78bfa"
            },
            "fonts": {
                "title": "Helvetica-Bold",
                "heading": "Helvetica-Bold",
                "normal": "Helvetica"
            }
        },
        "nature-green": {
            "colors": {
                "primary": "#059669",
                "secondary": "#047857",
                "background": "#f0fdf4",
                "text": "#064e3b",
                "accent": "#6ee7b7"
            },
            "fonts": {
                "title": "Helvetica-Bold",
                "heading": "Helvetica-Bold",
                "normal": "Helvetica"
            }
        },
        "coral-sunset": {
            "colors": {
                "primary": "#f43f5e",
                "secondary": "#e11d48",
                "background": "#fff1f2",
                "text": "#881337",
                "accent": "#fda4af"
            },
            "fonts": {
                "title": "Helvetica-Bold",
                "heading": "Helvetica-Bold",
                "normal": "Helvetica"
            }
        }
    }

    # انتخاب تم پیش‌فرض اگر تمی انتخاب نشده باشد
    selected_theme = themes.get(theme, themes["modern-blue"])

    timestamp = int(datetime.now().timestamp())
    filename = f"temp_resume_{resume_id}_{timestamp}.pdf"
    
    try:
        # تنظیمات سند
        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )

        # تعریف استایل‌ها با استفاده از تم انتخاب شده
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1,
            textColor=colors.HexColor(selected_theme["colors"]["primary"]),
            fontName=selected_theme["fonts"]["title"]
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceBefore=15,
            spaceAfter=10,
            textColor=colors.HexColor(selected_theme["colors"]["secondary"]),
            fontName=selected_theme["fonts"]["heading"]
        )
        
        sidebar_heading_style = ParagraphStyle(
            'SidebarHeading',
            parent=styles['Heading3'],
            fontSize=14,
            spaceBefore=10,
            spaceAfter=5,
            textColor=colors.white,
            fontName=selected_theme["fonts"]["heading"]
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=8,
            textColor=colors.HexColor(selected_theme["colors"]["text"]),
            fontName=selected_theme["fonts"]["normal"]
        )
        
        sidebar_text_style = ParagraphStyle(
            'SidebarText',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.white,
            fontName=selected_theme["fonts"]["normal"]
        )
        
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor(selected_theme["colors"]["accent"]),
            fontName=selected_theme["fonts"]["normal"]
        )

        # ساخت محتوا برای ستون اصلی و سایدبار
        main_elements = []
        sidebar_elements = []

        # سرصفحه با عنوان (در ستون اصلی)
        main_elements.append(Paragraph(resume.title, title_style))
        main_elements.append(Spacer(1, 20))

        # اطلاعات تماس (در سایدبار)
        sidebar_elements.append(Paragraph("Contact Information", sidebar_heading_style))
        sidebar_elements.append(Paragraph(f"<b>{resume.full_name}</b>", sidebar_text_style))
        sidebar_elements.append(Paragraph(f"Email: {resume.email}", sidebar_text_style))
        sidebar_elements.append(Paragraph(f"Phone: {resume.phone}", sidebar_text_style))
        sidebar_elements.append(Spacer(1, 20))

        # مهارت‌ها (در سایدبار)
        if resume.skills:
            sidebar_elements.append(Paragraph("Skills", sidebar_heading_style))
            try:
                skills_list = json.loads(resume.skills)
                for skill in skills_list:
                    sidebar_elements.append(
                        Paragraph(
                            f"<b>{skill['skill']}</b> - {skill['proficiency']}", 
                            sidebar_text_style
                        )
                    )
                sidebar_elements.append(Spacer(1, 15))
            except json.JSONDecodeError:
                print(f"Error parsing skills JSON for resume {resume_id}")

        # گواهینامه‌ها (در سایدبار)
        if resume.certifications:
            sidebar_elements.append(Paragraph("Certifications", sidebar_heading_style))
            try:
                certifications_list = json.loads(resume.certifications)
                for cert in certifications_list:
                    sidebar_elements.append(
                        Paragraph(f"<b>{cert['title']}</b>", sidebar_text_style)
                    )
                    sidebar_elements.append(
                        Paragraph(f"{cert['issuer']} ({cert['date']})", sidebar_text_style)
                    )
                sidebar_elements.append(Spacer(1, 15))
            except json.JSONDecodeError:
                print(f"Error parsing certifications JSON for resume {resume_id}")

        # خلاصه حرفه‌ای (در ستون اصلی)
        if resume.summary and resume.summary.strip():
            main_elements.append(Paragraph("Professional Summary", heading_style))
            main_elements.append(Paragraph(resume.summary, normal_style))
            main_elements.append(Spacer(1, 20))

        # بخش تجربیات (در ستون اصلی)
        if resume.experience:
            main_elements.append(Paragraph("Professional Experience", heading_style))
            try:
                experience_list = json.loads(resume.experience)
                for exp in experience_list:
                    main_elements.append(
                        Paragraph(
                            f"<b>{exp['position']}</b> at <b>{exp['company']}</b>", 
                            normal_style
                        )
                    )
                    main_elements.append(
                        Paragraph(
                            f"{exp['start_date']} - {exp['end_date']}", 
                            info_style
                        )
                    )
                    main_elements.append(Paragraph(exp['description'], normal_style))
                    main_elements.append(Spacer(1, 10))
            except json.JSONDecodeError:
                print(f"Error parsing experience JSON for resume {resume_id}")

        # بخش تحصیلات (در ستون اصلی)
        if resume.education:
            main_elements.append(Paragraph("Education", heading_style))
            try:
                education_list = json.loads(resume.education)
                for edu in education_list:
                    main_elements.append(
                        Paragraph(
                            f"<b>{edu['degree']}</b> - {edu['institution']}", 
                            normal_style
                        )
                    )
                    main_elements.append(
                        Paragraph(
                            f"{edu['start_date']} - {edu['end_date']}", 
                            info_style
                        )
                    )
                    if edu.get('description'):
                        main_elements.append(Paragraph(edu['description'], normal_style))
                    main_elements.append(Spacer(1, 10))
            except json.JSONDecodeError:
                print(f"Error parsing education JSON for resume {resume_id}")

        # بخش پروژه‌ها (در ستون اصلی)
        if resume.projects:
            main_elements.append(Paragraph("Projects", heading_style))
            try:
                projects_list = json.loads(resume.projects)
                for project in projects_list:
                    main_elements.append(
                        Paragraph(f"<b>{project['name']}</b>", normal_style)
                    )
                    main_elements.append(Paragraph(project['description'], normal_style))
                    if project.get('link'):
                        main_elements.append(
                            Paragraph(f"Link: {project['link']}", info_style)
                        )
                    main_elements.append(Spacer(1, 10))
            except json.JSONDecodeError:
                print(f"Error parsing projects JSON for resume {resume_id}")

        # ایجاد لایه‌بندی دو ستونی
        total_width = doc.width
        sidebar_width = total_width * 0.3
        main_width = total_width * 0.7

        # ساخت محتوا برای هر دو ستون
        sidebar_content = []
        for element in sidebar_elements:
            if isinstance(element, Spacer):
                sidebar_content.append([''])
            else:
                sidebar_content.append([element])

        main_content = []
        for element in main_elements:
            if isinstance(element, Spacer):
                main_content.append([''])
            else:
                main_content.append([element])

        # اطمینان از برابری تعداد سطرها در هر دو ستون
        max_rows = max(len(sidebar_content), len(main_content))
        while len(sidebar_content) < max_rows:
            sidebar_content.append([''])
        while len(main_content) < max_rows:
            main_content.append([''])

        # ترکیب ستون‌ها در جدول نهایی
        table_data = []
        for i in range(max_rows):
            table_data.append(sidebar_content[i] + main_content[i])

        # ایجاد جدول با استایل مناسب
        table = Table(table_data, colWidths=[sidebar_width, main_width])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor(selected_theme["colors"]["primary"])),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))

        # ساخت PDF
        doc.build([table])

        # تعریف تابع پاکسازی
        def cleanup():
            try:
                if os.path.exists(filename):
                    os.unlink(filename)
            except Exception as e:
                print(f"Error cleaning up file {filename}: {e}")

        # زمانبندی پاکسازی
        background_tasks.add_task(cleanup)

        # برگرداندن فایل PDF
        return FileResponse(
            path=filename,
            media_type='application/pdf',
            filename=f"{resume.title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
        )

    except Exception as e:
        # پاکسازی فایل در صورت بروز خطا
        if os.path.exists(filename):
            os.unlink(filename)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating PDF: {str(e)}"
        )