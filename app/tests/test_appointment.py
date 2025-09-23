# test_dao_appointment.py
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, date, time, timedelta
from app.dao import dao_appointment
from app.models import Appointment, AvailableSlot, Invoice, AppointmentStatus, InvoiceStatus, ConsultationType


class TestDAOAppointment(unittest.TestCase):

    def setUp(self):
        self.mock_db = MagicMock()

    # ---------- book_appointment ----------
    @patch("app.dao.dao_appointment.AvailableSlot")
    @patch("app.dao.dao_appointment.db")
    @patch("app.dao.dao_appointment.send_appointment_notification")
    def test_book_appointment_success(self, mock_send_notification, mock_db, mock_slot):
        # Mock data
        mock_slot_instance = MagicMock()
        mock_slot_instance.is_booked = False
        mock_slot_instance.doctor_id = 1
        mock_slot_instance.slot_date = date(2024, 1, 1)
        mock_slot_instance.start_time = time(9, 0)
        mock_slot_instance.end_time = time(10, 0)
        mock_slot_instance.doctor.consultation_fee = 200000

        mock_slot.query.get.return_value = mock_slot_instance

        # Mock appointment and invoice creation
        mock_db.session.add = MagicMock()
        mock_db.session.flush = MagicMock()
        mock_db.session.commit = MagicMock()

        # Execute
        result, message = dao_appointment.book_appointment(
            patient_id=1,
            slot_id=1,
            reason="Khám tổng quát",
            consultation_type=ConsultationType.Offline
        )

        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(message, "Đặt lịch thành công")
        mock_slot.query.get.assert_called_once_with(1)
        self.assertTrue(mock_slot_instance.is_booked)
        mock_db.session.add.assert_called()
        mock_db.session.commit.assert_called_once()
        mock_send_notification.assert_called_once()

    @patch("app.dao.dao_appointment.AvailableSlot")
    @patch("app.dao.dao_appointment.db")
    def test_book_appointment_slot_not_found(self, mock_db, mock_slot):
        mock_slot.query.get.return_value = None

        result, message = dao_appointment.book_appointment(1, 99, "Khám")

        self.assertIsNone(result)
        self.assertEqual(message, "Slot không tồn tại")
        mock_db.session.rollback.assert_not_called()

    @patch("app.dao.dao_appointment.AvailableSlot")
    @patch("app.dao.dao_appointment.db")
    def test_book_appointment_slot_already_booked(self, mock_db, mock_slot):
        mock_slot_instance = MagicMock()
        mock_slot_instance.is_booked = True
        mock_slot.query.get.return_value = mock_slot_instance

        result, message = dao_appointment.book_appointment(1, 1, "Khám")

        self.assertIsNone(result)
        self.assertEqual(message, "Slot đã được đặt")

    @patch("app.dao.dao_appointment.AvailableSlot")
    @patch("app.dao.dao_appointment.db")
    def test_book_appointment_exception(self, mock_db, mock_slot):
        mock_slot_instance = MagicMock()
        mock_slot_instance.is_booked = False
        mock_slot.query.get.return_value = mock_slot_instance
        mock_db.session.commit.side_effect = Exception("Database error")

        result, message = dao_appointment.book_appointment(1, 1, "Khám")

        self.assertIsNone(result)
        self.assertIn("Lỗi khi đặt lịch", message)
        mock_db.session.rollback.assert_called_once()

    # ---------- get_appointment_by_id ----------
    @patch("app.dao.dao_appointment.Appointment")
    def test_get_appointment_by_id_success(self, mock_appointment):
        fake_appointment = MagicMock(appointment_id=1, patient_id=1)
        mock_appointment.query.get.return_value = fake_appointment

        result = dao_appointment.get_appointment_by_id(1)

        self.assertIsNotNone(result)
        self.assertEqual(result.appointment_id, 1)
        mock_appointment.query.get.assert_called_once_with(1)

    @patch("app.dao.dao_appointment.Appointment")
    def test_get_appointment_by_id_not_found(self, mock_appointment):
        mock_appointment.query.get.return_value = None

        result = dao_appointment.get_appointment_by_id(99)

        self.assertIsNone(result)

    # ---------- get_patient_appointments ----------
    @patch("app.dao.dao_appointment.Appointment")
    def test_get_patient_appointments_success(self, mock_appointment):
        fake_appointments = [MagicMock(), MagicMock()]
        mock_query = MagicMock()
        mock_query.filter_by.return_value.order_by.return_value.all.return_value = fake_appointments
        mock_appointment.query = mock_query

        result = dao_appointment.get_patient_appointments(1)

        self.assertEqual(len(result), 2)
        mock_query.filter_by.assert_called_once_with(patient_id=1)
        mock_query.filter_by.return_value.order_by.assert_called_once()

    # ---------- get_doctor_appointments ----------
    @patch("app.dao.dao_appointment.Appointment")
    def test_get_doctor_appointments_success(self, mock_appointment):
        fake_appointments = [MagicMock(), MagicMock()]
        mock_query = MagicMock()
        mock_query.filter_by.return_value.order_by.return_value.all.return_value = fake_appointments
        mock_appointment.query = mock_query

        result = dao_appointment.get_doctor_appointments(1)

        self.assertEqual(len(result), 2)
        mock_query.filter_by.assert_called_once_with(doctor_id=1)

    # ---------- cancel_appointment ----------
    @patch("app.dao.dao_appointment.Appointment")
    @patch("app.dao.dao_appointment.AvailableSlot")
    @patch("app.dao.dao_appointment.db")
    @patch("app.dao.dao_appointment.send_appointment_notification")
    def test_cancel_appointment_success_by_patient(self, mock_send_notification, mock_db, mock_slot, mock_appointment):
        # Mock appointment
        mock_appointment_instance = MagicMock()
        mock_appointment_instance.appointment_time = datetime.now() + timedelta(days=2)  # 2 days later
        mock_appointment_instance.doctor_id = 1
        mock_appointment_instance.invoice = MagicMock()
        mock_appointment.query.get.return_value = mock_appointment_instance

        # Mock slot
        mock_slot_instance = MagicMock()
        mock_slot.query.filter_by.return_value.first.return_value = mock_slot_instance

        # Execute
        success, message = dao_appointment.cancel_appointment(1, "Bận việc", True)

        # Assert
        self.assertTrue(success)
        self.assertIn("thành công", message)
        self.assertEqual(mock_appointment_instance.status, AppointmentStatus.CancelledByPatient)
        self.assertEqual(mock_appointment_instance.invoice.status, InvoiceStatus.Cancelled)
        self.assertFalse(mock_slot_instance.is_booked)
        mock_db.session.commit.assert_called_once()
        mock_send_notification.assert_called_once()

    @patch("app.dao.dao_appointment.Appointment")
    @patch("app.dao.dao_appointment.db")
    def test_cancel_appointment_not_found(self, mock_db, mock_appointment):
        mock_appointment.query.get.return_value = None

        success, message = dao_appointment.cancel_appointment(99, "Lý do")

        self.assertFalse(success)
        self.assertEqual(message, "Lịch hẹn không tồn tại")

    @patch("app.dao.dao_appointment.Appointment")
    @patch("app.dao.dao_appointment.db")
    def test_cancel_appointment_less_than_24h(self, mock_db, mock_appointment):
        mock_appointment_instance = MagicMock()
        mock_appointment_instance.appointment_time = datetime.now() + timedelta(hours=23)  # Less than 24h
        mock_appointment.query.get.return_value = mock_appointment_instance

        success, message = dao_appointment.cancel_appointment(1, "Lý do")

        self.assertFalse(success)
        self.assertEqual(message, "Chỉ có thể hủy lịch hẹn trước 24 giờ")

    @patch("app.dao.dao_appointment.Appointment")
    @patch("app.dao.dao_appointment.AvailableSlot")
    @patch("app.dao.dao_appointment.db")
    def test_cancel_appointment_slot_not_found(self, mock_db, mock_slot, mock_appointment):
        mock_appointment_instance = MagicMock()
        mock_appointment_instance.appointment_time = datetime.now() + timedelta(days=2)
        mock_appointment_instance.doctor_id = 1
        mock_appointment_instance.invoice = MagicMock()
        mock_appointment.query.get.return_value = mock_appointment_instance

        mock_slot.query.filter_by.return_value.first.return_value = None

        success, message = dao_appointment.cancel_appointment(1, "Lý do")

        self.assertTrue(success)
        self.assertIn("không tìm thấy slot liên quan", message)

    # ---------- complete_appointment ----------
    @patch("app.dao.dao_appointment.Appointment")
    @patch("app.dao.dao_appointment.db")
    def test_complete_appointment_success(self, mock_db, mock_appointment):
        mock_appointment_instance = MagicMock()
        mock_appointment.query.get.return_value = mock_appointment_instance

        success, message = dao_appointment.complete_appointment(1)

        self.assertTrue(success)
        self.assertEqual(message, "Cập nhật trạng thái thành công")
        self.assertEqual(mock_appointment_instance.status, AppointmentStatus.Completed)
        mock_db.session.commit.assert_called_once()

    @patch("app.dao.dao_appointment.Appointment")
    @patch("app.dao.dao_appointment.db")
    def test_complete_appointment_not_found(self, mock_db, mock_appointment):
        mock_appointment.query.get.return_value = None

        success, message = dao_appointment.complete_appointment(99)

        self.assertFalse(success)
        self.assertEqual(message, "Lịch hẹn không tồn tại")

    # ---------- reschedule_appointment ----------
    @patch("app.dao.dao_appointment.Appointment")
    @patch("app.dao.dao_appointment.AvailableSlot")
    @patch("app.dao.dao_appointment.db")
    @patch("app.dao.dao_appointment.send_appointment_notification")
    def test_reschedule_appointment_success(self, mock_send_notification, mock_db, mock_slot, mock_appointment):
        # Mock appointment
        mock_appointment_instance = MagicMock()
        mock_appointment_instance.appointment_time = datetime.now() + timedelta(days=2)
        mock_appointment_instance.doctor_id = 1
        mock_appointment.query.get.return_value = mock_appointment_instance

        # Mock new slot
        mock_new_slot = MagicMock()
        mock_new_slot.is_booked = False
        mock_new_slot.doctor_id = 2
        mock_new_slot.slot_date = date(2024, 1, 2)
        mock_new_slot.start_time = time(10, 0)
        mock_new_slot.end_time = time(11, 0)
        mock_slot.query.get.return_value = mock_new_slot

        # Mock old slot
        mock_old_slot = MagicMock()
        mock_slot.query.filter_by.return_value.first.return_value = mock_old_slot

        success, message = dao_appointment.reschedule_appointment(1, 2, "Đổi lịch")

        self.assertTrue(success)
        self.assertEqual(message, "Sửa lịch hẹn thành công")
        self.assertFalse(mock_old_slot.is_booked)
        self.assertTrue(mock_new_slot.is_booked)
        mock_send_notification.assert_called_once()

    @patch("app.dao.dao_appointment.Appointment")
    def test_reschedule_appointment_not_found(self, mock_appointment):
        mock_appointment.query.get.return_value = None

        success, message = dao_appointment.reschedule_appointment(99, 1)

        self.assertFalse(success)
        self.assertEqual(message, "Lịch hẹn không tồn tại")

    @patch("app.dao.dao_appointment.Appointment")
    @patch("app.dao.dao_appointment.AvailableSlot")
    def test_reschedule_appointment_less_than_24h(self, mock_slot, mock_appointment):
        mock_appointment_instance = MagicMock()
        mock_appointment_instance.appointment_time = datetime.now() + timedelta(hours=23)
        mock_appointment.query.get.return_value = mock_appointment_instance

        mock_new_slot = MagicMock()
        mock_new_slot.is_booked = False
        mock_slot.query.get.return_value = mock_new_slot

        success, message = dao_appointment.reschedule_appointment(1, 2)

        self.assertFalse(success)
        self.assertEqual(message, "Chỉ có thể sửa lịch hẹn trước 24 giờ")

    @patch("app.dao.dao_appointment.Appointment")
    @patch("app.dao.dao_appointment.AvailableSlot")
    def test_reschedule_appointment_new_slot_not_found(self, mock_slot, mock_appointment):
        mock_appointment_instance = MagicMock()
        mock_appointment_instance.appointment_time = datetime.now() + timedelta(days=2)
        mock_appointment.query.get.return_value = mock_appointment_instance

        mock_slot.query.get.return_value = None

        success, message = dao_appointment.reschedule_appointment(1, 99)

        self.assertFalse(success)
        self.assertEqual(message, "Slot mới không tồn tại")

    @patch("app.dao.dao_appointment.Appointment")
    @patch("app.dao.dao_appointment.AvailableSlot")
    def test_reschedule_appointment_new_slot_booked(self, mock_slot, mock_appointment):
        mock_appointment_instance = MagicMock()
        mock_appointment_instance.appointment_time = datetime.now() + timedelta(days=2)
        mock_appointment.query.get.return_value = mock_appointment_instance

        mock_new_slot = MagicMock()
        mock_new_slot.is_booked = True
        mock_slot.query.get.return_value = mock_new_slot

        success, message = dao_appointment.reschedule_appointment(1, 2)

        self.assertFalse(success)
        self.assertEqual(message, "Slot mới đã được đặt")

    # ---------- get_patient_appointments_paginated ----------
    @patch("app.dao.dao_appointment.Appointment")
    @patch("app.dao.dao_appointment.joinedload")
    def test_get_patient_appointments_paginated(self, mock_joinedload, mock_appointment):
        mock_paginate = MagicMock()
        mock_paginate.items = [MagicMock(), MagicMock()]
        mock_query = MagicMock()
        mock_query.options.return_value.filter_by.return_value.order_by.return_value.paginate.return_value = mock_paginate
        mock_appointment.query = mock_query

        result = dao_appointment.get_patient_appointments_paginated(1, 1, 6)

        self.assertEqual(len(result.items), 2)
        mock_query.paginate.assert_called_once_with(page=1, per_page=6, error_out=False)

    # ---------- get_doctor_appointments_paginated ----------
    @patch("app.dao.dao_appointment.Appointment")
    def test_get_doctor_appointments_paginated(self, mock_appointment):
        fake_appointments = [MagicMock(), MagicMock()]
        mock_query = MagicMock()
        mock_query.filter_by.return_value.order_by.return_value.offset.return_value.limit.return_value = fake_appointments
        mock_appointment.query = mock_query

        result = dao_appointment.get_doctor_appointments_paginated(1, 1, 6)

        self.assertEqual(len(result), 2)
        mock_query.offset.assert_called_with(0)
        mock_query.limit.assert_called_with(6)

    # ---------- count_patient_appointments ----------
    @patch("app.dao.dao_appointment.Appointment")
    def test_count_patient_appointments(self, mock_appointment):
        mock_query = MagicMock()
        mock_query.filter_by.return_value.count.return_value = 5
        mock_appointment.query = mock_query

        result = dao_appointment.count_patient_appointments(1)

        self.assertEqual(result, 5)
        mock_query.filter_by.assert_called_once_with(patient_id=1)

    # ---------- count_doctor_appointments ----------
    @patch("app.dao.dao_appointment.Appointment")
    def test_count_doctor_appointments(self, mock_appointment):
        mock_query = MagicMock()
        mock_query.filter_by.return_value.count.return_value = 10
        mock_appointment.query = mock_query

        result = dao_appointment.count_doctor_appointments(1)

        self.assertEqual(result, 10)
        mock_query.filter_by.assert_called_once_with(doctor_id=1)

    # ---------- get_info_by_id, get_doctor_by_userid, get_patient_by_userid ----------
    @patch("app.dao.dao_appointment.User")
    def test_get_info_by_id(self, mock_user):
        fake_user = MagicMock(id=1)
        mock_user.query.get.return_value = fake_user

        result = dao_appointment.get_info_by_id(1)

        self.assertEqual(result, fake_user)
        mock_user.query.get.assert_called_once_with(1)

    @patch("app.dao.dao_appointment.Doctor")
    def test_get_doctor_by_userid(self, mock_doctor):
        fake_doctor = MagicMock(doctor_id=1)
        mock_doctor.query.filter_by.return_value.first.return_value = fake_doctor

        result = dao_appointment.get_doctor_by_userid(1)

        self.assertEqual(result, fake_doctor)
        mock_doctor.query.filter_by.assert_called_once_with(doctor_id=1)

    @patch("app.dao.dao_appointment.Patient")
    def test_get_patient_by_userid(self, mock_patient):
        fake_patient = MagicMock(patient_id=1)
        mock_patient.query.filter_by.return_value.first.return_value = fake_patient

        result = dao_appointment.get_patient_by_userid(1)

        self.assertEqual(result, fake_patient)
        mock_patient.query.filter_by.assert_called_once_with(patient_id=1)


if __name__ == "__main__":
    unittest.main()