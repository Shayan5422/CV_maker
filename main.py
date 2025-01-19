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

    # چهارگوشهٔ تصویر را گرد می‌کند
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
    db: Session = Depends(get_db),               # وابستگی پایگاه داده
    current_user: models.User = Depends(get_current_user),  # وابستگی احراز هویت
):
    # ۱) رزومه را از دیتابیس بخوانید
    resume = db.query(models.Resume).filter(
        models.Resume.id == resume_id,
        models.Resume.user_id == current_user.id
    ).first()
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")

    # ۲) نام فایل موقت
    timestamp = int(datetime.now().timestamp())
    filename = f"temp_resume_{resume_id}_{timestamp}.pdf"

    # ۳) داده‌های رزومه را استخراج کنیم
    #    اینجا فرض می‌کنیم فیلدهایی شبیه name, title, phone, email, summary, skills, experience... دارید:
    name = resume.full_name or "نام شما"
    job_title = resume.title or "عنوان شغل/موقعیت"
    phone = resume.phone or ""
    email = resume.email or ""
    summary_text = resume.summary or ""
    photo_data = resume.photo  # ممکن است base64 یا URL یا مسیر فایل باشد

    # تجربه‌های کاری یا تحصیلات یا مهارت‌ها ممکن است در قالب JSON باشند:
    experiences = []
    educations = []
    skills_list = []
    projects = []
    certifications = []
    import json
    if resume.projects:
        try:
            projects = json.loads(resume.projects)
        except:
            pass

    if resume.certifications:
        try:
            certifications = json.loads(resume.certifications)
        except:
            pass
        # اگر در دیتابیس JSON ذخیره شده، آن را تبدیل به دیکشنری/لیست کنیم
        
    if resume.experience:
        try:
            experiences = json.loads(resume.experience)
        except:
            pass
    if resume.education:
        try:
            educations = json.loads(resume.education)
        except:
            pass
    if resume.skills:
        try:
            skills_list = json.loads(resume.skills)  # [{"skill":"Python","proficiency":"Expert"}, ...]
        except:
            pass

    # ۴) ساخت استایل‌ها با reportlab
    styles = getSampleStyleSheet()

    # استایل بزرگ برای نام
    name_style = ParagraphStyle(
        'NameStyle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#333333'),
        spaceAfter=6
    )
    # استایل برای عنوان شغلی
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#666666'),
        spaceAfter=10
    )
    # استایل برای اطلاعات تماس
    contact_style = ParagraphStyle(
        'ContactStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#555555'),
        leading=12
    )
    # استایل بخش‌های داخلی
    section_heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#222222'),
        spaceBefore=10,
        spaceAfter=4
    )
    # متن عادی
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=12,
        textColor=colors.HexColor('#333333')
    )
    # متن راهنما (تاریخ، لینک، ...)
    info_style = ParagraphStyle(
        'InfoStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#777777')
    )

    try:
        # ۵) ایجاد سند PDF
        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            rightMargin=0, leftMargin=0,
            topMargin=20, bottomMargin=10
        )

        elements = []

        # -------------------------
        # (الف) هدر بالا (شامل نام، عنوان شغلی، اطلاعات تماس)
        # -------------------------
        header_left = []  # ستون چپ: نام و عنوان
        header_left.append(Paragraph(name, name_style))
        header_left.append(Paragraph(job_title, title_style))

        header_right = []  # ستون راست: تلفن، ایمیل، ...
        if phone:
            header_right.append(Paragraph(phone, contact_style))
        if email:
            header_right.append(Paragraph(email, contact_style))

        header_table_data = [
            [header_left, header_right]
        ]
        header_table = Table(header_table_data, colWidths=[3*inch, 3*inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))

        # خط افقی زیر هدر
        line_data = [['']]
        line_table = Table(line_data, colWidths=[6*inch])
        line_table.setStyle(TableStyle([
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#999999')),
        ]))

        # -------------------------
        # (ب) ساخت دو ستون اصلی در بدنه
        # ستون چپ (پروفایل، عکس، خلاصه، مهارت‌ها...) 
        # ستون راست (تجربیات، تحصیلات...)
        # -------------------------
        left_column = []

        # -- عکس پروفایل:
        if photo_data:
            try:
                pil_image = None
                if photo_data.startswith('data:image'):
                    # اگر base64 بود
                    header, encoded = photo_data.split(',', 1)
                    img_data = base64.b64decode(encoded)
                    pil_image = Image.open(io.BytesIO(img_data)).convert('RGBA')
                else:
                    # در غیر این صورت فرض می‌کنیم مسیر فایل است
                    pil_image = Image.open(photo_data).convert('RGBA')

                # گوشه‌گرد
                pil_image = round_corners(pil_image, 50)
                buf = io.BytesIO()
                pil_image.save(buf, format='PNG')
                buf.seek(0)
                rl_img = RLImage(buf, width=1.2*inch, height=1.2*inch)

                left_column.append(rl_img)
                left_column.append(Spacer(1, 10))
            except Exception as e:
                print("Error loading photo:", e)

        # -- بخش خلاصه (Profile)
        if summary_text.strip():
            left_column.append(Paragraph("<b>+ Profile</b>", section_heading_style))
            left_column.append(Paragraph(summary_text, body_style))
            left_column.append(Spacer(1, 10))

        # -- مهارت‌ها (چون در دیتابیس JSON داشتیم، احتمالاً [{"skill": "...", "proficiency": "..."}]):
        if skills_list:
            left_column.append(Paragraph("<b>+ Skills</b>", section_heading_style))
            for s in skills_list:
                skill_line = s['skill']
                # اگر میزان تسلط هم داشت
                if 'proficiency' in s:
                    skill_line += f" ({s['proficiency']})"
                left_column.append(Paragraph("• " + skill_line, body_style))
            left_column.append(Spacer(1, 10))

        # می‌توانید زبان‌ها، علاقه‌مندی‌ها یا سایر موارد را هم در همین ستون اضافه کنید

        # ستون راست
        right_column = []
        
        # -- تجربیات
        if experiences:
            right_column.append(Paragraph("<b>+ Professional experience</b>", section_heading_style))
            for exp in experiences:
                # exp = {"position": "...", "company": "...", "start_date": "...", "end_date": "...", "description": "..."}
                position = exp.get('position', '') 
                company = exp.get('company', '')
                start_date = exp.get('start_date', '')
                end_date = exp.get('end_date', '')
                desc = exp.get('description', '')

                # سطر تیتر
                right_column.append(Paragraph(f"<b>{position}</b> - {company}", body_style))
                # تاریخ
                date_info = f"{start_date} - {end_date}"
                right_column.append(Paragraph(date_info, info_style))
                # توضیحات
                if desc.strip():
                    right_column.append(Paragraph(desc, body_style))
                right_column.append(Spacer(1, 8))

        # -- تحصیلات
        if educations:
            right_column.append(Paragraph("<b>+ Education</b>", section_heading_style))
            for edu in educations:
                # edu = {"degree": "...", "institution": "...", "start_date": "...", "end_date": "...", "description": "..."}
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
                right_column.append(Spacer(1, 8))

                
        if projects:
            right_column.append(Paragraph("<b>+ Projects</b>", section_heading_style))
            for proj in projects:
                name = proj.get('name', '')
                description = proj.get('description', '')
                link = proj.get('link', '')
                
                right_column.append(Paragraph(f"<b>{name}</b>", body_style))
                if link:
                    right_column.append(Paragraph(f"Link: <a href='{link}'>{link}</a>", body_style))
                if description.strip():
                    right_column.append(Paragraph(description, body_style))
                right_column.append(Spacer(1, 8))

        # -- گواهی‌نامه‌ها
        if certifications:
            right_column.append(Paragraph("<b>+ Certifications</b>", section_heading_style))
            for cert in certifications:
                title = cert.get('title', '')
                issuer = cert.get('issuer', '')
                date = cert.get('date', '')
                
                right_column.append(Paragraph(f"<b>{title}</b>", body_style))
                right_column.append(Paragraph(f"Issuer: {issuer}", body_style))
                right_column.append(Paragraph(f"Date: {date}", body_style))
                right_column.append(Spacer(1, 8))


        # ساخت جدول دو ستونی
        body_table_data = [
            [left_column, right_column]
        ]
        body_table = Table(body_table_data, colWidths=[2.5*inch, 5*inch])
        body_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            # خط عمودی بین دو ستون
            ('LINEBEFORE', (1,0), (1,-1), 1, colors.HexColor('#aaaaaa')),
            # پدینگ
            ('LEFTPADDING', (0,0), (0,0), 6),
            ('RIGHTPADDING', (0,0), (0,0), 10),
            ('LEFTPADDING', (1,0), (1,0), 10),
            ('RIGHTPADDING', (1,0), (1,0), 6),
        ]))

        # مونتاژ نهایی
        elements.append(header_table)
        elements.append(Spacer(1, 6))
        elements.append(line_table)
        elements.append(Spacer(1, 12))
        elements.append(body_table)

        # ساخت PDF
        doc.build(elements)

        # پس از ساخت، با استفاده از BackgroundTasks فایل موقت را پاک می‌کنیم
        def cleanup():
            try:
                if os.path.exists(filename):
                    os.remove(filename)
            except:
                pass

        background_tasks.add_task(cleanup)

        # برگرداندن فایل به صورت دانلود
        return FileResponse(
            path=filename,
            media_type='application/pdf',
            filename=f"{name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
        )

    except Exception as e:
        # در صورت خطا، فایل را پاک کنید
        if os.path.exists(filename):
            os.remove(filename)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating PDF: {str(e)}"
        )
