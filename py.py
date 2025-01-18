from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, 
                                Table, TableStyle, Image as RLImage, Flowable)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from PIL import Image, ImageDraw
import io, base64, os

def round_corners(image, radius=20):
    """تابعی برای گرد کردن گوشه‌های تصویر پروفایل."""
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

def generate_stylish_resume(output_filename, resume_data):
    """
    یک تابع نمونه برای ساخت رزومه با چیدمان شبیه تصویر:
    - هدر بالا با نام و اطلاعات تماس
    - ستون چپ: عکس، پروفایل، مهارت‌ها
    - ستون راست: تجربیات، تحصیلات و...
    """

    # داده‌های فرضی رزومه (در عمل از دیتابیس یا فرم کاربر می‌گیرید)
    name = resume_data.get('name', 'نام و نام‌خانوادگی')
    title = resume_data.get('title', 'عنوان شغل / موقعیت')
    contact_address = resume_data.get('address', '')
    contact_phone = resume_data.get('phone', '')
    contact_email = resume_data.get('email', '')
    summary_text = resume_data.get('summary', 'متن خلاصه...')
    experiences = resume_data.get('experiences', [])
    educations = resume_data.get('educations', [])
    skills = resume_data.get('skills', [])
    languages = resume_data.get('languages', [])
    photo_data = resume_data.get('photo')  # می‌تواند base64 یا مسیر فایل باشد

    # استایل‌های پایه
    styles = getSampleStyleSheet()
    normal_style = styles['Normal']

    # استایل سفارشی برای نام بزرگ در هدر
    name_style = ParagraphStyle(
        'NameStyle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=22,
        textColor=colors.HexColor('#333333'),
        spaceAfter=6
    )
    # استایل عنوان شغلی
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading2'],
        fontSize=12,
        leading=14,
        textColor=colors.HexColor('#666666'),
        spaceAfter=10
    )
    # استایل متن برای اطلاعات تماس
    contact_style = ParagraphStyle(
        'ContactStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#555555'),
        leading=12
    )
    # تیترهای داخل بدنه (تجربیات، تحصیلات، ...)
    section_heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#222222'),
        spaceBefore=10,
        spaceAfter=4
    )
    # متن معمولی در رزومه
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=12,
        textColor=colors.HexColor('#333333')
    )
    # برای تاریخ یا اطلاعات جانبی
    info_style = ParagraphStyle(
        'InfoStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#777777')
    )
    
    # ساخت Document
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=A4,
        rightMargin=36, leftMargin=36,
        topMargin=36, bottomMargin=36
    )

    # -------------------------
    # (1) هدر بالا
    # -------------------------
    header_left = []  # قرار است نام و عنوان شغلی در این ستون باشد
    header_left.append(Paragraph(name, name_style))
    header_left.append(Paragraph(title, title_style))

    header_right = []  # اطلاعات تماس در سمت دیگر
    # آدرس:
    if contact_address:
        header_right.append(Paragraph(contact_address, contact_style))
    # شماره تلفن:
    if contact_phone:
        header_right.append(Paragraph(contact_phone, contact_style))
    # ایمیل:
    if contact_email:
        header_right.append(Paragraph(contact_email, contact_style))

    # تبدیل دو ستون به یک سطر جدول
    header_table_data = [
        [
            header_left,
            header_right
        ]
    ]
    header_table = Table(header_table_data, colWidths=[3*inch, 3*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))

    # -------------------------
    # (2) خط افقی باریک زیر هدر
    # -------------------------
    # ترفند: ساخت جدولی که یک خط ترسیم کند
    line_data = [['']]
    line_table = Table(line_data, colWidths=[6*inch])
    line_table.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#999999')),
    ]))

    # -------------------------
    # (3) بدنه: دو ستون اصلی (چپ: پروفایل، مهارت‌ها؛ راست: تجربه، تحصیلات و غیره)
    # -------------------------
    # ستون چپ
    left_column = []

    # -- عکس پروفایل
    if photo_data:
        try:
            pil_image = None
            if photo_data.startswith('data:image'):
                # Base64
                header, encoded = photo_data.split(',', 1)
                img_data = base64.b64decode(encoded)
                pil_image = Image.open(io.BytesIO(img_data)).convert('RGBA')
            else:
                # مسیر فایل
                pil_image = Image.open(photo_data).convert('RGBA')
            
            pil_image = round_corners(pil_image, 30)
            buf = io.BytesIO()
            pil_image.save(buf, format='PNG')
            buf.seek(0)
            rl_img = RLImage(buf, width=1.2*inch, height=1.2*inch)
            left_column.append(rl_img)
            left_column.append(Spacer(1, 10))
        except Exception as e:
            print("Error loading photo:", e)

    # -- پروفایل (خلاصه)
    left_column.append(Paragraph("<b>+ پروفایل</b>", section_heading_style))
    left_column.append(Paragraph(summary_text, body_style))
    left_column.append(Spacer(1, 10))

    # -- مهارت‌ها
    if skills:
        left_column.append(Paragraph("<b>+ مهارت‌ها</b>", section_heading_style))
        for skill in skills:
            left_column.append(Paragraph("• " + skill, body_style))
        left_column.append(Spacer(1, 10))

    # -- زبان‌ها
    if languages:
        left_column.append(Paragraph("<b>+ زبان‌ها</b>", section_heading_style))
        for lng in languages:
            left_column.append(Paragraph("• " + lng, body_style))
        left_column.append(Spacer(1, 10))

    # ستون راست
    right_column = []
    
    # -- تجربیات
    if experiences:
        right_column.append(Paragraph("<b>+ تجربیات حرفه‌ای</b>", section_heading_style))
        for exp in experiences:
            # exp = {"title": "...", "company": "...", "date": "...", "desc": "..."}
            right_column.append(Paragraph(f"<b>{exp['title']}</b> - {exp['company']}", body_style))
            right_column.append(Paragraph(exp['date'], info_style))
            if exp.get('desc'):
                right_column.append(Paragraph(exp['desc'], body_style))
            right_column.append(Spacer(1, 8))

    # -- تحصیلات
    if educations:
        right_column.append(Paragraph("<b>+ تحصیلات</b>", section_heading_style))
        for edu in educations:
            # edu = {"degree": "...", "university": "...", "date": "...", "desc": "..."}
            right_column.append(Paragraph(f"<b>{edu['degree']}</b> - {edu['university']}", body_style))
            right_column.append(Paragraph(edu['date'], info_style))
            if edu.get('desc'):
                right_column.append(Paragraph(edu['desc'], body_style))
            right_column.append(Spacer(1, 8))

    # ساخت جدول دو ستونی برای بدنه
    body_table_data = [
        [left_column, right_column]
    ]
    body_table = Table(body_table_data, colWidths=[2.5*inch, 3.5*inch])
    body_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        # رسم خط نازک بین دو ستون
        ('LINEBEFORE', (1,0), (1, -1), 1, colors.HexColor('#aaaaaa')),
        ('LEFTPADDING', (0,0), (0,0), 6),
        ('RIGHTPADDING', (0,0), (0,0), 6),
        ('LEFTPADDING', (1,0), (1,0), 10),
        ('RIGHTPADDING', (1,0), (1,0), 6),
    ]))

    # در نهایت همه بخش‌ها را در لیستی از flowableها قرار می‌دهیم
    elements = []
    elements.append(header_table)
    elements.append(Spacer(1, 6))
    elements.append(line_table)
    elements.append(Spacer(1, 12))
    elements.append(body_table)

    # ساخت PDF
    doc.build(elements)

