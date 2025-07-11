def handle_order(data, db_conn, emailer, zalo_bot):
    name = data.get('name', '').strip()
    phone = data.get('phone', '').strip()
    address = data.get('address', '').strip()
    email = data.get('email', '').strip() if 'email' in data else ''
    quote = data.get('quote', {})
    if not name or not phone or not address or not quote:
        return {"success": False, "message": "Thiếu thông tin đặt hàng."}
    try:
        db_conn.save_order(data)
    except Exception as e:
        return {"success": False, "message": f"Lỗi lưu đơn: {str(e)}"}
    try:
        emailer.send_order_email(email, data)
    except Exception as e:
        return {"success": False, "message": f"Lỗi gửi email: {str(e)}"}
    try:
        zalo_bot.send_order_notify(phone, data)
    except Exception as e:
        return {"success": False, "message": f"Lỗi gửi Zalo OA: {str(e)}"}
    return {"success": True, "message": "Đặt hàng thành công!"}