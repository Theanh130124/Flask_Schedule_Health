from flask_mail import Message
from flask import render_template, current_app
from app.extensions import mail
from app.dao import dao_user, dao_doctor , dao_appointment

def send_email(to, subject, template, **kwargs):
    """
    Gửi email với template HTML
    """
    try:
        msg = Message(
            subject=subject,
            sender=current_app.config['MAIL_USERNAME'],
            recipients=[to]
        )
        msg.html = render_template(template, **kwargs)
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Lỗi gửi email: {str(e)}")
        return False


def send_appointment_notification(appointment, action):
    """
    Gửi thông báo lịch hẹn cho cả bác sĩ và bệnh nhân
    action: 'booking', 'cancellation', 'reschedule'
    """


    # Lấy thông tin bệnh nhân
    patient = dao_appointment.get_info_by_id(appointment.patient_id)
    patient_email = patient.email
    patient_name = f"{patient.first_name} {patient.last_name}"

    # Lấy thông tin bác sĩ
    doctor_user = dao_appointment.get_info_by_id(appointment.doctor_id)
    doctor_email = doctor_user.email
    doctor_name = f"{doctor_user.first_name} {doctor_user.last_name}"

    # Lấy thông tin bệnh viện
    doctor = dao_appointment.get_doctor_by_userid(appointment.doctor_id)
    hospital_name = doctor.hospital.name if doctor and doctor.hospital else "Không xác định"

    # Template mapping
    templates = {
        'booking': 'email/appointment_booking.html',
        'cancellation': 'email/appointment_cancellation.html',
        'reschedule': 'email/appointment_reschedule.html'
    }

    subjects = {
        'booking': 'Xác nhận đặt lịch hẹn thành công',
        'cancellation': 'Thông báo hủy lịch hẹn',
        'reschedule': 'Thông báo thay đổi lịch hẹn'
    }

    template = templates.get(action)
    subject = subjects.get(action)

    if not template:
        return False

    # Dữ liệu chung cho template
    template_data = {
        'appointment': appointment,
        'doctor_name': doctor_name,
        'patient_name': patient_name,
        'hospital_name': hospital_name
    }

    # Gửi cho bệnh nhân
    send_email(
        to=patient_email,
        subject=f"{subject} - #{appointment.appointment_id}",
        template=template,
        recipient_name=patient_name,
        **template_data
    )

    # Gửi cho bác sĩ
    send_email(
        to=doctor_email,
        subject=f"{subject} - #{appointment.appointment_id}",
        template=template,
        recipient_name=doctor_name,
        **template_data
    )

    return True