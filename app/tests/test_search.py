# tests/test_search_doctors.py
import unittest
from unittest.mock import patch, MagicMock

# Đổi đường dẫn này nếu file của bạn có tên khác
from app.dao import dao_search as dao


def make_doctor(
    did=1,
    first="A",
    last="B",
    hospital_name="Hosp",
    specialty_name="Spec",
    exp=10,
    fee=200000.0,
    rating=4.5,
    accepts_ins=True,
    avatar="avt.png",
):
    d = MagicMock()
    d.doctor_id = did
    d.user = MagicMock(first_name=first, last_name=last, avatar=avatar)
    d.hospital = MagicMock(name=hospital_name, accepts_insurance=accepts_ins)
    d.specialty = MagicMock(name=specialty_name)
    d.years_experience = exp
    d.consultation_fee = fee
    d.average_rating = rating
    return d


def setup_chain(mock_db, result_list):
    """Tạo query mock chainable và trả về list theo .all()."""
    q = MagicMock()
    q.join.return_value = q
    q.filter.return_value = q
    q.order_by.return_value = q
    q.limit.return_value = q
    q.all.return_value = result_list
    mock_db.session.query.return_value = q
    return q


class TestSearchDoctors(unittest.TestCase):
    # -------- PASS 1: không filter, có 2 bác sĩ --------
    @patch("app.dao.dao_doctor_search.func")
    @patch("app.dao.dao_doctor_search.Specialty")
    @patch("app.dao.dao_doctor_search.Hospital")
    @patch("app.dao.dao_doctor_search.User")
    @patch("app.dao.dao_doctor_search.db")
    def test_search_no_filter_two_results(self, m_db, m_user, m_hosp, m_spec, m_func):
        docs = [make_doctor(did=1, first="An", last="Nguyen"),
                make_doctor(did=2, first="Binh", last="Tran")]
        q = setup_chain(m_db, docs)

        out = dao.search_doctors()

        self.assertEqual(len(out), 2)
        self.assertEqual(out[0]["doctor_id"], 1)
        self.assertIn("name", out[0])
        q.join.assert_called()             # đã join các bảng
        q.order_by.assert_called()         # đã order by tên

    # -------- FAIL 1: filter bệnh viện không khớp -> rỗng --------
    @patch("app.dao.dao_doctor_search.func")
    @patch("app.dao.dao_doctor_search.Specialty")
    @patch("app.dao.dao_doctor_search.Hospital")
    @patch("app.dao.dao_doctor_search.User")
    @patch("app.dao.dao_doctor_search.db")
    def test_search_hospital_not_found(self, m_db, *_):
        setup_chain(m_db, [])  # không có kết quả

        out = dao.search_doctors(hospital_name="NoSuch")
        self.assertEqual(out, [])

    # -------- PASS 2: filter accepts_insurance=True --------
    @patch("app.dao.dao_doctor_search.func")
    @patch("app.dao.dao_doctor_search.Specialty")
    @patch("app.dao.dao_doctor_search.Hospital")
    @patch("app.dao.dao_doctor_search.User")
    @patch("app.dao.dao_doctor_search.db")
    def test_search_accepts_insurance_true(self, m_db, *_):
        docs = [make_doctor(did=3, accepts_ins=True),
                make_doctor(did=4, accepts_ins=True)]
        q = setup_chain(m_db, docs)

        out = dao.search_doctors(hospital_accepts_insurance=True)

        self.assertEqual(len(out), 2)
        self.assertTrue(all(r["accepts_insurance"] for r in out))
        q.filter.assert_called()  # có áp dụng filter nhận bảo hiểm

    # -------- FAIL 2: filter accepts_insurance=False nhưng data đều True --------
    @patch("app.dao.dao_doctor_search.func")
    @patch("app.dao.dao_doctor_search.Specialty")
    @patch("app.dao.dao_doctor_search.Hospital")
    @patch("app.dao.dao_doctor_search.User")
    @patch("app.dao.dao_doctor_search.db")
    def test_search_accepts_insurance_false_no_match(self, m_db, *_):
        setup_chain(m_db, [])  # theo query mock là không khớp -> rỗng

        out = dao.search_doctors(hospital_accepts_insurance=False)
        self.assertEqual(out, [])

    # -------- PASS 3: filter theo tên bác sĩ + limit --------
    @patch("app.dao.dao_doctor_search.func")
    @patch("app.dao.dao_doctor_search.Specialty")
    @patch("app.dao.dao_doctor_search.Hospital")
    @patch("app.dao.dao_doctor_search.User")
    @patch("app.dao.dao_doctor_search.db")
    def test_search_doctor_name_with_limit(self, m_db, m_user, *_):
        d = make_doctor(did=5, first="Minh", last="Anh")
        q = setup_chain(m_db, [d])

        out = dao.search_doctors(doctor_name="Minh", limit=1)

        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["name"], "Minh Anh")
        q.limit.assert_called_once_with(1)  # đã áp hạn mức

    # -------- FAIL 3: filter chuyên khoa không có -> rỗng --------
    @patch("app.dao.dao_doctor_search.func")
    @patch("app.dao.dao_doctor_search.Specialty")
    @patch("app.dao.dao_doctor_search.Hospital")
    @patch("app.dao.dao_doctor_search.User")
    @patch("app.dao.dao_doctor_search.db")
    def test_search_specialty_not_found(self, m_db, *_):
        setup_chain(m_db, [])

        out = dao.search_doctors(specialty_name="NoSuchSpec")
        self.assertEqual(out, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
