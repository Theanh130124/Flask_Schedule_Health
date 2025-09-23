import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, date, time, timedelta
from app.models import AvailableSlot, Doctor, User, Hospital, Specialty
from app.dao import dao_available_slot  # Thay bằng tên file chứa DAO của bạn

class TestDAOAvailableSlot(unittest.TestCase):

    def setUp(self):
        self.mock_db = MagicMock()

    # ---------- get_available_slots ----------
    @patch("app.dao.dao_available_slot.AvailableSlot")
    @patch("app.dao.dao_available_slot.datetime")
    def test_get_available_slots_success(self, mock_datetime, mock_slot):
        # Mock datetime
        mock_now = datetime(2024, 1, 1, 10, 0)
        mock_datetime.now.return_value = mock_now
        mock_current_date = mock_now.date()
        mock_current_time = mock_now.time()

        # Mock query result
        fake_slots = [MagicMock(), MagicMock()]
        mock_query = MagicMock()
        mock_query.join.return_value.join.return_value.join.return_value.join.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = fake_slots
        mock_slot.query = mock_query

        # Execute
        result = dao_available_slot.get_available_slots()

        # Assert
        self.assertEqual(len(result), 2)
        mock_query.join.assert_called_with(Doctor, AvailableSlot.doctor_id == Doctor.doctor_id)
        mock_query.join.return_value.join.assert_called_with(User, Doctor.doctor_id == User.user_id)
        mock_query.join.return_value.join.return_value.join.assert_called_with(Hospital, Doctor.hospital_id == Hospital.hospital_id)
        mock_query.join.return_value.join.return_value.join.return_value.join.assert_called_with(Specialty, Doctor.specialty_id == Specialty.specialty_id)
        mock_query.join.return_value.join.return_value.join.return_value.join.return_value.filter.assert_called_with(AvailableSlot.is_booked == 0)
        mock_query.join.return_value.join.return_value.join.return_value.join.return_value.filter.return_value.filter.assert_called()

    # ---------- get_available_slots_by_filters ----------
    @patch("app.dao.dao_available_slot.AvailableSlot")
    @patch("app.dao.dao_available_slot.datetime")
    def test_get_available_slots_by_filters_success(self, mock_datetime, mock_slot):
        # Mock datetime
        mock_now = datetime(2024, 1, 1, 10, 0)
        mock_datetime.now.return_value = mock_now
        mock_current_date = mock_now.date()
        mock_current_time = mock_now.time()

        # Mock query result
        fake_slots = [MagicMock(), MagicMock()]
        mock_query = MagicMock()
        mock_query.join.return_value.join.return_value.join.return_value.join.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value = fake_slots
        mock_slot.query = mock_query

        # Execute
        result = dao_available_slot.get_available_slots_by_filters(
            hospital_id=1, specialty_id=2, doctor_id=3, date=date(2024, 1, 2)
        )

        # Assert
        self.assertEqual(result, fake_slots)
        mock_query.join.assert_called_with(Doctor, AvailableSlot.doctor_id == Doctor.doctor_id)
        mock_query.join.return_value.join.assert_called_with(User, Doctor.doctor_id == User.user_id)
        mock_query.join.return_value.join.return_value.join.assert_called_with(Hospital, Doctor.hospital_id == Hospital.hospital_id)
        mock_query.join.return_value.join.return_value.join.return_value.join.assert_called_with(Specialty, Doctor.specialty_id == Specialty.specialty_id)
        mock_query.join.return_value.join.return_value.join.return_value.join.return_value.filter.assert_called_with(AvailableSlot.is_booked == 0)
        mock_query.join.return_value.join.return_value.join.return_value.join.return_value.filter.return_value.filter.assert_any_call(Doctor.hospital_id == 1)
        mock_query.join.return_value.join.return_value.join.return_value.join.return_value.filter.return_value.filter.assert_any_call(Doctor.specialty_id == 2)
        mock_query.join.return_value.join.return_value.join.return_value.join.return_value.filter.return_value.filter.assert_any_call(Doctor.doctor_id == 3)
        mock_query.join.return_value.join.return_value.join.return_value.join.return_value.filter.return_value.filter.assert_any_call(AvailableSlot.slot_date == date(2024, 1, 2))

    @patch("app.dao.dao_available_slot.AvailableSlot")
    @patch("app.dao.dao_available_slot.datetime")
    def test_get_available_slots_by_filters_no_filters(self, mock_datetime, mock_slot):
        # Mock datetime
        mock_now = datetime(2024, 1, 1, 10, 0)
        mock_datetime.now.return_value = mock_now
        mock_current_date = mock_now.date()
        mock_current_time = mock_now.time()

        # Mock query result
        fake_slots = [MagicMock()]
        mock_query = MagicMock()
        mock_query.join.return_value.join.return_value.join.return_value.join.return_value.filter.return_value.filter.return_value.order_by.return_value = fake_slots
        mock_slot.query = mock_query

        # Execute
        result = dao_available_slot.get_available_slots_by_filters()

        # Assert
        self.assertEqual(result, fake_slots)
        mock_query.join.assert_called_with(Doctor, AvailableSlot.doctor_id == Doctor.doctor_id)
        mock_query.join.return_value.join.assert_called_with(User, Doctor.doctor_id == User.user_id)
        mock_query.join.return_value.join.return_value.join.assert_called_with(Hospital, Doctor.hospital_id == Hospital.hospital_id)
        mock_query.join.return_value.join.return_value.join.return_value.join.assert_called_with(Specialty, Doctor.specialty_id == Specialty.specialty_id)
        mock_query.join.return_value.join.return_value.join.return_value.join.return_value.filter.assert_called_with(AvailableSlot.is_booked == 0)

    # ---------- get_available_slots_by_filters_paginated ----------
    @patch("app.dao.dao_available_slot.AvailableSlot")
    @patch("app.dao.dao_available_slot.datetime")
    def test_get_available_slots_by_filters_paginated_success(self, mock_datetime, mock_slot):
        # Mock datetime
        mock_now = datetime(2024, 1, 1, 10, 0)
        mock_datetime.now.return_value = mock_now
        mock_current_date = mock_now.date()
        mock_current_time = mock_now.time()

        # Mock query result
        fake_slots = [MagicMock(), MagicMock()]
        mock_query = MagicMock()
        mock_query.join.return_value.join.return_value.join.return_value.join.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = fake_slots
        mock_slot.query = mock_query

        # Execute
        result = dao_available_slot.get_available_slots_by_filters_paginated(
            hospital_id=1, specialty_id=2, doctor_id=3, date=date(2024, 1, 2), page=2, per_page=6
        )

        # Assert
        self.assertEqual(len(result), 2)
        mock_query.join.assert_called_with(Doctor, AvailableSlot.doctor_id == Doctor.doctor_id)
        mock_query.join.return_value.join.assert_called_with(User, Doctor.doctor_id == User.user_id)
        mock_query.join.return_value.join.return_value.join.assert_called_with(Hospital, Doctor.hospital_id == Hospital.hospital_id)
        mock_query.join.return_value.join.return_value.join.return_value.join.assert_called_with(Specialty, Doctor.specialty_id == Specialty.specialty_id)
        mock_query.join.return_value.join.return_value.join.return_value.join.return_value.filter.assert_called_with(AvailableSlot.is_booked == 0)
        mock_query.join.return_value.join.return_value.join.return_value.join.return_value.filter.return_value.filter.assert_any_call(Doctor.hospital_id == 1)
        mock_query.join.return_value.join.return_value.join.return_value.join.return_value.filter.return_value.filter.assert_any_call(Doctor.specialty_id == 2)
        mock_query.join.return_value.join.return_value.join.return_value.join.return_value.filter.return_value.filter.assert_any_call(Doctor.doctor_id == 3)
        mock_query.join.return_value.join.return_value.join.return_value.join.return_value.filter.return_value.filter.assert_any_call(AvailableSlot.slot_date == date(2024, 1, 2))
        mock_query.join.return_value.join.return_value.join.return_value.join.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.assert_called_with(6)
        mock_query.join.return_value.join.return_value.join.return_value.join.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.assert_called_with(6)

    @patch("app.dao.dao_available_slot.AvailableSlot")
    @patch("app.dao.dao_available_slot.datetime")
    def test_get_available_slots_by_filters_paginated_no_filters(self, mock_datetime, mock_slot):
        # Mock datetime
        mock_now = datetime(2024, 1, 1, 10, 0)
        mock_datetime.now.return_value = mock_now
        mock_current_date = mock_now.date()
        mock_current_time = mock_now.time()

        # Mock query result
        fake_slots = [MagicMock()]
        mock_query = MagicMock()
        mock_query.join.return_value.join.return_value.join.return_value.join.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = fake_slots
        mock_slot.query = mock_query

        # Execute
        result = dao_available_slot.get_available_slots_by_filters_paginated(page=1, per_page=6)

        # Assert
        self.assertEqual(len(result), 1)
        mock_query.join.assert_called_with(Doctor, AvailableSlot.doctor_id == Doctor.doctor_id)
        mock_query.join.return_value.join.assert_called_with(User, Doctor.doctor_id == User.user_id)
        mock_query.join.return_value.join.return_value.join.assert_called_with(Hospital, Doctor.hospital_id == Hospital.hospital_id)
        mock_query.join.return_value.join.return_value.join.return_value.join.assert_called_with(Specialty, Doctor.specialty_id == Specialty.specialty_id)
        mock_query.join.return_value.join.return_value.join.return_value.join.return_value.filter.assert_called_with(AvailableSlot.is_booked == 0)
        mock_query.join.return_value.join.return_value.join.return_value.join.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.assert_called_with(0)
        mock_query.join.return_value.join.return_value.join.return_value.join.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.assert_called_with(6)

    # ---------- count_available_slots_by_filters ----------
    @patch("app.dao.dao_available_slot.AvailableSlot")
    @patch("app.dao.dao_available_slot.datetime")
    def test_count_available_slots_by_filters_success(self, mock_datetime, mock_slot):
        # Mock datetime
        mock_now = datetime(2024, 1, 1, 10, 0)
        mock_datetime.now.return_value = mock_now
        mock_current_date = mock_now.date()
        mock_current_time = mock_now.time()

        # Mock query result
        mock_query = MagicMock()
        mock_query.join.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.count.return_value = 5
        mock_slot.query = mock_query

        # Execute
        result = dao_available_slot.count_available_slots_by_filters(
            hospital_id=1, specialty_id=2, doctor_id=3, date=date(2024, 1, 2)
        )

        # Assert
        self.assertEqual(result, 5)
        mock_query.join.assert_called_with(Doctor, AvailableSlot.doctor_id == Doctor.doctor_id)
        mock_query.join.return_value.filter.assert_called_with(AvailableSlot.is_booked == 0)
        mock_query.join.return_value.filter.return_value.filter.assert_any_call(Doctor.hospital_id == 1)
        mock_query.join.return_value.filter.return_value.filter.assert_any_call(Doctor.specialty_id == 2)
        mock_query.join.return_value.filter.return_value.filter.assert_any_call(Doctor.doctor_id == 3)
        mock_query.join.return_value.filter.return_value.filter.assert_any_call(AvailableSlot.slot_date == date(2024, 1, 2))

    @patch("app.dao.dao_available_slot.AvailableSlot")
    @patch("app.dao.dao_available_slot.datetime")
    def test_count_available_slots_by_filters_no_filters(self, mock_datetime, mock_slot):
        # Mock datetime
        mock_now = datetime(2024, 1, 1, 10, 0)
        mock_datetime.now.return_value = mock_now
        mock_current_date = mock_now.date()
        mock_current_time = mock_now.time()

        # Mock query result
        mock_query = MagicMock()
        mock_query.join.return_value.filter.return_value.filter.return_value.count.return_value = 3
        mock_slot.query = mock_query

        # Execute
        result = dao_available_slot.count_available_slots_by_filters()

        # Assert
        self.assertEqual(result, 3)
        mock_query.join.assert_called_with(Doctor, AvailableSlot.doctor_id == Doctor.doctor_id)
        mock_query.join.return_value.filter.assert_called_with(AvailableSlot.is_booked == 0)

if __name__ == "__main__":
    unittest.main()