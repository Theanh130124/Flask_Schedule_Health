from functools import wraps
from flask import session, redirect, url_for, flash, abort
from flask_login import current_user


def role_only(role):
    def wrap(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.role not in role:
                flash("Bạn không có quyền thực hiện chức năng này", "forbidden")
                return redirect(url_for("index_controller"))
            else:
                return f(*args, **kwargs)
        return decorated_function
    return wrap