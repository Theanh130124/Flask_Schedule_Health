from app import app, db , login
from flask_login import current_user
from app.dao import dao_authen
from app import controllers


# Hàm này luôn truyền các info vào -> .html nao cung co
@app.context_processor
def common_attr():
    if current_user.is_authenticated:
        user = dao_authen.get_info_by_id(current_user.user_id)
        doctor = dao_authen.get_doctor_by_userid(current_user.user_id)
        return {
            'user': user,
            'doctor': doctor,
        }
    return {}

#Chi Flask lay user
@login.user_loader
def user_load(user_id):
    return dao_authen.get_info_by_id(user_id)


app.add_url_rule("/", "index_controller", controllers.index_controller) ##Navigate cho đăng nhập hoac chưa
app.add_url_rule("/home",'home', controllers.home)
app.add_url_rule("/login",'login' ,controllers.login ,methods=['GET', 'POST'])
app.add_url_rule("/logout",'logout_my_user',controllers.logout_my_user , methods=['get'])


app.add_url_rule("/oauth" , 'login_oauth', controllers.login_oauth)
app.add_url_rule("/callback" , 'oauth_callback', controllers.oauth_callback)

print("c")
print("c")
print("c")
print("c")
print("c")
print("c")
print("c")
if __name__ == '__main__':
#  with app.app_context():
        # db.create_all()   # Tạo tất cả bảng trong database

 app.run(host="localhost", port=5000, debug=True)
