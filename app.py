from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import logging
import requests
import tempfile
from werkzeug.exceptions import RequestEntityTooLarge
from modules.analyze_stl import analyze_stl, allowed_file
from modules.pricing import calculate_price
from modules.order_handler import handle_order
from modules.mesh_optimizer import mesh_optimizer
from utils.emailer import Emailer
from utils.zalo_bot import ZaloBot
from db import DBConn

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components
try:
    db_conn = DBConn()
    logger.info("Database connection initialized")
except Exception as e:
    logger.error(f"Failed to initialize database connection: {e}")
    db_conn = None

try:
    emailer = Emailer(
        smtp_user=os.environ.get('SMTP_USER', 'your_email@gmail.com'),
        smtp_password=os.environ.get('SMTP_PASSWORD', 'your_app_password')
    )
    logger.info("Emailer initialized")
except Exception as e:
    logger.error(f"Failed to initialize emailer: {e}")
    emailer = None

try:
    zalo_bot = ZaloBot()
    logger.info("ZaloBot initialized")
except Exception as e:
    logger.error(f"Failed to initialize ZaloBot: {e}")
    zalo_bot = None

@app.route('/', methods=['GET'])
def index():
    return '<h2>3D Pricing App is running!</h2>'

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify app status"""
    try:
        status = {
            'status': 'healthy',
            'modules': {
                'analyze_stl': analyze_stl is not None,
                'pricing': calculate_price is not None,
                'order_handler': handle_order is not None,
                'mesh_optimizer': mesh_optimizer is not None,
                'emailer': emailer is not None,
                'zalo_bot': zalo_bot is not None,
                'db_conn': db_conn is not None
            }
        }
        return jsonify(status)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@app.route('/analyze-url', methods=['POST'])
def analyze_url():
    """Analyze STL/OBJ file from Cloudinary URL"""
    try:
        data = request.get_json()
        if not data or 'file_url' not in data:
            return jsonify(success=False, message="Thiếu URL file."), 400
        
        file_url = data['file_url']
        logger.info(f"Analyzing file from URL: {file_url}")
        
        # Download file from Cloudinary URL
        response = requests.get(file_url, timeout=30)
        if not response.ok:
            return jsonify(success=False, message="Không thể tải file từ URL."), 400
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.stl') as temp_file:
            temp_file.write(response.content)
            temp_file_path = temp_file.name
        
        try:
            # Analyze the file
            with open(temp_file_path, 'rb') as f:
                from werkzeug.datastructures import FileStorage
                file_storage = FileStorage(
                    stream=f,
                    filename='temp.stl',
                    content_type='application/octet-stream'
                )
                result = analyze_stl(file_storage)
            
            logger.info(f"Analysis result: {result}")
            return jsonify({"success": True, **result})
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass
                
    except Exception as e:
        logger.error(f"Error analyzing file from URL: {e}")
        return jsonify(success=False, message=f"Lỗi phân tích file: {str(e)}"), 500

@app.route('/price', methods=['POST'])
def price():
    """Calculate price based on mass and technology"""
    try:
        data = request.get_json()
        if not data:
            return jsonify(success=False, message="Không có dữ liệu JSON."), 400
        
        mass_grams = data.get('mass_grams')
        tech = data.get('tech')
        material = data.get('material')
        
        if mass_grams is None or not tech or not material:
            return jsonify(success=False, message="Thiếu thông tin tính giá."), 400
        
        if not calculate_price:
            return jsonify(success=False, message="Module tính giá không khả dụng."), 500
        
        result = calculate_price(mass_grams, tech, material)
        return jsonify({"success": True, **result})
        
    except Exception as e:
        logger.error(f"Error in price calculation: {e}")
        return jsonify(success=False, message=f"Lỗi tính giá: {str(e)}"), 500

@app.route('/order', methods=['POST'])
def order():
    """Process order with Cloudinary URLs"""
    try:
        data = request.get_json()
        if not data:
            return jsonify(success=False, message="Không có dữ liệu JSON."), 400
        
        logger.info("Processing order with Cloudinary URLs")
        
        # Extract file URLs from order data
        file_urls = data.get('file_urls', [])
        files_info = data.get('files', [])
        
        if not file_urls:
            return jsonify(success=False, message="Không có file URLs trong đơn hàng."), 400
        
        logger.info(f"Order contains {len(file_urls)} files")
        
        # Process each file URL to get mass and volume
        processed_files = []
        total_mass = 0
        total_volume = 0
        
        for i, file_url in enumerate(file_urls):
            try:
                logger.info(f"Processing file {i+1}/{len(file_urls)}: {file_url}")
                
                # Download and analyze file
                response = requests.get(file_url, timeout=60)
                if not response.ok:
                    logger.error(f"Failed to download file {i+1}: {response.status_code}")
                    continue
                
                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.stl') as temp_file:
                    temp_file.write(response.content)
                    temp_file_path = temp_file.name
                
                try:
                    # Analyze the file
                    with open(temp_file_path, 'rb') as f:
                        from werkzeug.datastructures import FileStorage
                        file_storage = FileStorage(
                            stream=f,
                            filename=f'file_{i+1}.stl',
                            content_type='application/octet-stream'
                        )
                        analysis_result = analyze_stl(file_storage)
                    
                    # Get file info
                    file_info = files_info[i] if i < len(files_info) else {}
                    file_name = file_info.get('name', f'file_{i+1}')
                    file_size = file_info.get('size', 0)
                    
                    processed_file = {
                        'name': file_name,
                        'size': file_size,
                        'cloudinary_url': file_url,
                        'mass_grams': analysis_result['mass_grams'],
                        'volume_cm3': analysis_result['volume_cm3'],
                        'dimensions_mm': analysis_result['dimensions_mm']
                    }
                    
                    processed_files.append(processed_file)
                    total_mass += analysis_result['mass_grams']
                    total_volume += analysis_result['volume_cm3']
                    
                    logger.info(f"File {file_name} processed: {analysis_result['mass_grams']}g, {analysis_result['volume_cm3']}cm³")
                    
                finally:
                    # Clean up temporary file
                    try:
                        os.unlink(temp_file_path)
                    except:
                        pass
                        
            except Exception as e:
                logger.error(f"Error processing file {i+1}: {e}")
                continue
        
        if not processed_files:
            return jsonify(success=False, message="Không thể xử lý bất kỳ file nào."), 400
        
        # Calculate price
        technology = data.get('technology')
        color = data.get('color')
        resolution = data.get('resolution')
        
        if not technology:
            return jsonify(success=False, message="Thiếu thông tin công nghệ in."), 400
        
        material = 'PLA' if technology == 'FDM' else 'Resin'
        price_result = calculate_price(total_mass, technology, material)
        
        # Prepare order data for backend processing
        order_data = {
            'name': data.get('name', ''),
            'phone': data.get('phone', ''),
            'address': data.get('address', ''),
            'email': data.get('email', ''),
            'files': processed_files,
            'file_urls': file_urls,
            'technology': technology,
            'color': color,
            'resolution': resolution,
            'total_mass': total_mass,
            'total_volume': total_volume,
            'price': price_result.get('price', 0),
            'quote': {
                'filename': ', '.join([f['name'] for f in processed_files]),
                'mass_grams': total_mass,
                'volume_cm3': total_volume,
                'technology': technology,
                'material': material,
                'color': color,
                'resolution': resolution,
                'price': price_result.get('price', 0),
                'order_date': data.get('order_date', '')
            }
        }
        
        logger.info(f"Order processed: {len(processed_files)} files, {total_mass}g, ${price_result.get('price', 0)}")
        
        # Send to order handler
        if not handle_order:
            return jsonify(success=False, message="Module xử lý đơn hàng không khả dụng."), 500
        
        result = handle_order(order_data, db_conn, emailer, zalo_bot)
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error processing order: {e}")
        return jsonify(success=False, message=f"Lỗi xử lý đơn hàng: {str(e)}"), 500

@app.route('/test', methods=['GET'])
def test():
    """Test endpoint to verify the app is working"""
    return jsonify({
        'status': 'ok',
        'message': '3D Pricing App is running',
        'timestamp': '2024-01-01T00:00:00Z'
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True) 
