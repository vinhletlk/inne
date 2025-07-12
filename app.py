from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import logging
from modules.analyze_stl import analyze_stl, allowed_file
from modules.pricing import calculate_price
from modules.order_handler import handle_order
from modules.mesh_optimizer import mesh_optimizer
from utils.emailer import Emailer
from utils.zalo_bot import ZaloBot
from db import DBConn

app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB for large files

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
        # Get file size
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        logging.info(f"Uploading file: {file.filename}, size: {file_size / 1024 / 1024:.2f} MB")
        
        # Check if file is too large and needs optimization
        if file_size > 100 * 1024 * 1024:  # 100MB
            logging.info("File is large, attempting optimization...")
            
            try:
                # Optimize the mesh file
                optimized_path, was_optimized, original_size, optimized_size = mesh_optimizer.optimize_mesh_file(file)
                
                if was_optimized:
                    logging.info(f"File optimized: {original_size / 1024 / 1024:.2f} MB -> {optimized_size / 1024 / 1024:.2f} MB")
                    
                    # Create a new file object from the optimized file
                    with open(optimized_path, 'rb') as f:
                        from werkzeug.datastructures import FileStorage
                        optimized_file = FileStorage(
                            stream=f,
                            filename=file.filename,
                            content_type=file.content_type
                        )
                    
                    # Analyze the optimized file
                    result = analyze_stl(optimized_file)
                    
                    # Add optimization info to result
                    result['was_optimized'] = True
                    result['original_size_mb'] = round(original_size / 1024 / 1024, 2)
                    result['optimized_size_mb'] = round(optimized_size / 1024 / 1024, 2)
                    result['compression_ratio'] = round((1 - optimized_size / original_size) * 100, 1)
                    
                    # Clean up temporary files
                    mesh_optimizer.cleanup_temp_files(optimized_path)
                    
                    return jsonify({"success": True, **result})
                else:
                    # Optimization failed, try with original file
                    logging.warning("Mesh optimization failed, trying with original file")
                    file.seek(0)  # Reset file pointer
                    result = analyze_stl(file)
                    return jsonify({"success": True, **result})
                    
            except Exception as opt_error:
                logging.error(f"Optimization error: {str(opt_error)}")
                # If optimization fails, try with original file
                file.seek(0)  # Reset file pointer
                result = analyze_stl(file)
                return jsonify({"success": True, **result})
        else:
            # File is small enough, process normally
            result = analyze_stl(file)
            return jsonify({"success": True, **result})
            
    except Exception as e:
        logging.error(f"Upload error: {str(e)}")
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
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port) 
