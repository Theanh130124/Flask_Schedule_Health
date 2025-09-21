import uuid
from datetime import datetime , date, timedelta
from math import ceil
from sqlalchemy.orm import joinedload, subqueryload
from flask_login import current_user, login_required, logout_user, login_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask import flash, current_app
from app.form import LoginForm, ScheduleForm
from flask import render_template , redirect , request , url_for  , session , jsonify
from app.decorators import role_only
# Thêm import
from app.dao import dao_payment
from app.vnpay_service import VNPay  # Import VNPay
import math
from app.dao import dao_authen, dao_search, dao_doctor, dao_available_slot, dao_appointment, dao_payment, dao_patient, dao_healthrecord
from app.models import Hospital, Specialty, User, Doctor, RoleEnum, Patient, DayOfWeekEnum, HealthRecord, AvailableSlot, \
    ConsultationType, DoctorLicense, Appointment, Review, AppointmentStatus

import google.oauth2.id_token
import google.auth.transport.requests
import requests
from app import app , flow  #là import __init__
from app.extensions import db
from app.models import Hospital, Specialty, User, Doctor, RoleEnum, GenderEnum
from app.form import LoginForm, RegisterForm
from app.dao import dao_authen, dao_user, dao_search




@app.route("/api/hospitals")
def api_hospitals():
    q = request.args.get("q", "")
    results = (Hospital.query
               .filter(Hospital.name.ilike(f"%{q}%"))
               .order_by(Hospital.name.asc())
               .limit(10)
               .all())
    return jsonify([h.name for h in results])

@app.route("/api/specialties")
def api_specialties():
    q = request.args.get("q", "")
    results = (Specialty.query
               .filter(Specialty.name.ilike(f"%{q}%"))
               .order_by(Specialty.name.asc())
               .limit(10)
               .all())
    return jsonify([s.name for s in results])


@app.route("/api/doctors")
def api_doctors():
    q = (request.args.get("q", "") or "").strip()
    if not q:
        return jsonify([])

    results = (db.session.query(User)
               .join(Doctor)
               .filter(
                   User.role == RoleEnum.DOCTOR,
                   (User.first_name.ilike(f"%{q}%")) |
                   (User.last_name.ilike(f"%{q}%"))
               )
               .order_by(User.first_name.asc(), User.last_name.asc())
               .limit(10)
               .all())

    return jsonify([f"{u.first_name} {u.last_name}" for u in results])

# -------- VIEW ROUTES --------

def index():
    # không gán @app.route('/') ở đây: đã có index_controller() trỏ vào bằng add_url_rule
    hospitals = dao_search.get_all_hospitals()
    specialties = dao_search.get_all_specialties()
    return render_template('index.html', hospitals=hospitals, specialties=specialties)

@app.route('/search_doctor')
def search_doctor():
    hospital_name = request.args.get('hospital')
    specialty_name = request.args.get('specialty')
    doctor_name = request.args.get('doctor_name')

    # nếu dùng cho autocomplete có thể truyền limit=... vào dao
    doctors = dao_search.search_doctors(hospital_name, specialty_name, doctor_name)

    return render_template('search_results.html', doctors=doctors)

# Navigate cho đăng nhập hoặc chưa
def index_controller():
    if current_user.is_authenticated:
        if current_user.role == RoleEnum.ADMIN:
            return redirect("/admin")
        return redirect("/home")
    return redirect('/login')

@app.route('/home')
@login_required
def home():
    hospitals = Hospital.query.order_by(Hospital.name.asc()).all()
    specialties = Specialty.query.order_by(Specialty.name.asc()).all()
    return render_template('index.html', hospitals=hospitals, specialties=specialties)
