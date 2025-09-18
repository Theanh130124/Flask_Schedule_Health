from flask_login import logout_user, current_user
from flask_admin.contrib.sqla import ModelView
from flask_admin import expose, BaseView, Admin
from sqlalchemy import extract
from sqlalchemy.exc import IntegrityError

from app.form import DoctorUserForm
from app.models import (
    RoleEnum, User, Specialty, Hospital, Doctor, DoctorLicense,
    Patient, Appointment, HealthRecord, Invoice, Payment, Review, AppointmentStatus, GenderEnum
)
from flask_admin.actions import action
from flask_admin.model.template import EndpointLinkRowAction
from app.extensions import db
from app import app
from flask import redirect, request, flash, url_for
import hashlib
from app.dao import dao_stats , dao_doctor , dao_license
from datetime import datetime


# Base class for authenticated views
class AuthenticatedView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == RoleEnum.ADMIN

# Không cần truyền model
class AuthenticatedBaseView(BaseView):
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
        'username', 'email' , 'first_name', 'last_name', 'phone_number',
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

    # Formatter -> điển hiện ngoài ist
    def _user_formatter(view, context, model, name):
        return f"{model.user.first_name} {model.user.last_name}"

    def _hospital_formatter(view, context, model, name):
        return model.hospital.name

    def _specialty_formatter(view, context, model, name):
        return model.specialty.name

    column_formatters = {
        'user': _user_formatter,
        'hospital': _hospital_formatter,
        'specialty': _specialty_formatter
    }

    # Custom form args -> để hiển cả khi bấm vào create hoặc edit
    form_args = {
        'user': {
            'query_factory': lambda: User.query.filter_by(role=RoleEnum.DOCTOR),  #không viết bên dao được cứ viết thẳng vào vậy
            'get_label': lambda user: f"{user.first_name} {user.last_name}"
        },
        'hospital': {
            'query_factory': lambda: Hospital.query,
            'get_label': lambda hospital: hospital.name
        },
        'specialty': {
            'query_factory': lambda: Specialty.query,
            'get_label': lambda specialty: specialty.name
        }
    }


class DoctorLicenseView(AuthenticatedView):
    column_list = [
        'doctor', 'license_number', 'issuing_authority',
        'issue_date', 'expiry_date', 'is_verified', 'verification_date'
    ]

    column_labels = {
        'doctor': 'Bác sĩ',
        'license_number': 'Số giấy phép',
        'issuing_authority': 'Cơ quan cấp',
        'issue_date': 'Ngày cấp',
        'expiry_date': 'Ngày hết hạn',
        'is_verified': 'Đã xác minh',
        'verification_date': 'Ngày xác minh'
    }

    column_filters = ['is_verified', 'issuing_authority']
    can_view_details = True
    can_edit = False  # Vô hiệu hóa chỉnh sửa để bắt buộc sử dụng action verify

    # Thêm action để xác minh giấy phép
    action_disallowed_list = []  # Đảm bảo actions được cho phép
    allowed_actions = ['verify_license']

    # Formatter để hiển thị đẹp tên bác sĩ trong list view
    def _doctor_formatter(view, context, model, name):
        if model.doctor and model.doctor.user:
            return f"{model.doctor.user.first_name} {model.doctor.user.last_name}"
        return ""

    column_formatters = {
        'doctor': _doctor_formatter
    }

    # Custom action để xác minh giấy phép
    # Custom action để xác minh giấy phép
    @action('verify_license', 'Xác minh', 'Bạn có chắc muốn xác minh các giấy phép đã chọn?')
    def action_verify_license(self, ids):
        try:
            # Lấy ID admin hiện tại
            admin_id = current_user.user_id

            success_count = 0
            error_messages = []

            for license_id in ids:
                success, message = dao_license.verify_doctor_license(license_id, admin_id)
                if success:
                    success_count += 1
                else:
                    error_messages.append(f"Giấy phép {license_id}: {message}")

            if success_count > 0:
                flash(f'Đã xác minh {success_count} giấy phép và kích hoạt tài khoản bác sĩ thành công!', 'success')

            if error_messages:
                flash('Một số giấy phép không thể xác minh: ' + '; '.join(error_messages), 'warning')

        except Exception as e:
            flash(f'Lỗi hệ thống: {str(e)}', 'error')

        return redirect(request.referrer)

    # Custom form_args để dropdown chọn bác sĩ khi Create/Edit
    form_args = {
        'doctor': {
            'query_factory': lambda: Doctor.query,
            'get_label': lambda doctor: f"{doctor.user.first_name} {doctor.user.last_name}"
        },
        'verified_by_admin': {
            'query_factory': lambda: User.query.filter_by(role=RoleEnum.ADMIN),
            'get_label': lambda user: f"{user.first_name} {user.last_name}"
        }
    }

    # Ghi đè form chỉnh sửa để hiển thị thông tin xác minh khi xem giấy phép đã xác minh
    def edit_form(self, obj=None):
        form = super().edit_form(obj)
        if obj and obj.is_verified:
            # Vô hiệu hóa chỉnh sửa cho giấy phép đã xác minh
            for field in form:
                field.render_kw = {'disabled': True}
        return form

