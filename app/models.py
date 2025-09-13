from datetime import datetime
import enum

from flask_login import UserMixin

from app.extensions import db
from flask_sqlalchemy import SQLAlchemy


# Base Model`
class BaseModel(db.Model):
    __abstract__ = True  # Không tạo bảng riêng

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.now,
        onupdate=datetime.now
    )

class DayOfWeekEnum(enum.Enum):
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"


# Enums
class RoleEnum(enum.Enum):
    PATIENT = "PATIENT"
    DOCTOR = "DOCTOR"
    ADMIN = "ADMIN"


class GenderEnum(enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class AppointmentStatus(enum.Enum):
    Scheduled = "Scheduled"
    Completed = "Completed"
    CancelledByPatient = "CancelledByPatient"
    CancelledByDoctor = "CancelledByDoctor"
    NoShow = "NoShow"

class PaymentMethodEnum(enum.Enum):
    MoMo = "MoMo"
    ZaloPay = "ZaloPay"

class ConsultationType(enum.Enum):
    Offline = "Offline"
    Online = "Online"


class InvoiceStatus(enum.Enum):
    Pending = "Pending"
    Paid = "Paid"
    Cancelled = "Cancelled"
    Overdue = "Overdue"


class PaymentStatus(enum.Enum):
    Pending = "Pending"
    Completed = "Completed"
    Failed = "Failed"
    Refunded = "Refunded"


# User
class User(BaseModel ,UserMixin):
    __tablename__ = 'user'

    user_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    address = db.Column(db.Text, nullable=False)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.Enum(GenderEnum))
    role = db.Column(db.Enum(RoleEnum), nullable=False)
    avatar = db.Column(
        db.String(255),
        default="https://res.cloudinary.com/dxiawzgnz/image/upload/v1732632586/pfvvxablnkaeqmmbqeit.png"
    )
    is_active = db.Column(db.Boolean, default=True)

    patient = db.relationship('Patient', lazy=True, backref='user', uselist=False)
    doctor = db.relationship('Doctor', lazy=True, backref='user', uselist=False)
    verified_licenses = db.relationship('DoctorLicense', backref='verified_by_admin')

    def get_id(self):
        return str(self.user_id) # Flask-Login cần id dạng string

# Specialty
class Specialty(db.Model):
    __tablename__ = 'specialty'

    specialty_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)




# Hospital
class Hospital(BaseModel):
    __tablename__ = 'hospital'

    hospital_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    address = db.Column(db.Text, nullable=False)
    phone_number = db.Column(db.String(20))
    accepts_insurance = db.Column(db.Boolean, default=False)


# Doctor
class Doctor(db.Model):
    __tablename__ = 'doctor'

    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey('user.user_id', ondelete='CASCADE'),
        primary_key=True
    )
    hospital_id = db.Column(
        db.Integer,
        db.ForeignKey('hospital.hospital_id', ondelete='RESTRICT'),
        nullable=False
    )
    specialty_id = db.Column(
        db.Integer,
        db.ForeignKey('specialty.specialty_id', ondelete='RESTRICT'),
        nullable=False
    )
    years_experience = db.Column(db.Integer, default=0)
    educational_level = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text)
    consultation_fee = db.Column(db.Numeric(10, 2), default=0.00)
    average_rating = db.Column(db.Numeric(3, 2), default=0.00)

    hospital = db.relationship('Hospital', backref='doctors')
    specialty = db.relationship('Specialty', backref='doctor')
    licenses = db.relationship('DoctorLicense', backref='doctor', cascade='all, delete')


# DoctorLicense
class DoctorLicense(BaseModel):
    __tablename__ = 'doctorlicense'

    license_id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey('doctor.doctor_id', ondelete='CASCADE'),
        nullable=False
    )
    license_number = db.Column(db.String(100), unique=True, nullable=False)
    issuing_authority = db.Column(db.String(255), nullable=False)
    issue_date = db.Column(db.Date, nullable=False)
    expiry_date = db.Column(db.Date)
    scope_description = db.Column(db.Text)
    is_verified = db.Column(db.Boolean, default=False)
    verification_date = db.Column(db.Date)
    verified_by_admin_id = db.Column(
        db.Integer,
        db.ForeignKey('user.user_id', ondelete='SET NULL')
    )


