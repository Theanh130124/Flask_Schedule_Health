from app.models import HealthRecord
from app.extensions import db
from datetime import datetime

#Tạo HealthRecord rỗng cho bệnh nhân mới.
def create_empty_health_record(patient_id):

    record = HealthRecord(
        patient_id=patient_id,
        user_id=None,
        appointment_id=None,
        record_date=datetime.now(),
        symptoms=None,
        diagnosis=None,
        prescription=None,
        notes=None
    )
    db.session.add(record)
    return record

#Lấy danh sách HealthRecord của một bệnh nhân.
def get_records_by_patient(patient_id, limit=10):

    return (HealthRecord.query
            .filter(HealthRecord.patient_id == patient_id)
            .order_by(HealthRecord.record_date.desc())
            .limit(limit)
            .all())
def update_healthrecord(record_id, data: dict):
    record = HealthRecord.query.get(record_id)
    if not record:
        return None
    for key, value in data.items():
        if hasattr(record, key):
            setattr(record, key, value)
    db.session.commit()
    return record

def delete_healthrecord(record_id):
    record = HealthRecord.query.get(record_id)
    if not record:
        return False
    db.session.delete(record)
    db.session.commit()
    return True