# Patient management view
class PatientView(AuthenticatedView):
    column_list = ['user', 'medical_history_summary']

    column_labels = {
        'user': 'Bệnh nhân',
        'medical_history_summary': 'Tóm tắt tiền sử bệnh'
    }

    can_view_details = True

    # formatter: hiển thị tên bệnh nhân trong list view
    def _user_formatter(view, context, model, name):
        if model.user:
            return f"{model.user.first_name} {model.user.last_name}"
        return ""

    column_formatters = {
        'user': _user_formatter
    }

    # khi create/edit: chỉ lấy user có role = PATIENT
    form_args = {
        'user': {
            'query_factory': lambda: User.query.filter_by(role=RoleEnum.PATIENT),
            'get_label': lambda user: f"{user.first_name} {user.last_name}"
        }
    }



# Appointment management view
class AppointmentView(AuthenticatedView):
    column_list = [
        'patient', 'doctor', 'appointment_time', 'duration_minutes',
        'reason', 'status', 'consultation_type', 'cancellation_reason'
    ]

    column_labels = {
        'patient': 'Bệnh nhân',
        'doctor': 'Bác sĩ',
        'appointment_time': 'Thời gian khám',
        'duration_minutes': 'Thời lượng (phút)',
        'reason': 'Lý do khám',
        'status': 'Trạng thái',
        'consultation_type': 'Hình thức tư vấn',
        'cancellation_reason': 'Lý do hủy'
    }

    can_view_details = True

    # formatters hiển thị tên bệnh nhân & bác sĩ
    def _patient_formatter(view, context, model, name):
        if model.patient and model.patient.user:
            return f"{model.patient.user.first_name} {model.patient.user.last_name}"
        return ""

    def _doctor_formatter(view, context, model, name):
        if model.doctor and model.doctor.user:
            return f"{model.doctor.user.first_name} {model.doctor.user.last_name}"
        return ""

    column_formatters = {
        'patient': _patient_formatter,
        'doctor': _doctor_formatter
    }

    # dropdown cho patient và doctor
    form_args = {
        'patient': {
            'query_factory': lambda: Patient.query.join(User).filter(User.role == RoleEnum.PATIENT),
            'get_label': lambda patient: f"{patient.user.first_name} {patient.user.last_name}"
        },
        'doctor': {
            'query_factory': lambda: Doctor.query.join(User).filter(User.role == RoleEnum.DOCTOR),
            'get_label': lambda doctor: f"{doctor.user.first_name} {doctor.user.last_name}"
        }
    }