if __name__ == "__main__":
    # دادهٔ نمونه (به جای دریافت از دیتابیس یا API)
    dummy_data = {
        "name": "SHAYAN HASHEMI",
        "title": "Stage Master 1 Management de l'intelligence artificielle en santé (6 mois)",
        "address": "2 Avenue Nelson Mandela, Lille, 59160, France",
        "phone": "07 55 96 36 30",
        "email": "shayan.hashemi27@gmail.com",
        "summary": """Je suis un professionnel expérimenté avec 7 années d’expérience dans le domaine du projet académique ...""",
        "photo": "data:image/png;base64,...",  # یا مسیر فایل "path/to/myphoto.png"
        "skills": [
            "Data Science", "Machine Learning", "Python", 
            "SQL", "Git/Github", "HTML/CSS"
        ],
        "languages": ["Français (C1)", "Anglais (B2)", "Persan (Natif)"],
        "experiences": [
            {
                "title": "PROJET ACADÉMIQUE",
                "company": "Lille Central",
                "date": "SEPT. 2023 - MARS 2024",
                "desc": """Modélisation du parcours patient et optimisation ..."""
            },
            {
                "title": "ADMINISTRATEURS INFORMATIQUES",
                "company": "Institut pédagogique de Novin Parsian - Ahvaz, Iran",
                "date": "JANV. 2019 - JUILL. 2021",
                "desc": """Conception et développement de sites web attrayants ..."""
            },
        ],
        "educations": [
            {
                "degree": "MANAGEMENT DE L’INTELLIGENCE ARTIFICIELLE EN SANTÉ",
                "university": "Centrale Lille, France",
                "date": "2023",
                "desc": """Master en Management de l'intelligence artificielle en santé, Bac+4"""
            },
            {
                "degree": "NUTRITION ET SCIENCES DES ALIMENTS",
                "university": "Université des sciences médicales de Jondishapour - Ahvaz, Iran",
                "date": "2015",
                "desc": """Licence en Nutrition et sciences des aliments"""
            }
        ]
    }

    generate_stylish_resume("resume_output.pdf", dummy_data)
    print("PDF generated: resume_output.pdf")
