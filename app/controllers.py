import uuid
from datetime import datetime , date
from math import ceil
from flask_login import current_user, login_required, logout_user, login_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask import flash, current_app
from app.form import LoginForm, ScheduleForm
from flask import render_template , redirect , request , url_for  , session , jsonify
from app.decorators import role_only

from sqlalchemy.orm import joinedload, subqueryload
from app.models import Appointment,AppointmentStatus
import math
from app.dao import dao_authen, dao_search, dao_doctor, dao_available_slot, dao_appointment, dao_user
from app.models import Hospital, Specialty, User, Doctor, RoleEnum, Patient, DayOfWeekEnum, HealthRecord, AvailableSlot,  ConsultationType,DoctorAvailability, Review

# Thêm import
from app.dao import dao_payment
from app.vnpay_service import VNPay  # Import VNPay
import math
from app.dao import dao_authen, dao_search, dao_doctor, dao_available_slot, dao_appointment, dao_payment
from app.models import Hospital, Specialty, User, Doctor, RoleEnum, Patient, DayOfWeekEnum, HealthRecord, AvailableSlot, \
    ConsultationType, DoctorLicense


import google.oauth2.id_token
import google.auth.transport.requests
import requests
from app import app , flow  
from app.extensions import db
from app.form import LoginForm, RegisterForm



# Thôngtinchitietbacsi

@app.route("/doctor/<int:doctor_id>", endpoint="doctor_detail")
def doctor_detail(doctor_id: int):
    d = (db.session.query(Doctor)
         .options(
             joinedload(Doctor.user),
             joinedload(Doctor.specialty),
             joinedload(Doctor.hospital),
             subqueryload(Doctor.licenses),
             subqueryload(Doctor.available_slots),
             # nếu bạn đã thêm relationship:
             # subqueryload(Doctor.availabilities),
             # subqueryload(Doctor.reviews),
         )
         .filter(Doctor.doctor_id == doctor_id)
         .first_or_404())

    # Tính avg_rating 
    avg_rating = float(d.average_rating) if d.average_rating is not None else None

    # Slot trống
    upcoming_slots = [s for s in d.available_slots if not s.is_booked]
    upcoming_slots.sort(key=lambda s: (s.slot_date, s.start_time))

    # Lấy các appointment đã hoàn tất của bệnh nhân hiện tại
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
    if current_user.role == RoleEnum.PATIENT:
        appointments = dao_appointment.get_patient_appointments(current_user.user_id)
        template = 'patient_appointments.html'
    elif current_user.role == RoleEnum.DOCTOR:
        appointments = dao_appointment.get_doctor_appointments(current_user.user_id)
        template = 'doctor_appointments.html'
    else:
        flash('Chức năng này chỉ dành cho bệnh nhân và bác sĩ', 'error')
        return redirect(url_for('home'))

    return render_template(template, appointments=appointments)


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