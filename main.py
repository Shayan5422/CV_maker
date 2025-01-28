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
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
from fastapi.responses import FileResponse
import json
import io
import os
from fastapi import BackgroundTasks
from fastapi.responses import FileResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
import io
import os
import json
from datetime import datetime
from reportlab.platypus import KeepTogether, FrameBreak
from reportlab.platypus import Frame, PageTemplate, NextPageTemplate

# ReportLab and Pillow Imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from fastapi.responses import FileResponse
from PIL import Image, ImageDraw
import base64

from reportlab.pdfgen import canvas
import math

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


def draw_vertical_line(canvas, doc, line_color=colors.HexColor('#AAAAAA')):
    """Draw a vertical line for the two-column layout"""
    height = doc.pagesize[1]  # Get page height
    x = 2.7 * inch  # Position for vertical line (adjust based on your column width)
    
    # Draw line from top to bottom of page
    canvas.setStrokeColor(line_color)
    canvas.setLineWidth(0.5)
    canvas.line(x, 30, x, height - 30)

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        """Add page info to each page (page x of y)"""
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        # Only draw page numbers if there are multiple pages
        if page_count > 1:
            self.setFont("Helvetica", 8)
            self.drawRightString(
                A4[0] - 20,
                20,
                f"Page {self._pageNumber} of {page_count}"
            )

