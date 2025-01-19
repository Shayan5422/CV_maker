# main.py
import base64
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List
from reportlab.platypus import Image
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

# ReportLab and Pillow Imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from fastapi.responses import FileResponse
from PIL import Image, ImageDraw
import base64

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


def round_corners(image, radius=40):
    """
    تابعی برای گرد کردن گوشه‌های تصویر پروفایل. 
    اگر عکس نهایی گوشه‌گرد نمی‌خواهید، این تابع را حذف کنید.
    """
    circle = Image.new('L', (radius*2, radius*2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, radius*2, radius*2), fill=255)
    alpha = Image.new('L', image.size, 255)
    w, h = image.size

    alpha.paste(circle.crop((0,0,radius,radius)), (0, 0))
    alpha.paste(circle.crop((radius,0,radius*2,radius)), (w-radius, 0))
    alpha.paste(circle.crop((0,radius,radius,radius*2)), (0, h-radius))
    alpha.paste(circle.crop((radius,radius,radius*2,radius*2)), (w-radius, h-radius))
    image.putalpha(alpha)
    return image


@app.get("/resumes/{resume_id}/pdf")
async def download_resume_pdf(
    resume_id: int,
    background_tasks: BackgroundTasks,
    theme: str = Query(None),  # مثلاً ?theme=elegant-dark
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # ۱) رزومه را از DB می‌خوانیم:
    resume = db.query(models.Resume).filter(
        models.Resume.id == resume_id,
        models.Resume.user_id == current_user.id
    ).first()
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")

    # ۲) فایل PDF موقت
    timestamp = int(datetime.now().timestamp())
    filename = f"temp_resume_{resume_id}_{timestamp}.pdf"

    # ۳) داده‌های رزومه
    name = resume.full_name or ""
    job_title = resume.title or ""
    phone = resume.phone or ""
    email = resume.email or ""
    # address = resume.address or ""  # فرض می‌کنیم فیلد address داشته باشید
    summary_text = resume.summary or ""
    photo_data = resume.photo

    # بارگذاری تجربیات، تحصیلات، مهارت‌ها و...
    def safe_load_json(json_str):
        try: 
            return json.loads(json_str)
        except:
            return []
    experiences = safe_load_json(resume.experience) if resume.experience else []
    educations  = safe_load_json(resume.education)  if resume.education  else []
    skills_list = safe_load_json(resume.skills)     if resume.skills     else []
    projects    = safe_load_json(resume.projects)   if resume.projects   else []
    certifications = safe_load_json(resume.certifications) if resume.certifications else []

    # ۴) تشخیص تم
    selected_theme = theme or ""  # اگر خالی بود یعنی تم پیش‌فرض

    try:
        # ۵) ساخت سند PDF
        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            rightMargin=0, leftMargin=0,
            topMargin=0, bottomMargin=10
        )
        elements = []

        # ---------------------------------------------------
        # استایل‌های پیش‌فرض (روشن)
        # ---------------------------------------------------
        default_styles = getSampleStyleSheet()

        name_style_default = ParagraphStyle(
            'NameStyleDefault',
            parent=default_styles['Heading1'],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor('#333333'),
            spaceAfter=6
        )
        title_style_default = ParagraphStyle(
            'TitleStyleDefault',
            parent=default_styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#666666'),
            spaceAfter=10
        )
        contact_style_default = ParagraphStyle(
            'ContactStyleDefault',
            parent=default_styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#555555'),
            leading=12
        )
        section_heading_style_default = ParagraphStyle(
            'SectionHeadingDefault',
            parent=default_styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#222222'),
            spaceBefore=10,
            spaceAfter=4
        )
        body_style_default = ParagraphStyle(
            'BodyStyleDefault',
            parent=default_styles['Normal'],
            fontSize=10,
            leading=12,
            textColor=colors.HexColor('#333333')
        )
        info_style_default = ParagraphStyle(
            'InfoStyleDefault',
            parent=default_styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#777777')
        )

        # ---------------------------------------------------
        # استایل‌های تم تیره (elegant-dark)
        # ---------------------------------------------------
        dark_styles = getSampleStyleSheet()

        # در تصویر نمونه، هدر خیلی تیره (#333333)، و نوشته‌ها سفید
        name_style_dark = ParagraphStyle(
            'NameStyleDark',
            parent=dark_styles['Heading1'],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor('#FFFFFF'),
            spaceAfter=6
        )
        title_style_dark = ParagraphStyle(
            'TitleStyleDark',
            parent=dark_styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#DDDDDD'),
            spaceAfter=4
        )
        contact_style_dark = ParagraphStyle(
            'ContactStyleDark',
            parent=dark_styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#EEEEEE'),
            leading=12
        )
        section_heading_style_dark = ParagraphStyle(
            'SectionHeadingDark',
            parent=dark_styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#333333'),  # برای هدینگ روی پس‌زمینه روشن
            backColor=colors.HexColor('#F0F0F0'),
            spaceBefore=8,
            spaceAfter=6,
            leftIndent=4,
            rightIndent=4
        )
        body_style_dark = ParagraphStyle(
            'BodyStyleDark',
            parent=dark_styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#444444')
        )
        info_style_dark = ParagraphStyle(
            'InfoStyleDark',
            parent=dark_styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#555555')
        )

        # رنگ‌های خط‌کشی
        if selected_theme == "elegant-dark":
            name_style      = name_style_dark
            title_style     = title_style_dark
            contact_style   = contact_style_dark
            section_heading_style = section_heading_style_dark
            body_style      = body_style_dark
            info_style      = info_style_dark

            # رنگ خط‌های جداکننده
            line_color = colors.HexColor('#FFFFFF')
            vertical_line_color = colors.HexColor('#EEEEEE')
        else:
            # تم پیش‌فرض روشن
            name_style      = name_style_default
            title_style     = title_style_default
            contact_style   = contact_style_default
            section_heading_style = section_heading_style_default
            body_style      = body_style_default
            info_style      = info_style_default
            line_color      = colors.HexColor('#999999')
            vertical_line_color = colors.HexColor('#AAAAAA')

        # ---------------------------------------------------
        # (الف) ساخت هدر تیره شبیه تصویر
        # ---------------------------------------------------
        if selected_theme == "elegant-dark":
            try:
                # محتوای هدر: نام، عنوان، اطلاعات تماس
                header_content = []
                header_content.append(Paragraph(name.upper(), name_style))
                if job_title:
                    header_content.append(Paragraph(job_title, title_style))

                contact_info = []
                if phone:
                    contact_info.append(phone)
                if email:
                    contact_info.append(email)

                if contact_info:
                    contact_text = " | ".join(contact_info)
                    header_content.append(Paragraph(contact_text, contact_style))

                # داده‌های جدول را یک‌جا می‌سازیم (۱ ردیف × ۱ ستون)
                header_dark_data = [[header_content]]

                # حالا جدول را روی این data می‌سازیم
                header_dark = Table(header_dark_data, colWidths=[8*inch])
                header_dark.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#333333')),
                    ('LEFTPADDING', (0,0), (-1,-1), 20),
                    ('RIGHTPADDING', (0,0), (-1,-1), 20),
                    ('TOPPADDING', (0,0), (-1,-1), 16),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 16),
                ]))

                elements.append(header_dark)

            except Exception as e:
                print("Error creating dark header:", e)

        else:
            # اگر تم پیش‌فرض است، یک هدر ساده مثل قبل (مثلاً نام و شماره تماس در بالا)
            header_left = []
            header_left.append(Paragraph(name, name_style))
            header_left.append(Paragraph(job_title, title_style))

            header_right = []
            if phone:
                header_right.append(Paragraph(phone, contact_style))
            if email:
                header_right.append(Paragraph(email, contact_style))

            # ساخت جدول هدر
            header_table_data = [[header_left, header_right]]
            header_table = Table(header_table_data, colWidths=[3.5*inch, 3.5*inch])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 20),
                ('RIGHTPADDING', (0,0), (-1,-1), 20),
            ]))
            elements.append(header_table)

            # خط افقی زیر هدر
            line_data = [['']]
            line_table = Table(line_data, colWidths=[7*inch])
            line_table.setStyle(TableStyle([
                ('LINEBELOW', (0, 0), (-1, 0), 1, line_color),
            ]))
            elements.append(Spacer(1,5))
            elements.append(line_table)

        elements.append(Spacer(1, 12))

        # ---------------------------------------------------
        # (ب) ساخت محتوای اصلی: دو ستون (سمت چپ: پروفایل و مهارت‌ها، سمت راست: تجربه و تحصیلات و...)
        # ---------------------------------------------------

        left_column = []
        # اگر عکس داریم، نمایش دهیم
        if photo_data:
            try:
                if photo_data.startswith('data:image'):
                    # base64
                    header, encoded = photo_data.split(',', 1)
                    img_data = base64.b64decode(encoded)
                    pil_image = Image.open(io.BytesIO(img_data)).convert('RGBA')
                else:
                    # مسیر فایل
                    pil_image = Image.open(photo_data).convert('RGBA')

                pil_image = round_corners(pil_image, 40)
                buf = io.BytesIO()
                pil_image.save(buf, format='PNG')
                buf.seek(0)
                rl_img = RLImage(buf, width=1.3*inch, height=1.3*inch)
                left_column.append(rl_img)
                left_column.append(Spacer(1, 10))
            except Exception as e:
                print("Error loading photo:", e)

        # پروفایل
        if summary_text.strip():
            left_column.append(Paragraph("PROFIL", section_heading_style))
            left_column.append(Paragraph(summary_text, body_style))
            left_column.append(Spacer(1, 12))

        # مهارت‌ها
        if skills_list:
            left_column.append(Paragraph("COMPÉTENCES", section_heading_style))
            for s in skills_list:
                skill_line = s.get('skill', '')
                proficiency = s.get('proficiency')
                if proficiency:
                    skill_line += f" ({proficiency})"
                left_column.append(Paragraph("• " + skill_line, body_style))
            left_column.append(Spacer(1, 12))

        # ستون راست
        right_column = []

        # تجربیات
        if experiences:
            right_column.append(Paragraph("EXPÉRIENCES PROFESSIONNELLES", section_heading_style))
            for exp in experiences:
                position = exp.get('position', '')
                company = exp.get('company', '')
                start_date = exp.get('start_date', '')
                end_date = exp.get('end_date', '')
                desc = exp.get('description', '')

                right_column.append(Paragraph(f"<b>{position}</b> - {company}", body_style))
                date_info = f"{start_date} - {end_date}"
                right_column.append(Paragraph(date_info, info_style))
                if desc.strip():
                    right_column.append(Paragraph(desc, body_style))
                right_column.append(Spacer(1, 10))

        # تحصیلات
        if educations:
            right_column.append(Paragraph("ÉDUCATION", section_heading_style))
            for edu in educations:
                deg = edu.get('degree', '')
                inst = edu.get('institution', '')
                sd = edu.get('start_date', '')
                ed = edu.get('end_date', '')
                dsc = edu.get('description', '')

                right_column.append(Paragraph(f"<b>{deg}</b> - {inst}", body_style))
                date_info = f"{sd} - {ed}"
                right_column.append(Paragraph(date_info, info_style))
                if dsc.strip():
                    right_column.append(Paragraph(dsc, body_style))
                right_column.append(Spacer(1, 10))

        # پروژه‌ها
        if projects:
            right_column.append(Paragraph("PROJETS", section_heading_style))
            for proj in projects:
                proj_name = proj.get('name', '')
                description = proj.get('description', '')
                link = proj.get('link', '')

                right_column.append(Paragraph(f"<b>{proj_name}</b>", body_style))
                if link:
                    right_column.append(Paragraph(f"Link: <a href='{link}'>{link}</a>", body_style))
                if description.strip():
                    right_column.append(Paragraph(description, body_style))
                right_column.append(Spacer(1, 10))

        # گواهی‌نامه‌ها
        if certifications:
            right_column.append(Paragraph("CERTIFICATIONS", section_heading_style))
            for cert in certifications:
                title = cert.get('title', '')
                issuer = cert.get('issuer', '')
                cdate = cert.get('date', '')

                right_column.append(Paragraph(f"<b>{title}</b>", body_style))
                right_column.append(Paragraph(f"Issuer: {issuer}", body_style))
                right_column.append(Paragraph(f"Date: {cdate}", body_style))
                right_column.append(Spacer(1, 10))

        # جدول دو ستونی
        content_table_data = [[left_column, right_column]]
        content_table = Table(content_table_data, colWidths=[2.5*inch, 5*inch])
        content_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LINEBEFORE', (1,0), (1,-1), 1, vertical_line_color),
            ('LEFTPADDING', (0,0), (0,0), 12),
            ('RIGHTPADDING', (0,0), (0,0), 6),
            ('LEFTPADDING', (1,0), (1,0), 12),
            ('RIGHTPADDING', (1,0), (1,0), 6),
        ]))
        elements.append(content_table)

        # ۶) ساخت PDF
        doc.build(elements)

        # پاک‌سازی فایل موقت با BackgroundTasks
        def cleanup():
            if os.path.exists(filename):
                os.remove(filename)
        background_tasks.add_task(cleanup)

        # بازگشت فایل
        return FileResponse(
            path=filename,
            media_type='application/pdf',
            filename=f"{name.replace(' ', '_')}_{selected_theme or 'default'}_{datetime.now().strftime('%Y%m%d')}.pdf"
        )

    except Exception as e:
        if os.path.exists(filename):
            os.remove(filename)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating PDF: {str(e)}"
        )