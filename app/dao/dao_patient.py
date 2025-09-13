from app.models import User, RoleEnum
from app.extensions import db
from sqlalchemy import or_, and_


#lấy toàn bộ thông tin bệnh nhân
def get_all_patients(limit=50, offset=0):
    return (User.query
            .filter(User.role == RoleEnum.PATIENT)
            .order_by(User.last_name.asc(), User.first_name)
            .offset(offset)
            .limit(limit)
            .all())
def search_patient(q=None, active=None,inactive = None, date_from=None, date_to=None,
                   limit=50, offset=0):
    """
       Tìm kiếm bệnh nhân theo nhiều tiêu chí:
       - q: từ khóa (tìm trong tên, username, phone, email)
       - active/inactive: lọc theo trạng thái
       - date_from/date_to: lọc theo ngày đăng ký
       """
    query=User.query.filter(User.role == RoleEnum.PATIENT)

    # tìm kiếm chung
    if q:
        q= q.strip()
        query= query.filter(
            or_(
                User.first_name.ilike(f"{q}%"),
                User.last_name.ilike(f"{q}%"),
                User.username.ilike(f"{q}%"),
                User.email.ilike(f"{q}%"),
                User.phone_number.ilike(f"{q}%")
            )
        )
    # lọc trạng thái
    if active and not inactive:
        query=query.filter(User.is_active==True)
    elif inactive and not active:
        query=query.filter(User.is_active==False)

    #lọc ngày đăng ký
    if date_from and date_to:
        query=query.filter(
            and_(
                User.created_at>=date_from,
                User.created_at<=date_to
            )
        )

    return (query.order_by(User.last_name.asc(), User.first_name.asc())
            .offset(offset)
            .limit(limit)
            .all())

def get_patient_by_id(patient_id):
    return User.query.filter_by(id=patient_id, role=RoleEnum).first()

# tổng bệnh nhân có trong hệ thống
def count_patient():
    return User.query.filter(User.role==RoleEnum.PATIENT).count()