# Thôngtinchitietbacsi
@app.route("/doctor/<int:doctor_id>", endpoint="doctor_detail")
def doctor_detail(doctor_id: int):
    # Lấy thông tin bác sĩ
    d = (db.session.query(Doctor)
         .options(
             joinedload(Doctor.user),
             joinedload(Doctor.specialty),
             joinedload(Doctor.hospital),
             subqueryload(Doctor.licenses),
             subqueryload(Doctor.available_slots),
         )
         .filter(Doctor.doctor_id == doctor_id)
         .first_or_404())

    # Tính avg_rating
    avg_rating = float(d.average_rating) if d.average_rating is not None else None

    # Slot trống
    upcoming_slots = [s for s in d.available_slots if not s.is_booked]
    upcoming_slots.sort(key=lambda s: (s.slot_date, s.start_time))

    # Lấy các appointment đã hoàn tất của bệnh nhân hiện tại (nếu đã đăng nhập)
    eligible_appts = []
    if current_user.is_authenticated and current_user.role == RoleEnum.PATIENT:
        eligible_appts = (
            db.session.query(Appointment)
            .outerjoin(Review, Review.appointment_id == Appointment.appointment_id)
            .filter(
                Appointment.doctor_id == doctor_id,
                Appointment.patient_id == current_user.user_id,
                Appointment.status == AppointmentStatus.Completed,
                Review.appointment_id.is_(None)  # chưa review
            )
            .order_by(Appointment.appointment_time.desc())
            .all()
        )

    # Lấy reviews để hiển thị
    reviews = (Review.query
               .filter_by(doctor_id=doctor_id, is_visible=True)
               .order_by(Review.review_date.desc())
               .all())

    return render_template(
        "doctor_detail.html",
        d=d,
        avg_rating=avg_rating,
        upcoming_slots=upcoming_slots[:10],
        reviews=reviews,
        eligible_appts=eligible_appts
    )
# chitiettimkiem



def login():
    mse = ""
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = dao_authen.get_user_by_username(username=username)
        if not user:
            mse = "Tài khoản không tồn tại trong hệ thống"
        else:
            if dao_authen.check_password_md5(user, password):
                # Kiểm tra nếu là doctor chưa kích hoạt
                if user.role == RoleEnum.DOCTOR and not user.is_active:
                    # Lưu thông tin user vào session thay vì đăng nhập
                    session['pending_doctor_id'] = user.user_id
                    session['pending_doctor_username'] = user.username
                    return redirect(url_for('upload_license'))

                # Các trường hợp khác: đăng nhập bình thường
                login_user(user)
                return redirect(url_for('index_controller'))
            else:
                mse = "Mật khẩu không đúng"

    return render_template('login.html', form=form, mse=mse)

def logout_my_user():
    logout_user()
    return redirect('/login')

def login_oauth():
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )
    session["state"] = state
    return redirect(authorization_url)
def oauth_callback():
    # đảm bảo Google trả về state đúng
    if request.args.get("state") != session.get("state"):
        return "State mismatch!", 400

    try:
        # lấy token từ Google
        flow.fetch_token(authorization_response=request.url)

        credentials = flow.credentials
        request_session = requests.session()
        token_request = google.auth.transport.requests.Request(session=request_session)

        # verify id_token
        id_info = google.oauth2.id_token.verify_oauth2_token(
            id_token=credentials._id_token,
            request=token_request,
            audience=flow.client_config["client_id"],
            clock_skew_in_seconds=10  # cho phép lệch tối đa 10 giây
        )

        email = id_info.get("email")
        name = id_info.get("name")

        # kiểm tra user trong DB
        user = dao_authen.get_user_by_username(email)
        if not user:
            user = User(
                username=email,
                email=email,
                password="",  # OAuth không dùng mật khẩu
                role=RoleEnum.PATIENT,
                first_name=name.split(" ")[0] if name else "Google",
                last_name=" ".join(name.split(" ")[1:]) if name and len(name.split()) > 1 else "User",
                phone_number=f"GG-{uuid.uuid4().hex[:8]}",  #SĐT giả
                address="Unknown"
            )
            db.session.add(user)
            db.session.flush()
            if user.role == RoleEnum.PATIENT:
                patient = Patient(
                    patient_id=user.user_id,
                    medical_history_summary="Created from Google OAuth"
                )
                db.session.add(patient)
                # Tạo một HealthRecord trống cho lần đầu khám
                health_record = HealthRecord(
                    patient_id=user.user_id,
                    record_date=datetime.now().date(),
                    symptoms="",
                    diagnosis="",
                    prescription="",
                    notes="Bệnh nhân mới - Hồ sơ được tạo tự động từ OAuth"
                )
                db.session.add(health_record)
                db.session.commit()
                #
        login_user(user)

        return redirect(url_for("index_controller"))

    except Exception as e:
        app.logger.error(f"OAuth Callback Error: {e}")

        return f"Login failed: {e}", 400


