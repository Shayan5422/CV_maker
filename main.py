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

    # Theme definitions
    themes = {
        "modern-blue": {
            "colors": {
                "primary": "#2563eb",
                "secondary": "#1d4ed8",
                "background": "#f8fafc",
                "text": "#1e293b",
                "accent": "#60a5fa",
                "sidebar": "#1e3a8a"
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
                "accent": "#94a3b8",
                "sidebar": "#0f172a"
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
                "accent": "#a78bfa",
                "sidebar": "#5b21b6"
            },
            "fonts": {
                "title": "Helvetica-Bold",
                "heading": "Helvetica-Bold",
                "normal": "Helvetica"
            }
        }
    }

    selected_theme = themes.get(theme, themes["modern-blue"])

    # تعریف نمادها با استفاده از کاراکترهای سازگار با ReportLab
    icons = {
        'phone': '☏',  # یا '✆'
        'email': '✉',
        'location': '⌖',
        'education': '◆',
        'experience': '▶',
        'skills': '★',
        'languages': '◈',
        'projects': '▣',
        'interests': '❖',
        'certifications': '❋',
        'awards': '✯'
    }

    timestamp = int(datetime.now().timestamp())
    filename = f"temp_resume_{resume_id}_{timestamp}.pdf"
    
    try:
        # Document setup with zero margins
        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            rightMargin=0,
            leftMargin=0,
            topMargin=-6,
            bottomMargin=0
        )

        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=22,
            spaceAfter=16,
            alignment=1,
            textColor=colors.HexColor(selected_theme["colors"]["primary"]),
            fontName=selected_theme["fonts"]["title"]
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=10,
            spaceAfter=6,
            textColor=colors.HexColor(selected_theme["colors"]["secondary"]),
            fontName=selected_theme["fonts"]["heading"]
        )
        
        sidebar_heading_style = ParagraphStyle(
            'SidebarHeading',
            parent=styles['Heading3'],
            fontSize=12,
            spaceBefore=8,
            spaceAfter=4,
            textColor=colors.white,
            fontName=selected_theme["fonts"]["heading"]
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            textColor=colors.HexColor(selected_theme["colors"]["text"]),
            fontName=selected_theme["fonts"]["normal"]
        )
        
        sidebar_text_style = ParagraphStyle(
            'SidebarText',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.white,
            fontName=selected_theme["fonts"]["normal"],
            spaceBefore=2,
            spaceAfter=4
        )
        
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor(selected_theme["colors"]["accent"]),
            fontName=selected_theme["fonts"]["normal"]
        )

        # Build content for main column and sidebar
        main_elements = []
        sidebar_elements = []

        # Header with Title (in main column)
        main_elements.append(Paragraph(resume.title, title_style))
        main_elements.append(Spacer(1, 16))

        # Contact Information (in sidebar)
        sidebar_elements.append(Paragraph(f"{icons['phone']} Contact", sidebar_heading_style))
        sidebar_elements.append(Paragraph(f"<b>{resume.full_name}</b>", sidebar_text_style))
        sidebar_elements.append(Paragraph(f"{icons['email']} {resume.email}", sidebar_text_style))
        if resume.phone:
            sidebar_elements.append(Paragraph(f"{icons['phone']} {resume.phone}", sidebar_text_style))
        sidebar_elements.append(Spacer(1, 12))

        # Skills (in sidebar)
        if resume.skills:
            sidebar_elements.append(Paragraph(f"{icons['skills']} Skills", sidebar_heading_style))
            try:
                skills_list = json.loads(resume.skills)
                for skill in skills_list:
                    sidebar_elements.append(
                        Paragraph(
                            f"<b>{skill['skill']}</b> - {skill['proficiency']}", 
                            sidebar_text_style
                        )
                    )
                sidebar_elements.append(Spacer(1, 12))
            except json.JSONDecodeError:
                print(f"Error parsing skills JSON for resume {resume_id}")

        # Languages (if available)
        if hasattr(resume, 'languages') and resume.languages:
            try:
                languages_list = json.loads(resume.languages)
                if languages_list:
                    sidebar_elements.append(Paragraph(f"{icons['languages']} Languages", sidebar_heading_style))
                    for lang in languages_list:
                        sidebar_elements.append(
                            Paragraph(f"{lang['language']} - {lang['level']}", sidebar_text_style)
                        )
                    sidebar_elements.append(Spacer(1, 12))
            except json.JSONDecodeError:
                pass

        # Certifications (in sidebar)
        if resume.certifications:
            sidebar_elements.append(Paragraph(f"{icons['certifications']} Certifications", sidebar_heading_style))
            try:
                certifications_list = json.loads(resume.certifications)
                for cert in certifications_list:
                    sidebar_elements.append(
                        Paragraph(f"<b>{cert['title']}</b>", sidebar_text_style)
                    )
                    sidebar_elements.append(
                        Paragraph(f"{cert['issuer']} ({cert['date']})", sidebar_text_style)
                    )
                sidebar_elements.append(Spacer(1, 12))
            except json.JSONDecodeError:
                print(f"Error parsing certifications JSON for resume {resume_id}")

        # Professional Summary (in main column)
        if resume.summary and resume.summary.strip():
            main_elements.append(Paragraph(f"Professional Summary", heading_style))
            main_elements.append(Paragraph(resume.summary, normal_style))
            main_elements.append(Spacer(1, 16))

        # Experience Section (in main column)
        if resume.experience:
            main_elements.append(Paragraph(f"{icons['experience']} Professional Experience", heading_style))
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
                    main_elements.append(Spacer(1, 8))
            except json.JSONDecodeError:
                print(f"Error parsing experience JSON for resume {resume_id}")

        # Education Section (in main column)
        if resume.education:
            main_elements.append(Paragraph(f"{icons['education']} Education", heading_style))
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
                    main_elements.append(Spacer(1, 8))
            except json.JSONDecodeError:
                print(f"Error parsing education JSON for resume {resume_id}")

        # Projects Section (in main column)
        if resume.projects:
            main_elements.append(Paragraph(f"{icons['projects']} Projects", heading_style))
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
                    main_elements.append(Spacer(1, 8))
            except json.JSONDecodeError:
                print(f"Error parsing projects JSON for resume {resume_id}")

        # ساخت یک جدول اصلی برای کل صفحه
        page_width, page_height = A4
        sidebar_width = page_width * 0.28
        main_width = page_width * 0.72

        # اضافه کردن سلول‌های خالی به سایدبار برای پر کردن کل ارتفاع
        min_rows = 115  # تعداد حداقل سطرها برای پوشش کل صفحه
        while len(sidebar_elements) < min_rows:
            sidebar_elements.append(Spacer(1, 12))

        # تبدیل المان‌ها به محتوای جدول
        sidebar_content = [[element] for element in sidebar_elements]
        main_content = [[element] for element in main_elements]

        # اطمینان از برابری تعداد سطرها
        max_rows = max(len(sidebar_content), len(main_content), min_rows)
        while len(sidebar_content) < max_rows:
            sidebar_content.append([''])
        while len(main_content) < max_rows:
            main_content.append([''])

        # ترکیب محتوا در جدول نهایی
        table_data = []
        
        # ابتدا یک ردیف برای کل سایدبار
        sidebar_data = []
        for item in sidebar_elements:
            if isinstance(item, Spacer):
                sidebar_data.append(Paragraph("<br/>", sidebar_text_style))
            else:
                sidebar_data.append(item)
        
        # یک ردیف با دو ستون: سایدبار و محتوای اصلی
        main_data = []
        for item in main_elements:
            if isinstance(item, Spacer):
                main_data.append(Paragraph("<br/>", normal_style))
            else:
                main_data.append(item)
                
        table_data.append([
            sidebar_data,  # ستون سایدبار
            main_data     # ستون محتوای اصلی
        ])

        # ایجاد جدول با استایل
        table = Table(table_data, colWidths=[sidebar_width, main_width])
        table_style = TableStyle([
            # Background color for sidebar
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor(selected_theme["colors"]["sidebar"])),
            # Text color for sidebar
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            # Vertical alignment
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            # Minimum padding
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            # Prevent table from breaking across pages
            ('NOSPLIT', (0, 0), (-1, -1)),
            # Make sure content uses full width
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ])
        table.setStyle(table_style)

        # ساخت PDF
        elements = [table]
        doc.build(elements)

        # تابع پاکسازی
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
        if os.path.exists(filename):
            os.unlink(filename)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating PDF: {str(e)}"
        )