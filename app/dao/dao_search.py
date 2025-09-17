from app.models import db, Doctor, Hospital, Specialty, User, RoleEnum
from sqlalchemy import or_,func

def search_doctors(hospital_name=None, specialty_name=None, doctor_name=None,
                   limit=None, hospital_accepts_insurance=None):
    query = (db.session.query(Doctor)
             .join(User)
             .join(Hospital)
             .join(Specialty)
             .filter(User.role == RoleEnum.DOCTOR))

    if hospital_name:
        query = query.filter(Hospital.name.ilike(f"%{hospital_name}%"))
    if specialty_name:
        query = query.filter(Specialty.name.ilike(f"%{specialty_name}%"))
    if doctor_name:
        full_name = func.concat(User.first_name, " ", User.last_name)
        query = query.filter(or_(
            User.first_name.ilike(f"%{doctor_name}%"),
            User.last_name.ilike(f"%{doctor_name}%"),
            full_name.ilike(f"%{doctor_name}%")
        ))

  
    if hospital_accepts_insurance is True:
        query = query.filter(Hospital.accepts_insurance.is_(True))
    elif hospital_accepts_insurance is False:
        query = query.filter(Hospital.accepts_insurance.is_(False))

    query = query.order_by(User.first_name.asc(), User.last_name.asc())
    if limit:
        query = query.limit(limit)

    doctors = query.all()
    results = []
    for d in doctors:
        results.append({
            "doctor_id": d.doctor_id,
            "name": f"{d.user.first_name} {d.user.last_name}",
            "hospital": d.hospital.name,
            "specialty": d.specialty.name,
            "experience": d.years_experience,
            "consultation_fee": float(d.consultation_fee) if d.consultation_fee is not None else None,
            "rating": float(d.average_rating) if d.average_rating is not None else None,
            "avatar": d.user.avatar,
            "accepts_insurance": bool(d.hospital.accepts_insurance),
        })
    return results

