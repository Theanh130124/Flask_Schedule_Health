from flask_login import current_user , login_user , logout_user , login_required

from app.form import LoginForm
from app.models import RoleEnum
from flask import render_template , redirect , request , url_for
from app.decorators import role_only
import math
from app import app  #là import __init__
from app.form import LoginForm
from app.dao import dao_authen


def index_controller():
    if current_user.is_authenticated:
        if current_user.user_role == RoleEnum.ADMIN:
            return redirect("/admin")
        return redirect("/home")
    return redirect('/login')


# Nếu truyền url_for sẽ vào function -> truyền redirect thì vào theo tên .html
@login_required
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