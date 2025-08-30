from werkzeug.security import generate_password_hash
from models import User
from config import db

def register_user(username, email, password, phone=None, full_name=None):

    # Kiểm tra trùng trung lap username va email
    if get_user_by_username(username) or check_email_exists(email):
        return None  # đã tồn tại

    # Băm mật khẩu MD5
    hashed_password = hashlib.md5(password.strip().encode("utf-8")).hexdigest()

    # Tạo đối tượng User
    new_user = User(
        username=username.strip(),
        email=email.strip(),
        password=hashed_password,
        phone=phone.strip() if phone else None,
        full_name=full_name.strip() if full_name else None
    )

    try:
        db.session.add(new_user)
        db.session.commit()
        return new_user
    except Exception as ex:
        db.session.rollback()
        print(f" Loi dang ky : {ex}")
        return None

def check_email_exists(email):
    return User.query.filter_by(email=email).first() is not None

def check_username_exists(username):
    return User.query.filter_by(username=username).first() is not None

def check_phone_exists(phone):
    return User.query.filter_by(phone=phone).first() is not None