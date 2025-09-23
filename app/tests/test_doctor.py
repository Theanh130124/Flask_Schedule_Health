import unittest
from unittest.mock import patch, MagicMock
from datetime import time
from app.models import User, Doctor, DoctorAvailability, DayOfWeekEnum
from app.dao import dao_doctor_availability  # Thay bằng tên file chứa DAO của bạn
from app.extensions import db


class TestDAODoctorAvailability(unittest.TestCase):

    def setUp(self):
        self.mock_db = MagicMock()

    # ---------- get_list_doctor ----------
    @patch("app.dao.dao_doctor_availability.Doctor")
    def test_get_list_doctor_success(self, mock_doctor):
        # Mock query result
        fake_doctors = [MagicMock(), MagicMock()]
        mock_query = MagicMock()
        mock_query.join.return_value.order_by.return_value.all.return_value = fake_doctors
        mock_doctor.query = mock_query

        # Execute
        result = dao_doctor_availability.get_list_doctor()

        # Assert
        self.assertEqual(len(result), 2)
        mock_query.join.assert_called_with(User)
        mock_query.join.return_value.order_by.assert_called_with(User.first_name, User.last_name)
        mock_query.join.return_value.order_by.return_value.all.assert_called_once()

    # ---------- create_doctor_availability ----------
    @patch("app.dao.dao_doctor_availability.DoctorAvailability")
    @patch("app.dao.dao_doctor_availability.db")
    def test_create_doctor_availability_new_success(self, mock_db, mock_availability):
        # Mock query result (no existing availability)
        mock_availability.query.filter_by.return_value.first.return_value = None

        # Execute
        result = dao_doctor_availability.create_doctor_availability(
            doctor_id=1,
            day_of_week="Monday",
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_available=True
        )

        # Assert
        self.assertTrue(result)
        mock_availability.query.filter_by.assert_called_with(
            doctor_id=1,
            day_of_week=DayOfWeekEnum.Monday
        )
        mock_db.session.add.assert_called_once()
        mock_db.session.commit.assert_called_once()

    @patch("app.dao.dao_doctor_availability.DoctorAvailability")
    @patch("app.dao.dao_doctor_availability.db")
    def test_create_doctor_availability_update_success(self, mock_db, mock_availability):
        # Mock existing availability
        mock_existing = MagicMock()
        mock_availability.query.filter_by.return_value.first.return_value = mock_existing

        # Execute
        result = dao_doctor_availability.create_doctor_availability(
            doctor_id=1,
            day_of_week="Monday",
            start_time=time(10, 0),
            end_time=time(18, 0),
            is_available=False
        )

        # Assert
        self.assertTrue(result)
        mock_availability.query.filter_by.assert_called_with(
            doctor_id=1,
            day_of_week=DayOfWeekEnum.Monday
        )
        self.assertEqual(mock_existing.start_time, time(10, 0))
        self.assertEqual(mock_existing.end_time, time(18, 0))
        self.assertFalse(mock_existing.is_available)
        mock_db.session.add.assert_not_called()
        mock_db.session.commit.assert_called_once()

    @patch("app.dao.dao_doctor_availability.DoctorAvailability")
    @patch("app.dao.dao_doctor_availability.db")
    def test_create_doctor_availability_invalid_day(self, mock_db, mock_availability):
        # Mock query result
        mock_availability.query.filter_by.return_value.first.side_effect = KeyError("Invalid day")

        # Execute
        result = dao_doctor_availability.create_doctor_availability(
            doctor_id=1,
            day_of_week="InvalidDay",
            start_time=time(9, 0),
            end_time=time(17, 0)
        )

        # Assert
        self.assertTrue(result)  # Hàm vẫn commit dù có lỗi KeyError
        mock_db.session.commit.assert_called_once()

    # ---------- get_doctor_availabilities ----------
    @patch("app.dao.dao_doctor_availability.DoctorAvailability")
    def test_get_doctor_availabilities_success(self, mock_availability):
        # Mock query result
        fake_availabilities = [MagicMock(), MagicMock()]
        mock_query = MagicMock()
        mock_query.filter_by.return_value.all.return_value = fake_availabilities
        mock_availability.query = mock_query

        # Execute
        result = dao_doctor_availability.get_doctor_availabilities(doctor_id=1)

        # Assert
        self.assertEqual(len(result), 2)
        mock_query.filter_by.assert_called_with(doctor_id=1)
        mock_query.filter_by.return_value.all.assert_called_once()

    @patch("app.dao.dao_doctor_availability.DoctorAvailability")
    def test_get_doctor_availabilities_no_results(self, mock_availability):
        # Mock query result (empty)
        mock_query = MagicMock()
        mock_query.filter_by.return_value.all.return_value = []
        mock_availability.query = mock_query

        # Execute
        result = dao_doctor_availability.get_doctor_availabilities(doctor_id=1)

        # Assert
        self.assertEqual(result, [])
        mock_query.filter_by.assert_called_with(doctor_id=1)

    # ---------- get_doctor_availabilities_detail ----------
    @patch("app.dao.dao_doctor_availability.DoctorAvailability")
    @patch("app.dao.dao_doctor_availability.current_app")
    def test_get_doctor_availabilities_detail_success(self, mock_current_app, mock_availability):
        # Mock query result
        fake_availabilities = [MagicMock(), MagicMock()]
        mock_query = MagicMock()
        mock_query.filter_by.return_value.order_by.return_value.all.return_value = fake_availabilities
        mock_availability.query = mock_query

        # Execute
        result = dao_doctor_availability.get_doctor_availabilities_detail(doctor_id=1)

        # Assert
        self.assertEqual(len(result), 2)
        mock_query.filter_by.assert_called_with(doctor_id=1)
        mock_query.filter_by.return_value.order_by.assert_called_with(DoctorAvailability.day_of_week)
        mock_current_app.logger.error.assert_not_called()

    @patch("app.dao.dao_doctor_availability.DoctorAvailability")
    @patch("app.dao.dao_doctor_availability.current_app")
    def test_get_doctor_availabilities_detail_exception(self, mock_current_app, mock_availability):
        # Mock query to raise an exception
        mock_query = MagicMock()
        mock_query.filter_by.side_effect = Exception("Database error")
        mock_availability.query = mock_query

        # Execute
        result = dao_doctor_availability.get_doctor_availabilities_detail(doctor_id=1)

        # Assert
        self.assertEqual(result, [])
        mock_current_app.logger.error.assert_called_once_with("Error getting doctor availabilities: Database error")

    # ---------- get_doctor_availability_by_day ----------
    @patch("app.dao.dao_doctor_availability.DoctorAvailability")
    def test_get_doctor_availability_by_day_success(self, mock_availability):
        # Mock query result
        fake_availability = MagicMock()
        mock_query = MagicMock()
        mock_query.filter_by.return_value.first.return_value = fake_availability
        mock_availability.query = mock_query

        # Execute
        result = dao_doctor_availability.get_doctor_availability_by_day(doctor_id=1, day_of_week="Monday")

        # Assert
        self.assertEqual(result, fake_availability)
        mock_query.filter_by.assert_called_with(
            doctor_id=1,
            day_of_week=DayOfWeekEnum.Monday
        )
        mock_query.filter_by.return_value.first.assert_called_once()

    @patch("app.dao.dao_doctor_availability.DoctorAvailability")
    def test_get_doctor_availability_by_day_not_found(self, mock_availability):
        # Mock query result (not found)
        mock_query = MagicMock()
        mock_query.filter_by.return_value.first.return_value = None
        mock_availability.query = mock_query

        # Execute
        result = dao_doctor_availability.get_doctor_availability_by_day(doctor_id=1, day_of_week="Monday")

        # Assert
        self.assertIsNone(result)
        mock_query.filter_by.assert_called_with(
            doctor_id=1,
            day_of_week=DayOfWeekEnum.Monday
        )

    @patch("app.dao.dao_doctor_availability.DoctorAvailability")
    def test_get_doctor_availability_by_day_invalid_day(self, mock_availability):
        # Mock query to raise KeyError for invalid day
        mock_query = MagicMock()
        mock_query.filter_by.side_effect = KeyError("Invalid day")
        mock_availability.query = mock_query

        # Execute
        result = dao_doctor_availability.get_doctor_availability_by_day(doctor_id=1, day_of_week="InvalidDay")

        # Assert
        self.assertIsNone(result)
        mock_query.filter_by.assert_called_with(
            doctor_id=1,
            day_of_week=DayOfWeekEnum.InvalidDay
        )

if __name__ == "__main__":
    unittest.main()