@app.route('/upload_license', methods=['GET', 'POST'])
def upload_license():
    # Kiểm tra nếu có pending doctor trong session
    if 'pending_doctor_id' not in session:
        flash('Vui lòng đăng nhập trước', 'error')
        return redirect(url_for('login'))

    doctor_id = session['pending_doctor_id']

    if request.method == 'POST':
        # Xử lý upload license
        license_number = request.form.get('license_number')
        issuing_authority = request.form.get('issuing_authority')
        issue_date = request.form.get('issue_date')
        expiry_date = request.form.get('expiry_date')
        scope_description = request.form.get('scope_description')

        # Lưu license vào database
        try:
            new_license = DoctorLicense(
                doctor_id=doctor_id,
                license_number=license_number,
                issuing_authority=issuing_authority,
                issue_date=datetime.strptime(issue_date, '%Y-%m-%d').date(),
                expiry_date=datetime.strptime(expiry_date, '%Y-%m-%d').date() if expiry_date else None,
                scope_description=scope_description,
                is_verified=False  # Chờ admin xác thực
            )
            db.session.add(new_license)
            db.session.commit()

            # Xóa session pending
            session.pop('pending_doctor_id', None)
            session.pop('pending_doctor_username', None)

            flash('Đã gửi chứng chỉ thành công. Vui lòng chờ xác thực từ quản trị viên.', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')

    return render_template('upload_license.html', doctor_id=doctor_id)

def register():
    form = RegisterForm()
    mse = None
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        phone_number = form.phone_number.data
        address = form.address.data
        date_of_birth = form.date_of_birth.data
        gender = form.gender.data

        # Tạo user bằng dao_user
        new_user = dao_user.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            address=address,
            date_of_birth=date_of_birth,
            gender=gender
        )

        if new_user:
            flash("Đăng ký thành công! Hãy đăng nhập.", "success")
            return redirect(url_for("login"))
        else:
            mse = "Tên đăng nhập hoặc email đã tồn tại!"

    return render_template("register.html", form=form, mse=mse)

#Lịch làm việc bác sĩ
@app.route('/create_schedule', methods=['GET', 'POST'])
@login_required
@role_only([RoleEnum.DOCTOR])
def create_schedule():
    form = ScheduleForm()
    # Lấy thông tin doctor từ current_user
    doctor = dao_authen.get_doctor_by_userid(current_user.user_id)
    if not doctor:
        flash("Bạn không phải là bác sĩ", "error")
        return redirect(url_for('home'))
    if form.validate_on_submit():
        try:
            # Tạo lịch làm việc
            dao_doctor.create_doctor_availability(
                doctor_id=doctor.doctor_id,
                day_of_week=form.day_of_week.data,
                start_time=form.start_time.data,
                end_time=form.end_time.data,
                is_available=form.is_available.data
            )

            flash("Lịch làm việc đã được cập nhật thành công!", "success")
            return redirect(url_for('view_schedule'))

        except Exception as e:
            flash(f"Có lỗi xảy ra: {str(e)}", "error")

    # Hiển thị form với dữ liệu hiện tại nếu có
    return render_template('create_schedule.html', form=form, doctor=doctor)


@app.route('/view_schedule')
@login_required
@role_only([RoleEnum.DOCTOR])
def view_schedule():
    # Lấy thông tin doctor từ current_user
    doctor = dao_authen.get_doctor_by_userid(current_user.user_id)

    if not doctor:
        flash("Bạn không phải là bác sĩ", "error")
        return redirect(url_for('home'))

    # Lấy tất cả lịch làm việc của bác sĩ
    availabilities = dao_doctor.get_doctor_availabilities(doctor.doctor_id)

    # Tạo danh sách tất cả các ngày trong tuần
    days = []
    for day in DayOfWeekEnum:
        availability = next((a for a in availabilities if a.day_of_week == day), None)
        days.append({
            'name': day.value,
            'enum_name': day.name,
            'start_time': availability.start_time.strftime('%H:%M') if availability else 'N/A',
            'end_time': availability.end_time.strftime('%H:%M') if availability else 'N/A',
            'is_available': availability.is_available if availability else False
        })

    return render_template('view_schedule.html', days=days, doctor=doctor)


