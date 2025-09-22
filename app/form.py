from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import TimeField, BooleanField, TextAreaField, DecimalField
from wtforms.fields import StringField, EmailField, SubmitField, PasswordField, SelectField, DateField, IntegerField
from wtforms.validators import InputRequired, Length, NumberRange, Regexp, DataRequired, ValidationError, Email, EqualTo, Optional
from app.dao import dao_user
from app.models import DayOfWeekEnum


class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired()],
                           render_kw={"placeholder": "Tên đăng nhập"})
    password = PasswordField(validators=[InputRequired()], render_kw={"placeholder": "Mật khẩu"})
    SubmitFieldLogin = SubmitField("Đăng nhập")


class RegisterForm(FlaskForm):
    username = StringField('Tên đăng nhập', validators=[
        DataRequired(message='Tên đăng nhập là bắt buộc'),
        Length(min=3, max=50, message='Tên đăng nhập phải từ 3-50 ký tự')
    ])

    email = StringField('Email', validators=[
        DataRequired(message='Email là bắt buộc'),
        Email(message='Email không hợp lệ')
    ])

    password = PasswordField('Mật khẩu', validators=[
        DataRequired(message='Mật khẩu là bắt buộc'),
        Length(min=6, message='Mật khẩu phải có ít nhất 6 ký tự'),
        EqualTo('confirm_password', message='Mật khẩu xác nhận không khớp')
    ])

    confirm_password = PasswordField('Xác nhận mật khẩu', validators=[
        DataRequired(message='Xác nhận mật khẩu là bắt buộc')
    ])

    first_name = StringField('Họ', validators=[
        DataRequired(message='Họ là bắt buộc'),
        Length(max=50, message='Họ không được vượt quá 50 ký tự')
    ])

    last_name = StringField('Tên', validators=[
        DataRequired(message='Tên là bắt buộc'),
        Length(max=50, message='Tên không được vượt quá 50 ký tự')
    ])

    phone_number = StringField('Số điện thoại', validators=[
        DataRequired(message='Số điện thoại là bắt buộc'),
        Length(min=10, max=10, message='Số điện thoại phải từ 10 số')
    ])

    address = StringField('Địa chỉ', validators=[
        DataRequired(message='Địa chỉ là bắt buộc'),
        Length(max=200, message='Địa chỉ không được vượt quá 200 ký tự')
    ])

    date_of_birth = DateField('Ngày sinh', validators=[
        DataRequired(message='Ngày sinh là bắt buộc')
    ])

    gender = SelectField('Giới tính', choices=[
        ('MALE', 'Nam'),
        ('FEMALE', 'Nữ'),
        ('OTHER', 'Khác')
    ], validators=[DataRequired(message='Giới tính là bắt buộc')])

    submit = SubmitField('Đăng ký')

    def validate_username(self, username):
        """Custom validation cho username"""
        if dao_user.check_username_exists(username.data):
            raise ValidationError('Tên đăng nhập đã tồn tại')

    def validate_email(self, email):
        """Custom validation cho email"""
        if dao_user.check_email_exists(email.data):
            raise ValidationError('Email đã tồn tại')

    def validate_phone_number(self, phone_number):
        """Custom validation cho số điện thoại"""
        # Kiểm tra định dạng số điện thoại Việt Nam
        if not phone_number.data.isdigit():
            raise ValidationError('Số điện thoại chỉ được chứa số')

        if dao_user.check_phone_exists(phone_number.data):
            raise ValidationError('Số điện thoại đã tồn tại')


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