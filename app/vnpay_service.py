import hashlib
import hmac
import urllib.parse
from datetime import datetime
from decimal import Decimal

from flask import current_app


class VNPay:
    def __init__(self):
        self.tmn_code = current_app.config.get('VNPAY_TMN_CODE')
        self.hash_secret = current_app.config.get('VNPAY_HASH_SECRET')
        self.url = current_app.config.get('VNPAY_URL')
        self.return_url = current_app.config.get('VNPAY_RETURN_URL')

    def create_payment_url(self, order_info, amount, order_id, ip_addr):
        vnp_params = {
            'vnp_Version': '2.1.0',
            'vnp_Command': 'pay',
            'vnp_TmnCode': self.tmn_code,
            'vnp_Amount': str(int(amount * 100)),  # VNPAY yêu cầu amount * 100
            'vnp_CurrCode': 'VND',
            'vnp_TxnRef': str(order_id),
            'vnp_OrderInfo': order_info,
            'vnp_OrderType': 'billpayment',
            'vnp_Locale': 'vn',
            'vnp_ReturnUrl': self.return_url,
            'vnp_IpAddr': ip_addr,
            'vnp_CreateDate': datetime.now().strftime('%Y%m%d%H%M%S')
        }

        # Sắp xếp tham số theo thứ tự alphabet
        vnp_params_sorted = sorted(vnp_params.items(), key=lambda x: x[0])

        # Tạo query string
        query_string = '&'.join([f'{key}={urllib.parse.quote_plus(str(value))}'
                                 for key, value in vnp_params_sorted if value])

        # Tạo checksum
        secure_hash = hmac.new(self.hash_secret.encode(),
                               query_string.encode(),
                               hashlib.sha512).hexdigest()

        # Thêm checksum vào query string
        payment_url = f'{self.url}?{query_string}&vnp_SecureHash={secure_hash}'

        return payment_url

    def verify_response(self, params):
        vnp_params = {k: v for k, v in params.items() if k.startswith('vnp_') and k != 'vnp_SecureHash'}
        vnp_secure_hash = params.get('vnp_SecureHash', '')

        # Sắp xếp tham số
        vnp_params_sorted = sorted(vnp_params.items(), key=lambda x: x[0])
        query_string = '&'.join([f'{key}={urllib.parse.quote_plus(str(value))}'
                                 for key, value in vnp_params_sorted if value])

        # Verify checksum
        computed_hash = hmac.new(self.hash_secret.encode(),
                                 query_string.encode(),
                                 hashlib.sha512).hexdigest()

        return computed_hash == vnp_secure_hash