@app.route('/availableslot')
@login_required
@role_only([RoleEnum.PATIENT])
def available_slots():
    # Lấy các tham số lọc từ query string
    hospital_id = request.args.get('hospital_id', type=int)
    specialty_id = request.args.get('specialty_id', type=int)
    doctor_id = request.args.get('doctor_id', type=int)
    date_str = request.args.get('date')
    page = request.args.get('page', 1, type=int)  # Thêm phân trang
    per_page = 6  # Số slot mỗi trang (phù hợp với layout 2-3 cột)

    date_filter = None
    if date_str:
        try:
            date_filter = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    # Lấy danh sách slot khả dụng với bộ lọc (cập nhật hàm DAO)
    available_slots = dao_available_slot.get_available_slots_by_filters_paginated(
        hospital_id=hospital_id,
        specialty_id=specialty_id,
        doctor_id=doctor_id,
        date=date_filter,
        page=page,
        per_page=per_page
    )

    # Lấy tổng số slot để tính toán phân trang
    total_slots = dao_available_slot.count_available_slots_by_filters(
        hospital_id=hospital_id,
        specialty_id=specialty_id,
        doctor_id=doctor_id,
        date=date_filter
    )

    # Lấy danh sách bệnh viện và chuyên khoa cho dropdown
    hospitals = Hospital.query.order_by(Hospital.name).all()
    specialties = Specialty.query.order_by(Specialty.name).all()

    # Lấy ngày hiện tại để set min date cho input
    current_date = date.today().strftime('%Y-%m-%d')

    total_pages = ceil(total_slots / per_page) if total_slots > 0 else 1

    return render_template('available_slots.html',
                           available_slots=available_slots,
                           hospitals=hospitals,
                           specialties=specialties,
                           selected_hospital=hospital_id,
                           selected_specialty=specialty_id,
                           selected_doctor=doctor_id,
                           selected_date=date_str,
                           current_date=current_date,
                           current_page=page,
                           total_pages=total_pages,
                           total_slots=total_slots)

@app.route('/cancel_appointment/<int:appointment_id>', methods=['POST'])
@login_required
@role_only([RoleEnum.PATIENT])
def cancel_appointment_route(appointment_id):
    reason = request.form.get('reason')
    success, message = dao_appointment.cancel_appointment(appointment_id, reason, cancelled_by_patient=True)
    if success:
        flash(message, "success")   # Hiện thông báo thành công
    else:
        flash(message, "danger")    # Hiện thông báo lỗi (ví dụ ít hơn 24h)
    return redirect(url_for('appointment_detail', appointment_id=appointment_id))

@app.route('/book_appointment/<int:slot_id>', methods=['GET', 'POST'])
@login_required
@role_only([RoleEnum.PATIENT])
def book_appointment(slot_id):
    # Lấy thông tin slot
    slot = AvailableSlot.query.get_or_404(slot_id)

    if request.method == 'POST':
        reason = request.form.get('reason', '')
        consultation_type = request.form.get('consultation_type', ConsultationType.Offline.value)

        # Đặt lịch
        appointment, message = dao_appointment.book_appointment(
            patient_id=current_user.user_id,
            slot_id=slot_id,
            reason=reason,
            consultation_type=ConsultationType(consultation_type)
        )

        if appointment:
            flash(message, 'success')
            return redirect(url_for('appointment_detail', appointment_id=appointment.appointment_id))
        else:
            flash(message, 'error')

    return render_template('book_appointment.html', slot=slot)


@app.route('/appointment/<int:appointment_id>')
@login_required
def appointment_detail(appointment_id):
    appointment = dao_appointment.get_appointment_by_id(appointment_id)

    if not appointment:
        flash('Lịch hẹn không tồn tại', 'error')
        return redirect(url_for('home'))

    # Kiểm tra quyền truy cập
    if (appointment.patient_id != current_user.user_id and
            (current_user.role != RoleEnum.DOCTOR or appointment.doctor_id != current_user.user_id)
            ):
        flash('Bạn không có quyền xem lịch hẹn này', 'error')
        return redirect(url_for('home'))

    return render_template('appointment_detail.html', appointment=appointment)


@app.route('/my_appointments')
@login_required
def my_appointments():
    page = request.args.get('page', 1, type=int)
    per_page = 6  # Số lịch hẹn mỗi trang

    if current_user.role == RoleEnum.PATIENT:
        appointments = dao_appointment.get_patient_appointments_paginated(current_user.user_id, page, per_page)
        total_appointments = dao_appointment.count_patient_appointments(current_user.user_id)
        template = 'patient_appointments.html'
    elif current_user.role == RoleEnum.DOCTOR:
        appointments = dao_appointment.get_doctor_appointments_paginated(current_user.user_id, page, per_page)
        total_appointments = dao_appointment.count_doctor_appointments(current_user.user_id)
        template = 'doctor_appointments.html'
    else:
        flash('Chức năng này chỉ dành cho bệnh nhân và bác sĩ', 'error')
        return redirect(url_for('home'))

    total_pages = math.ceil(total_appointments / per_page) if total_appointments > 0 else 1

    return render_template(template,
                           appointments=appointments,
                           current_page=page,
                           total_pages=total_pages,
                           total_appointments=total_appointments)


