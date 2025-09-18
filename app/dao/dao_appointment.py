
from app import db
from app.models import AvailableSlot, Appointment, AppointmentStatus, Invoice, InvoiceStatus, Payment, PaymentStatus, \
    ConsultationType
from datetime import datetime


#Đặt lịch
def book_appointment(patient_id, slot_id, reason, consultation_type=ConsultationType.Offline):
    try:
        slot = AvailableSlot.query.get(slot_id)
        if not slot:
            return None, "Slot không tồn tại"

        if slot.is_booked:
            return None, "Slot đã được đặt"

        # Tạo appointment
        appointment = Appointment(
            patient_id=patient_id,
            doctor_id=slot.doctor_id,
            appointment_time=datetime.combine(slot.slot_date, slot.start_time),
            duration_minutes=(slot.end_time.hour * 60 + slot.end_time.minute) -
                             (slot.start_time.hour * 60 + slot.start_time.minute),
            reason=reason,
            consultation_type=consultation_type,
            status=AppointmentStatus.Scheduled
        )
        db.session.add(appointment)
        db.session.flush()

        # Tạo invoice
        invoice = Invoice(
            appointment_id=appointment.appointment_id,
            amount=slot.doctor.consultation_fee,
            issue_date=datetime.now(),
            due_date=slot.slot_date,
            status=InvoiceStatus.Pending
        )
        db.session.add(invoice)

        # Đánh dấu slot đã được đặt
        slot.is_booked = True
        db.session.commit()
        return appointment, "Đặt lịch thành công"
    except Exception as e:
        db.session.rollback()
        return None, f"Lỗi khi đặt lịch: {str(e)}"

def get_appointment_by_id(appointment_id):
    return Appointment.query.get(appointment_id)


def get_patient_appointments(patient_id):
    return (Appointment.query
                .filter_by(patient_id=patient_id)
                .order_by(Appointment.appointment_time.desc())
                .all())
def get_doctor_appointments(doctor_id):
        return (Appointment.query
                .filter_by(doctor_id=doctor_id)
                .order_by(Appointment.appointment_time.desc())
                .all())

#Hủy lịch
def cancel_appointment(appointment_id, reason, cancelled_by_patient=True):
    try:
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return False, "Lịch hẹn không tồn tại"

        # Kiểm tra thời gian hủy (trước 24 giờ so với giờ hẹn)
        current_time = datetime.now()
        appointment_time = appointment.appointment_time
        time_difference = appointment_time - current_time

        # Nếu thời gian từ hiện tại đến cuộc hẹn ít hơn 24 giờ
        if time_difference.total_seconds() < 24 * 3600:
            return False, "Chỉ có thể hủy lịch hẹn trước 24 giờ"

        # QUAN TRỌNG: Tìm slot dựa trên thời gian và bác sĩ
        slot_date = appointment.appointment_time.date()
        start_time = appointment.appointment_time.time()

        # Tìm slot khớp với thông tin appointment
        slot = AvailableSlot.query.filter_by(
            doctor_id=appointment.doctor_id,
            slot_date=slot_date,
            start_time=start_time,
            is_booked=True  # Chỉ tìm những slot đã được đặt
        ).first()

        if slot:
            slot.is_booked = False  # Đặt lại trạng thái slot về chưa đặt
            db.session.add(slot)
            slot_found = True
        else:
            slot_found = False

        # Cập nhật trạng thái appointment
        if cancelled_by_patient:
            appointment.status = AppointmentStatus.CancelledByPatient
        else:
            appointment.status = AppointmentStatus.CancelledByDoctor

        appointment.cancellation_reason = reason

        # Cập nhật invoice status nếu có
        if appointment.invoice:
            appointment.invoice.status = InvoiceStatus.Cancelled

        db.session.commit()

        if slot_found:
            return True, "Hủy lịch hẹn thành công và slot đã được mở lại"
        else:
            return True, "Hủy lịch hẹn thành công (không tìm thấy slot liên quan)"

    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi hủy lịch hẹn: {str(e)}"

def complete_appointment(appointment_id):
    try:
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return False, "Lịch hẹn không tồn tại"

        appointment.status = AppointmentStatus.Completed
        db.session.commit()
        return True, "Cập nhật trạng thái thành công"

    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi cập nhật trạng thái: {str(e)}"

<<<<<<< HEAD
# ------------------sử lý với role DOCTOR ---------------------
#
=======

def reschedule_appointment(appointment_id, new_slot_id, reason=None):
    try:
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return False, "Lịch hẹn không tồn tại"

        # Kiểm tra thời gian sửa (trước 24 giờ so với giờ hẹn)
        current_time = datetime.now()
        appointment_time = appointment.appointment_time
        time_difference = appointment_time - current_time

        # Nếu thời gian từ hiện tại đến cuộc hẹn ít hơn 24 giờ
        if time_difference.total_seconds() < 24 * 3600:
            return False, "Chỉ có thể sửa lịch hẹn trước 24 giờ"

        # Kiểm tra slot mới
        new_slot = AvailableSlot.query.get(new_slot_id)
        if not new_slot:
            return False, "Slot mới không tồn tại"

        if new_slot.is_booked:
            return False, "Slot mới đã được đặt"

        # Tìm slot cũ dựa trên thời gian và bác sĩ
        old_slot_date = appointment.appointment_time.date()
        old_start_time = appointment.appointment_time.time()

        # Tìm slot cũ khớp với thông tin appointment
        old_slot = AvailableSlot.query.filter_by(
            doctor_id=appointment.doctor_id,
            slot_date=old_slot_date,
            start_time=old_start_time,
            is_booked=True
        ).first()

        # Cập nhật thông tin appointment
        appointment.doctor_id = new_slot.doctor_id
        appointment.appointment_time = datetime.combine(new_slot.slot_date, new_slot.start_time)
        appointment.duration_minutes = (new_slot.end_time.hour * 60 + new_slot.end_time.minute) - \
                                       (new_slot.start_time.hour * 60 + new_slot.start_time.minute)

        if reason:
            appointment.reason = reason

        # Cập nhật trạng thái slot
        if old_slot:
            old_slot.is_booked = False  # Mở lại slot cũ

        new_slot.is_booked = True  # Đặt slot mới

        db.session.commit()
        return True, "Sửa lịch hẹn thành công"

    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi sửa lịch hẹn: {str(e)}"
>>>>>>> ed3d74782b899ea7888b2510c792dff09926ee2b
