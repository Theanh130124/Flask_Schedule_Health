from app.models import User, RoleEnum, Patient
from app.extensions import db
from sqlalchemy import or_, and_
from datetime import datetime
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
