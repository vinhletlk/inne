from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
from modules.analyze_stl import analyze_stl, allowed_file
from modules.pricing import calculate_price
from modules.order_handler import handle_order
from utils.emailer import Emailer
from utils.zalo_bot import ZaloBot
from db import DBConn

app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20MB

db_conn = DBConn()
emailer = Emailer(
    smtp_user=os.environ.get('SMTP_USER', 'your_email@gmail.com'),
    smtp_password=os.environ.get('SMTP_PASSWORD', 'your_app_password')
)
zalo_bot = ZaloBot()

@app.route('/', methods=['GET'])
def index():
    return '<h2>3D Pricing App is running!</h2>'

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify(success=False, message="Không có file được upload."), 400
    file = request.files['file']
    if not file or not file.filename:
        return jsonify(success=False, message="Không có file được chọn."), 400
    if not allowed_file(file.filename):
        return jsonify(success=False, message="Chỉ hỗ trợ file STL hoặc OBJ."), 400
    try:
        result = analyze_stl(file)
        return jsonify({"success": True, **result})
    except Exception as e:
        return jsonify(success=False, message=f"Lỗi xử lý file: {str(e)}"), 500

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'file' not in request.files:
        return jsonify(success=False, message="Không có file được upload."), 400
    file = request.files['file']
    if not file or not file.filename:
        return jsonify(success=False, message="Không có file được chọn."), 400
    if not allowed_file(file.filename):
        return jsonify(success=False, message="Chỉ hỗ trợ file STL hoặc OBJ."), 400
    try:
        result = analyze_stl(file)
        return jsonify({"success": True, **result})
    except Exception as e:
        return jsonify(success=False, message=f"Lỗi phân tích: {str(e)}"), 500

@app.route('/price', methods=['POST'])
def price():
    data = request.get_json()
    mass_grams = data.get('mass_grams')
    tech = data.get('tech')
    material = data.get('material')
    if mass_grams is None or not tech or not material:
        return jsonify(success=False, message="Thiếu thông tin tính giá."), 400
    try:
        result = calculate_price(mass_grams, tech, material)
        return jsonify({"success": True, **result})
    except Exception as e:
        return jsonify(success=False, message=f"Lỗi tính giá: {str(e)}"), 500

@app.route('/order', methods=['POST'])
def order():
    data = request.get_json()
    result = handle_order(data, db_conn, emailer, zalo_bot)
    if result.get('success'):
        return jsonify(result)
    else:
        return jsonify(result), 400

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