@app.route('/cancel_appointment/<int:appointment_id>', methods=['POST'])
@login_required
def cancel_appointment(appointment_id):
    appointment = dao_appointment.get_appointment_by_id(appointment_id)

    if not appointment:
        flash('Lịch hẹn không tồn tại', 'error')
        return redirect(url_for('my_appointments'))

    # Kiểm tra quyền
    if appointment.patient_id != current_user.user_id:
        flash('Bạn không có quyền hủy lịch hẹn này', 'error')
        return redirect(url_for('my_appointments'))

    reason = request.form.get('reason', '')
    success, message = dao_appointment.cancel_appointment(
        appointment_id, reason, cancelled_by_patient=(appointment.patient_id == current_user.user_id)
    )

    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')

    return redirect(url_for('appointment_detail', appointment_id=appointment_id))


@app.route('/complete_appointment/<int:appointment_id>', methods=['POST'])
@login_required
@role_only([RoleEnum.DOCTOR])
def complete_appointment(appointment_id):
    appointment = dao_appointment.get_appointment_by_id(appointment_id)

    if not appointment:
        flash('Lịch hẹn không tồn tại', 'error')
        return redirect(url_for('my_appointments'))

    # Kiểm tra quyền - chỉ bác sĩ của lịch hẹn mới được đánh dấu hoàn thành
    if appointment.doctor_id != current_user.user_id:
        flash('Bạn không có quyền thực hiện thao tác này', 'error')
        return redirect(url_for('my_appointments'))

    success, message = dao_appointment.complete_appointment(appointment_id)

    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')

    return redirect(url_for('appointment_detail', appointment_id=appointment_id))


@app.route('/reschedule_appointment/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
@role_only([RoleEnum.PATIENT])
def reschedule_appointment(appointment_id):
    appointment = dao_appointment.get_appointment_by_id(appointment_id)

    if not appointment:
        flash('Lịch hẹn không tồn tại', 'error')
        return redirect(url_for('my_appointments'))

    # Kiểm tra quyền
    if appointment.patient_id != current_user.user_id:
        flash('Bạn không có quyền sửa lịch hẹn này', 'error')
        return redirect(url_for('my_appointments'))

    # Kiểm tra thời gian (trước 24 giờ)
    current_time = datetime.now()
    time_difference = appointment.appointment_time - current_time
    if time_difference.total_seconds() < 24 * 3600:
        flash('Chỉ có thể sửa lịch hẹn trước 24 giờ', 'error')
        return redirect(url_for('appointment_detail', appointment_id=appointment_id))

    # Lấy danh sách slot khả dụng
    available_slots = dao_available_slot.get_available_slots()

    if request.method == 'POST':
        new_slot_id = request.form.get('new_slot_id')
        reason = request.form.get('reason', appointment.reason)

        success, message = dao_appointment.reschedule_appointment(
            appointment_id, new_slot_id, reason
        )

        if success:
            flash(message, 'success')
            return redirect(url_for('appointment_detail', appointment_id=appointment_id))
        else:
            flash(message, 'error')

    return render_template('reschedule_appointment.html',
                           appointment=appointment,
                           available_slots=available_slots)





# Thêm routes mới
@app.route('/payment/vnpay/<int:appointment_id>')
@login_required
@role_only([RoleEnum.PATIENT])
def vnpay_payment(appointment_id):
    appointment = dao_appointment.get_appointment_by_id(appointment_id)

    if not appointment or appointment.patient_id != current_user.user_id:
        flash('Lịch hẹn không tồn tại', 'error')
        return redirect(url_for('my_appointments'))

    # Tạo payment
    payment, message = dao_payment.create_vnpay_payment(appointment)
    if not payment:
        flash(message, 'error')
        return redirect(url_for('appointment_detail', appointment_id=appointment_id))

    # Tạo payment URL
    vnpay = VNPay()
    order_info = f"Thanh toan lich hen #{appointment_id}"
    amount = float(appointment.invoice.amount)
    ip_addr = request.remote_addr

    payment_url = vnpay.create_payment_url(
        order_info=order_info,
        amount=amount,
        order_id=payment.payment_id,
        ip_addr=ip_addr
    )

    return redirect(payment_url)


@app.route('/payment/vnpay_return')
def vnpay_return():
    params = request.args.to_dict()
    success, message = dao_payment.process_vnpay_callback(params)

    if success:
        flash('Thanh toán thành công!', 'success')
    else:
        flash(f'Thanh toán thất bại: {message}', 'error')

    return redirect(url_for('my_appointments'))


@app.route("/api/patients")
@login_required
@role_only([RoleEnum.DOCTOR])
def api_patients():
    """
    API trả về danh sách bệnh nhân mà bác sĩ đã từng có appointment
    """
    # Query string từ URL
    q = (request.args.get("q", "") or "").strip()
    phone = (request.args.get("phone", "") or "").strip()
    active = request.args.get("active")
    inactive = request.args.get("inactive")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 50))

    # Lấy danh sách bệnh nhân từ DAO
    patients, total = dao_patient.get_patients_by_doctor(
        doctor_id=current_user.user_id,
        page=page,
        per_page=per_page,
        filters={
            'q': q,
            'phone': phone,
            'active': active,
            'inactive': inactive
        }
    )

    # Trả JSON với thông tin đầy đủ
    patient_data = []
    for patient in patients:
        status_count = dao_patient.get_appointment_status_count(patient.user_id, current_user.user_id)

        patient_data.append({
            "id": patient.user_id,
            "name": f"{patient.first_name} {patient.last_name}",
            "age": dao_patient.calculate_age(patient.date_of_birth),
            "gender": patient.gender.name if patient.gender else None,
            "contact": patient.phone_number,
            "last_visit_date": dao_patient.get_last_visit_date(patient.user_id, current_user.user_id),
            "appointment_status": status_count,
            "total_appointments": sum(status_count.values())
        })

    return jsonify(patient_data)


