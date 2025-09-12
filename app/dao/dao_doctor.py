from app.extensions import db
from app.models import User, Doctor, DoctorAvailability, DayOfWeekEnum


def get_list_doctor():
    Doctor.query.join(User).order_by(User.first_name, User.last_name).all()

def create_doctor_availability(doctor_id, day_of_week, start_time, end_time, is_available=True):
    # Kiểm tra xem đã có lịch cho ngày này chưa
    existing = DoctorAvailability.query.filter_by(
        doctor_id=doctor_id,
        day_of_week=DayOfWeekEnum[day_of_week]
    ).first()
    if existing:
        # Cập nhật nếu đã tồn tại
        existing.start_time = start_time
        existing.end_time = end_time
        existing.is_available = is_available
    else:
        # Tạo mới nếu chưa tồn tại
        availability = DoctorAvailability(
            doctor_id=doctor_id,
            day_of_week=DayOfWeekEnum[day_of_week],
            start_time=start_time,
            end_time=end_time,
            is_available=is_available
        )
        db.session.add(availability)
    db.session.commit()
    return True

#Lấy tất cả lịch làm của bác sĩ
def get_doctor_availabilities(doctor_id):
    return DoctorAvailability.query.filter_by(doctor_id=doctor_id).all()

#Lấy lịch làm bs theo ngày
def get_doctor_availability_by_day(doctor_id, day_of_week):
    return DoctorAvailability.query.filter_by(
        doctor_id=doctor_id,
        day_of_week=DayOfWeekEnum[day_of_week]
    ).first()