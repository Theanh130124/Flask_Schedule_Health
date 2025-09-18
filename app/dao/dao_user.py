import hashlib
from app.models import User, Patient, RoleEnum
from app.extensions import db
from app.dao import dao_healthrecord
from datetime import datetime


def create_user_with_role(username, email, password, first_name, last_name,
                          phone_number, address, date_of_birth=None,
                          gender=None, role=RoleEnum.PATIENT):
    """
    Tạo user mới theo role. Nếu role=PATIENT thì tự tạo Patient + HealthRecord.
    """
    # Kiểm tra trùng
    if check_username_exists(username) or check_email_exists(email) or check_phone_exists(phone_number):
        return None

    hashed_password = hashlib.md5(password.strip().encode("utf-8")).hexdigest()

    user = User(
        username=username,
        email=email,
        password=hashed_password,
        first_name=first_name,
        last_name=last_name,
        phone_number=phone_number,
        address=address,
        date_of_birth=date_of_birth,
        gender=gender,
        role=role,
        is_active=True
    )

    try:
        db.session.add(user)
        db.session.flush()  # để có user_id

        if role == RoleEnum.PATIENT:
            patient = Patient(patient_id=user.user_id)
            db.session.add(patient)

            # tạo healthrecord trống
            dao_healthrecord.create_empty_health_record(user.user_id)

        db.session.commit()
        return user

    except Exception as ex:
        db.session.rollback()
        print(f"Lỗi tạo user: {ex}")
        return None



def check_email_exists(email):
    return User.query.filter_by(email=email).first() is not None

def check_username_exists(username):
    return User.query.filter_by(username=username).first() is not None

def check_phone_exists(phone):
    return User.query.filter_by(phone_number=phone).first() is not None

def get_user_by_username(username):
    return User.query.filter_by(username=username).first()
