import hashlib
from app.models import User
from flask_login import current_user


def get_info_by_id(id):
    return User.query.get(id)

def get_doctor_by_userid(userid):
    return User.query.get(userid)

def auth_user(username , password):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    return User.query.filter(User.username.__eq__(username.strip()),
                             User.password.__eq__(password)).first()
