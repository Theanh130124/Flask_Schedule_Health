from app.models import User, RoleEnum, Patient, Appointment
from app.extensions import db
from sqlalchemy import or_, and_
from datetime import datetime, date
from .dao_healthrecord import get_records_by_patient
from sqlalchemy.orm import joinedload


# ---------------- READ ----------------
def get_all_patients(limit=50, offset=0):
    return (db.session.query(User, Patient)
            .join(Patient, Patient.patient_id == User.user_id)
            .filter(User.role == RoleEnum.PATIENT)
            .order_by(User.last_name.asc(), User.first_name.asc())
            .offset(offset)
            .limit(limit)
            .all())


def search_patient(q=None, active=None, inactive=None, date_from=None, date_to=None,
                   limit=50, offset=0):
    query = (db.session.query(User, Patient)
             .join(Patient, Patient.patient_id == User.user_id)
             .filter(User.role == RoleEnum.PATIENT))

    if q:
        q = q.strip()
        query = query.filter(
            or_(
                User.first_name.ilike(f"%{q}%"),
                User.last_name.ilike(f"%{q}%"),
                User.username.ilike(f"%{q}%"),
                User.email.ilike(f"%{q}%"),
                User.phone_number.ilike(f"%{q}%"),
                Patient.medical_history_summary.ilike(f"%{q}%")
            )
        )

    if active and not inactive:
        query = query.filter(User.is_active == True)
    elif inactive and not active:
        query = query.filter(User.is_active == False)

    if date_from and date_to:
        query = query.filter(
            and_(
                User.created_at >= date_from,
                User.created_at <= date_to
            )
        )

    return (query.order_by(User.last_name.asc(), User.first_name.asc())
            .offset(offset)
            .limit(limit)
            .all())


def get_patient_by_id(patient_id: int):
    return (User.query
            .options(joinedload(User.patient))
            .filter(User.user_id == patient_id, User.role == RoleEnum.PATIENT)
            .first())


def count_patient():
    return User.query.filter(User.role == RoleEnum.PATIENT).count()


# ---------------- UPDATE ----------------
def update_patient(patient_id: int, user_data=None, patient_data=None):
    user = User.query.filter_by(user_id=patient_id, role=RoleEnum.PATIENT).first()
    patient = Patient.query.filter_by(patient_id=patient_id).first()

    if not user or not patient:
        return None

    if user_data:
        for key, value in user_data.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)
        user.updated_at = datetime.now()

    if patient_data:
        for key, value in patient_data.items():
            if hasattr(patient, key) and value is not None:
                setattr(patient, key, value)

    db.session.commit()
    return user, patient


# ---------------- DELETE ----------------
def delete_patient(patient_id: int):
    user = User.query.filter_by(user_id=patient_id, role=RoleEnum.PATIENT).first()
    patient = Patient.query.filter_by(patient_id=patient_id).first()

    if not user:
        return False

    if patient:
        db.session.delete(patient)
    db.session.delete(user)
    db.session.commit()
    return True


def get_patient_with_records(patient_id, limit=10):
    user = (User.query
            .options(joinedload(User.patient))
            .filter(User.user_id == patient_id, User.role == RoleEnum.PATIENT)
            .first())
    if not user:
        return None

    records = get_records_by_patient(patient_id, limit=limit)
    return user, records


# kiểm tra bác sĩ có quyền truy cập vào bệnh nhân hay không
def has_doctor_with_patient(doctor_id, patient_id):
    return db.session.query(  # Sửa sesion → session
        Appointment.query.filter(
            Appointment.doctor_id == doctor_id,
            Appointment.patient_id == patient_id
        ).exists()
    ).scalar()


