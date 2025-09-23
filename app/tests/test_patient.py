import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, date
from app.models import User, Patient, Appointment, RoleEnum
from app.extensions import db
from app.dao import dao_patient  # Thay bằng tên file chứa DAO của bạn
from sqlalchemy import or_, and_


class TestDAOPatient(unittest.TestCase):

    def setUp(self):
        self.mock_db = MagicMock()

    # ---------- get_all_patients ----------
    @patch("app.dao.dao_patient.db")
    def test_get_all_patients_success(self, mock_db):
        # Mock query result
        fake_patients = [(MagicMock(), MagicMock()), (MagicMock(), MagicMock())]
        mock_query = MagicMock()
        mock_query.join.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = fake_patients
        mock_db.session.query.return_value = mock_query

        # Execute
        result = dao_patient.get_all_patients(limit=50, offset=0)

        # Assert
        self.assertEqual(len(result), 2)
        mock_db.session.query.assert_called_once_with(User, Patient)
        mock_query.join.assert_called_once_with(Patient, Patient.patient_id == User.user_id)
        mock_query.join.return_value.filter.assert_called_once_with(User.role == RoleEnum.PATIENT)
        mock_query.join.return_value.filter.return_value.order_by.assert_called_once_with(User.last_name.asc(), User.first_name.asc())
        mock_query.join.return_value.filter.return_value.order_by.return_value.offset.assert_called_once_with(0)
        mock_query.join.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.assert_called_once_with(50)

    # ---------- search_patient ----------
    @patch("app.dao.dao_patient.db")
    def test_search_patient_with_filters_success(self, mock_db):
        # Mock query result
        fake_patients = [(MagicMock(), MagicMock())]
        mock_query = MagicMock()
        mock_query.join.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = fake_patients
        mock_db.session.query.return_value = mock_query

        # Execute
        result = dao_patient.search_patient(q="John", active=True, inactive=False, date_from=date(2023, 1, 1), date_to=date(2023, 12, 31), limit=50, offset=0)

        # Assert
        self.assertEqual(len(result), 1)
        mock_db.session.query.assert_called_once_with(User, Patient)
        mock_query.join.assert_called_once_with(Patient, Patient.patient_id == User.user_id)
        mock_query.join.return_value.filter.assert_called_once_with(User.role == RoleEnum.PATIENT)
        mock_query.join.return_value.filter.return_value.filter.assert_any_call(
            or_(
                User.first_name.ilike("%John%"),
                User.last_name.ilike("%John%"),
                User.username.ilike("%John%"),
                User.email.ilike("%John%"),
                User.phone_number.ilike("%John%"),
                Patient.medical_history_summary.ilike("%John%")
            )
        )
        mock_query.join.return_value.filter.return_value.filter.assert_any_call(User.is_active == True)
        mock_query.join.return_value.filter.return_value.filter.assert_any_call(
            and_(
                User.created_at >= date(2023, 1, 1),
                User.created_at <= date(2023, 12, 31)
            )
        )
        mock_query.join.return_value.filter.return_value.filter.return_value.order_by.assert_called_once_with(User.last_name.asc(), User.first_name.asc())

    @patch("app.dao.dao_patient.db")
    def test_search_patient_no_filters(self, mock_db):
        # Mock query result
        fake_patients = [(MagicMock(), MagicMock())]
        mock_query = MagicMock()
        mock_query.join.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = fake_patients
        mock_db.session.query.return_value = mock_query

        # Execute
        result = dao_patient.search_patient(limit=50, offset=0)

        # Assert
        self.assertEqual(len(result), 1)
        mock_db.session.query.assert_called_once_with(User, Patient)
        mock_query.join.assert_called_once_with(Patient, Patient.patient_id == User.user_id)
        mock_query.join.return_value.filter.assert_called_once_with(User.role == RoleEnum.PATIENT)

    # ---------- get_patient_by_id ----------
    @patch("app.dao.dao_patient.User")
    def test_get_patient_by_id_success(self, mock_user):
        # Mock query result
        fake_user = MagicMock()
        mock_query = MagicMock()
        mock_query.options.return_value.filter.return_value.first.return_value = fake_user
        mock_user.query = mock_query

        # Execute
        result = dao_patient.get_patient_by_id(patient_id=1)

        # Assert
        self.assertEqual(result, fake_user)
        mock_query.options.assert_called_once_with(joinedload(User.patient))
        mock_query.options.return_value.filter.assert_called_once_with(User.user_id == 1, User.role == RoleEnum.PATIENT)

    @patch("app.dao.dao_patient.User")
    def test_get_patient_by_id_not_found(self, mock_user):
        # Mock query result (not found)
        mock_query = MagicMock()
        mock_query.options.return_value.filter.return_value.first.return_value = None
        mock_user.query = mock_query

        # Execute
        result = dao_patient.get_patient_by_id(patient_id=99)

        # Assert
        self.assertIsNone(result)
        mock_query.options.assert_called_once_with(joinedload(User.patient))
        mock_query.options.return_value.filter.assert_called_once_with(User.user_id == 99, User.role == RoleEnum.PATIENT)

    # ---------- count_patient ----------
    @patch("app.dao.dao_patient.User")
    def test_count_patient_success(self, mock_user):
        # Mock query result
        mock_query = MagicMock()
        mock_query.filter.return_value.count.return_value = 5
        mock_user.query = mock_query

        # Execute
        result = dao_patient.count_patient()

        # Assert
        self.assertEqual(result, 5)
        mock_query.filter.assert_called_once_with(User.role == RoleEnum.PATIENT)

    # ---------- update_patient ----------
    @patch("app.dao.dao_patient.User")
    @patch("app.dao.dao_patient.Patient")
    @patch("app.dao.dao_patient.db")
    @patch("app.dao.dao_patient.datetime")
    def test_update_patient_success(self, mock_datetime, mock_db, mock_patient, mock_user):
        # Mock datetime
        mock_now = datetime(2024, 1, 1, 10, 0)
        mock_datetime.now.return_value = mock_now

        # Mock User and Patient instances
        mock_user_instance = MagicMock()
        mock_patient_instance = MagicMock()
        mock_user.query.filter_by.return_value.first.return_value = mock_user_instance
        mock_patient.query.filter_by.return_value.first.return_value = mock_patient_instance

        # Data to update
        user_data = {"first_name": "John", "last_name": "Doe"}
        patient_data = {"medical_history_summary": "Allergic to penicillin"}

        # Execute
        result_user, result_patient = dao_patient.update_patient(patient_id=1, user_data=user_data, patient_data=patient_data)

        # Assert
        self.assertEqual(result_user, mock_user_instance)
        self.assertEqual(result_patient, mock_patient_instance)
        self.assertEqual(mock_user_instance.first_name, "John")
        self.assertEqual(mock_user_instance.last_name, "Doe")
        self.assertEqual(mock_user_instance.updated_at, mock_now)
        self.assertEqual(mock_patient_instance.medical_history_summary, "Allergic to penicillin")
        mock_db.session.commit.assert_called_once()

    @patch("app.dao.dao_patient.User")
    @patch("app.dao.dao_patient.Patient")
    def test_update_patient_not_found(self, mock_patient, mock_user):
        # Mock query result (not found)
        mock_user.query.filter_by.return_value.first.return_value = None
        mock_patient.query.filter_by.return_value.first.return_value = None

        # Execute
        result = dao_patient.update_patient(patient_id=99, user_data={"first_name": "John"})

        # Assert
        self.assertIsNone(result)
        mock_user.query.filter_by.assert_called_once_with(user_id=99, role=RoleEnum.PATIENT)
        mock_patient.query.filter_by.assert_called_once_with(patient_id=99)

    # ---------- delete_patient ----------
    @patch("app.dao.dao_patient.User")
    @patch("app.dao.dao_patient.Patient")
    @patch("app.dao.dao_patient.db")
    def test_delete_patient_success(self, mock_db, mock_patient, mock_user):
        # Mock User and Patient instances
        mock_user_instance = MagicMock()
        mock_patient_instance = MagicMock()
        mock_user.query.filter_by.return_value.first.return_value = mock_user_instance
        mock_patient.query.filter_by.return_value.first.return_value = mock_patient_instance

        # Execute
        result = dao_patient.delete_patient(patient_id=1)

        # Assert
        self.assertTrue(result)
        mock_user.query.filter_by.assert_called_once_with(user_id=1, role=RoleEnum.PATIENT)
        mock_patient.query.filter_by.assert_called_once_with(patient_id=1)
        mock_db.session.delete.assert_any_call(mock_patient_instance)
        mock_db.session.delete.assert_any_call(mock_user_instance)
        mock_db.session.commit.assert_called_once()

    @patch("app.dao.dao_patient.User")
    @patch("app.dao.dao_patient.db")
    def test_delete_patient_not_found(self, mock_db, mock_user):
        # Mock query result (not found)
        mock_user.query.filter_by.return_value.first.return_value = None

        # Execute
        result = dao_patient.delete_patient(patient_id=99)

        # Assert
        self.assertFalse(result)
        mock_user.query.filter_by.assert_called_once_with(user_id=99, role=RoleEnum.PATIENT)
        mock_db.session.delete.assert_not_called()
        mock_db.session.commit.assert_not_called()

    # ---------- get_patient_with_records ----------
    @patch("app.dao.dao_patient.User")
    @patch("app.dao.dao_patient.get_records_by_patient")
    def test_get_patient_with_records_success(self, mock_get_records, mock_user):
        # Mock User instance
        mock_user_instance = MagicMock()
        mock_query = MagicMock()
        mock_query.options.return_value.filter.return_value.first.return_value = mock_user_instance
        mock_user.query = mock_query

        # Mock records
        fake_records = [MagicMock(), MagicMock()]
        mock_get_records.return_value = fake_records

        # Execute
        result_user, result_records = dao_patient.get_patient_with_records(patient_id=1, limit=10)

        # Assert
        self.assertEqual(result_user, mock_user_instance)
        self.assertEqual(result_records, fake_records)
        mock_query.options.assert_called_once_with(joinedload(User.patient))
        mock_query.options.return_value.filter.assert_called_once_with(User.user_id == 1, User.role == RoleEnum.PATIENT)
        mock_get_records.assert_called_once_with(patient_id=1, limit=10)

    @patch("app.dao.dao_patient.User")
    def test_get_patient_with_records_not_found(self, mock_user):
        # Mock query result (not found)
        mock_query = MagicMock()
        mock_query.options.return_value.filter.return_value.first.return_value = None
        mock_user.query = mock_query

        # Execute
        result = dao_patient.get_patient_with_records(patient_id=99, limit=10)

        # Assert
        self.assertIsNone(result)
        mock_query.options.assert_called_once_with(joinedload(User.patient))
        mock_query.options.return_value.filter.assert_called_once_with(User.user_id == 99, User.role == RoleEnum.PATIENT)

    # ---------- has_doctor_with_patient ----------
    @patch("app.dao.dao_patient.db")
    @patch("app.dao.dao_patient.Appointment")
    def test_has_doctor_with_patient_true(self, mock_appointment, mock_db):
        # Mock query result
        mock_query = MagicMock()
        mock_query.filter.return_value.exists.return_value = True
        mock_appointment.query = mock_query
        mock_db.session.query.return_value.scalar.return_value = True

        # Execute
        result = dao_patient.has_doctor_with_patient(doctor_id=1, patient_id=2)

        # Assert
        self.assertTrue(result)
        mock_appointment.query.filter.assert_called_once_with(
            Appointment.doctor_id == 1,
            Appointment.patient_id == 2
        )
        mock_db.session.query.assert_called_once()

    @patch("app.dao.dao_patient.db")
    @patch("app.dao.dao_patient.Appointment")
    def test_has_doctor_with_patient_false(self, mock_appointment, mock_db):
        # Mock query result
        mock_query = MagicMock()
        mock_query.filter.return_value.exists.return_value = False
        mock_appointment.query = mock_query
        mock_db.session.query.return_value.scalar.return_value = False

        # Execute
        result = dao_patient.has_doctor_with_patient(doctor_id=1, patient_id=2)

        # Assert
        self.assertFalse(result)
        mock_appointment.query.filter.assert_called_once_with(
            Appointment.doctor_id == 1,
            Appointment.patient_id == 2
        )

    # ---------- get_patients_by_doctor ----------
    @patch("app.dao.dao_patient.db")
    def test_get_patients_by_doctor_success(self, mock_db):
        # Mock query result
        fake_patients = [MagicMock(), MagicMock()]
        mock_query = MagicMock()
        mock_query.join.return_value.join.return_value.filter.return_value.distinct.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = fake_patients
        mock_db.session.query.return_value = mock_query

        # Execute
        patients, total = dao_patient.get_patients_by_doctor(doctor_id=1, page=1, per_page=50, filters={"q": "John"})

        # Assert
        self.assertEqual(len(patients), 2)
        self.assertEqual(total, 2)
        mock_db.session.query.assert_called_once_with(User)
        mock_query.join.assert_any_call(Patient, Patient.patient_id == User.user_id)
        mock_query.join.assert_any_call(Appointment, Appointment.patient_id == Patient.patient_id)
        mock_query.join.return_value.join.return_value.filter.assert_called_once_with(
            User.role == RoleEnum.PATIENT,
            Appointment.doctor_id == 1
        )
        mock_query.join.return_value.join.return_value.filter.return_value.distinct.assert_called_once()
        mock_query.join.return_value.join.return_value.filter.return_value.distinct.return_value.filter.assert_called_once_with(
            or_(
                User.first_name.ilike("%John%"),
                User.last_name.ilike("%John%"),
                User.username.ilike("%John%"),
                User.email.ilike("%John%"),
                User.phone_number.ilike("%John%"),
                Patient.medical_history_summary.ilike("%John%")
            )
        )

    # ---------- calculate_age ----------
    @patch("app.dao.dao_patient.date")
    def test_calculate_age_success(self, mock_date):
        # Mock date
        mock_date.today.return_value = date(2024, 1, 1)

        # Execute
        result = dao_patient.calculate_age(date_of_birth=date(1990, 5, 1))

        # Assert
        self.assertEqual(result, 33)
        mock_date.today.assert_called_once()

    def test_calculate_age_none(self):
        # Execute
        result = dao_patient.calculate_age(date_of_birth=None)

        # Assert
        self.assertIsNone(result)

    # ---------- get_last_visit_date ----------
    @patch("app.dao.dao_patient.Appointment")
    def test_get_last_visit_date_success(self, mock_appointment):
        # Mock Appointment instance
        mock_appointment_instance = MagicMock()
        mock_appointment_instance.appointment_time = datetime(2024, 1, 1, 10, 0)
        mock_query = MagicMock()
        mock_query.filter_by.return_value.order_by.return_value.first.return_value = mock_appointment_instance
        mock_appointment.query = mock_query

        # Execute
        result = dao_patient.get_last_visit_date(patient_id=1, doctor_id=2)

        # Assert
        self.assertEqual(result, mock_appointment_instance.appointment_time)
        mock_query.filter_by.assert_called_once_with(patient_id=1, doctor_id=2)
        mock_query.filter_by.return_value.order_by.assert_called_once_with(Appointment.appointment_time.desc())

    @patch("app.dao.dao_patient.Appointment")
    def test_get_last_visit_date_not_found(self, mock_appointment):
        # Mock query result (not found)
        mock_query = MagicMock()
        mock_query.filter_by.return_value.order_by.return_value.first.return_value = None
        mock_appointment.query = mock_query

        # Execute
        result = dao_patient.get_last_visit_date(patient_id=1, doctor_id=2)

        # Assert
        self.assertIsNone(result)
        mock_query.filter_by.assert_called_once_with(patient_id=1, doctor_id=2)

    # ---------- get_appointment_status_count ----------
    @patch("app.dao.dao_patient.db")
    def test_get_appointment_status_count_success(self, mock_db):
        # Mock query result
        fake_status_count = [(MagicMock(name="Scheduled"), 3), (MagicMock(name="Completed"), 2)]
        mock_query = MagicMock()
        mock_query.filter_by.return_value.group_by.return_value.all.return_value = fake_status_count
        mock_db.session.query.return_value = mock_query

        # Execute
        result = dao_patient.get_appointment_status_count(patient_id=1, doctor_id=2)

        # Assert
        self.assertEqual(result, {"Scheduled": 3, "Completed": 2})
        mock_db.session.query.assert_called_once_with(Appointment.status, db.func.count(Appointment.appointment_id))
        mock_query.filter_by.assert_called_once_with(patient_id=1, doctor_id=2)

    # ---------- get_patients_by_doctor_with_status_filter ----------
    @patch("app.dao.dao_patient.db")
    def test_get_patients_by_doctor_with_status_filter_success(self, mock_db):
        # Mock query result
        fake_patients = [MagicMock(), MagicMock()]
        mock_subquery = MagicMock()
        mock_query = MagicMock()
        mock_query.join.return_value.filter.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = fake_patients
        mock_db.session.query.return_value = mock_query
        mock_db.session.query.return_value.filter.return_value.distinct.return_value.subquery.return_value = mock_subquery

        # Execute
        patients, total = dao_patient.get_patients_by_doctor_with_status_filter(doctor_id=1, status_filter="Scheduled", page=1, per_page=50, filters={"q": "John"})

        # Assert
        self.assertEqual(len(patients), 2)
        self.assertEqual(total, 2)
        mock_db.session.query.assert_any_call(Appointment.patient_id)
        mock_db.session.query.assert_any_call(User)
        mock_query.join.assert_called_once_with(Patient, Patient.patient_id == User.user_id)
        mock_query.join.return_value.filter.assert_called_once_with(User.user_id.in_(mock_subquery))
        mock_query.join.return_value.filter.return_value.filter.assert_called_once_with(
            or_(
                User.first_name.ilike("%John%"),
                User.last_name.ilike("%John%"),
                User.phone_number.ilike("%John%")
            )
        )

    @patch("app.dao.dao_patient.db")
    def test_get_patients_by_doctor_with_status_filter_no_status(self, mock_db):
        # Mock query result
        fake_patients = [MagicMock()]
        mock_query = MagicMock()
        mock_query.join.return_value.join.return_value.filter.return_value.distinct.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = fake_patients
        mock_db.session.query.return_value = mock_query

        # Execute
        patients, total = dao_patient.get_patients_by_doctor_with_status_filter(doctor_id=1, status_filter=None, page=1, per_page=50)

        # Assert
        self.assertEqual(len(patients), 1)
        self.assertEqual(total, 1)
        mock_db.session.query.assert_called_once_with(User)
        mock_query.join.assert_any_call(Patient, Patient.patient_id == User.user_id)
        mock_query.join.assert_any_call(Appointment, Appointment.patient_id == Patient.patient_id)
        mock_query.join.return_value.join.return_value.filter.assert_called_once_with(
            User.role == RoleEnum.PATIENT,
            Appointment.doctor_id == 1
        )

if __name__ == "__main__":
    unittest.main()