@app.get("/resumes/{resume_id}/pdf")
async def download_resume_pdf(
    resume_id: int,
    background_tasks: BackgroundTasks,
    theme: str = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        resume = db.query(models.Resume).filter(
            models.Resume.id == resume_id,
            models.Resume.user_id == current_user.id
        ).first()
        if resume is None:
            raise HTTPException(status_code=404, detail="Resume not found")

        timestamp = int(datetime.now().timestamp())
        filename = f"temp_resume_{resume_id}_{timestamp}.pdf"

        name = resume.full_name or ""
        job_title = resume.title or ""
        phone = resume.phone or ""
        email = resume.email or ""
        city = resume.city or ""
        summary_text = resume.summary or ""
        photo_data = resume.photo

        # Define theme outside the try_build_pdf function
        selected_theme = theme or ""
        print(f"Selected theme: {selected_theme}")  # Debug log

        def safe_load_json(json_str):
            if not json_str:
                return []
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                return []
            except Exception as e:
                print(f"Unexpected error loading JSON: {e}")
                return []

        try:
            experiences = safe_load_json(resume.experience)
            educations = safe_load_json(resume.education)
            skills_list = safe_load_json(resume.skills)
            projects = safe_load_json(resume.projects)
            certifications = safe_load_json(resume.certifications)
            languages = safe_load_json(resume.languages)
        except Exception as e:
            print(f"Error loading resume data: {e}")
            experiences = []
            educations = []
            skills_list = []
            projects = []
            certifications = []
            languages = []

        def try_build_pdf(height_multiplier=1.0):
            try:
                # Create custom page size
                custom_page_size = (A4[0], A4[1] * height_multiplier)
                
                # Create the PDF document with custom settings
                doc = SimpleDocTemplate(
                    filename,
                    pagesize=custom_page_size,
                    rightMargin=10*mm,
                    leftMargin=10*mm,
                    topMargin=0*mm,
                    bottomMargin=0*mm,
                    allowSplitting=0,  # Disable page splitting
                    displayDocTitle=True,
                    pageCompression=0,  # Disable page compression
                    showBoundary=0,  # Hide page boundaries
                )

                # Create a basic template for single page
                frame = Frame(
                    doc.leftMargin, 
                    doc.bottomMargin,
                    doc.width,
                    doc.height,
                    leftPadding=0,
                    rightPadding=0,
                    topPadding=0,
                    bottomPadding=0,
                    showBoundary=0,
                    id='normal'
                )

                # Create a template that uses the frame
                template = PageTemplate(
                    id='OneCol',
                    frames=[frame],
                    onPage=lambda canvas, doc: None
                )
                doc.addPageTemplates([template])

                # Get the default styles from ReportLab
                styles = getSampleStyleSheet()

                # Define common colors
                line_color = colors.HexColor('#999999')
                vertical_line_color = colors.HexColor('#AAAAAA')
                light_blue = colors.HexColor('#E3F2FD')
                primary_blue = colors.HexColor('#1E88E5')
                dark_blue = colors.HexColor('#1565C0')
                
                # Nature Green theme colors
                nature_green = colors.HexColor('#4CAF50')  # Main green
                light_green = colors.HexColor('#E8F5E9')  # Light green for background
                dark_green = colors.HexColor('#2E7D32')   # Dark green for headings
                leaf_green = colors.HexColor('#81C784')   # Accent green

                # Initialize elements list
                elements = []

                # Nature Green theme styles
                green_name_style = ParagraphStyle(
                    'GreenNameStyle',
                    parent=styles['Heading1'],
                    fontSize=24,
                    leading=28,
                    textColor=dark_green,
                    spaceAfter=6,
                    fontName='Helvetica-Bold'
                )
                green_title_style = ParagraphStyle(
                    'GreenTitleStyle',
                    parent=styles['Heading2'],
                    fontSize=14,
                    textColor=nature_green,
                    spaceAfter=12
                )
                green_contact_style = ParagraphStyle(
                    'GreenContactStyle',
                    parent=styles['Normal'],
                    fontSize=10,
                    textColor=colors.HexColor('#555555'),
                    leading=12
                )
                green_section_heading = ParagraphStyle(
                    'GreenSectionHeading',
                    parent=styles['Heading2'],
                    fontSize=14,
                    textColor=dark_green,
                    spaceBefore=12,
                    spaceAfter=6,
                    borderColor=leaf_green,
                    borderWidth=0.5,
                    borderPadding=4,
                    borderRadius=2
                )
                green_body_style = ParagraphStyle(
                    'GreenBodyStyle',
                    parent=styles['Normal'],
                    fontSize=10,
                    leading=14,
                    textColor=colors.HexColor('#333333')
                )
                green_info_style = ParagraphStyle(
                    'GreenInfoStyle',
                    parent=styles['Normal'],
                    fontSize=9,
                    textColor=nature_green
                )

                # Modern Blue theme styles
                blue_name_style = ParagraphStyle(
                    'BlueNameStyle',
                    parent=styles['Heading1'],
                    fontSize=24,
                    leading=28,
                    textColor=dark_blue,
                    spaceAfter=6
                )
                blue_title_style = ParagraphStyle(
                    'BlueTitleStyle',
                    parent=styles['Heading2'],
                    fontSize=14,
                    textColor=primary_blue,
                    spaceAfter=12
                )
                blue_contact_style = ParagraphStyle(
                    'BlueContactStyle',
                    parent=styles['Normal'],
                    fontSize=10,
                    textColor=colors.HexColor('#555555'),
                    leading=12
                )
                blue_section_heading = ParagraphStyle(
                    'BlueSectionHeading',
                    parent=styles['Heading2'],
                    fontSize=16,
                    textColor=dark_blue,
                    spaceBefore=15,
                    spaceAfter=8,
                    borderColor=primary_blue,
                    borderWidth=1,
                    borderPadding=5,
                    borderRadius=3
                )
                blue_body_style = ParagraphStyle(
                    'BlueBodyStyle',
                    parent=styles['Normal'],
                    fontSize=10,
                    leading=14,
                    textColor=colors.HexColor('#333333')
                )
                blue_info_style = ParagraphStyle(
                    'BlueInfoStyle',
                    parent=styles['Normal'],
                    fontSize=9,
                    textColor=primary_blue
                )

                # Elegant Dark theme styles
                name_style_dark = ParagraphStyle(
                    'NameStyleDark',
                    parent=styles['Heading1'],
                    fontSize=20,
                    leading=24,
                    textColor=colors.HexColor('#FFFFFF'),
                    spaceAfter=6
                )
                title_style_dark = ParagraphStyle(
                    'TitleStyleDark',
                    parent=styles['Heading2'],
                    fontSize=12,
                    textColor=colors.HexColor('#DDDDDD'),
                    spaceAfter=4
                )
                contact_style_dark = ParagraphStyle(
                    'ContactStyleDark',
                    parent=styles['Normal'],
                    fontSize=10,
                    textColor=colors.HexColor('#EEEEEE'),
                    leading=12
                )
                section_heading_style_dark = ParagraphStyle(
                    'SectionHeadingDark',
                    parent=styles['Heading2'],
                    fontSize=12,
                    textColor=colors.HexColor('#333333'),
                    backColor=colors.HexColor('#F0F0F0'),
                    spaceBefore=8,
                    spaceAfter=6,
                    leftIndent=4,
                    rightIndent=4
                )
                body_style_dark = ParagraphStyle(
                    'BodyStyleDark',
                    parent=styles['Normal'],
                    fontSize=10,
                    leading=14,
                    textColor=colors.HexColor('#444444')
                )
                info_style_dark = ParagraphStyle(
                    'InfoStyleDark',
                    parent=styles['Normal'],
                    fontSize=9,
                    textColor=colors.HexColor('#555555')
                )

                # Creative Purple theme styles
                left_heading_style = ParagraphStyle(
                    'LeftHeadingStyle',
                    parent=styles['Heading2'],
                    fontSize=12,
                    leading=14,
                    textColor=colors.HexColor('#FFFFFF'),
                    spaceAfter=5
                )
                left_body_style = ParagraphStyle(
                    'LeftBodyStyle',
                    parent=styles['Normal'],
                    fontSize=10,
                    leading=12,
                    textColor=colors.HexColor('#FFFFFF')
                )
                left_name_style = ParagraphStyle(
                    'LeftNameStyle',
                    parent=styles['Heading1'],
                    fontSize=16,
                    leading=20,
                    textColor=colors.HexColor('#FFFFFF'),
                    alignment=1,  # Center alignment
                    spaceAfter=6
                )
                right_name_style = ParagraphStyle(
                    'RightNameStyle',
                    parent=styles['Heading1'],
                    fontSize=18,
                    textColor=colors.HexColor('#000000'),
                    spaceAfter=4
                )
                right_title_style = ParagraphStyle(
                    'RightTitleStyle',
                    parent=styles['Heading2'],
                    fontSize=12,
                    textColor=colors.HexColor('#555555'),
                    spaceAfter=6
                )
                right_body_style = ParagraphStyle(
                    'RightBodyStyle',
                    parent=styles['Normal'],
                    fontSize=10,
                    leading=14,
                    textColor=colors.HexColor('#333333')
                )
                right_section_heading = ParagraphStyle(
                    'RightSectionHeading',
                    parent=styles['Heading2'],
                    fontSize=14,
                    textColor=colors.HexColor('#4B0082'),  # Purple accent
                    spaceBefore=12,
                    spaceAfter=6
                )
                right_info_style = ParagraphStyle(
                    'RightInfoStyle',
                    parent=styles['Normal'],
                    fontSize=9,
                    textColor=colors.HexColor('#777777')
                )

                if selected_theme == "nature-green":
                    # Create header content
                    header_content = []
                    if name:
                        header_content.append(Paragraph(name, green_name_style))
                    if job_title:
                        header_content.append(Paragraph(job_title, green_title_style))

                    # Contact info
                    contact_items = []
                    if city: contact_items.append(city)
                    if phone: contact_items.append(phone)
                    if email: contact_items.append(email)
                    if contact_items:
                        contact_str = " | ".join(contact_items)
                        header_content.append(Paragraph(contact_str, green_contact_style))

                    # Create left and right columns
                    left_column = []
                    right_column = []

                    # Profile Photo
                    if photo_data:
                        try:
                            if photo_data.startswith('data:image'):
                                _, encoded = photo_data.split(',', 1)
                                img_data = base64.b64decode(encoded)
                                pil_image = Image.open(io.BytesIO(img_data)).convert('RGBA')
                            else:
                                pil_image = Image.open(photo_data).convert('RGBA')

                            pil_image = round_corners(pil_image, radius=40)
                            
                            max_size = 1.2 * inch
                            w, h = pil_image.size
                            aspect_ratio = w / float(h)
                            if aspect_ratio > 1:
                                new_w = max_size
                                new_h = max_size / aspect_ratio
                            else:
                                new_h = max_size
                                new_w = max_size * aspect_ratio

                            buf = io.BytesIO()
                            pil_image.save(buf, format='PNG')
                            buf.seek(0)
                            profile_img = RLImage(buf, width=new_w, height=new_h)
                            
                            left_column.append(profile_img)
                            left_column.append(Spacer(1, 15))
                        except Exception as e:
                            print("Error loading photo:", e)

                    # Summary / Profile
                    if summary_text.strip():
                        left_column.append(Paragraph("Profile", green_section_heading))
                        left_column.append(Paragraph(summary_text, green_body_style))
                        left_column.append(Spacer(1, 15))

                    # Skills
                    if skills_list:
                        left_column.append(Paragraph("Skills", green_section_heading))
                        for s in skills_list:
                            skill_line = s.get('skill', '')
                            proficiency = s.get('proficiency', '')
                            if proficiency:
                                skill_line += f" ({proficiency})"
                            left_column.append(Paragraph("• " + skill_line, green_body_style))
                        left_column.append(Spacer(1, 15))

                    # Languages
                    if languages:
                        left_column.append(Paragraph("Languages", green_section_heading))
                        for lang in languages:
                            lang_name = lang.get('language', '')
                            prof = lang.get('proficiency', '')
                            left_column.append(Paragraph(f"• {lang_name} - {prof}", green_body_style))
                        left_column.append(Spacer(1, 15))

                    # Experience
                    if experiences:
                        right_column.append(Paragraph("Experience", green_section_heading))
                        for exp in experiences:
                            pos = exp.get('position', '')
                            comp = exp.get('company', '')
                            sd = exp.get('start_date', '')
                            is_current = exp.get('is_current', False)
                            ed = 'Present' if is_current else exp.get('end_date', '')
                            desc = exp.get('description', '')

                            right_column.append(Paragraph(f"<b>{pos}</b>", green_body_style))
                            right_column.append(Paragraph(comp, green_info_style))
                            right_column.append(Paragraph(f"{sd} - {ed}", green_info_style))
                            if desc.strip():
                                right_column.append(Paragraph(desc, green_body_style))
                            right_column.append(Spacer(1, 10))

                    # Education
                    if educations:
                        right_column.append(Paragraph("Education", green_section_heading))
                        for edu in educations:
                            deg = edu.get('degree', '')
                            inst = edu.get('institution', '')
                            sd = edu.get('start_date', '')
                            is_cur = edu.get('is_current', False)
                            ed = 'Present' if is_cur else edu.get('end_date', '')
                            dsc = edu.get('description', '')

                            right_column.append(Paragraph(f"<b>{deg}</b>", green_body_style))
                            right_column.append(Paragraph(inst, green_info_style))
                            right_column.append(Paragraph(f"{sd} - {ed}", green_info_style))
                            if dsc.strip():
                                right_column.append(Paragraph(dsc, green_body_style))
                            right_column.append(Spacer(1, 10))

                    # Projects
                    if projects:
                        right_column.append(Paragraph("Projects", green_section_heading))
                        for proj in projects:
                            proj_name = proj.get('name', '')
                            description = proj.get('description', '')
                            link = proj.get('link', '')

                            right_column.append(Paragraph(f"<b>{proj_name}</b>", green_body_style))
                            if link:
                                right_column.append(Paragraph(f"Link: <a href='{link}'>{link}</a>", green_info_style))
                            if description.strip():
                                right_column.append(Paragraph(description, green_body_style))
                            right_column.append(Spacer(1, 10))

                    # Certifications
                    if certifications:
                        right_column.append(Paragraph("Certifications", green_section_heading))
                        for cert in certifications:
                            ctitle = cert.get('title', '')
                            issuer = cert.get('issuer', '')
                            cdate = cert.get('date', '')

                            right_column.append(Paragraph(f"<b>{ctitle}</b>", green_body_style))
                            right_column.append(Paragraph(f"Issuer: {issuer}", green_info_style))
                            right_column.append(Paragraph(f"Date: {cdate}", green_info_style))
                            right_column.append(Spacer(1, 10))

                    # Create a single table for both header and content
                    main_table_data = [
                        # Header row with light green background
                        [Table([[cell] for cell in header_content], 
                              colWidths=[doc.width],
                              style=TableStyle([
                                  ('BACKGROUND', (0, 0), (-1, -1), light_green),
                                  ('LEFTPADDING', (0, 0), (-1, -1), 15),
                                  ('RIGHTPADDING', (0, 0), (-1, -1), 15),
                                  ('TOPPADDING', (0, 0), (-1, -1), 20),
                                  ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
                                  ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                              ]))],
                        # Content row with two columns
                        [Table([[left_column, right_column]], 
                              colWidths=[doc.width * 0.35, doc.width * 0.65],
                              style=TableStyle([
                                  ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                  ('LEFTPADDING', (0, 0), (-1, -1), 15),
                                  ('RIGHTPADDING', (0, 0), (-1, -1), 15),
                                  ('LINEBEFORE', (1, 0), (1, -1), 0.5, leaf_green),
                              ]))]
                    ]

                    # Create the main table
                    main_table = Table(main_table_data, colWidths=[doc.width])
                    main_table.setStyle(TableStyle([
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ]))

                    elements.append(main_table)

                elif selected_theme == "modern-blue":
                    # Create a single table for all content
                    header_content = []
                    if name:
                        header_content.append(Paragraph(name, blue_name_style))
                    if job_title:
                        header_content.append(Paragraph(job_title, blue_title_style))

                    # Contact info
                    contact_items = []
                    if city: contact_items.append(city)
                    if phone: contact_items.append(phone)
                    if email: contact_items.append(email)
                    if contact_items:
                        contact_str = " | ".join(contact_items)
                        header_content.append(Paragraph(contact_str, blue_contact_style))

                    # Create left and right columns
                    left_column = []
                    right_column = []

                    # Profile Photo (if available)
                    if photo_data:
                        try:
                            if photo_data.startswith('data:image'):
                                _, encoded = photo_data.split(',', 1)
                                img_data = base64.b64decode(encoded)
                                pil_image = Image.open(io.BytesIO(img_data)).convert('RGBA')
                            else:
                                pil_image = Image.open(photo_data).convert('RGBA')

                            pil_image = round_corners(pil_image, radius=40)
                            
                            max_size = 1.2 * inch
                            w, h = pil_image.size
                            aspect_ratio = w / float(h)
                            if aspect_ratio > 1:
                                new_w = max_size
                                new_h = max_size / aspect_ratio
                            else:
                                new_h = max_size
                                new_w = max_size * aspect_ratio

                            buf = io.BytesIO()
                            pil_image.save(buf, format='PNG')
                            buf.seek(0)
                            profile_img = RLImage(buf, width=new_w, height=new_h)
                            
                            left_column.append(profile_img)
                            left_column.append(Spacer(1, 15))
                        except Exception as e:
                            print("Error loading photo:", e)

                    # Add other content to columns
                    # Summary / Profile
                    if summary_text.strip():
                        left_column.append(Paragraph("Profile", blue_section_heading))
                        left_column.append(Paragraph(summary_text, blue_body_style))
                        left_column.append(Spacer(1, 15))

                    # Skills
                    if skills_list:
                        left_column.append(Paragraph("Skills", blue_section_heading))
                        for s in skills_list:
                            skill_line = s.get('skill', '')
                            proficiency = s.get('proficiency', '')
                            if proficiency:
                                skill_line += f" ({proficiency})"
                            left_column.append(Paragraph("• " + skill_line, blue_body_style))
                        left_column.append(Spacer(1, 15))

                    # Languages
                    if languages:
                        left_column.append(Paragraph("Languages", blue_section_heading))
                        for lang in languages:
                            lang_name = lang.get('language', '')
                            prof = lang.get('proficiency', '')
                            left_column.append(Paragraph(f"• {lang_name} - {prof}", blue_body_style))
                        left_column.append(Spacer(1, 15))

                    # Experience
                    if experiences:
                        right_column.append(Paragraph("Experience", blue_section_heading))
                        for exp in experiences:
                            pos = exp.get('position', '')
                            comp = exp.get('company', '')
                            sd = exp.get('start_date', '')
                            is_current = exp.get('is_current', False)
                            ed = 'Present' if is_current else exp.get('end_date', '')
                            desc = exp.get('description', '')

                            right_column.append(Paragraph(f"<b>{pos}</b>", blue_body_style))
                            right_column.append(Paragraph(comp, blue_info_style))
                            right_column.append(Paragraph(f"{sd} - {ed}", blue_info_style))
                            if desc.strip():
                                right_column.append(Paragraph(desc, blue_body_style))
                            right_column.append(Spacer(1, 10))

                    # Education
                    if educations:
                        right_column.append(Paragraph("Education", blue_section_heading))
                        for edu in educations:
                            deg = edu.get('degree', '')
                            inst = edu.get('institution', '')
                            sd = edu.get('start_date', '')
                            is_cur = edu.get('is_current', False)
                            ed = 'Present' if is_cur else edu.get('end_date', '')
                            dsc = edu.get('description', '')

                            right_column.append(Paragraph(f"<b>{deg}</b>", blue_body_style))
                            right_column.append(Paragraph(inst, blue_info_style))
                            right_column.append(Paragraph(f"{sd} - {ed}", blue_info_style))
                            if dsc.strip():
                                right_column.append(Paragraph(dsc, blue_body_style))
                            right_column.append(Spacer(1, 10))

                    # Projects
                    if projects:
                        right_column.append(Paragraph("Projects", blue_section_heading))
                        for proj in projects:
                            proj_name = proj.get('name', '')
                            description = proj.get('description', '')
                            link = proj.get('link', '')

                            right_column.append(Paragraph(f"<b>{proj_name}</b>", blue_body_style))
                            if link:
                                right_column.append(Paragraph(f"Link: <a href='{link}'>{link}</a>", blue_info_style))
                            if description.strip():
                                right_column.append(Paragraph(description, blue_body_style))
                            right_column.append(Spacer(1, 10))

                    # Certifications
                    if certifications:
                        right_column.append(Paragraph("Certifications", blue_section_heading))
                        for cert in certifications:
                            ctitle = cert.get('title', '')
                            issuer = cert.get('issuer', '')
                            cdate = cert.get('date', '')

                            right_column.append(Paragraph(f"<b>{ctitle}</b>", blue_body_style))
                            right_column.append(Paragraph(f"Issuer: {issuer}", blue_info_style))
                            right_column.append(Paragraph(f"Date: {cdate}", blue_info_style))
                            right_column.append(Spacer(1, 10))

                    # Create a single table for both header and content
                    main_table_data = [
                        # Header row with blue background
                        [Table([[cell] for cell in header_content], 
                              colWidths=[doc.width],
                              style=TableStyle([
                                  ('BACKGROUND', (0, 0), (-1, -1), light_blue),
                                  ('LEFTPADDING', (0, 0), (-1, -1), 10),
                                  ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                                  ('TOPPADDING', (0, 0), (-1, -1), 20),
                                  ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
                                  ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                              ]))],
                        # Content row with two columns
                        [Table([[left_column, right_column]], 
                              colWidths=[doc.width * 0.35, doc.width * 0.65],
                              style=TableStyle([
                                  ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                  ('LEFTPADDING', (0, 0), (-1, -1), 20),
                                  ('RIGHTPADDING', (0, 0), (-1, -1), 20),
                                  ('LINEBEFORE', (1, 0), (1, -1), 0.5, vertical_line_color),
                              ]))]
                    ]

                    # Create the main table
                    main_table = Table(main_table_data, colWidths=[doc.width])
                    main_table.setStyle(TableStyle([
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ]))

                    elements.append(main_table)

                elif selected_theme == "creative-purple":
                    # Create left column flowables
                    left_col_flowables = []

                    # Profile Photo
                    if photo_data:
                        try:
                            if photo_data.startswith('data:image'):
                                _, encoded = photo_data.split(',', 1)
                                img_data = base64.b64decode(encoded)
                                pil_image = Image.open(io.BytesIO(img_data)).convert('RGBA')
                            else:
                                pil_image = Image.open(photo_data).convert('RGBA')

                            pil_image = round_corners(pil_image, radius=40)

                            max_size = 1.2 * inch  # Reduced from 1.5 inch
                            w, h = pil_image.size
                            aspect_ratio = w / float(h)
                            if aspect_ratio > 1:
                                new_w = max_size
                                new_h = max_size / aspect_ratio
                            else:
                                new_h = max_size
                                new_w = max_size * aspect_ratio

                            buf = io.BytesIO()
                            pil_image.save(buf, format='PNG')
                            buf.seek(0)
                            profile_img = RLImage(buf, width=new_w, height=new_h)

                            left_col_flowables.append(profile_img)
                            left_col_flowables.append(Spacer(1, 10))
                        except Exception as e:
                            print("Error loading photo:", e)

                    # Summary / Profile
                    if summary_text.strip():
                        left_col_flowables.append(Paragraph("PROFILE", left_heading_style))
                        left_col_flowables.append(Paragraph(summary_text, left_body_style))
                        left_col_flowables.append(Spacer(1, 10))

                    # Skills
                    if skills_list:
                        left_col_flowables.append(Paragraph("SKILLS", left_heading_style))
                        for s in skills_list:
                            skill_line = s.get('skill', '')
                            proficiency = s.get('proficiency', '')
                            if proficiency:
                                skill_line += f" ({proficiency})"
                            left_col_flowables.append(Paragraph("• " + skill_line, left_body_style))
                        left_col_flowables.append(Spacer(1, 10))

                    # Languages
                    if languages:
                        left_col_flowables.append(Paragraph("LANGUAGES", left_heading_style))
                        for lang in languages:
                            lang_name = lang.get('language', '')
                            prof = lang.get('proficiency', '')
                            left_col_flowables.append(Paragraph(f"• {lang_name} - {prof}", left_body_style))
                        left_col_flowables.append(Spacer(1, 10))

                    # Create left column table with purple background
                    left_table = Table([[flow] for flow in left_col_flowables], 
                                     colWidths=[2.2 * inch],
                                     splitByRow=True)  # Enable splitting
                    left_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#4B0082')),
                        ('LEFTPADDING', (0, 0), (-1, -1), 20),     # Reduced from 15
                        ('RIGHTPADDING', (0, 0), (-1, -1), 8),    # Reduced from 10
                        ('TOPPADDING', (0, 0), (-1, -1), 8),      # Reduced from 10
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),   # Reduced from 10
                    ]))

                    # Create right column flowables
                    right_col_flowables = []

                    # Name & Job Title
                    if name:
                        right_col_flowables.append(Paragraph(name, right_name_style))
                    if job_title:
                        right_col_flowables.append(Paragraph(job_title, right_title_style))

                    # Contact Info
                    contact_items = []
                    if city: contact_items.append(city)
                    if phone: contact_items.append(phone)
                    if email: contact_items.append(email)
                    if contact_items:
                        contact_str = " | ".join(contact_items)
                        right_col_flowables.append(Paragraph(contact_str, right_body_style))
                        right_col_flowables.append(Spacer(1, 8))

                    # Experience
                    if experiences:
                        right_col_flowables.append(Paragraph("Experience", right_section_heading))
                        for exp in experiences:
                            pos = exp.get('position', '')
                            comp = exp.get('company', '')
                            sd = exp.get('start_date', '')
                            is_current = exp.get('is_current', False)
                            ed = 'Present' if is_current else exp.get('end_date', '')
                            desc = exp.get('description', '')

                            right_col_flowables.append(Paragraph(f"<b>{pos}</b> - {comp}", right_body_style))
                            date_info = f"{sd} - {ed}"
                            right_col_flowables.append(Paragraph(date_info, right_info_style))
                            if desc.strip():
                                right_col_flowables.append(Paragraph(desc, right_body_style))
                            right_col_flowables.append(Spacer(1, 10))

                    # Education
                    if educations:
                        right_col_flowables.append(Paragraph("Education", right_section_heading))
                        for edu in educations:
                            deg = edu.get('degree', '')
                            inst = edu.get('institution', '')
                            sd = edu.get('start_date', '')
                            is_cur = edu.get('is_current', False)
                            ed = 'Present' if is_cur else edu.get('end_date', '')
                            dsc = edu.get('description', '')

                            right_col_flowables.append(Paragraph(f"<b>{deg}</b> - {inst}", right_body_style))
                            date_info = f"{sd} - {ed}"
                            right_col_flowables.append(Paragraph(date_info, right_info_style))
                            if dsc.strip():
                                right_col_flowables.append(Paragraph(dsc, right_body_style))
                            right_col_flowables.append(Spacer(1, 10))

                    # Projects
                    if projects:
                        right_col_flowables.append(Paragraph("Projects", right_section_heading))
                        for proj in projects:
                            proj_name = proj.get('name', '')
                            description = proj.get('description', '')
                            link = proj.get('link', '')

                            right_col_flowables.append(Paragraph(f"<b>{proj_name}</b>", right_body_style))
                            if link:
                                right_col_flowables.append(Paragraph(f"Link: <a href='{link}'>{link}</a>", right_body_style))
                            if description.strip():
                                right_col_flowables.append(Paragraph(description, right_body_style))
                            right_col_flowables.append(Spacer(1, 10))

                    # Certifications
                    if certifications:
                        right_col_flowables.append(Paragraph("Certifications", right_section_heading))
                        for cert in certifications:
                            ctitle = cert.get('title', '')
                            issuer = cert.get('issuer', '')
                            cdate = cert.get('date', '')

                            right_col_flowables.append(Paragraph(f"<b>{ctitle}</b>", right_body_style))
                            right_col_flowables.append(Paragraph(f"Issuer: {issuer}", right_body_style))
                            right_col_flowables.append(Paragraph(f"Date: {cdate}", right_body_style))
                            right_col_flowables.append(Spacer(1, 10))

                    # Combine into a two-column table
                    main_table = Table([
                        [left_table, right_col_flowables]
                    ], colWidths=[2.7 * inch, 5.6 * inch])  # Adjusted widths
                    main_table.setStyle(TableStyle([
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('LEFTPADDING', (0, 0), (0, -1), 0),    # Left column padding
                        ('RIGHTPADDING', (-1, 0), (-1, -1), 8), # Right column padding
                        ('TOPPADDING', (0, 0), (-1, -1), 0),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                    ]))

                    elements.append(main_table)

                elif selected_theme == "elegant-dark":
                    # Create left and right columns
                    left_elements = []
                    right_elements = []

                    # Create header content
                    header_content = []
                    header_content.append(Paragraph(name.upper(), name_style_dark))
                    if job_title:
                        header_content.append(Paragraph(job_title, title_style_dark))

                    # Contact info
                    contact_items = []
                    if city: contact_items.append(city)
                    if phone: contact_items.append(phone)
                    if email: contact_items.append(email)
                    if contact_items:
                        contact_str = " | ".join(contact_items)
                        header_content.append(Paragraph(contact_str, contact_style_dark))

                    # Profile Photo
                    if photo_data:
                        try:
                            if photo_data.startswith('data:image'):
                                _, encoded = photo_data.split(',', 1)
                                img_data = base64.b64decode(encoded)
                                pil_image = Image.open(io.BytesIO(img_data)).convert('RGBA')
                            else:
                                pil_image = Image.open(photo_data).convert('RGBA')

                            pil_image = round_corners(pil_image, radius=40)

                            max_size = 1.2 * inch
                            w, h = pil_image.size
                            aspect_ratio = w / float(h)
                            if aspect_ratio > 1:
                                new_w = max_size
                                new_h = max_size / aspect_ratio
                            else:
                                new_h = max_size
                                new_w = max_size * aspect_ratio

                            buf = io.BytesIO()
                            pil_image.save(buf, format='PNG')
                            buf.seek(0)
                            profile_img = RLImage(buf, width=new_w, height=new_h)

                            img_table = Table([[profile_img]], colWidths=[2*inch])
                            img_table.setStyle(TableStyle([
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ]))
                            left_elements.append(img_table)
                            left_elements.append(Spacer(1, 15))
                        except Exception as e:
                            print("Error loading photo:", e)

                    # Add other content to columns
                    # Summary / Profile
                    if summary_text.strip():
                        left_elements.append(Paragraph("Profile", section_heading_style_dark))
                        left_elements.append(Paragraph(summary_text, body_style_dark))
                        left_elements.append(Spacer(1, 15))

                    # Skills
                    if skills_list:
                        left_elements.append(Paragraph("Skills", section_heading_style_dark))
                        for s in skills_list:
                            skill_line = s.get('skill', '')
                            proficiency = s.get('proficiency', '')
                            if proficiency:
                                skill_line += f" ({proficiency})"
                            left_elements.append(Paragraph("• " + skill_line, body_style_dark))
                        left_elements.append(Spacer(1, 15))

                    # Languages
                    if languages:
                        left_elements.append(Paragraph("Languages", section_heading_style_dark))
                        for lang in languages:
                            lang_name = lang.get('language', '')
                            prof = lang.get('proficiency', '')
                            left_elements.append(Paragraph(f"• {lang_name} - {prof}", body_style_dark))
                            left_elements.append(Spacer(1, 15))

                    # Experience
                    if experiences:
                        right_elements.append(Paragraph("Experience", section_heading_style_dark))
                        for exp in experiences:
                            pos = exp.get('position', '')
                            comp = exp.get('company', '')
                            sd = exp.get('start_date', '')
                            is_current = exp.get('is_current', False)
                            ed = 'Present' if is_current else exp.get('end_date', '')
                            desc = exp.get('description', '')

                            right_elements.append(Paragraph(f"<b>{pos}</b> - {comp}", body_style_dark))
                            right_elements.append(Paragraph(f"{sd} - {ed}", info_style_dark))
                            if desc.strip():
                                right_elements.append(Paragraph(desc, body_style_dark))
                            right_elements.append(Spacer(1, 10))

                    # Education
                    if educations:
                        right_elements.append(Paragraph("Education", section_heading_style_dark))
                        for edu in educations:
                            deg = edu.get('degree', '')
                            inst = edu.get('institution', '')
                            sd = edu.get('start_date', '')
                            is_cur = edu.get('is_current', False)
                            ed = 'Present' if is_cur else edu.get('end_date', '')
                            dsc = edu.get('description', '')

                            right_elements.append(Paragraph(f"<b>{deg}</b> - {inst}", body_style_dark))
                            right_elements.append(Paragraph(f"{sd} - {ed}", info_style_dark))
                            if dsc.strip():
                                right_elements.append(Paragraph(dsc, body_style_dark))
                            right_elements.append(Spacer(1, 10))

                    # Projects
                    if projects:
                        right_elements.append(Paragraph("Projects", section_heading_style_dark))
                        for proj in projects:
                            proj_name = proj.get('name', '')
                            description = proj.get('description', '')
                            link = proj.get('link', '')

                            right_elements.append(Paragraph(f"<b>{proj_name}</b>", body_style_dark))
                            if link:
                                right_elements.append(Paragraph(f"Link: <a href='{link}'>{link}</a>", info_style_dark))
                            if description.strip():
                                right_elements.append(Paragraph(description, body_style_dark))
                            right_elements.append(Spacer(1, 10))

                    # Certifications
                    if certifications:
                        right_elements.append(Paragraph("Certifications", section_heading_style_dark))
                        for cert in certifications:
                            ctitle = cert.get('title', '')
                            issuer = cert.get('issuer', '')
                            cdate = cert.get('date', '')

                            right_elements.append(Paragraph(f"<b>{ctitle}</b>", body_style_dark))
                            right_elements.append(Paragraph(f"Issuer: {issuer}", info_style_dark))
                            right_elements.append(Paragraph(f"Date: {cdate}", info_style_dark))
                            right_elements.append(Spacer(1, 10))

                    # Create a single table for both header and content
                    main_table_data = [
                        # Header row with dark background
                        [Table([[cell] for cell in header_content], 
                              colWidths=[doc.width],
                              style=TableStyle([
                                  ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#333333')),
                                  ('LEFTPADDING', (0, 0), (-1, -1), 10),
                                  ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                                  ('TOPPADDING', (0, 0), (-1, -1), 16),
                                  ('BOTTOMPADDING', (0, 0), (-1, -1), 16),
                              ]))],
                        # Content row with two columns
                        [Table([[left_elements, right_elements]], 
                              colWidths=[2.2*inch, 5.6*inch],
                              style=TableStyle([
                                  ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                  ('LEFTPADDING', (0, 0), (-1, -1), 8),
                                  ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                              ]))]
                    ]

                    # Create the main table
                    main_table = Table(main_table_data, colWidths=[doc.width])
                    main_table.setStyle(TableStyle([
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ]))

                    elements.append(main_table)

                else:
                    # Default header
                    header_left = []
                    header_left.append(Paragraph(name, name_style_default))
                    header_left.append(Paragraph(job_title, title_style_default))

                    header_right = []
                    if city:
                        header_right.append(Paragraph(city, contact_style_default))
                    if phone:
                        header_right.append(Paragraph(phone, contact_style_default))
                    if email:
                        header_right.append(Paragraph(email, contact_style_default))

                    header_table_data = [[header_left, header_right]]
                    header_table = Table(header_table_data, colWidths=[2.7*inch, 5.6*inch], splitByRow=True)
                    header_table.setStyle(TableStyle([
                        ('VALIGN', (0,0), (-1,-1), 'TOP'),
                        ('LEFTPADDING', (0,0), (-1,-1), 20),
                        ('RIGHTPADDING', (0,0), (-1,-1), 20),
                        ('TOPPADDING', (0,0), (-1,-1), 0),
                    ]))
                    elements.append(header_table)

                    # Horizontal line under the header
                    line_data = [['']]
                    line_table = Table(line_data, colWidths=[8*inch])
                    line_table.setStyle(TableStyle([
                        ('LINEBELOW', (0, 0), (-1, 0), 1, line_color),
                    ]))
                    elements.append(Spacer(1, 5))
                    elements.append(line_table)
                    elements.append(Spacer(1, 12))

                    # Two-column layout
                    left_elements = []
                    right_elements = []

                    # Profile Photo
                    if photo_data:
                        try:
                            if photo_data.startswith('data:image'):
                                _, encoded = photo_data.split(',', 1)
                                img_data = base64.b64decode(encoded)
                                pil_image = Image.open(io.BytesIO(img_data)).convert('RGBA')
                            else:
                                pil_image = Image.open(photo_data).convert('RGBA')

                            pil_image = round_corners(pil_image, radius=40)

                            max_size = 1.2 * inch  # Reduced from 1.5 inch
                            w, h = pil_image.size
                            aspect_ratio = w / float(h)
                            if aspect_ratio > 1:
                                new_w = max_size
                                new_h = max_size / aspect_ratio
                            else:
                                new_h = max_size
                                new_w = max_size * aspect_ratio

                            buf = io.BytesIO()
                            pil_image.save(buf, format='PNG')
                            buf.seek(0)
                            profile_img = RLImage(buf, width=new_w, height=new_h)

                            img_table = Table([[profile_img]], colWidths=[2*inch])
                            img_table.setStyle(TableStyle([
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ]))
                            left_elements.append(img_table)
                            left_elements.append(Spacer(1, 15))
                        except Exception as e:
                            print("Error loading photo:", e)

                    # Summary / Profile
                    if summary_text.strip():
                        left_elements.append(Paragraph("Profile", section_heading_style_default))
                        left_elements.append(Paragraph(summary_text, body_style_default))
                        left_elements.append(Spacer(1, 15))

                    # Skills
                    if skills_list:
                        left_elements.append(Paragraph("Skills", section_heading_style_default))
                        for s in skills_list:
                            skill_line = s.get('skill', '')
                            proficiency = s.get('proficiency', '')
                            if proficiency:
                                skill_line += f" ({proficiency})"
                            left_elements.append(Paragraph("• " + skill_line, body_style_default))
                        left_elements.append(Spacer(1, 15))

                    # Languages
                    if languages:
                        left_elements.append(Paragraph("Languages", section_heading_style_default))
                        for lang in languages:
                            lang_name = lang.get('language', '')
                            prof = lang.get('proficiency', '')
                            left_elements.append(Paragraph(f"• {lang_name} - {prof}", body_style_default))
                            left_elements.append(Spacer(1, 15))

                    # Experience
                    if experiences:
                        right_elements.append(Paragraph("Experience", section_heading_style_default))
                        for exp in experiences:
                            pos = exp.get('position', '')
                            comp = exp.get('company', '')
                            sd = exp.get('start_date', '')
                            is_current = exp.get('is_current', False)
                            ed = 'Present' if is_current else exp.get('end_date', '')
                            desc = exp.get('description', '')

                            right_elements.append(Paragraph(f"<b>{pos}</b> - {comp}", body_style_default))
                            right_elements.append(Paragraph(f"{sd} - {ed}", info_style_default))
                            if desc.strip():
                                right_elements.append(Paragraph(desc, body_style_default))
                            right_elements.append(Spacer(1, 10))

                    # Education
                    if educations:
                        right_elements.append(Paragraph("Education", section_heading_style_default))
                        for edu in educations:
                            deg = edu.get('degree', '')
                            inst = edu.get('institution', '')
                            sd = edu.get('start_date', '')
                            is_cur = edu.get('is_current', False)
                            ed = 'Present' if is_cur else edu.get('end_date', '')
                            dsc = edu.get('description', '')

                            right_elements.append(Paragraph(f"<b>{deg}</b> - {inst}", body_style_default))
                            right_elements.append(Paragraph(f"{sd} - {ed}", info_style_default))
                            if dsc.strip():
                                right_elements.append(Paragraph(dsc, body_style_default))
                            right_elements.append(Spacer(1, 10))

                    # Projects
                    if projects:
                        right_elements.append(Paragraph("Projects", section_heading_style_default))
                        for proj in projects:
                            proj_name = proj.get('name', '')
                            description = proj.get('description', '')
                            link = proj.get('link', '')

                            right_elements.append(Paragraph(f"<b>{proj_name}</b>", body_style_default))
                            if link:
                                right_elements.append(Paragraph(f"Link: <a href='{link}'>{link}</a>", info_style_default))
                            if description.strip():
                                right_elements.append(Paragraph(description, body_style_default))
                            right_elements.append(Spacer(1, 10))

                    # Certifications
                    if certifications:
                        right_elements.append(Paragraph("Certifications", section_heading_style_default))
                        for cert in certifications:
                            ctitle = cert.get('title', '')
                            issuer = cert.get('issuer', '')
                            cdate = cert.get('date', '')

                            right_elements.append(Paragraph(f"<b>{ctitle}</b>", body_style_default))
                            right_elements.append(Paragraph(f"Issuer: {issuer}", info_style_default))
                            right_elements.append(Paragraph(f"Date: {cdate}", info_style_default))
                            right_elements.append(Spacer(1, 10))

                    # Create content table with splitting enabled
                    content_table = Table([[left_elements, right_elements]], 
                                        colWidths=[2.3*inch, 5.6*inch],
                                        splitByRow=True)  # Enable splitting
                    content_table.setStyle(TableStyle([
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('LEFTPADDING', (0, 0), (-1, -1), 0),    # Reduced from 15
                        ('RIGHTPADDING', (0, 0), (-1, -1), 15),   # Reduced from 15
                        ('LINEBEFORE', (1, 0), (1, -1), 0.5, vertical_line_color),  # Reduced line width from 1
                    ]))
                    elements.append(content_table)

                # Build the document
                doc.build(elements)
                return True
            except Exception as e:
                if "too large on page" in str(e) and height_multiplier < 3.0:  # Maximum 3 times A4 height
                    print(f"Trying with height multiplier: {height_multiplier + 0.1}")
                    return try_build_pdf(height_multiplier + 0.1)
                else:
                    raise e

        # Try to build PDF with incrementally increasing height
        try_build_pdf()

        # Return the generated PDF
        return FileResponse(
            path=filename,
            media_type='application/pdf',
            filename=f"{name.replace(' ', '_')}_{selected_theme or 'default'}_{datetime.now().strftime('%Y%m%d')}.pdf",
            background=background_tasks
        )

    except Exception as e:
        print(f"Error building PDF document: {e}")
        if os.path.exists(filename):
            os.remove(filename)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating PDF: {str(e)}"
        )

def create_section(title, items, style_heading, style_body, style_info):
    elements = []
    elements.append(Paragraph(title, style_heading))
    for item in items:
        for p in item:
            elements.append(p)
        elements.append(Spacer(1, 8))
    return elements