# lọc bệnh nhân theo trạng thái trong lịch hẹn
@app.route("/api/patients/filter-by-status/<status>")
@login_required
@role_only([RoleEnum.DOCTOR])
def api_patients_filter_by_status(status):
    try:
        status_enum = AppointmentStatus[status]
    except KeyError:
        return jsonify({"error": "Trạng thái không hợp lệ"}), 400

    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 50))

    patients, total = dao_patient.get_patients_by_doctor_with_status_filter(
        doctor_id=current_user.user_id,
        status_filter=status_enum,
        page=page,
        per_page=per_page
    )

    # Trả JSON với thông tin đầy đủ (THIẾU PHẦN NÀY)
    patient_data = []
    for patient in patients:
        status_count = dao_patient.get_appointment_status_count(patient.user_id, current_user.user_id)

        patient_data.append({
            "id": patient.user_id,
            "name": f"{patient.first_name} {patient.last_name}",
            "age": dao_patient.calculate_age(patient.date_of_birth),
            "gender": patient.gender.name if patient.gender else None,
            "contact": patient.phone_number,
            "last_visit_date": dao_patient.get_last_visit_date(patient.user_id, current_user.user_id),
            "appointment_status": status_count,
            "total_appointments": sum(status_count.values())
        })

    # Thêm thông tin phân trang (optional)
    response = {
        "patients": patient_data,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": math.ceil(total / per_page) if total > 0 else 1
        }
    }

    return jsonify(response)
# hiển thị trang làm việc của bác sĩ
@app.route("/patients/search")
@login_required
@role_only([RoleEnum.DOCTOR])
def patient_search():

    return render_template("patient_search.html")

# hồ sơ bệnh nhân
@app.route('/patient/<int:patient_id>')
@login_required
def patient_detail(patient_id):
    # Sử dụng DAO để lấy thông tin
    user = dao_patient.get_patient_by_id(patient_id)
    if not user:
        flash('Bệnh nhân không tồn tại', 'error')
        return redirect(url_for('home'))

    patient = user.patient

    # Lấy danh sách appointments gần đây (SỬA Ở ĐÂY)
    appointments_result = dao_appointment.get_patient_appointments_paginated(patient_id, page=1, per_page=5)
    appointments = appointments_result.items if appointments_result else []
    # lấy healthrecord
    health_records=dao_healthrecord.get_records_by_patient(patient_id, limit=10)

    # Kiểm tra quyền truy cập
    if current_user.role.name == "DOCTOR":
        has_access = dao_patient.has_doctor_with_patient(current_user.user_id, patient_id)
        if not has_access:
            flash('Bạn không có quyền xem thông tin bệnh nhân này', 'error')
            return redirect(url_for('patient_search'))

    elif current_user.role.name == "PATIENT":
        if current_user.user_id != patient_id:
            flash('Bạn chỉ có thể xem thông tin của chính mình', 'error')
            return redirect(url_for('home'))

    return render_template("patient_detail.html",
                           patient=patient,
                           user=user,
                           appointments=appointments,
                           health_records=health_records,
                           calculate_age=dao_patient.calculate_age,
                           now=datetime.now())

