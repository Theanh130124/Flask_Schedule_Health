from datetime import datetime
from app.models import AvailableSlot, Doctor, User, Hospital, Specialty
from app.extensions import db
from sqlalchemy import desc


#Lấy tất cả slot khả dụng với thời gian lớn hơn hiện tại

def get_available_slots():
    now = datetime.now()
    current_date = now.date()
    current_time = now.time()
    available_slots = (AvailableSlot.query
                       .join(Doctor, AvailableSlot.doctor_id == Doctor.doctor_id)
                       .join(User, Doctor.doctor_id == User.user_id)
                       .join(Hospital, Doctor.hospital_id == Hospital.hospital_id)
                       .join(Specialty, Doctor.specialty_id == Specialty.specialty_id)
                       .filter(AvailableSlot.is_booked == 0)
                       .filter(
        (AvailableSlot.slot_date > current_date) |
        ((AvailableSlot.slot_date == current_date) &
         (AvailableSlot.start_time > current_time))
    )
                       .order_by(desc(AvailableSlot.slot_date), AvailableSlot.start_time)  # <--- thay đổi ở đây
                       .all())

    return available_slots

def get_available_slots_by_filters(hospital_id=None, specialty_id=None, doctor_id=None, date=None):
    now = datetime.now()
    current_date = now.date()
    current_time = now.time()
    query = (AvailableSlot.query
             .join(Doctor, AvailableSlot.doctor_id == Doctor.doctor_id)
             .join(User, Doctor.doctor_id == User.user_id)
             .join(Hospital, Doctor.hospital_id == Hospital.hospital_id)
             .join(Specialty, Doctor.specialty_id == Specialty.specialty_id)
             .filter(AvailableSlot.is_booked == 0)
             .filter(
                 (AvailableSlot.slot_date > current_date) |
                 ((AvailableSlot.slot_date == current_date) &
                  (AvailableSlot.start_time > current_time))
             ))
    if hospital_id:
        query = query.filter(Doctor.hospital_id == hospital_id)
    if specialty_id:
        query = query.filter(Doctor.specialty_id == specialty_id)
    if doctor_id:
        query = query.filter(Doctor.doctor_id == doctor_id)
    if date:
        query = query.filter(AvailableSlot.slot_date == date)

    return query.order_by(desc(AvailableSlot.slot_date), desc(AvailableSlot.start_time))


def get_available_slots_by_filters_paginated(hospital_id=None, specialty_id=None, doctor_id=None, date=None, page=1,
                                             per_page=6):
    now = datetime.now()
    current_date = now.date()
    current_time = now.time()

    query = (AvailableSlot.query
    .join(Doctor, AvailableSlot.doctor_id == Doctor.doctor_id)
    .join(User, Doctor.doctor_id == User.user_id)
    .join(Hospital, Doctor.hospital_id == Hospital.hospital_id)
    .join(Specialty, Doctor.specialty_id == Specialty.specialty_id)
    .filter(AvailableSlot.is_booked == 0)
    .filter(
        (AvailableSlot.slot_date > current_date) |
        ((AvailableSlot.slot_date == current_date) &
         (AvailableSlot.start_time > current_time))
    ))

    if hospital_id:
        query = query.filter(Doctor.hospital_id == hospital_id)
    if specialty_id:
        query = query.filter(Doctor.specialty_id == specialty_id)
    if doctor_id:
        query = query.filter(Doctor.doctor_id == doctor_id)
    if date:
        query = query.filter(AvailableSlot.slot_date == date)

    # Phân trang
    return query.order_by(desc(AvailableSlot.slot_date), desc(AvailableSlot.start_time)) \
        .offset((page - 1) * per_page) \
        .limit(per_page) \
        .all()


def count_available_slots_by_filters(hospital_id=None, specialty_id=None, doctor_id=None, date=None):
    now = datetime.now()
    current_date = now.date()
    current_time = now.time()

    query = (AvailableSlot.query
    .join(Doctor, AvailableSlot.doctor_id == Doctor.doctor_id)
    .filter(AvailableSlot.is_booked == 0)
    .filter(
        (AvailableSlot.slot_date > current_date) |
        ((AvailableSlot.slot_date == current_date) &
         (AvailableSlot.start_time > current_time))
    ))

    if hospital_id:
        query = query.filter(Doctor.hospital_id == hospital_id)
    if specialty_id:
        query = query.filter(Doctor.specialty_id == specialty_id)
    if doctor_id:
        query = query.filter(Doctor.doctor_id == doctor_id)
    if date:
        query = query.filter(AvailableSlot.slot_date == date)

    return query.count()