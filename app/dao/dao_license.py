from datetime import datetime
from app.extensions import db
from app.models import DoctorLicense, Doctor


def verify_doctor_license(license_id, admin_id):
    """
    Xác minh giấy phép bác sĩ và kích hoạt tài khoản bác sĩ
    """
    try:
        # Lấy giấy phép
        license = DoctorLicense.query.get(license_id)
        if not license:
            return False, "Không tìm thấy giấy phép"

        # Kiểm tra xem giấy phép đã được xác minh chưa
        if license.is_verified:
            return False, "Giấy phép đã được xác minh trước đó"

        # Cập nhật thông tin xác minh giấy phép
        license.is_verified = True
        license.verification_date = datetime.now().date()
        license.verified_by_admin_id = admin_id

        # Lấy bác sĩ và kích hoạt tài khoản
        doctor = Doctor.query.get(license.doctor_id)
        if doctor and doctor.user:
            doctor.user.is_active = True

        db.session.commit()
        return True, "Xác minh giấy phép và kích hoạt bác sĩ thành công"

    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi: {str(e)}"