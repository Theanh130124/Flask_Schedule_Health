import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, date
from app.models import User, Patient, RoleEnum
from app.extensions import db
import hashlib
from app.dao import dao_user  # Thay bằng tên file chứa DAO của bạn
from app.dao import dao_healthrecord


class TestDAOUser(unittest.TestCase):

    def setUp(self):
        self.mock_db = MagicMock()

    # ---------- create_user_with_role ----------
    @patch("app.dao.dao_user.User")
    @patch("app.dao.dao_user.Patient")
    @patch("app.dao.dao_user.db")
    @patch("app.dao.dao_user.dao_healthrecord")
    @patch("app.dao.dao_user.check_username_exists")
    @patch("app.dao.dao_user.check_email_exists")
    @patch("app.dao.dao_user.check_phone_exists")
    def test_create_user_with_role_patient_success(self, mock_check_phone, mock_check_email, mock_check_username, mock_healthrecord, mock_db, mock_patient, mock_user):
        # Mock checks for existing user
        mock_check_username.return_value = False
        mock_check_email.return_value = False
        mock_check_phone.return_value = False

        # Mock User and Patient instances
        mock_user_instance = MagicMock()
        mock_user_instance.user_id = 1
        mock_user.return_value = mock_user_instance
        mock_patient_instance = MagicMock()
        mock_patient.return_value = mock_patient_instance

        # Mock health record creation
        mock_healthrecord.create_empty_health_record.return_value = MagicMock()

        # Execute
        result = dao_user.create_user_with_role(
            username="johndoe",
            email="john@example.com",
            password="password123",
            first_name="John",
            last_name="Doe",
            phone_number="1234567890",
            address="123 Main St",
            date_of_birth=date(1990, 5, 1),
            gender="Male",
            role=RoleEnum.PATIENT
        )

        # Assert
        self.assertEqual(result, mock_user_instance)
        mock_check_username.assert_called_once_with("johndoe")
        mock_check_email.assert_called_once_with("john@example.com")
        mock_check_phone.assert_called_once_with("1234567890")
        mock_user.assert_called_once_with(
            username="johndoe",
            email="john@example.com",
            password=hashlib.md5("password123".encode("utf-8")).hexdigest(),
            first_name="John",
            last_name="Doe",
            phone_number="1234567890",
            address="123 Main St",
            date_of_birth=date(1990, 5, 1),
            gender="Male",
            role=RoleEnum.PATIENT,
            is_active=True
        )
        mock_db.session.add.assert_any_call(mock_user_instance)
        mock_patient.assert_called_once_with(patient_id=1)
        mock_db.session.add.assert_any_call(mock_patient_instance)
        mock_healthrecord.create_empty_health_record.assert_called_once_with(1)
        mock_db.session.commit.assert_called_once()
        mock_db.session.rollback.assert_not_called()

    @patch("app.dao.dao_user.check_username_exists")
    def test_create_user_with_role_username_exists(self, mock_check_username):
        # Mock username exists
        mock_check_username.return_value = True

        # Execute
        result = dao_user.create_user_with_role(
            username="johndoe",
            email="john@example.com",
            password="password123",
            first_name="John",
            last_name="Doe",
            phone_number="1234567890",
            address="123 Main St"
        )

        # Assert
        self.assertIsNone(result)
        mock_check_username.assert_called_once_with("johndoe")

    @patch("app.dao.dao_user.check_email_exists")
    @patch("app.dao.dao_user.check_username_exists")
    def test_create_user_with_role_email_exists(self, mock_check_username, mock_check_email):
        # Mock email exists
        mock_check_username.return_value = False
        mock_check_email.return_value = True

        # Execute
        result = dao_user.create_user_with_role(
            username="johndoe",
            email="john@example.com",
            password="password123",
            first_name="John",
            last_name="Doe",
            phone_number="1234567890",
            address="123 Main St"
        )

        # Assert
        self.assertIsNone(result)
        mock_check_email.assert_called_once_with("john@example.com")

    @patch("app.dao.dao_user.check_phone_exists")
    @patch("app.dao.dao_user.check_email_exists")
    @patch("app.dao.dao_user.check_username_exists")
    def test_create_user_with_role_phone_exists(self, mock_check_username, mock_check_email, mock_check_phone):
        # Mock phone exists
        mock_check_username.return_value = False
        mock_check_email.return_value = False
        mock_check_phone.return_value = True

        # Execute
        result = dao_user.create_user_with_role(
            username="johndoe",
            email="john@example.com",
            password="password123",
            first_name="John",
            last_name="Doe",
            phone_number="1234567890",
            address="123 Main St"
        )

        # Assert
        self.assertIsNone(result)
        mock_check_phone.assert_called_once_with("1234567890")

    @patch("app.dao.dao_user.User")
    @patch("app.dao.dao_user.db")
    @patch("app.dao.dao_user.check_username_exists")
    @patch("app.dao.dao_user.check_email_exists")
    @patch("app.dao.dao_user.check_phone_exists")
    def test_create_user_with_role_exception(self, mock_check_phone, mock_check_email, mock_check_username, mock_db, mock_user):
        # Mock checks for existing user
        mock_check_username.return_value = False
        mock_check_email.return_value = False
        mock_check_phone.return_value = False

        # Mock User instance
        mock_user_instance = MagicMock()
        mock_user_instance.user_id = 1
        mock_user.return_value = mock_user_instance

        # Mock commit to raise an exception
        mock_db.session.commit.side_effect = Exception("Database error")

        # Execute
        result = dao_user.create_user_with_role(
            username="johndoe",
            email="john@example.com",
            password="password123",
            first_name="John",
            last_name="Doe",
            phone_number="1234567890",
            address="123 Main St",
            role=RoleEnum.PATIENT
        )

        # Assert
        self.assertIsNone(result)
        mock_db.session.rollback.assert_called_once()

    # ---------- check_email_exists ----------
    @patch("app.dao.dao_user.User")
    def test_check_email_exists_true(self, mock_user):
        # Mock query result
        mock_query = MagicMock()
        mock_query.filter_by.return_value.first.return_value = MagicMock()
        mock_user.query = mock_query

        # Execute
        result = dao_user.check_email_exists("john@example.com")

        # Assert
        self.assertTrue(result)
        mock_query.filter_by.assert_called_once_with(email="john@example.com")

    @patch("app.dao.dao_user.User")
    def test_check_email_exists_false(self, mock_user):
        # Mock query result (not found)
        mock_query = MagicMock()
        mock_query.filter_by.return_value.first.return_value = None
        mock_user.query = mock_query

        # Execute
        result = dao_user.check_email_exists("john@example.com")

        # Assert
        self.assertFalse(result)
        mock_query.filter_by.assert_called_once_with(email="john@example.com")

    # ---------- check_username_exists ----------
    @patch("app.dao.dao_user.User")
    def test_check_username_exists_true(self, mock_user):
        # Mock query result
        mock_query = MagicMock()
        mock_query.filter_by.return_value.first.return_value = MagicMock()
        mock_user.query = mock_query

        # Execute
        result = dao_user.check_username_exists("johndoe")

        # Assert
        self.assertTrue(result)
        mock_query.filter_by.assert_called_once_with(username="johndoe")

    @patch("app.dao.dao_user.User")
    def test_check_username_exists_false(self, mock_user):
        # Mock query result (not found)
        mock_query = MagicMock()
        mock_query.filter_by.return_value.first.return_value = None
        mock_user.query = mock_query

        # Execute
        result = dao_user.check_username_exists("johndoe")

        # Assert
        self.assertFalse(result)
        mock_query.filter_by.assert_called_once_with(username="johndoe")

    # ---------- check_phone_exists ----------
    @patch("app.dao.dao_user.User")
    def test_check_phone_exists_true(self, mock_user):
        # Mock query result
        mock_query = MagicMock()
        mock_query.filter_by.return_value.first.return_value = MagicMock()
        mock_user.query = mock_query

        # Execute
        result = dao_user.check_phone_exists("1234567890")

        # Assert
        self.assertTrue(result)
        mock_query.filter_by.assert_called_once_with(phone_number="1234567890")

    @patch("app.dao.dao_user.User")
    def test_check_phone_exists_false(self, mock_user):
        # Mock query result (not found)
        mock_query = MagicMock()
        mock_query.filter_by.return_value.first.return_value = None
        mock_user.query = mock_query

        # Execute
        result = dao_user.check_phone_exists("1234567890")

        # Assert
        self.assertFalse(result)
        mock_query.filter_by.assert_called_once_with(phone_number="1234567890")

    # ---------- get_user_by_username ----------
    @patch("app.dao.dao_user.User")
    def test_get_user_by_username_success(self, mock_user):
        # Mock query result
        mock_user_instance = MagicMock()
        mock_query = MagicMock()
        mock_query.filter_by.return_value.first.return_value = mock_user_instance
        mock_user.query = mock_query

        # Execute
        result = dao_user.get_user_by_username("johndoe")

        # Assert
        self.assertEqual(result, mock_user_instance)
        mock_query.filter_by.assert_called_once_with(username="johndoe")

    @patch("app.dao.dao_user.User")
    def test_get_user_by_username_not_found(self, mock_user):
        # Mock query result (not found)
        mock_query = MagicMock()
        mock_query.filter_by.return_value.first.return_value = None
        mock_user.query = mock_query

        # Execute
        result = dao_user.get_user_by_username("johndoe")

        # Assert
        self.assertIsNone(result)
        mock_query.filter_by.assert_called_once_with(username="johndoe")

if __name__ == "__main__":
    unittest.main()