from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms.fields import StringField, EmailField, SubmitField, PasswordField, SelectField, DateField, IntegerField
from wtforms.validators import InputRequired, Length, NumberRange, Regexp, DataRequired, ValidationError, Email, EqualTo


class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired()],
                           render_kw={"placeholder": "Tên đăng nhập"})
    password = PasswordField(validators=[InputRequired()], render_kw={"placeholder": "Mật khẩu"})
    SubmitFieldLogin = SubmitField("Đăng nhập")
class RegisterForm(FlaskForm):
    username = StringField("Tên đăng nhập", validators=[DataRequired(), Length(min=4, max=50)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Mật khẩu", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField("Xác nhận mật khẩu", validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField("Đăng ký")