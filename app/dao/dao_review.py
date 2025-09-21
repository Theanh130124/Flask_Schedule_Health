# app/dao/dao_review.py
from datetime import datetime
from sqlalchemy import func
from app.extensions import db
from app.models import Review, Appointment, AppointmentStatus, Doctor

__all__ = ["add_review", "update_review", "delete_review", "doctor_reply", "_recompute_avg"]

def add_review(*, appointment_id: int, patient_id: int, doctor_id: int, rating: int, comment: str):
    appt = (Appointment.query
            .filter_by(appointment_id=appointment_id,
                       patient_id=patient_id,
                       doctor_id=doctor_id,
                       status=AppointmentStatus.Completed)
            .first())
    if not appt:
        return None, "Chỉ được đánh giá sau khi bạn đã khám xong bác sĩ này.",
    if Review.query.filter_by(appointment_id=appointment_id).first():
        return None, "Lịch hẹn này đã có đánh giá rồi.",
    rv = Review(
        appointment_id=appointment_id,
        patient_id=patient_id,
        doctor_id=doctor_id,
        rating=rating,
        comment=(comment or "").strip()
    )
    db.session.add(rv)
    db.session.flush()
    _recompute_avg(doctor_id)
    db.session.commit()
    return rv, "Đánh giá đã được gửi!"

def _recompute_avg(doctor_id: int):
    avg = (db.session.query(func.avg(Review.rating))
           .filter(Review.doctor_id == doctor_id, Review.is_visible == True)
           .scalar()) or 0
    doc = Doctor.query.get(doctor_id)
    if doc:
        doc.average_rating = round(float(avg), 2)

def update_review(*, review_id: int, patient_id: int, rating: int, comment: str):
    rv = Review.query.filter_by(review_id=review_id, patient_id=patient_id).first()
    if not rv:
        return None, "Bạn không có quyền sửa đánh giá này."
    # CHẶN: chỉ cho phép sửa 1 lần duy nhất
    if getattr(rv, "updated_at", None):
        return None, "Bạn chỉ được sửa đánh giá một lần."

    if not isinstance(rating, int) or not (1 <= rating <= 5):
        return None, "Điểm đánh giá phải từ 1 đến 5."

    rv.rating = rating
    rv.comment = (comment or "").strip()
    rv.updated_at = datetime.utcnow()
    db.session.flush()
    _recompute_avg(rv.doctor_id)
    db.session.commit()
    return rv, "Lưu thay đổi thành công!"

def delete_review(*, review_id: int, patient_id: int):
    rv = Review.query.filter_by(review_id=review_id, patient_id=patient_id).first()
    if not rv:
        return None, "Bạn không có quyền xóa đánh giá này.", None
    doctor_id = rv.doctor_id
    db.session.delete(rv)
    db.session.flush()
    _recompute_avg(doctor_id)
    db.session.commit()
    return True, "Đã xóa đánh giá.", doctor_id

def doctor_reply(review_id: int, doctor_id: int, response_text: str):
    rv = Review.query.filter_by(review_id=review_id, doctor_id=doctor_id).first()
    if not rv:
        return None, "Không tìm thấy review thuộc về bạn.", None

    txt = (response_text or "").strip()
    if not txt:
        return None, "Nội dung phản hồi không được để trống.", rv.doctor_id

    # Quy ước:
    # - Chưa có phản hồi: tạo mới (set response_date)
    # - ĐÃ có phản hồi:
    #     + Nếu đã từng sửa (response_updated_at có giá trị) -> từ chối
    #     + Nếu chưa sửa -> cho sửa lần DUY NHẤT (set response_updated_at)
    if rv.doctor_response is None:
        rv.doctor_response = txt
        rv.response_date = datetime.utcnow()
    else:
        if getattr(rv, "response_updated_at", None):  # đã sửa 1 lần
            return None, "Bạn đã sửa phản hồi một lần rồi. Không thể sửa thêm.", rv.doctor_id
        rv.doctor_response = txt
        # giữ nguyên response_date là lần tạo đầu, và đánh dấu lần sửa duy nhất:
        rv.response_updated_at = datetime.utcnow()

    db.session.commit()
    return rv, "Đã lưu phản hồi.", rv.doctor_id
