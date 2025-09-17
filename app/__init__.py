from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_migrate import Migrate
from flask_login import LoginManager
from dotenv import load_dotenv
import os
from google_auth_oauthlib.flow import Flow
from .extensions import db, mail, migrate, login
import pathlib

# Nạp biến môi trường từ .env
load_dotenv()
app = Flask(__name__)
# Flask secret key
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  #để đăng nhập đc trên localhost

# Database config
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Mail config
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')


# Thêm vào các config khác
app.config['VNPAY_TMN_CODE'] = os.getenv('VNPAY_TMN_CODE')
app.config['VNPAY_HASH_SECRET'] = os.getenv('VNPAY_HASH_SECRET')
app.config['VNPAY_URL'] = os.getenv('VNPAY_URL', 'https://sandbox.vnpayment.vn/paymentv2/vpcpay.html')
app.config['VNPAY_RETURN_URL'] = os.getenv('VNPAY_RETURN_URL', 'http://localhost:5000/payment/vnpay_return')


GOOGLE_CLIENT_SECRETS_FILE = os.path.join(pathlib.Path(__file__).parent, "oauth_config.json")

flow = Flow.from_client_secrets_file(
    GOOGLE_CLIENT_SECRETS_FILE,
    scopes=["https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
            "openid"],
    redirect_uri="http://localhost:5000/callback"

)
# App settings
PAGE_SIZE = 8
# Khởi tạo các extension
db.init_app(app)
mail.init_app(app)
migrate.init_app(app, db)
login.init_app(app)

# Import routes và models
from app import  models
from app import admin






