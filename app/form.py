from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import TimeField, BooleanField, TextAreaField, DecimalField
from wtforms.fields import StringField, EmailField, SubmitField, PasswordField, SelectField, DateField, IntegerField
from wtforms.validators import InputRequired, Length, NumberRange, Regexp, DataRequired, ValidationError, Email, EqualTo, Optional

from app.models import DayOfWeekEnum


class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired()],
                           render_kw={"placeholder": "Tên đăng nhập"})
    password = PasswordField(validators=[InputRequired()], render_kw={"placeholder": "Mật khẩu"})
    SubmitFieldLogin = SubmitField("Đăng nhập")

class RegisterForm(FlaskForm):
    # Các trường bắt buộc theo schema của bạn (NOT NULL)
    username = StringField(
        "Tên đăng nhập",
        validators=[DataRequired(), Length(min=4, max=100)],
        render_kw={"placeholder": "Tên đăng nhập"}
    )
    email = EmailField(
        "Email",
        validators=[DataRequired(), Email(), Length(max=255)],
        render_kw={"placeholder": "Email"}
    )
    password = PasswordField(
        "Mật khẩu",
        validators=[DataRequired(), Length(min=6)],
        render_kw={"placeholder": "Mật khẩu"}
    )
    confirm_password = PasswordField(
        "Xác nhận mật khẩu",
        validators=[DataRequired(), EqualTo("password", message="Mật khẩu không khớp")],
        render_kw={"placeholder": "Xác nhận mật khẩu"}
    )
    # Họ / Tên (cần thiết theo schema)
    first_name = StringField(
        "Họ",
        validators=[DataRequired(), Length(min=1, max=100)],
        render_kw={"placeholder": "Họ (ví dụ: Nguyễn)"}
    )
    last_name = StringField(
        "Tên",
        validators=[DataRequired(), Length(min=1, max=100)],
        render_kw={"placeholder": "Tên (ví dụ: Kiên An)"}
    )
    # SĐT và địa chỉ (bắt buộc)
    phone_number = StringField(
        "Số điện thoại",
        validators=[
            DataRequired(),
            Length(min=8, max=20),
            Regexp(r'^\+?\d[\d\s\-]{6,}$', message="Số điện thoại không hợp lệ")
        ],
        render_kw={"placeholder": "Số điện thoại (ví dụ: +84901234567)"}
    )
    address = StringField(
        "Địa chỉ",
        validators=[DataRequired(), Length(min=3, max=500)],
        render_kw={"placeholder": "Địa chỉ"}
    )
    # Những trường không bắt buộc (DB cho phép NULL)
    date_of_birth = DateField(
        "Ngày sinh",
        format="%Y-%m-%d",
        validators=[Optional()],
        render_kw={"placeholder": "YYYY-MM-DD"}
    )
    gender = SelectField(
        "Giới tính",
        choices=[("MALE", "Nam"), ("FEMALE", "Nữ"), ("OTHER", "Khác")],
        validators=[Optional()]
    )
    submit = SubmitField("Đăng ký")


class ScheduleForm(FlaskForm):
    day_of_week = SelectField('Ngày trong tuần', choices=[(day.name, day.value) for day in DayOfWeekEnum],
                              validators=[DataRequired()])
    start_time = TimeField('Giờ bắt đầu', format='%H:%M', validators=[DataRequired()])
    end_time = TimeField('Giờ kết thúc', format='%H:%M', validators=[DataRequired()])
    is_available = BooleanField('Có sẵn', default=True)
    submit = SubmitField("Đăng ký")
# User -- những thông tin thường sử dụng và thay đổi

class BaseUserForm(FlaskForm):
    first_name = StringField(
        "Họ", validators=[DataRequired(), Length(min=1, max=100)]
    )
    last_name = StringField(
        "Tên", validators=[DataRequired(), Length(min=1, max=100)]
    )
    phone_number = StringField(
        "Số điện thoại",
        validators=[DataRequired(), Length(min=8, max=20)]
    )
    address = StringField(
        "Địa chỉ", validators=[DataRequired(), Length(min=3, max=500)]
    )
    date_of_birth = DateField(
        "Ngày sinh", format="%Y-%m-%d", validators=[Optional()]
    )
    gender = SelectField(
        "Giới tính",
        choices=[("MALE", "Nam"), ("FEMALE", "Nữ"), ("OTHER", "Khác")],
        validators=[Optional()]
    )


class PatientUpdateForm(BaseUserForm):
    medical_history_summary = StringField(
        "Tiền sử bệnh án",
        validators=[Optional(), Length(max=500)],
        render_kw={"placeholder": "Ví dụ: Bệnh tim, tiểu đường..."}
    )


    submit = SubmitField("Cập nhật")


class DoctorUserForm(FlaskForm):
    # User fields
    username = StringField('Tên đăng nhập', validators=[DataRequired(), Length(min=3, max=100)])
    password = PasswordField('Mật khẩu', validators=[DataRequired(), Length(min=6)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('Tên', validators=[DataRequired()])
    last_name = StringField('Họ', validators=[DataRequired()])
    phone_number = StringField('Số điện thoại', validators=[DataRequired()])
    address = TextAreaField('Địa chỉ', validators=[DataRequired()])
    date_of_birth = StringField('Ngày sinh (YYYY-MM-DD)')
    gender = SelectField('Giới tính', choices=[
        ('MALE', 'Nam'),
        ('FEMALE', 'Nữ'),
        ('OTHER', 'Khác')
    ])

    # Doctor fields
    hospital_id = SelectField('Bệnh viện', coerce=int, validators=[DataRequired()])
    specialty_id = SelectField('Chuyên khoa', coerce=int, validators=[DataRequired()])
    years_experience = IntegerField('Số năm kinh nghiệm', default=0)
    educational_level = StringField('Trình độ học vấn', validators=[DataRequired()])
    bio = TextAreaField('Tiểu sử')
    consultation_fee = DecimalField('Phí tư vấn', places=2, default=0.00)

    # License fields (optional)
    license_number = StringField('Số giấy phép')
    issuing_authority = StringField('Cơ quan cấp')
    issue_date = StringField('Ngày cấp (YYYY-MM-DD)')
    expiry_date = StringField('Ngày hết hạn (YYYY-MM-DD)')