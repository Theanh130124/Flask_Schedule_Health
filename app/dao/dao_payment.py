from datetime import datetime
from decimal import Decimal
from app import db
from app.models import Payment, PaymentStatus, PaymentMethodEnum, Invoice, InvoiceStatus, AppointmentStatus
from app.vnpay_service import VNPay  # Import VNPay từ service


def create_vnpay_payment(appointment):
    """Tạo thanh toán VNPAY cho lịch hẹn"""
    # Kiểm tra điều kiện thanh toán
    if appointment.status not in [AppointmentStatus.Scheduled, AppointmentStatus.Completed]:
        return None, "Chỉ có thể thanh toán cho lịch hẹn đã lên lịch hoặc hoàn thành"

    if not appointment.invoice or appointment.invoice.status != InvoiceStatus.Pending:
        return None, "Hóa đơn không tồn tại hoặc đã được thanh toán"

    #Nếu tại dùng luôn
    existing_payment = Payment.query.filter_by(invoice_id=appointment.invoice.invoice_id).first()
    if existing_payment:
        return existing_payment, "Đã có payment cho hóa đơn này"

    # Tạo payment record
    payment = Payment(
        invoice_id=appointment.invoice.invoice_id,
        amount_paid=appointment.invoice.amount,
        payment_method=PaymentMethodEnum.VNPay,
        status=PaymentStatus.Pending
    )

    db.session.add(payment)
    db.session.commit()

    return payment, "Tạo thanh toán thành công"


def process_vnpay_callback(params):
    """Xử lý callback từ VNPAY"""
    vnpay = VNPay()

    if not vnpay.verify_response(params):
        return False, "Checksum không hợp lệ"

    order_id = params.get('vnp_TxnRef')
    response_code = params.get('vnp_ResponseCode')
    transaction_id = params.get('vnp_TransactionNo')
    amount = Decimal(params.get('vnp_Amount', 0)) / 100  # Chuyển đổi về VND

    # Lấy payment từ database
    payment = Payment.query.filter_by(payment_id=order_id).first()
    if not payment:
        return False, "Payment không tồn tại"

    # Lấy invoice và appointment liên quan
    invoice = payment.invoice
    appointment = invoice.appointment

    if response_code == '00':  # Thành công
        # CẬP NHẬT QUAN TRỌNG: Đảm bảo cả Payment và Invoice đều được cập nhật
        payment.status = PaymentStatus.Completed
        payment.transaction_id = transaction_id
        payment.payment_date = datetime.now()

        # Cập nhật invoice status thành Paid
        invoice.status = InvoiceStatus.Paid

        # Nếu appointment chưa completed và đã thanh toán, có thể cập nhật trạng thái
        if appointment.status == AppointmentStatus.Scheduled:
            # Có thể thêm logic để đánh dấu appointment là đã thanh toán
            # hoặc giữ nguyên trạng thái Scheduled
            pass

        db.session.commit()
        return True, "Thanh toán thành công"
    else:
        payment.status = PaymentStatus.Failed
        db.session.commit()
        return False, f"Thanh toán thất bại: {response_code}"