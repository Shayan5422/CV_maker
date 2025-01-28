import os
import sys

# تنظیم مسیر پروژه
path = '/home/CVmaker/CV_maker'
if path not in sys.path:
    sys.path.append(path)

# تنظیم متغیرهای محیطی
os.environ['DATABASE_URL'] = 'sqlite:///./sql_app.db'
os.environ['SECRET_KEY'] = 'your-secret-key-here'  # این را تغییر دهید
os.environ['CORS_ORIGINS'] = 'https://cvmaker.pythonanywhere.com,http://localhost:4200'

# فعال‌سازی محیط مجازی
activate_this = '/home/CVmaker/CV_maker/venv/bin/activate_this.py'
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))

from main import app as application 