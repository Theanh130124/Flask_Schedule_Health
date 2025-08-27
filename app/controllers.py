from flask_login import current_user, login_required, logout_user, login_user
from flask import render_template, redirect, request, url_for, session, jsonify
from app import app, flow, db  
from app.form import LoginForm
from app.decorators import role_only
from app.dao import dao_authen, dao_search
from app.models import Hospital, Specialty, User, Doctor, RoleEnum  # ✅ thêm RoleEnum
import google.oauth2.id_token
import google.auth.transport.requests
import requests

# -------- AUTOCOMPLETE APIs --------

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
                   User.role == RoleEnum.DOCTOR,                 # ✅ Enum, không dùng chuỗi
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
    # ✅ dùng validate_on_submit thay vì gọi field Submit
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
    if request.args.get("state") != session.get("state"):
        return "State mismatch!", 400

    try:
        flow.fetch_token(authorization_response=request.url)

        credentials = flow.credentials
        request_session = requests.session()
        token_request = google.auth.transport.requests.Request(session=request_session)

        id_info = google.oauth2.id_token.verify_oauth2_token(
            id_token=credentials._id_token,
            request=token_request,
            audience=flow.client_config["client_id"],
            clock_skew_in_seconds=10
        )

        email = id_info.get("email")
        name = id_info.get("name") or ""

        user = dao_authen.get_user_by_username(email)
        if not user:
            # ✅ tránh NOT NULL: phone_number/address phải có giá trị
            first = name.split(" ")[0] if name else "Google"
            last = " ".join(name.split(" ")[1:]) if name and len(name.split()) > 1 else "User"
            user = User(
                username=email,
                email=email,
                password="",                 # cột password đang nullable=False
                role=RoleEnum.PATIENT,
                first_name=first,
                last_name=last,
                phone_number="0000000000",   # tránh null
                address="Unknown"            # tránh null
            )
            db.session.add(user)
            db.session.commit()

        login_user(user)
        return redirect(url_for("index_controller"))

    except Exception as e:
        app.logger.error(f"OAuth Callback Error: {e}")
        return f"Login failed: {e}", 400
