def handle_order(data, db_conn, emailer, zalo_bot):
    """
    Xử lý một đơn đặt hàng, bao gồm lưu vào DB, gửi email và gửi thông báo Zalo.

    Args:
        data (dict): Dữ liệu đơn hàng, bao gồm 'name', 'phone', 'address', 'email', 'quote'.
        db_conn: Đối tượng kết nối cơ sở dữ liệu với phương thức save_order(data).
        emailer: Đối tượng gửi email với phương thức send_order_email(email, data).
        zalo_bot: Đối tượng Zalo bot với phương thức send_order_notify(phone, data).

    Returns:
        dict: Trạng thái xử lý đơn hàng, bao gồm 'success' (bool) và 'message' (str)
              hoặc 'errors' (list of str).
    """
    name = data.get('name', '').strip()
    phone = data.get('phone', '').strip()
    address = data.get('address', '').strip()
    email = data.get('email', '').strip()
    quote = data.get('quote', {})

    # 1. Kiểm tra dữ liệu đầu vào bắt buộc
    if not name or not phone or not address or not quote:
        return {"success": False, "message": "Thiếu thông tin đặt hàng bắt buộc."}

    # Danh sách để lưu trữ các lỗi không nghiêm trọng (ví dụ: lỗi gửi thông báo)
    non_critical_errors = []

    # 2. Lưu đơn hàng vào cơ sở dữ liệu (bước quan trọng nhất)
    try:
        db_conn.save_order(data)
        db_save_success = True
    except Exception as e:
        # Nếu lưu DB thất bại, coi như toàn bộ đơn hàng thất bại và trả về ngay
        return {"success": False, "message": f"Lỗi nghiêm trọng: Không thể lưu đơn hàng vào cơ sở dữ liệu: {str(e)}"}

    # 3. Gửi email xác nhận (nếu có email)
    if email: # Chỉ cố gắng gửi email nếu có địa chỉ email
        try:
            emailer.send_order_email(email, data)
        except Exception as e:
            non_critical_errors.append(f"Lỗi gửi email xác nhận: {str(e)}")
    else:
        non_critical_errors.append("Không có địa chỉ email được cung cấp để gửi xác nhận.")


    # 4. Gửi thông báo Zalo OA
    try:
        zalo_bot.send_order_notify(phone, data)
    except Exception as e:
        non_critical_errors.append(f"Lỗi gửi thông báo Zalo OA: {str(e)}")

    # 5. Trả về kết quả tổng thể
    if non_critical_errors:
        # Nếu có lỗi không nghiêm trọng, đơn hàng vẫn được lưu nhưng có cảnh báo
        return {
            "success": True, # Đơn hàng đã được lưu thành công
            "message": "Đặt hàng thành công nhưng có một số vấn đề với thông báo.",
            "warnings": non_critical_errors
        }
    else:
        return {"success": True, "message": "Đặt hàng thành công!"}

