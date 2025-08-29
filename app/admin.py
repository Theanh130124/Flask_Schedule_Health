
from flask_login import logout_user, current_user
from flask_admin.contrib.sqla import ModelView
from app.models import RoleEnum
from flask_admin import expose, BaseView , Admin
from app.extensions import db
from app import app
from flask import redirect, request
from app.models import User
import hashlib
# De authen
class AuthenticatedView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == RoleEnum.ADMIN


class LogoutView(BaseView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect('/admin')

    #Doctor sẽ không thấy nút
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role ==  RoleEnum.ADMIN  # Phải có dòng sau này để người dùng DOCTOR không thể truy cập admin


class LoginUserView(BaseView):
    @expose('/')
    def index(self):
        return redirect('/login')
    def is_accessible(self):
        return not current_user.is_authenticated



class UserView(AuthenticatedView):
    column_list = ['username', 'password','email' , 'first_name', 'last_name', 'phone_number' , 'address','date_of_birth', 'gender', 'role',]

    column_labels = {
        'username': 'Tên đăng nhập',
        'password': 'Mật khẩu',
        'email':'Địa chỉ email',
        'date_of_birth':"Ngày sinh",
        'gender':'Giới tính',
        'last_name': 'Họ',
        'first_name':'Tên',
        'phone_number':"SĐT",
        "address":"Địa chỉ",
        'role': 'Vai trò',
        'is_active': 'Trạng thái',
    }

    column_filters = [
        'username',
        'role',
        'is_active',
    ]
    can_view_details = True


    #Để sửa pass thì băm
    def on_model_change(self, form, model, is_created):

        def hash_password(password):
            return str(hashlib.md5(password.encode('utf-8')).hexdigest())

        if is_created:
            model.password = hash_password(form.password.data)
        elif form.password.data:
            model.password = hash_password(form.password.data)
        return super().on_model_change(form, model, is_created)







admin = Admin(app, name='Quản lý Đặt lịch khám trực tuyến', template_mode='bootstrap4' )
admin.add_view(UserView(User, db.session, name='Người dùng'))
admin.add_view(LogoutView(name='Đăng xuất'))
admin.add_view(LoginUserView(name='Về trang đăng nhập người dùng'))