class HealthRecordView(AuthenticatedView):
    column_list = ['patient', 'appointment', 'record_date', 'diagnosis']

    column_labels = {
        'patient': 'Bệnh nhân',
        'appointment': 'Cuộc hẹn',
        'record_date': 'Ngày ghi nhận',
        'diagnosis': 'Chẩn đoán'
    }

    can_view_details = True

    # formatters
    def _patient_formatter(view, context, model, name):
        if model.patient and model.patient.user:
            return f"{model.patient.user.first_name} {model.patient.user.last_name}"
        return ""

    def _appointment_formatter(view, context, model, name):
        if model.appointment and model.appointment.appointment_time:
            return f"#{model.appointment.appointment_id} - {model.appointment.appointment_time.strftime('%d/%m/%Y %H:%M')}"
        return ""

    column_formatters = {
        'patient': _patient_formatter,
        'appointment': _appointment_formatter
    }

    # dropdown config
    form_args = {
        'patient': {
            'query_factory': lambda: Patient.query.join(User).filter(User.role == RoleEnum.PATIENT),
            'get_label': lambda patient: f"{patient.user.first_name} {patient.user.last_name}"
        },
        'appointment': {
            'query_factory': lambda: Appointment.query,
            'get_label': lambda appt: f"#{appt.appointment_id} - {appt.appointment_time.strftime('%d/%m/%Y %H:%M')}"
        }
    }



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

    def _appointment_formatter(view, context, model, name):
        if model.appointment:
            return f"#{model.appointment.appointment_id} - {model.appointment.appointment_time.strftime('%d/%m/%Y %H:%M')}"
        return ""

    column_formatters = {
        'appointment': _appointment_formatter
    }

    form_args = {
        'appointment': {
            'query_factory': lambda: Appointment.query,
            'get_label': lambda appt: f"#{appt.appointment_id} - {appt.appointment_time.strftime('%d/%m/%Y %H:%M')}"
        }
    }


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

    def _invoice_formatter(view, context, model, name):
        if model.invoice and model.invoice.appointment:
            return f"HĐ#{model.invoice.invoice_id} - Cuộc hẹn {model.invoice.appointment.appointment_id}"
        return ""

    column_formatters = {
        'invoice': _invoice_formatter
    }

    form_args = {
        'invoice': {
            'query_factory': lambda: Invoice.query,
            'get_label': lambda inv: f"HĐ#{inv.invoice_id} - Cuộc hẹn {inv.appointment.appointment_id if inv.appointment else ''}"
        }
    }

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

    # Formatters
    def _appointment_formatter(view, context, model, name):
        if model.appointment:
            return f"#{model.appointment.appointment_id} - {model.appointment.appointment_time.strftime('%d/%m/%Y %H:%M')}"
        return ""

    def _patient_formatter(view, context, model, name):
        if model.patient and model.patient.user:
            return f"{model.patient.user.first_name} {model.patient.user.last_name}"
        return ""

    def _doctor_formatter(view, context, model, name):
        if model.doctor and model.doctor.user:
            return f"BS {model.doctor.user.first_name} {model.doctor.user.last_name}"
        return ""

    column_formatters = {
        'appointment': _appointment_formatter,
        'patient': _patient_formatter,
        'doctor': _doctor_formatter
    }

    # dropdown filter theo role
    form_args = {
        'appointment': {
            'query_factory': lambda: Appointment.query,
            'get_label': lambda appt: f"#{appt.appointment_id} - {appt.appointment_time.strftime('%d/%m/%Y %H:%M')}"
        },
        'patient': {
            'query_factory': lambda: Patient.query.join(User).filter(User.role == RoleEnum.PATIENT),
            'get_label': lambda p: f"{p.user.first_name} {p.user.last_name}"
        },
        'doctor': {
            'query_factory': lambda: Doctor.query.join(User).filter(User.role == RoleEnum.DOCTOR),
            'get_label': lambda d: f"BS {d.user.first_name} {d.user.last_name}"
        }
    }

class StatsView(AuthenticatedBaseView):
    @expose('/')
    def index(self):
        # Lấy tham số từ query string
        year = request.args.get('year', type=int)
        quarter = request.args.get('quarter', type=int)
        month = request.args.get('month', type=int)
        doctor_id = request.args.get('doctor_id', type=int)

        # Lấy danh sách năm có dữ liệu
        years = db.session.query(
            extract('year', Appointment.appointment_time).label('year')
        ).join(Invoice).filter(
            Appointment.status == AppointmentStatus.Completed
        ).group_by(
            extract('year', Appointment.appointment_time)
        ).order_by(
            extract('year', Appointment.appointment_time).desc()
        ).all()
        years = [int(y[0]) for y in years]

        # Lấy danh sách bác sĩ
        doctors = Doctor.query.join(User).all()

        # Lấy dữ liệu thống kê
        stats_data = dao_stats.get_revenue_by_time_period(year, quarter, month)
        doctor_stats = dao_stats.get_appointment_stats(year, quarter, month, doctor_id)

        # Lấy thống kê tổng quan theo tất cả bác sĩ (khi không chọn bác sĩ cụ thể)
        all_doctor_stats = []
        if not doctor_id:
            all_doctor_stats = dao_stats.get_appointment_stats(year, quarter, month)

        # Chuẩn bị dữ liệu cho biểu đồ
        chart_labels = []
        chart_appointments = []
        chart_revenues = []

        for stat in stats_data:
            year_val = getattr(stat, "year", None)
            quarter_val = getattr(stat, "quarter", None)
            month_val = getattr(stat, "month", None)

            if month_val:
                chart_labels.append(f"{int(month_val)}/{int(year_val)}")
            elif quarter_val:
                chart_labels.append(f"Q{int(quarter_val)}/{int(year_val)}")
            else:
                chart_labels.append(str(int(year_val)))

            # Thêm dữ liệu số lượt khám và doanh thu
            chart_appointments.append(stat.appointment_count)
            chart_revenues.append(float(stat.total_revenue) if stat.total_revenue else 0)

        return self.render(
            'admin/stats.html',
            stats_data=stats_data,
            doctor_stats=doctor_stats,
            all_doctor_stats=all_doctor_stats,
            doctors=doctors,
            years=years,
            selected_year=year,
            selected_quarter=quarter,
            selected_month=month,
            selected_doctor=doctor_id,
            chart_labels=chart_labels,
            chart_appointments=chart_appointments,
            chart_revenues=chart_revenues
        )