class DoctorAvailability(BaseModel):
    __tablename__ = 'doctoravailability'

    availability_id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey('doctor.doctor_id', ondelete='CASCADE'),
        nullable=False
    )
    day_of_week = db.Column(db.Enum(DayOfWeekEnum), nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    # Đảm bảo mỗi bác sĩ chỉ có một thiết lập cho mỗi ngày trong tuần
    __table_args__ = (
        db.UniqueConstraint('doctor_id', 'day_of_week', name='unique_doctor_day'),
    )


class AvailableSlot(BaseModel):
    __tablename__ = 'availableslot'

    slot_id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey('doctor.doctor_id', ondelete='CASCADE'),
        nullable=False
    )
    slot_date = db.Column(db.Date, nullable=False)
    is_booked = db.Column(db.Boolean, default=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    doctor = db.relationship('Doctor', backref='available_slots', lazy=True)
    # Để tối ưu hiệu suất truy vấn
    __table_args__ = (
        db.Index('idx_doctor_date', 'doctor_id', 'slot_date'),
        db.Index('idx_available_slots', 'doctor_id', 'slot_date', 'is_booked'),
    )
# Patient
class Patient(db.Model):
    __tablename__ = 'patient'

    patient_id = db.Column(
        db.Integer,
        db.ForeignKey('user.user_id', ondelete='CASCADE'),
        primary_key=True
    )
    medical_history_summary = db.Column(db.Text)

    appointments = db.relationship('Appointment', backref='patient', cascade='all, delete')
    health_records = db.relationship('HealthRecord', backref='patient', cascade='all, delete')


# Appointment
class Appointment(BaseModel):
    __tablename__ = 'appointment'

    appointment_id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(
        db.Integer,
        db.ForeignKey('patient.patient_id', ondelete='CASCADE'),
        nullable=False
    )
    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey('doctor.doctor_id', ondelete='CASCADE'),
        nullable=False
    )
    appointment_time = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, default=30)
    reason = db.Column(db.Text)
    status = db.Column(db.Enum(AppointmentStatus), default=AppointmentStatus.Scheduled)
    consultation_type = db.Column(db.Enum(ConsultationType), default=ConsultationType.Offline)
    cancellation_reason = db.Column(db.Text)

    invoice = db.relationship('Invoice', backref='appointment', uselist=False)
    health_record = db.relationship('HealthRecord', backref='appointment', uselist=False)
    doctor = db.relationship('Doctor')  # vẫn giữ nguyên vì không có đối ứng


# HealthRecord
class HealthRecord(BaseModel):
    __tablename__ = 'healthrecord'

    record_id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(
        db.Integer,
        db.ForeignKey('patient.patient_id', ondelete='CASCADE'),
        nullable=False
    )
    appointment_id = db.Column(
        db.Integer,
        db.ForeignKey('appointment.appointment_id', ondelete='SET NULL'),
        nullable=True
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.user_id', ondelete='SET NULL'),
        nullable=True
    )
    record_date = db.Column(db.Date, nullable=False)
    symptoms = db.Column(db.Text)
    diagnosis = db.Column(db.Text)
    prescription = db.Column(db.Text)
    notes = db.Column(db.Text)

    creator = db.relationship('User')


# Invoice
class Invoice(BaseModel):
    __tablename__ = 'invoice'

    invoice_id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(
        db.Integer,
        db.ForeignKey('appointment.appointment_id', ondelete='CASCADE'),
        nullable=False,
        unique=True
    )
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    issue_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.Date)
    status = db.Column(db.Enum(InvoiceStatus), default=InvoiceStatus.Pending)

    payment = db.relationship('Payment', backref='invoice', uselist=False)


# Payment
class Payment(db.Model):
    __tablename__ = 'payment'

    payment_id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(
        db.Integer,
        db.ForeignKey('invoice.invoice_id', ondelete='RESTRICT'),
        nullable=False,
        unique=True
    )
    amount_paid = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.Enum(PaymentMethodEnum), nullable=False)
    transaction_id = db.Column(db.String(255), unique=True)
    status = db.Column(db.Enum(PaymentStatus), default=PaymentStatus.Pending)
    payment_date = db.Column(db.DateTime, default=datetime.now)
    notes = db.Column(db.Text)




# Review
class Review(BaseModel):
    __tablename__ = 'review'

    review_id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(
        db.Integer,
        db.ForeignKey('appointment.appointment_id', ondelete='CASCADE'),
        nullable=False,
        unique=True
    )
    patient_id = db.Column(
        db.Integer,
        db.ForeignKey('patient.patient_id', ondelete='CASCADE'),
        nullable=False
    )
    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey('doctor.doctor_id', ondelete='CASCADE'),
        nullable=False
    )
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    review_date = db.Column(db.DateTime, default=datetime.utcnow)
    doctor_response = db.Column(db.Text)
    response_date = db.Column(db.DateTime)
    is_visible = db.Column(db.Boolean, default=True)

    appointment = db.relationship('Appointment')
    patient = db.relationship('Patient')
    doctor = db.relationship('Doctor')
