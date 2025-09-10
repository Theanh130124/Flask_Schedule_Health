from app.models import User, Doctor


def get_list_doctor():
    Doctor.query.join(User).order_by(User.first_name, User.last_name).all()

