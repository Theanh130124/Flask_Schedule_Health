from app.models import db, Doctor, Hospital, Specialty, User, RoleEnum
from sqlalchemy import or_

def get_all_hospitals():
    # sắp xếp A→Z để tiện hiển thị
    return Hospital.query.order_by(Hospital.name.asc()).all()

def get_all_specialties():
    # sắp xếp A→Z để tiện hiển thị
    return Specialty.query.order_by(Specialty.name.asc()).all()

def search_doctors(hospital_name=None, specialty_name=None, doctor_name=None, limit=None):
    # JOIN 4 bảng & lọc đúng vai trò bác sĩ bằng Enum
    query = (db.session.query(Doctor)
             .join(User)        # Doctor.doctor_id -> User.user_id
             .join(Hospital)    # Doctor.hospital_id -> Hospital.hospital_id
             .join(Specialty)   # Doctor.specialty_id -> Specialty.specialty_id
             .filter(User.role == RoleEnum.DOCTOR))

    if hospital_name:
        query = query.filter(Hospital.name.ilike(f"%{hospital_name}%"))
    if specialty_name:
        query = query.filter(Specialty.name.ilike(f"%{specialty_name}%"))
    if doctor_name:
        # có thể gõ họ hoặc tên; muốn gõ "Nguyen Van" thì có thể gộp first + last
        query = query.filter(
            or_(
                User.first_name.ilike(f"%{doctor_name}%"),
                User.last_name.ilike(f"%{doctor_name}%"),
                (User.first_name + " " + User.last_name).ilike(f"%{doctor_name}%")  # bật nếu cần
            )
        )

    # sắp xếp theo tên, bỏ trùng, và (tùy chọn) giới hạn số dòng
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
            "rating": float(d.average_rating) if d.average_rating is not None else None
        })
    return results
