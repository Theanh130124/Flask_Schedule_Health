
from app import db
from app.models import Appointment, AppointmentStatus, Invoice, InvoiceStatus, Payment, PaymentStatus, \
    ConsultationType
from datetime import datetime


#Đặt lịch

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




def get_patient_appointment(patient_id):
    """
    Lấy danh sách các lịch hẹn của 1 bệnh nhân.
    """
    return (Appointment.query
            .filter(Appointment.patient_id == patient_id)
            .order_by(Appointment.appointment_time.desc())
            .all())