class CreateDoctorView(AuthenticatedBaseView):

    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == RoleEnum.ADMIN

    @expose('/', methods=('GET', 'POST'))
    def index(self):
        form = DoctorUserForm()

        # Populate dropdowns
        form.hospital_id.choices = [(h.hospital_id, h.name) for h in Hospital.query.all()]
        form.specialty_id.choices = [(s.specialty_id, s.name) for s in Specialty.query.all()]

        if form.validate_on_submit():
            try:
                # Hash password
                def hash_password(password):
                    return str(hashlib.md5(password.encode('utf-8')).hexdigest())

                # Create User with is_active=False
                user = User(
                    username=form.username.data,
                    password=hash_password(form.password.data),
                    email=form.email.data,
                    first_name=form.first_name.data,
                    last_name=form.last_name.data,
                    phone_number=form.phone_number.data,
                    address=form.address.data,
                    date_of_birth=datetime.strptime(form.date_of_birth.data,
                                                    '%Y-%m-%d') if form.date_of_birth.data else None,
                    gender=GenderEnum[form.gender.data] if form.gender.data else None,
                    role=RoleEnum.DOCTOR,
                    is_active=False  # Set to False as requested
                )

                db.session.add(user)
                db.session.flush()  # Get the user_id without committing

                # Create Doctor
                doctor = Doctor(
                    doctor_id=user.user_id,
                    hospital_id=form.hospital_id.data,
                    specialty_id=form.specialty_id.data,
                    years_experience=form.years_experience.data,
                    educational_level=form.educational_level.data,
                    bio=form.bio.data,
                    consultation_fee=form.consultation_fee.data
                )

                db.session.add(doctor)

                # Create License if provided
                if form.license_number.data:
                    license = DoctorLicense(
                        doctor_id=user.user_id,
                        license_number=form.license_number.data,
                        issuing_authority=form.issuing_authority.data,
                        issue_date=datetime.strptime(form.issue_date.data,
                                                     '%Y-%m-%d') if form.issue_date.data else None,
                        expiry_date=datetime.strptime(form.expiry_date.data,
                                                      '%Y-%m-%d') if form.expiry_date.data else None,
                        is_verified=False
                    )
                    db.session.add(license)

                db.session.commit()
                flash('Đã tạo bác sĩ và tài khoản thành công! Tài khoản đang ở trạng thái chưa kích hoạt.', 'success')
                return redirect(url_for('doctor.index_view'))

            except IntegrityError:
                db.session.rollback()
                flash('Tên đăng nhập hoặc email đã tồn tại!', 'error')
            except Exception as e:
                db.session.rollback()
                flash(f'Lỗi khi tạo bác sĩ: {str(e)}', 'error')

        return self.render('admin/create_doctor.html', form=form)
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
admin.add_view(StatsView(name='Thống kê', endpoint='stats'))
admin.add_view(CreateDoctorView(name='Tạo Bác Sĩ Mới', endpoint='create_doctor'))
admin.add_view(LogoutView(name='Đăng xuất'))
admin.add_view(LoginUserView(name='Về trang đăng nhập'))