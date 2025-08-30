from flask_login import logout_user, current_user
from flask_admin.contrib.sqla import ModelView
from flask_admin import expose, BaseView, Admin
from app.models import (
    RoleEnum, User, Specialty, Hospital, Doctor, DoctorLicense,
    Patient, Appointment, HealthRecord, Invoice, Payment, Review
)
from app.extensions import db
from app import app
from flask import redirect, request
import hashlib
from datetime import datetime


# Base class for authenticated views
class AuthenticatedView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == RoleEnum.ADMIN


# Logout view
class LogoutView(BaseView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect('/admin')

    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == RoleEnum.ADMIN


# Login redirect view
class LoginUserView(BaseView):
    @expose('/')
    def index(self):
        return redirect('/login')

    def is_accessible(self):
        return not current_user.is_authenticated


# User management view
class UserView(AuthenticatedView):
    column_list = [
        'username', 'email', 'first_name', 'last_name', 'phone_number',
        'address', 'date_of_birth', 'gender', 'role', 'is_active'
    ]

    column_labels = {
        'username': 'Tên đăng nhập',
        'email': 'Email',
        'first_name': 'Tên',
        'last_name': 'Họ',
        'phone_number': 'Số điện thoại',
        'address': 'Địa chỉ',
        'date_of_birth': 'Ngày sinh',
        'gender': 'Giới tính',
        'role': 'Vai trò',
        'is_active': 'Kích hoạt'
    }

    column_filters = ['username', 'email', 'role', 'is_active']
    can_view_details = True

    def on_model_change(self, form, model, is_created):
        def hash_password(password):
            return str(hashlib.md5(password.encode('utf-8')).hexdigest())

        if is_created:
            model.password = hash_password(form.password.data)
        elif form.password.data:
            model.password = hash_password(form.password.data)
        return super().on_model_change(form, model, is_created)


# Specialty management view
class SpecialtyView(AuthenticatedView):
    column_list = ['name', 'description']
    column_labels = {'name': 'Tên chuyên khoa', 'description': 'Mô tả'}
    column_searchable_list = ['name']
    can_view_details = True


# Hospital management view
class HospitalView(AuthenticatedView):
    column_list = ['name', 'address', 'phone_number', 'accepts_insurance']
    column_labels = {
        'name': 'Tên bệnh viện',
        'address': 'Địa chỉ',
        'phone_number': 'Số điện thoại',
        'accepts_insurance': 'Chấp nhận bảo hiểm'
    }
    column_filters = ['name', 'accepts_insurance']
    can_view_details = True


# Doctor management view
class DoctorView(AuthenticatedView):
    column_list = [
        'user', 'hospital', 'specialty', 'years_experience',
        'educational_level', 'consultation_fee', 'average_rating'
    ]

    column_labels = {
        'user': 'Bác sĩ',
        'hospital': 'Bệnh viện',
        'specialty': 'Chuyên khoa',
        'years_experience': 'Số năm kinh nghiệm',
        'educational_level': 'Trình độ học vấn',
        'consultation_fee': 'Phí tư vấn',
        'average_rating': 'Đánh giá trung bình'
    }

    column_filters = ['hospital.name', 'specialty.name']
    can_view_details = True


# Doctor license management view
class DoctorLicenseView(AuthenticatedView):
    column_list = [
        'doctor', 'license_number', 'issuing_authority',
        'issue_date', 'expiry_date', 'is_verified'
    ]

    column_labels = {
        'doctor': 'Bác sĩ',
        'license_number': 'Số giấy phép',
        'issuing_authority': 'Cơ quan cấp',
        'issue_date': 'Ngày cấp',
        'expiry_date': 'Ngày hết hạn',
        'is_verified': 'Đã xác minh'
    }

    column_filters = ['is_verified', 'issuing_authority']
    can_view_details = True


# Patient management view
class PatientView(AuthenticatedView):
    column_list = ['user', 'medical_history_summary']
    column_labels = {
        'user': 'Bệnh nhân',
        'medical_history_summary': 'Tóm tắt tiền sử bệnh'
    }
    can_view_details = True


# Appointment management view
class AppointmentView(AuthenticatedView):
    column_list = [
        'patient', 'doctor', 'appointment_time', 'duration_minutes',
        'status', 'consultation_type'
    ]

    column_labels = {
        'patient': 'Bệnh nhân',
        'doctor': 'Bác sĩ',
        'appointment_time': 'Thời gian hẹn',
        'duration_minutes': 'Thời lượng (phút)',
        'status': 'Trạng thái',
        'consultation_type': 'Hình thức tư vấn'
    }

    column_filters = ['status', 'consultation_type', 'appointment_time']
    can_view_details = True


# Health record management view
class HealthRecordView(AuthenticatedView):
    column_list = ['patient', 'appointment', 'record_date', 'diagnosis']
    column_labels = {
        'patient': 'Bệnh nhân',
        'appointment': 'Cuộc hẹn',
        'record_date': 'Ngày ghi nhận',
        'diagnosis': 'Chẩn đoán'
    }
    can_view_details = True


# Invoice management view
class InvoiceView(AuthenticatedView):
    column_list = ['appointment', 'amount', 'issue_date', 'due_date', 'status']
    column_labels = {
        'appointment': 'Cuộc hẹn',
        'amount': 'Số tiền',
        'issue_date': 'Ngày tạo',
        'due_date': 'Hạn thanh toán',
        'status': 'Trạng thái'
    }
    column_filters = ['status', 'issue_date']
    can_view_details = True


# Payment management view
class PaymentView(AuthenticatedView):
    column_list = ['invoice', 'amount_paid', 'payment_method', 'status', 'payment_date']
    column_labels = {
        'invoice': 'Hóa đơn',
        'amount_paid': 'Số tiền thanh toán',
        'payment_method': 'Phương thức thanh toán',
        'status': 'Trạng thái',
        'payment_date': 'Ngày thanh toán'
    }
    column_filters = ['status', 'payment_method']
    can_view_details = True


# Review management view
class ReviewView(AuthenticatedView):
    column_list = ['appointment', 'patient', 'doctor', 'rating', 'review_date', 'is_visible']
    column_labels = {
        'appointment': 'Cuộc hẹn',
        'patient': 'Bệnh nhân',
        'doctor': 'Bác sĩ',
        'rating': 'Đánh giá',
        'review_date': 'Ngày đánh giá',
        'is_visible': 'Hiển thị'
    }
    column_filters = ['rating', 'is_visible']
    can_view_details = True


# Initialize admin
admin = Admin(app, name='Quản lý Đặt lịch khám trực tuyến', template_mode='bootstrap4')

# Add views to admin
admin.add_view(UserView(User, db.session, name='Người dùng'))
admin.add_view(SpecialtyView(Specialty, db.session, name='Chuyên khoa'))
admin.add_view(HospitalView(Hospital, db.session, name='Bệnh viện'))
admin.add_view(DoctorView(Doctor, db.session, name='Bác sĩ'))
admin.add_view(DoctorLicenseView(DoctorLicense, db.session, name='Giấy phép bác sĩ'))
admin.add_view(PatientView(Patient, db.session, name='Bệnh nhân'))
admin.add_view(AppointmentView(Appointment, db.session, name='Cuộc hẹn'))
admin.add_view(HealthRecordView(HealthRecord, db.session, name='Hồ sơ sức khỏe'))
admin.add_view(InvoiceView(Invoice, db.session, name='Hóa đơn'))
admin.add_view(PaymentView(Payment, db.session, name='Thanh toán'))
admin.add_view(ReviewView(Review, db.session, name='Đánh giá'))

admin.add_view(LogoutView(name='Đăng xuất'))
admin.add_view(LoginUserView(name='Về trang đăng nhập'))