# Apply to index.html
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class Emailer:
    def __init__(self, smtp_user, smtp_password, smtp_server='smtp.gmail.com', smtp_port=587):
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port

    def send_order_email(self, to_email, data):
        name = data.get('name', '')
        phone = data.get('phone', '')
        address = data.get('address', '')
        quote = data.get('quote', {})
        subject = "Xác nhận đơn hàng in 3D"
        body = f"""
        <h3>Thông tin đơn hàng in 3D</h3>
        <ul>
            <li><b>Khách hàng:</b> {name}</li>
            <li><b>Số điện thoại:</b> {phone}</li>
            <li><b>Địa chỉ nhận hàng:</b> {address}</li>
        </ul>
        <h4>Thông tin sản phẩm:</h4>
        <ul>
            <li><b>Tên file:</b> {quote.get('filename','')}</li>
            <li><b>Công nghệ in:</b> {quote.get('tech','')}</li>
            <li><b>Khối lượng:</b> {quote.get('mass_grams','')} gram</li>
            <li><b>Kích thước:</b> {quote.get('dimensions_mm',{})}</li>
            <li><b>Giá tiền:</b> {quote.get('price','')} đ</li>
        </ul>
        """
        msg = MIMEMultipart()
        msg['From'] = self.smtp_user
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        server = smtplib.SMTP(self.smtp_server, self.smtp_port)
        server.starttls()
        server.login(self.smtp_user, self.smtp_password)
        server.sendmail(self.smtp_user, to_email, msg.as_string())
        server.quit()