# sử lý chuẩn đoán


# ... các import và route khác ...

@app.route('/api/update-diagnosis', methods=['POST'])
@login_required
@role_only([RoleEnum.DOCTOR])
def update_diagnosis():
    try:
        # Nhận dữ liệu JSON từ frontend
        data = request.get_json()

        if not data:
            return jsonify({'success': False, 'message': 'Dữ liệu không hợp lệ'})

        appointment_id = data.get('appointment_id')
        patient_id = data.get('patient_id')
        doctor_id = data.get('doctor_id')
        symptoms = data.get('symptoms', '')
        diagnosis = data.get('diagnosis', '')
        prescription = data.get('prescription', '')
        notes = data.get('notes', '')
        record_id = data.get('record_id')

        # KIỂM TRA QUYỀN TRUY CẬP
        if int(doctor_id) != current_user.user_id:
            return jsonify({'success': False, 'message': 'Không có quyền thực hiện chuẩn đoán'})

        # TÌM APPOINTMENT
        appointment = Appointment.query.get(appointment_id)
        if not appointment or appointment.patient_id != int(patient_id) or appointment.doctor_id != int(doctor_id):
            return jsonify({'success': False, 'message': 'Không tìm thấy lịch hẹn phù hợp'})

        # KIỂM TRA TRẠNG THÁI APPOINTMENT - CHỈ CHO PHÉP KHI LÀ "Scheduled"
        if appointment.status != AppointmentStatus.Scheduled:
            return jsonify({
                'success': False,
                'message': f'Chỉ có thể chuẩn đoán cho lịch hẹn đang chờ khám. Trạng thái hiện tại: {appointment.status.value}'
            })

        # KIỂM TRA THỜI GIAN - CHỈ CHO PHÉP TRONG VÒNG 1 TIẾNG TRƯỚC VÀ SAU GIỜ HẸN
        current_time = datetime.now()
        appointment_time = appointment.appointment_time
        one_hour_before = appointment_time - timedelta(hours=1)
        one_hour_after = appointment_time + timedelta(hours=1)

        if current_time < one_hour_before or current_time > one_hour_after:
            return jsonify({
                'success': False,
                'message': 'Chỉ có thể chuẩn đoán trong khoảng thời gian từ 1 giờ trước đến 1 giờ sau giờ hẹn khám.'
            })

        # TÌM HOẶC TẠO HEALTH RECORD
        if record_id:
            # Cập nhật health record hiện tại bằng DAO
            update_data = {
                'symptoms': symptoms,
                'diagnosis': diagnosis,
                'prescription': prescription,
                'notes': notes,
                'record_date': datetime.now().date()
            }
            health_record = dao_healthrecord.update_healthrecord(record_id, update_data)

            if not health_record:
                return jsonify({'success': False, 'message': 'Health record không hợp lệ'})
        else:
            # Tạo health record mới bằng DAO
            health_record = HealthRecord(
                patient_id=patient_id,
                appointment_id=appointment_id,
                user_id=current_user.user_id,
                record_date=datetime.now().date(),
                symptoms=symptoms,
                diagnosis=diagnosis,
                prescription=prescription,
                notes=notes
            )
            db.session.add(health_record)

        # CẬP NHẬT TRẠNG THÁI APPOINTMENT THÀNH HOÀN THÀNH
        appointment.status = AppointmentStatus.Completed

        # LƯU VÀO DATABASE
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Chuẩn đoán đã được lưu thành công',
            'record_id': health_record.record_id
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Lỗi khi cập nhật chuẩn đoán: {str(e)}")
        return jsonify({'success': False, 'message': f'Lỗi hệ thống: {str(e)}'}), 500
