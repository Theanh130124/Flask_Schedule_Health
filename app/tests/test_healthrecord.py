import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from app.models import HealthRecord
from app.extensions import db
from app.dao import dao_health_record  # Thay bằng tên file chứa DAO của bạn


class TestDAOHealthRecord(unittest.TestCase):

    def setUp(self):
        self.mock_db = MagicMock()

    # ---------- create_empty_health_record ----------
    @patch("app.dao.dao_health_record.HealthRecord")
    @patch("app.dao.dao_health_record.db")
    @patch("app.dao.dao_health_record.datetime")
    def test_create_empty_health_record_success(self, mock_datetime, mock_db, mock_health_record):
        # Mock datetime
        mock_now = datetime(2024, 1, 1, 10, 0)
        mock_datetime.now.return_value = mock_now

        # Mock HealthRecord instance
        mock_record_instance = MagicMock()
        mock_health_record.return_value = mock_record_instance

        # Execute
        result = dao_health_record.create_empty_health_record(patient_id=1)

        # Assert
        self.assertEqual(result, mock_record_instance)
        mock_health_record.assert_called_once_with(
            patient_id=1,
            user_id=None,
            appointment_id=None,
            record_date=mock_now,
            symptoms=None,
            diagnosis=None,
            prescription=None,
            notes=None
        )
        mock_db.session.add.assert_called_once_with(mock_record_instance)
        mock_db.session.commit.assert_called_once()

    # ---------- get_records_by_patient ----------
    @patch("app.dao.dao_health_record.HealthRecord")
    def test_get_records_by_patient_success(self, mock_health_record):
        # Mock query result
        fake_records = [MagicMock(), MagicMock()]
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = fake_records
        mock_health_record.query = mock_query

        # Execute
        result = dao_health_record.get_records_by_patient(patient_id=1, limit=10)

        # Assert
        self.assertEqual(len(result), 2)
        mock_query.filter.assert_called_once_with(HealthRecord.patient_id == 1)
        mock_query.filter.return_value.order_by.assert_called_once_with(HealthRecord.record_date.desc())
        mock_query.filter.return_value.order_by.return_value.limit.assert_called_once_with(10)
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.assert_called_once()

    @patch("app.dao.dao_health_record.HealthRecord")
    def test_get_records_by_patient_no_results(self, mock_health_record):
        # Mock query result (empty)
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        mock_health_record.query = mock_query

        # Execute
        result = dao_health_record.get_records_by_patient(patient_id=1, limit=10)

        # Assert
        self.assertEqual(result, [])
        mock_query.filter.assert_called_once_with(HealthRecord.patient_id == 1)
        mock_query.filter.return_value.order_by.assert_called_once_with(HealthRecord.record_date.desc())
        mock_query.filter.return_value.order_by.return_value.limit.assert_called_once_with(10)

    # ---------- update_healthrecord ----------
    @patch("app.dao.dao_health_record.HealthRecord")
    @patch("app.dao.dao_health_record.db")
    def test_update_healthrecord_success(self, mock_db, mock_health_record):
        # Mock HealthRecord instance
        mock_record_instance = MagicMock()
        mock_health_record.query.get.return_value = mock_record_instance

        # Data to update
        update_data = {
            "symptoms": "Fever",
            "diagnosis": "Flu",
            "prescription": "Paracetamol",
            "notes": "Rest for 3 days"
        }

        # Execute
        result = dao_health_record.update_healthrecord(record_id=1, data=update_data)

        # Assert
        self.assertEqual(result, mock_record_instance)
        mock_health_record.query.get.assert_called_once_with(1)
        self.assertEqual(mock_record_instance.symptoms, "Fever")
        self.assertEqual(mock_record_instance.diagnosis, "Flu")
        self.assertEqual(mock_record_instance.prescription, "Paracetamol")
        self.assertEqual(mock_record_instance.notes, "Rest for 3 days")
        mock_db.session.commit.assert_called_once()

    @patch("app.dao.dao_health_record.HealthRecord")
    def test_update_healthrecord_not_found(self, mock_health_record):
        # Mock query result (not found)
        mock_health_record.query.get.return_value = None

        # Execute
        result = dao_health_record.update_healthrecord(record_id=99, data={"symptoms": "Fever"})

        # Assert
        self.assertIsNone(result)
        mock_health_record.query.get.assert_called_once_with(99)

    @patch("app.dao.dao_health_record.HealthRecord")
    @patch("app.dao.dao_health_record.db")
    def test_update_healthrecord_invalid_field(self, mock_db, mock_health_record):
        # Mock HealthRecord instance
        mock_record_instance = MagicMock()
        mock_health_record.query.get.return_value = mock_record_instance

        # Data with invalid field
        update_data = {
            "symptoms": "Fever",
            "invalid_field": "Invalid"
        }

        # Execute
        result = dao_health_record.update_healthrecord(record_id=1, data=update_data)

        # Assert
        self.assertEqual(result, mock_record_instance)
        self.assertEqual(mock_record_instance.symptoms, "Fever")
        self.assertFalse(hasattr(mock_record_instance, "invalid_field"))
        mock_db.session.commit.assert_called_once()

    # ---------- delete_healthrecord ----------
    @patch("app.dao.dao_health_record.HealthRecord")
    @patch("app.dao.dao_health_record.db")
    def test_delete_healthrecord_success(self, mock_db, mock_health_record):
        # Mock HealthRecord instance
        mock_record_instance = MagicMock()
        mock_health_record.query.get.return_value = mock_record_instance

        # Execute
        result = dao_health_record.delete_healthrecord(record_id=1)

        # Assert
        self.assertTrue(result)
        mock_health_record.query.get.assert_called_once_with(1)
        mock_db.session.delete.assert_called_once_with(mock_record_instance)
        mock_db.session.commit.assert_called_once()

    @patch("app.dao.dao_health_record.HealthRecord")
    @patch("app.dao.dao_health_record.db")
    def test_delete_healthrecord_not_found(self, mock_db, mock_health_record):
        # Mock query result (not found)
        mock_health_record.query.get.return_value = None

        # Execute
        result = dao_health_record.delete_healthrecord(record_id=99)

        # Assert
        self.assertFalse(result)
        mock_health_record.query.get.assert_called_once_with(99)
        mock_db.session.delete.assert_not_called()
        mock_db.session.commit.assert_not_called()

if __name__ == "__main__":
    unittest.main()