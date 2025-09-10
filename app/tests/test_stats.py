# test_stats.py
import unittest
from unittest.mock import patch, MagicMock
from app.dao import dao_stats


class TestDAOStats(unittest.TestCase):

    # ---------- get_appointment_stats ----------
    @patch("app.dao.dao_stats.db")
    def test_get_appointment_stats_success(self, mock_db):
        fake_result = [
            MagicMock(
                doctor_id=1,
                first_name="Anh",
                last_name="Nguyen",
                specialty_name="Cardiology",
                appointment_count=5,
                total_revenue=2000,
                average_rating=4.5
            )
        ]

        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.outerjoin.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = fake_result

        mock_db.session.query.return_value = mock_query

        result = dao_stats.get_appointment_stats(year=2024, month=5, doctor_id=1)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].doctor_id, 1)
        self.assertEqual(result[0].specialty_name, "Cardiology")
        self.assertEqual(result[0].appointment_count, 5)
        self.assertEqual(result[0].total_revenue, 2000)
        self.assertEqual(result[0].average_rating, 4.5)
        mock_db.session.query.assert_called_once()

    @patch("app.dao.dao_stats.db")
    def test_get_appointment_stats_empty(self, mock_db):
        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.outerjoin.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []

        mock_db.session.query.return_value = mock_query

        result = dao_stats.get_appointment_stats()
        self.assertEqual(result, [])
        mock_db.session.query.assert_called_once()

    # ---------- get_revenue_by_time_period ----------
    @patch("app.dao.dao_stats.db")
    def test_get_revenue_by_time_period_year(self, mock_db):
        fake_result = [
            MagicMock(year=2024, appointment_count=10, total_revenue=5000)
        ]

        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = fake_result

        mock_db.session.query.return_value = mock_query

        result = dao_stats.get_revenue_by_time_period(year=2024)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].year, 2024)
        self.assertEqual(result[0].appointment_count, 10)
        self.assertEqual(result[0].total_revenue, 5000)

    @patch("app.dao.dao_stats.db")
    def test_get_revenue_by_time_period_quarter(self, mock_db):
        fake_result = [
            MagicMock(year=2024, quarter=2, appointment_count=3, total_revenue=1500)
        ]

    #Gán các thao tác
        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = fake_result
    #Thực hiện truy vấn
        mock_db.session.query.return_value = mock_query
    #Gọi actual -> nhưng test với fake data.
        result = dao_stats.get_revenue_by_time_period(year=2024, quarter=2)

        self.assertEqual(result[0].quarter, 2)
        self.assertEqual(result[0].appointment_count, 3)
        self.assertEqual(result[0].total_revenue, 1500)

    @patch("app.dao.dao_stats.db")
    def test_get_revenue_by_time_period_month(self, mock_db):
        fake_result = [
            MagicMock(year=2024, month=7, appointment_count=8, total_revenue=3000)
        ]

        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = fake_result

        mock_db.session.query.return_value = mock_query

        result = dao_stats.get_revenue_by_time_period(year=2024, month=7)

        self.assertEqual(result[0].month, 7)
        self.assertEqual(result[0].appointment_count, 8)
        self.assertEqual(result[0].total_revenue, 3000)


if __name__ == "__main__":
    unittest.main()
