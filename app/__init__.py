from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_migrate import Migrate

app = Flask(__name__)

# Database config
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:123456@localhost/healthdb_flask?charset=utf8mb4"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Mail config
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'theanhtran13012004@gmail.com'
app.config['MAIL_PASSWORD'] = 'kmui vkff bpwd wyke'

mail = Mail(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Import routes và models
from app import routes, models
