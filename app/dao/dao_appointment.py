
from app import db
from app.models import AvailableSlot, Appointment, AppointmentStatus, Invoice, InvoiceStatus, Payment, PaymentStatus, \
    ConsultationType
from datetime import datetime


#Đặt lịch
def book_appointment(patient_id, slot_id, reason, consultation_type=ConsultationType.Offline):
    try:
        # Lấy thông tin slot
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
        db.session.flush()  # Lấy ID của appointment
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

        # Cập nhật trạng thái
        if cancelled_by_patient:
            appointment.status = AppointmentStatus.CancelledByPatient
        else:
            appointment.status = AppointmentStatus.CancelledByDoctor

        appointment.cancellation_reason = reason

        # Cập nhật invoice status
        if appointment.invoice:
            appointment.invoice.status = InvoiceStatus.Cancelled

        db.session.commit()
        return True, "Hủy lịch hẹn thành công"

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