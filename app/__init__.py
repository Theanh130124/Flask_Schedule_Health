from flask import Flask
from dotenv import load_dotenv
import os
import pathlib
from google_auth_oauthlib.flow import Flow
from app.extensions import db, mail, migrate, login

# Nạp biến môi trường
load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# Database config
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Mail config
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

# Google OAuth
GOOGLE_CLIENT_SECRETS_FILE = os.path.join(pathlib.Path(__file__).parent, "oauth_config.json")
flow = Flow.from_client_secrets_file(
    GOOGLE_CLIENT_SECRETS_FILE,
    scopes=["https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
            "openid"],
    redirect_uri="http://localhost:5000/callback"
)

PAGE_SIZE = 8


db.init_app(app)
mail.init_app(app)
migrate.init_app(app, db)
login.init_app(app)

# Import models để SQLAlchemy biết
from app import models

# Import admin sau khi db đã init
from app import admin
