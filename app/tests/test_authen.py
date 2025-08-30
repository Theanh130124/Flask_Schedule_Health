# test_dao.py
import unittest
import hashlib
from unittest.mock import patch, MagicMock
from app.dao import dao_authen


class TestDAO(unittest.TestCase):

    # ---------- get_info_by_id ----------
    @patch("app.dao.dao_authen.User")
    def test_get_info_by_id_success(self, mock_user):
        fake_user = MagicMock(id=1, username="theanh")
        mock_user.query.get.return_value = fake_user

        result = dao_authen.get_info_by_id(1)

        self.assertIsNotNone(result)
        self.assertEqual(result.id, 1)
        self.assertEqual(result.username, "theanh")
        mock_user.query.get.assert_called_once_with(1)

    @patch("app.dao.dao_authen.User")
    def test_get_info_by_id_fail(self, mock_user):
        mock_user.query.get.return_value = None

        result = dao_authen.get_info_by_id(99)

        self.assertIsNone(result)
        mock_user.query.get.assert_called_once_with(99)

    # ---------- get_doctor_by_userid ----------
    @patch("app.dao.dao_authen.Doctor")
    def test_get_doctor_by_userid_success(self, mock_doctor):
        fake_doctor = MagicMock(doctor_id=99)
        mock_doctor.query.filter_by.return_value.first.return_value = fake_doctor

        result = dao_authen.get_doctor_by_userid(99)

        self.assertIsNotNone(result)
        self.assertEqual(result.doctor_id, 99)
        mock_doctor.query.filter_by.assert_called_once_with(doctor_id=99)

    @patch("app.dao.dao_authen.Doctor")
    def test_get_doctor_by_userid_fail(self, mock_doctor):
        mock_doctor.query.filter_by.return_value.first.return_value = None

        result = dao_authen.get_doctor_by_userid(123)

        self.assertIsNone(result)
        mock_doctor.query.filter_by.assert_called_once_with(doctor_id=123)

    # ---------- auth_user ----------
    @patch("app.dao.dao_authen.User")
    def test_auth_user_success(self, mock_user):
        fake_user = MagicMock(username="theanh",
                              password=hashlib.md5("123".encode("utf-8")).hexdigest())
        mock_user.query.filter.return_value.first.return_value = fake_user

        result = dao_authen.auth_user("theanh", "123")

        self.assertIsNotNone(result)
        self.assertEqual(result.username, "theanh")

    @patch("app.dao.dao_authen.User")
    def test_auth_user_fail(self, mock_user):
        mock_user.query.filter.return_value.first.return_value = None

        result = dao_authen.auth_user("wrong", "pass")

        self.assertIsNone(result)

    # ---------- get_user_by_username ----------
    @patch("app.dao.dao_authen.User")
    def test_get_user_by_username_success(self, mock_user):
        fake_user = MagicMock(username="theanh")
        mock_user.query.filter_by.return_value.first.return_value = fake_user

        result = dao_authen.get_user_by_username("theanh")

        self.assertIsNotNone(result)
        self.assertEqual(result.username, "theanh")
        mock_user.query.filter_by.assert_called_once_with(username="theanh")

    @patch("app.dao.dao_authen.User")
    def test_get_user_by_username_fail(self, mock_user):
        mock_user.query.filter_by.return_value.first.return_value = None

        result = dao_authen.get_user_by_username("ghost")

        self.assertIsNone(result)
        mock_user.query.filter_by.assert_called_once_with(username="ghost")

    # ---------- check_password_md5 ----------
    def test_check_password_md5_success(self):
        fake_user = MagicMock(password=hashlib.md5("123".encode("utf-8")).hexdigest())

        result = dao_authen.check_password_md5(fake_user, "123")
        self.assertTrue(result)

    def test_check_password_md5_fail(self):
        fake_user = MagicMock(password=hashlib.md5("123".encode("utf-8")).hexdigest())

        result = dao_authen.check_password_md5(fake_user, "wrongpass")
        self.assertFalse(result)

    def test_check_password_md5_no_user(self):
        result = dao_authen.check_password_md5(None, "123")
        self.assertFalse(result)

    # ---------- check_email_exists ----------
    @patch("app.dao.dao_authen.User")
    def test_check_email_exists_true(self, mock_user):
        mock_user.query.filter_by.return_value.first.return_value = MagicMock()

        result = dao_authen.check_email_exists("test@example.com")

        self.assertTrue(result)
        mock_user.query.filter_by.assert_called_once_with(email="test@example.com")

    @patch("app.dao.dao_authen.User")
    def test_check_email_exists_false(self, mock_user):
        mock_user.query.filter_by.return_value.first.return_value = None

        result = dao_authen.check_email_exists("notfound@example.com")

        self.assertFalse(result)
        mock_user.query.filter_by.assert_called_once_with(email="notfound@example.com")

    # ---------- check_phone_exists ----------
    @patch("app.dao.dao_authen.User")
    def test_check_phone_exists_true(self, mock_user):
        mock_user.query.filter_by.return_value.first.return_value = MagicMock()

        result = dao_authen.check_phone_exists("0123456789")

        self.assertTrue(result)
        mock_user.query.filter_by.assert_called_once_with(phone="0123456789")

    @patch("app.dao.dao_authen.User")
    def test_check_phone_exists_false(self, mock_user):
        mock_user.query.filter_by.return_value.first.return_value = None

        result = dao_authen.check_phone_exists("0000000000")

        self.assertFalse(result)
        mock_user.query.filter_by.assert_called_once_with(phone="0000000000")


if __name__ == "__main__":
    unittest.main()