# lấy danh sách của bệnh nhân có lịch khám với bác sĩ
def get_patients_by_doctor(doctor_id, page=1, per_page=50, filters=None):
    query = (db.session.query(User)
             .join(Patient, Patient.patient_id == User.user_id)
             .join(Appointment, Appointment.patient_id == Patient.patient_id)
             .filter(
        User.role == RoleEnum.PATIENT,
        Appointment.doctor_id == doctor_id
    )
             .distinct())

    # có áp dụng filter
    if filters:
        if filters.get('q'):
            q = filters['q']
            query = query.filter(  # Sửa filters → filter
                or_(
                    User.first_name.ilike(f"%{q}%"),
                    User.last_name.ilike(f"%{q}%"),
                    User.username.ilike(f"%{q}%"),
                    User.email.ilike(f"%{q}%"),
                    User.phone_number.ilike(f"%{q}%"),
                    Patient.medical_history_summary.ilike(f"%{q}%")
                )
            )
        if filters.get('phone'):
            query = query.filter(User.phone_number.ilike(f"%{filters['phone']}%"))

        # Lọc theo trạng thái active/inactive
        active = filters.get('active')
        inactive = filters.get('inactive')
        if active == "1" and inactive != "1":
            query = query.filter(User.is_active == True)
        elif inactive == "1" and active != "1":
            query = query.filter(User.is_active == False)

    # Đếm tổng số bệnh nhân
    total = query.count()

    # Phân trang
    patients = (query.order_by(User.last_name.asc(), User.first_name.asc())
                .offset((page - 1) * per_page)
                .limit(per_page)
                .all())

    return patients, total  # Thêm return


# tính số tuổi của bệnh nhân
def calculate_age(date_of_birth):
    if not date_of_birth:
        return None

    today = date.today()
    return today.year - date_of_birth.year - (
            (today.month, today.day) < (date_of_birth.month, date_of_birth.day)
    )


# lấy ngày bênh nhân khám gần nhất ( giao diện bác sĩ )
def get_last_visit_date(patient_id, doctor_id):
    last_appointment = (Appointment.query
                        .filter_by(
        patient_id=patient_id,
        doctor_id=doctor_id
    )
                        .order_by(Appointment.appointment_time.desc())
                        .first())
    return last_appointment.appointment_time if last_appointment else None  # Thêm return


# lấy số lượng theo trạng thái
def get_appointment_status_count(patient_id, doctor_id):
    status_count = (db.session.query(
        Appointment.status,
        db.func.count(Appointment.appointment_id)
    )
                    .filter_by(
        patient_id=patient_id,
        doctor_id=doctor_id
    )
                    .group_by(Appointment.status)
                    .all())
    return {status.name: count for status, count in status_count}


# Lấy danh sách theo trạng thái lọc theo lịch hẹn
def get_patients_by_doctor_with_status_filter(doctor_id, status_filter=None, page=1, per_page=50, filters=None):


    if status_filter:
        subquery = (db.session.query(Appointment.patient_id)
                    .filter(
            Appointment.doctor_id == doctor_id,
            Appointment.status == status_filter
        )
                    .distinct()
                    .subquery())

        query = (db.session.query(User)
                 .join(Patient, Patient.patient_id == User.user_id)
                 .filter(User.user_id.in_(subquery)))
    else:
        # Lấy tất cả bệnh nhân có appointment với bác sĩ
        query = (db.session.query(User)
                 .join(Patient, Patient.patient_id == User.user_id)
                 .join(Appointment, Appointment.patient_id == Patient.patient_id)
                 .filter(
            User.role == RoleEnum.PATIENT,
            Appointment.doctor_id == doctor_id
        )
                 .distinct())

    # Áp dụng filters
    if filters:
        if filters.get('q'):
            q = filters['q']
            query = query.filter(
                or_(
                    User.first_name.ilike(f"%{q}%"),
                    User.last_name.ilike(f"%{q}%"),
                    User.phone_number.ilike(f"%{q}%")
                )
            )
        if filters.get('phone'):
            query = query.filter(User.phone_number.ilike(f"%{filters['phone']}%"))

        active = filters.get('active')
        inactive = filters.get('inactive')
        if active == "1" and inactive != "1":
            query = query.filter(User.is_active == True)
        elif inactive == "1" and active != "1":
            query = query.filter(User.is_active == False)

    total = query.count()
    patients = (query.order_by(User.last_name.asc(), User.first_name.asc())
                .offset((page - 1) * per_page)
                .limit(per_page)
                .all())

    return patients, total