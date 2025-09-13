import uuid

from flask_login import current_user, login_required, logout_user, login_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask import flash
from app.form import LoginForm
from flask import render_template , redirect , request , url_for  , session , jsonify
from app.decorators import role_only

import math
from app.dao import dao_authen, dao_search
from app.models import Hospital, Specialty, User, Doctor, RoleEnum, Patient

import google.oauth2.id_token
import google.auth.transport.requests
import requests
from app import app , flow  #là import __init__
from app.extensions import db
from app.models import Hospital, Specialty, User, Doctor, RoleEnum
from app.form import LoginForm, RegisterForm
from app.dao import dao_authen, dao_user, dao_search
from app.models import User
from datetime import date



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
                db.session.commit()
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

@app.route("/patients/search")
@login_required
def patient_search():

    return render_template("patient_search.html")

@app.route("/api/patients")
@login_required
def api_patients():
    """
    API trả về danh sách bệnh nhân theo từng filter (search + lọc ).
    Dùng cho giao diện Patient Search (Bootstrap/React).
    """
    # Query string từ URL
    q = (request.args.get("q", "") or "").strip()
    phone = (request.args.get("phone", "") or "").strip()
    active = request.args.get("active")  # "1", "0" hoặc None
    inactive = request.args.get("inactive")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 50))

    query = User.query.filter(User.role == RoleEnum.PATIENT)

    # Lọc theo từ khóa
    if q:
        query = query.filter(
            (User.first_name.ilike(f"%{q}%")) |
            (User.last_name.ilike(f"%{q}%")) |
            (User.username.ilike(f"%{q}%")) |
            (User.email.ilike(f"%{q}%")) |
            (User.phone_number.ilike(f"%{q}%"))
        )

    # Lọc theo trạng thái
    if active == "1" and inactive != "1":
        query = query.filter(User.is_active == True)
    elif inactive == "1" and active != "1":
        query = query.filter(User.is_active == False)
    # lọc theo số điện thoại
    if phone:
        query = query.filter(User.phone_number.ilike(f"%{phone}%"))

    # Phân trang
    patients = (query.order_by(User.last_name.asc(), User.first_name.asc())
                     .offset((page - 1) * per_page)
                     .limit(per_page)
                     .all())

    # Trả JSON
    return jsonify([
        {
            "id": u.user_id,
            "name": f"{u.first_name} {u.last_name}",
            "age": u.get_age() if hasattr(u, "get_age") else None,
            "gender": u.gender.name if u.gender else None,
            "contact": u.phone_number,
            "last_visit_date": u.last_visit_date.strftime("%Y-%m-%d") if getattr(u, "last_visit_date", None) else None
        }
        for u in patients
    ])

# chi tiết sổ tay khám bệnh của patient
@app.route("/patients/<int:patient_id>")
@login_required
def patient_detail(patient_id):
    """
    Xem chi tiết 1 bệnh nhân (theo ID).
    """
    patient = User.query.filter_by(user_id=patient_id, role=RoleEnum.PATIENT).first_or_404()
    return render_template("patient_detail.html", patient=patient)

