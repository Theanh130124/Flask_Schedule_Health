# tests/test_review.py
import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock
from app.dao import dao_review


class TestDAOReview(unittest.TestCase):

    # ---------- PASS 1: add_review thành công ----------
    @patch("app.dao.dao_review._recompute_avg")
    @patch("app.dao.dao_review.db")
    @patch("app.dao.dao_review.Review")
    @patch("app.dao.dao_review.Appointment")
    def test_add_review_success(self, mock_appt, mock_review, mock_db, _recomp):
        # lịch hẹn hoàn tất
        mock_appt.query.filter_by.return_value.first.return_value = MagicMock()
        # chưa có review cho appointment này
        mock_review.query.filter_by.return_value.first.return_value = None
        # instance Review tạo ra
        new_rv = MagicMock()
        mock_review.return_value = new_rv

        rv, msg = dao_review.add_review(
            appointment_id=1, patient_id=10, doctor_id=20, rating=5, comment="ok"
        )

        self.assertIs(rv, new_rv)
        self.assertIn("Đánh giá đã được gửi", msg)
        mock_db.session.add.assert_called_once_with(new_rv)
        mock_db.session.commit.assert_called_once()

    # ---------- FAIL 1: add_review – lịch hẹn chưa hoàn tất ----------
    @patch("app.dao.dao_review.Appointment")
    def test_add_review_fail_not_completed(self, mock_appt):
        mock_appt.query.filter_by.return_value.first.return_value = None

        rv, msg = dao_review.add_review(
            appointment_id=1, patient_id=10, doctor_id=20, rating=5, comment="x"
        )

        self.assertIsNone(rv)
        self.assertIn("Chỉ được đánh giá sau khi bạn đã khám xong", msg)

    # ---------- PASS 2: update_review – sửa lần đầu ----------
    @patch("app.dao.dao_review._recompute_avg")
    @patch("app.dao.dao_review.db")
    @patch("app.dao.dao_review.Review")
    def test_update_review_success_first_time(self, mock_review, mock_db, _recomp):
        rv_obj = MagicMock(review_id=3, doctor_id=20, updated_at=None)
        mock_review.query.filter_by.return_value.first.return_value = rv_obj

        rv, msg = dao_review.update_review(
            review_id=3, patient_id=10, rating=4, comment="cập nhật"
        )

        self.assertIs(rv, rv_obj)
        self.assertIn("Lưu thay đổi thành công", msg)
        self.assertEqual(rv_obj.rating, 4)
        self.assertEqual(rv_obj.comment, "cập nhật")
        mock_db.session.commit.assert_called_once()

    # ---------- FAIL 2: update_review – đã sửa 1 lần ----------
    @patch("app.dao.dao_review.Review")
    def test_update_review_fail_already_updated(self, mock_review):
        rv_obj = MagicMock(review_id=3, updated_at=datetime.utcnow())
        mock_review.query.filter_by.return_value.first.return_value = rv_obj

        rv, msg = dao_review.update_review(
            review_id=3, patient_id=10, rating=5, comment="again"
        )

        self.assertIsNone(rv)
        self.assertIn("chỉ được sửa đánh giá một lần", msg)

    # ---------- PASS 3: doctor_reply – phản hồi lần đầu ----------
    @patch("app.dao.dao_review.db")
    @patch("app.dao.dao_review.Review")
    def test_doctor_reply_success_first_time(self, mock_review, mock_db):
        rv_obj = MagicMock(review_id=7, doctor_id=20, doctor_response=None)
        mock_review.query.filter_by.return_value.first.return_value = rv_obj

        rv, msg, did = dao_review.doctor_reply(
            review_id=7, doctor_id=20, response_text="Cảm ơn bạn"
        )

        self.assertIs(rv, rv_obj)
        self.assertIn("Đã lưu phản hồi", msg)
        self.assertEqual(did, 20)
        self.assertEqual(rv_obj.doctor_response, "Cảm ơn bạn")
        mock_db.session.commit.assert_called_once()

    # ---------- FAIL 3: doctor_reply – đã sửa 1 lần rồi ----------
    @patch("app.dao.dao_review.Review")
    def test_doctor_reply_fail_already_edited_once(self, mock_review):
        rv_obj = MagicMock(
            review_id=8,
            doctor_id=20,
            doctor_response="đã trả lời",
            response_updated_at=datetime.utcnow(),
        )
        mock_review.query.filter_by.return_value.first.return_value = rv_obj

        rv, msg, did = dao_review.doctor_reply(
            review_id=8, doctor_id=20, response_text="muốn sửa nữa"
        )

        self.assertIsNone(rv)
        self.assertIn("đã sửa phản hồi một lần", msg)
        self.assertEqual(did, 20)


if __name__ == "__main__":
    unittest.main(verbosity=2)
