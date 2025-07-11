class ZaloBot:
    def __init__(self, access_token=None):
        self.access_token = access_token

    def send_order_notify(self, phone, data):
        print(f"[Zalo OA] Gửi thông báo đơn hàng mới tới {phone}: {data}")