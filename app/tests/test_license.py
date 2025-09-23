import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, date
from app.models import DoctorLicense, Doctor, User
from app.extensions import db
from app.dao import dao_doctor_license  # Thay bằng tên file chứa DAO của bạn


class TestDAODoctorLicense(unittest.TestCase):

    def setUp(self):
        self.mock_db = MagicMock()

    # ---------- verify_doctor_license ----------
    @patch("app.dao.dao_doctor_license.DoctorLicense")
    @patch("app.dao.dao_doctor_license.Doctor")
    @patch("app.dao.dao_doctor_license.db")
    @patch("app.dao.dao_doctor_license.datetime")
    def test_verify_doctor_license_success(self, mock_datetime, mock_db, mock_doctor, mock_license):
        # Mock datetime
        mock_now = datetime(2024, 1, 1, 10, 0)
        mock_datetime.now.return_value.date.return_value = date(2024, 1, 1)

        # Mock DoctorLicense instance
        mock_license_instance = MagicMock()
        mock_license_instance.is_verified = False
        mock_license_instance.doctor_id = 1
        mock_license.query.get.return_value = mock_license_instance

        # Mock Doctor and User instances
        mock_doctor_instance = MagicMock()
        mock_user_instance = MagicMock()
        mock_doctor_instance.user = mock_user_instance
        mock_doctor.query.get.return_value = mock_doctor_instance

        # Execute
        success, message = dao_doctor_license.verify_doctor_license(license_id=1, admin_id=2)

        # Assert
        self.assertTrue(success)
        self.assertEqual(message, "Xác minh giấy phép và kích hoạt bác sĩ thành công")
        mock_license.query.get.assert_called_once_with(1)
        self.assertTrue(mock_license_instance.is_verified)
        self.assertEqual(mock_license_instance.verification_date, date(2024, 1, 1))
        self.assertEqual(mock_license_instance.verified_by_admin_id, 2)
        mock_doctor.query.get.assert_called_once_with(1)
        self.assertTrue(mock_user_instance.is_active)
        mock_db.session.commit.assert_called_once()
        mock_db.session.rollback.assert_not_called()

    @patch("app.dao.dao_doctor_license.DoctorLicense")
    @patch("app.dao.dao_doctor_license.db")
    def test_verify_doctor_license_not_found(self, mock_db, mock_license):
        # Mock query result (license not found)
        mock_license.query.get.return_value = None

        # Execute
        success, message = dao_doctor_license.verify_doctor_license(license_id=99, admin_id=2)

        # Assert
        self.assertFalse(success)
        self.assertEqual(message, "Không tìm thấy giấy phép")
        mock_license.query.get.assert_called_once_with(99)
        mock_db.session.commit.assert_not_called()
        mock_db.session.rollback.assert_not_called()

    @patch("app.dao.dao_doctor_license.DoctorLicense")
    @patch("app.dao.dao_doctor_license.db")
    def test_verify_doctor_license_already_verified(self, mock_db, mock_license):
        # Mock DoctorLicense instance (already verified)
        mock_license_instance = MagicMock()
        mock_license_instance.is_verified = True
        mock_license.query.get.return_value = mock_license_instance

        # Execute
        success, message = dao_doctor_license.verify_doctor_license(license_id=1, admin_id=2)

        # Assert
        self.assertFalse(success)
        self.assertEqual(message, "Giấy phép đã được xác minh trước đó")
        mock_license.query.get.assert_called_once_with(1)
        mock_db.session.commit.assert_not_called()
        mock_db.session.rollback.assert_not_called()

    @patch("app.dao.dao_doctor_license.DoctorLicense")
    @patch("app.dao.dao_doctor_license.Doctor")
    @patch("app.dao.dao_doctor_license.db")
    @patch("app.dao.dao_doctor_license.datetime")
    def test_verify_doctor_license_doctor_not_found(self, mock_datetime, mock_db, mock_doctor, mock_license):
        # Mock datetime
        mock_now = datetime(2024, 1, 1, 10, 0)
        mock_datetime.now.return_value.date.return_value = date(2024, 1, 1)

        # Mock DoctorLicense instance
        mock_license_instance = MagicMock()
        mock_license_instance.is_verified = False
        mock_license_instance.doctor_id = 1
        mock_license.query.get.return_value = mock_license_instance

        # Mock Doctor query (not found)
        mock_doctor.query.get.return_value = None

        # Execute
        success, message = dao_doctor_license.verify_doctor_license(license_id=1, admin_id=2)

        # Assert
        self.assertTrue(success)
        self.assertEqual(message, "Xác minh giấy phép và kích hoạt bác sĩ thành công")
        mock_license.query.get.assert_called_once_with(1)
        self.assertTrue(mock_license_instance.is_verified)
        self.assertEqual(mock_license_instance.verification_date, date(2024, 1, 1))
        self.assertEqual(mock_license_instance.verified_by_admin_id, 2)
        mock_doctor.query.get.assert_called_once_with(1)
        mock_db.session.commit.assert_called_once()
        mock_db.session.rollback.assert_not_called()

    @patch("app.dao.dao_doctor_license.DoctorLicense")
    @patch("app.dao.dao_doctor_license.Doctor")
    @patch("app.dao.dao_doctor_license.db")
    @patch("app.dao.dao_doctor_license.datetime")
    def test_verify_doctor_license_no_user(self, mock_datetime, mock_db, mock_doctor, mock_license):
        # Mock datetime
        mock_now = datetime(2024, 1, 1, 10, 0)
        mock_datetime.now.return_value.date.return_value = date(2024, 1, 1)

        # Mock DoctorLicense instance
        mock_license_instance = MagicMock()
        mock_license_instance.is_verified = False
        mock_license_instance.doctor_id = 1
        mock_license.query.get.return_value = mock_license_instance

        # Mock Doctor instance with no user
        mock_doctor_instance = MagicMock()
        mock_doctor_instance.user = None
        mock_doctor.query.get.return_value = mock_doctor_instance

        # Execute
        success, message = dao_doctor_license.verify_doctor_license(license_id=1, admin_id=2)

        # Assert
        self.assertTrue(success)
        self.assertEqual(message, "Xác minh giấy phép và kích hoạt bác sĩ thành công")
        mock_license.query.get.assert_called_once_with(1)
        self.assertTrue(mock_license_instance.is_verified)
        self.assertEqual(mock_license_instance.verification_date, date(2024, 1, 1))
        self.assertEqual(mock_license_instance.verified_by_admin_id, 2)
        mock_doctor.query.get.assert_called_once_with(1)
        mock_db.session.commit.assert_called_once()
        mock_db.session.rollback.assert_not_called()

    @patch("app.dao.dao_doctor_license.DoctorLicense")
    @patch("app.dao.dao_doctor_license.db")
    @patch("app.dao.dao_doctor_license.datetime")
    def test_verify_doctor_license_exception(self, mock_datetime, mock_db, mock_license):
        # Mock datetime
        mock_now = datetime(2024, 1, 1, 10, 0)
        mock_datetime.now.return_value.date.return_value = date(2024, 1, 1)

        # Mock DoctorLicense instance
        mock_license_instance = MagicMock()
        mock_license_instance.is_verified = False
        mock_license.query.get.return_value = mock_license_instance

        # Mock commit to raise an exception
        mock_db.session.commit.side_effect = Exception("Database error")

        # Execute
        success, message = dao_doctor_license.verify_doctor_license(license_id=1, admin_id=2)

        # Assert
        self.assertFalse(success)
        self.assertEqual(message, "Lỗi: Database error")
        mock_license.query.get.assert_called_once_with(1)
        mock_db.session.commit.assert_called_once()
        mock_db.session.rollback.assert_called_once()

if __name__ == "__main__":
    unittest.main()