from flask_login import current_user, login_required, logout_user, login_user

from app.form import LoginForm
from app.models import RoleEnum
from flask import render_template , redirect , request , url_for  , session
from app.decorators import role_only
import math
import google.oauth2.id_token
import google.auth.transport.requests
import requests
from app import app , flow ,db #là import __init__
from app.form import LoginForm
from app.dao import dao_authen
from app.models import User


#Navigate cho đăng nhập hoac chưa
def index_controller():
    if current_user.is_authenticated:
        if current_user.user_role == RoleEnum.ADMIN:
            return redirect("/admin")
        return redirect("/home")
    return redirect('/login')


# Nếu truyền url_for sẽ vào function -> truyền redirect thì vào theo tên .html
@login_required #-> có login_required bắt buộc phải đăng nhập (current_user.is_authenticated == True )
@role_only([RoleEnum.ADMIN,RoleEnum.PATIENT])
def home():
    page = request.args.get('page', 1 , type=int) # này giữ vậy
    total = 3 #nữa thêm sao
    return render_template('index.html',  current_page=page,
                           total_pages=math.ceil(total/app.config["PAGE_SIZE"]) )  # Trang home (index.html)


def login():
    mse = ""
    form = LoginForm()
    if request.method == "POST" and form.SubmitFieldLogin():
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
    # luôn yêu cầu quyền offline để lấy refresh_token
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"   # bắt user chọn lại account, tránh lỗi reused code
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
                phone_number="0000000000",  # placeholder
                address="Unknown"
            )
            db.session.add(user)
            db.session.commit()

        login_user(user)

        return redirect(url_for("index_controller"))

    except Exception as e:
        app.logger.error(f"OAuth Callback Error: {e}")
        return f"Login failed: {e}", 400