# lấy hồ sơ sức khỏe
@app.route('/api/get-diagnosis/<int:appointment_id>')
@login_required
@role_only([RoleEnum.DOCTOR])
def get_diagnosis(appointment_id):
    try:
        # TÌM APPOINTMENT VÀ KIỂM TRA QUYỀN TRUY CẬP
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return jsonify({'success': False, 'message': 'Lịch hẹn không tồn tại'}), 404

        # KIỂM TRA BÁC SĨ CÓ QUYỀN XEM APPOINTMENT NÀY KHÔNG
        if appointment.doctor_id != current_user.user_id:
            return jsonify({'success': False, 'message': 'Bạn không có quyền xem chuẩn đoán này'}), 403

        # KIỂM TRA THỜI GIAN - CHỈ CHO PHÉP TRONG VÒNG 1 TIẾNG TRƯỚC VÀ SAU GIỜ HẸN
        current_time = datetime.now()
        appointment_time = appointment.appointment_time
        one_hour_before = appointment_time - timedelta(hours=1)
        one_hour_after = appointment_time + timedelta(hours=1)
        is_within_time_window = one_hour_before <= current_time <= one_hour_after

        # Tìm health record dựa trên appointment_id
        health_record = HealthRecord.query.filter_by(appointment_id=appointment_id).first()

        if health_record:
            return jsonify({
                'success': True,
                'record_id': health_record.record_id,
                'symptoms': health_record.symptoms or '',
                'diagnosis': health_record.diagnosis or '',
                'prescription': health_record.prescription or '',
                'notes': health_record.notes or '',
                'appointment_status': appointment.status.value,
                'can_edit': appointment.status == AppointmentStatus.Scheduled and is_within_time_window,
                'is_within_time_window': is_within_time_window
            })
        else:
            return jsonify({
                'success': True,
                'record_id': None,
                'symptoms': '',
                'diagnosis': '',
                'prescription': '',
                'notes': '',
                'appointment_status': appointment.status.value,
                'can_edit': appointment.status == AppointmentStatus.Scheduled and is_within_time_window,
                'is_within_time_window': is_within_time_window
            })

    except Exception as e:
        app.logger.error(f"Lỗi khi lấy dữ liệu chuẩn đoán: {str(e)}")
        return jsonify({'success': False, 'message': f'Lỗi hệ thống: {str(e)}'}), 500

# patient_cập nhật thông tin cá nhân
@app.route('/api/update-patient-info', methods=['POST'])
@login_required
@role_only([RoleEnum.PATIENT])
def update_patient_info():
    try:
        data = request.get_json()

        # Kiểm tra quyền truy cập - patient chỉ được cập nhật thông tin của chính mình
        patient_id = int(data.get('patient_id'))
        if current_user.user_id != patient_id:
            return jsonify({'success': False, 'message': 'Bạn không có quyền cập nhật thông tin này'})

        # Chuẩn bị dữ liệu để cập nhật
        user_data = {
            'first_name': data.get('first_name'),
            'last_name': data.get('last_name'),
            'phone_number': data.get('phone_number'),
            'email': data.get('email'),
            'address': data.get('address'),
        }

        # Xử lý ngày sinh
        dob_str = data.get('date_of_birth')
        if dob_str:
            try:
                user_data['date_of_birth'] = datetime.strptime(dob_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'success': False, 'message': 'Định dạng ngày sinh không hợp lệ'})

        # Xử lý giới tính
        gender_str = data.get('gender')
        if gender_str:
            if gender_str in GenderEnum.__members__:
                user_data['gender'] = GenderEnum[gender_str]
            else:
                return jsonify({'success': False, 'message': 'Giới tính không hợp lệ'})

        # Chuẩn bị dữ liệu patient
        patient_data = {
            'medical_history_summary': data.get('medical_history_summary', '')
        }

        # Sử dụng DAO để cập nhật thông tin
        result = dao_patient.update_patient(patient_id, user_data, patient_data)

        if not result:
            return jsonify({'success': False, 'message': 'Cập nhật thông tin thất bại'})

        user, patient = result

        return jsonify({
            'success': True,
            'message': 'Cập nhật thông tin thành công',
            'data': {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'phone_number': user.phone_number,
                'medical_history_summary': patient.medical_history_summary if patient else ''
            }
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Lỗi khi cập nhật thông tin patient: {str(e)}")
        return jsonify({'success': False, 'message': f'Lỗi hệ thống: {str(e)}'}), 500