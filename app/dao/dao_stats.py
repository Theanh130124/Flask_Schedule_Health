from sqlalchemy import func, extract, case
from app.models import Appointment, Invoice, AppointmentStatus, Doctor, User, Specialty, Review
from app.extensions import db
from datetime import datetime


def get_appointment_stats(year=None, quarter=None, month=None, doctor_id=None):
    """
    Thống kê số lượt khám và doanh thu theo bác sĩ
    """
    query = db.session.query(
        Appointment.doctor_id,
        User.first_name,
        User.last_name,
        Specialty.name.label('specialty_name'),
        func.count(Appointment.appointment_id).label('appointment_count'),
        func.sum(Invoice.amount).label('total_revenue'),
        func.avg(Review.rating).label('average_rating')
    ).join(
        Doctor, Appointment.doctor_id == Doctor.doctor_id
    ).join(
        User, Doctor.doctor_id == User.user_id
    ).join(
        Specialty, Doctor.specialty_id == Specialty.specialty_id
    ).join(
        Invoice, Appointment.appointment_id == Invoice.appointment_id
    ).outerjoin(
        Review, Appointment.appointment_id == Review.appointment_id
    ).filter(
        Appointment.status == AppointmentStatus.Completed
    )

    # Áp dụng các bộ lọc thời gian
    if year:
        query = query.filter(extract('year', Appointment.appointment_time) == year)

        if quarter:
            query = query.filter(extract('quarter', Appointment.appointment_time) == quarter)

        if month:
            query = query.filter(extract('month', Appointment.appointment_time) == month)

    if doctor_id:
        query = query.filter(Appointment.doctor_id == doctor_id)

    # Nhóm theo bác sĩ
    query = query.group_by(
        Appointment.doctor_id,
        User.first_name,
        User.last_name,
        Specialty.name
    )

    return query.all()

def get_revenue_by_time_period(year=None, quarter=None, month=None):
    """
    Thống kê doanh thu theo khoảng thời gian
    """
    # Xác định SELECT fields và GROUP BY fields
    select_fields = [
        extract('year', Appointment.appointment_time).label('year')
    ]
    group_by_fields = [extract('year', Appointment.appointment_time)]
    order_by_fields = [extract('year', Appointment.appointment_time)]

    if year and month:
        select_fields.append(extract('month', Appointment.appointment_time).label('month'))
        group_by_fields.append(extract('month', Appointment.appointment_time))
        order_by_fields.append(extract('month', Appointment.appointment_time))

    elif year and quarter:
        select_fields.append(extract('quarter', Appointment.appointment_time).label('quarter'))
        group_by_fields.append(extract('quarter', Appointment.appointment_time))
        order_by_fields.append(extract('quarter', Appointment.appointment_time))

    # Truy vấn
    query = db.session.query(
        *select_fields,
        func.count(Appointment.appointment_id).label('appointment_count'),
        func.sum(Invoice.amount).label('total_revenue')
    ).join(
        Invoice, Appointment.appointment_id == Invoice.appointment_id
    ).filter(
        Appointment.status == AppointmentStatus.Completed
    )

    # Áp dụng filter
    if year:
        query = query.filter(extract('year', Appointment.appointment_time) == year)

        if quarter:
            query = query.filter(extract('quarter', Appointment.appointment_time) == quarter)

        if month:
            query = query.filter(extract('month', Appointment.appointment_time) == month)

    # Nhóm và sắp xếp
    query = query.group_by(*group_by_fields).order_by(*order_by_fields)

    return query.all()