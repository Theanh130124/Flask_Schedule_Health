from werkzeug.security import generate_password_hash
from app.models  import User
from app import db

def create_user(fullname, username, email, phone, password):
    hashed_pw = generate_password_hash(password.strip())
    new_user = User(
        fullname=fullname.strip(),
        username=username.strip(),
        email=email.strip(),
        phone=phone.strip() if phone else None,
        password=hashed_pw
    )
    db.session.add(new_user)
    db.session.commit()
    return new_user

def check_email_exists(email):
    return User.query.filter_by(email=email).first() is not None

def check_username_exists(username):
    return User.query.filter_by(username=username).first() is not None

def check_phone_exists(phone):
    return User.query.filter_by(phone=phone).first() is not None
