from werkzeug.security import generate_password_hash
from app.models import User, db
from flask_login import current_user
import hashlib

def create_user(username, email, password, first_name, last_name, phone_number, address,
                date_of_birth=None, gender=None):
    """
    Tạo user mới, mặc định role = PATIENT
    """

    # Kiểm tra trùng username, email, phone
    if check_username_exists(username) or check_email_exists(email) or check_phone_exists(phone_number):
        return None  # đã tồn tại

    # Băm mật khẩu MD5
    hashed_password = hashlib.md5(password.strip().encode("utf-8")).hexdigest()

    # Tạo đối tượng User
    new_user = User(
        username=username,
        email=email,
        password=hashed_password,
        first_name=first_name,
        last_name=last_name,
        phone_number=phone_number,
        address=address,
        date_of_birth=date_of_birth,
        gender=gender,
        role="PATIENT"  # mặc định là bệnh nhân
    )

    try:
        db.session.add(new_user)
        db.session.commit()
        return new_user
    except Exception as ex:
        db.session.rollback()
        print(f"Lỗi đăng ký: {ex}")
        return None


# ======================= HÀM HỖ TRỢ =======================

def check_email_exists(email):
    return User.query.filter_by(email=email).first() is not None

def check_username_exists(username):
    return User.query.filter_by(username=username).first() is not None

def check_phone_exists(phone):
    return User.query.filter_by(phone_number=phone).first() is not None

def get_user_by_username(username):
    return User.query.filter_by(username=username).first()
