from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import logging
import traceback
import sys
from werkzeug.exceptions import RequestEntityTooLarge

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Import modules with error handling
try:
    from modules.analyze_stl import analyze_stl, allowed_file
    logger.info("Successfully imported analyze_stl module")
except ImportError as e:
    logger.error(f"Failed to import analyze_stl module: {e}")
    analyze_stl = None
    allowed_file = None

try:
    from modules.pricing import calculate_price
    logger.info("Successfully imported pricing module")
except ImportError as e:
    logger.error(f"Failed to import pricing module: {e}")
    calculate_price = None

try:
    from modules.order_handler import handle_order
    logger.info("Successfully imported order_handler module")
except ImportError as e:
    logger.error(f"Failed to import order_handler module: {e}")
    handle_order = None

try:
    from modules.mesh_optimizer import mesh_optimizer
    logger.info("Successfully imported mesh_optimizer module")
except ImportError as e:
    logger.error(f"Failed to import mesh_optimizer module: {e}")
    mesh_optimizer = None

try:
    from utils.emailer import Emailer
    logger.info("Successfully imported Emailer")
except ImportError as e:
    logger.error(f"Failed to import Emailer: {e}")
    Emailer = None

try:
    from utils.zalo_bot import ZaloBot
    logger.info("Successfully imported ZaloBot")
except ImportError as e:
    logger.error(f"Failed to import ZaloBot: {e}")
    ZaloBot = None

try:
    from db import DBConn
    logger.info("Successfully imported DBConn")
except ImportError as e:
    logger.error(f"Failed to import DBConn: {e}")
    DBConn = None

app = Flask(__name__)
CORS(app)

# Configure app
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB for large files
app.config['UPLOAD_FOLDER'] = '/tmp'  # Ensure upload folder exists

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize components with error handling
try:
    db_conn = DBConn() if DBConn else None
    logger.info("Database connection initialized")
except Exception as e:
    logger.error(f"Failed to initialize database connection: {e}")
    db_conn = None

try:
    emailer = Emailer(
        smtp_user=os.environ.get('SMTP_USER', 'your_email@gmail.com'),
        smtp_password=os.environ.get('SMTP_PASSWORD', 'your_app_password')
    ) if Emailer else None
    logger.info("Emailer initialized")
except Exception as e:
    logger.error(f"Failed to initialize emailer: {e}")
    emailer = None

try:
    zalo_bot = ZaloBot() if ZaloBot else None
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
            },
            'upload_folder': app.config['UPLOAD_FOLDER'],
            'max_content_length': app.config['MAX_CONTENT_LENGTH']
        }
        return jsonify(status)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload():
    """Enhanced upload endpoint with detailed error handling"""
    logger.info("Upload endpoint called")
    
    try:
        # Check if file is present
        if 'file' not in request.files:
            logger.warning("No file in request")
            return jsonify(success=False, message="Không có file được upload."), 400
        
        file = request.files['file']
        logger.info(f"File received: {file.filename}")
        
        if not file or not file.filename:
            logger.warning("Empty file or no filename")
            return jsonify(success=False, message="Không có file được chọn."), 400
        
        if not allowed_file or not allowed_file(file.filename):
            logger.warning(f"Invalid file type: {file.filename}")
            return jsonify(success=False, message="Chỉ hỗ trợ file STL hoặc OBJ."), 400
        
        # Get file size
        try:
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset to beginning
            logger.info(f"File size: {file_size / 1024 / 1024:.2f} MB")
        except Exception as e:
            logger.error(f"Error getting file size: {e}")
            return jsonify(success=False, message="Lỗi khi đọc thông tin file."), 400
        
        # Check if file is too large
        if file_size > app.config['MAX_CONTENT_LENGTH']:
            logger.warning(f"File too large: {file_size} bytes")
            return jsonify(success=False, message="File quá lớn. Kích thước tối đa là 200MB."), 400
        
        # Process file based on size
        if file_size > 100 * 1024 * 1024:  # 100MB
            logger.info("Processing large file with optimization")
            return process_large_file(file, file_size)
        else:
            logger.info("Processing normal file")
            return process_normal_file(file)
            
    except RequestEntityTooLarge:
        logger.error("Request entity too large")
        return jsonify(success=False, message="File quá lớn. Kích thước tối đa là 200MB."), 413
    except Exception as e:
        logger.error(f"Unexpected error in upload: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify(success=False, message=f"Lỗi xử lý file: {str(e)}"), 500

def process_large_file(file, file_size):
    """Process large files with optimization"""
    try:
        if not mesh_optimizer:
            logger.warning("Mesh optimizer not available, trying normal processing")
            return process_normal_file(file)
        
        logger.info("Attempting mesh optimization...")
        
        # Optimize the mesh file
        optimized_path, was_optimized, original_size, optimized_size = mesh_optimizer.optimize_mesh_file(file)
        
        if was_optimized:
            logger.info(f"File optimized: {original_size / 1024 / 1024:.2f} MB -> {optimized_size / 1024 / 1024:.2f} MB")
            
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
            try:
                mesh_optimizer.cleanup_temp_files(optimized_path)
            except Exception as cleanup_error:
                logger.warning(f"Cleanup error: {cleanup_error}")
            
            return jsonify({"success": True, **result})
        else:
            # Optimization failed, try with original file
            logger.warning("Mesh optimization failed, trying with original file")
            file.seek(0)  # Reset file pointer
            return process_normal_file(file)
            
    except Exception as opt_error:
        logger.error(f"Optimization error: {opt_error}")
        logger.error(f"Optimization traceback: {traceback.format_exc()}")
        # If optimization fails, try with original file
        try:
            file.seek(0)  # Reset file pointer
            return process_normal_file(file)
        except Exception as e:
            logger.error(f"Fallback processing also failed: {e}")
            return jsonify(success=False, message=f"Lỗi xử lý file: {str(e)}"), 500

def process_normal_file(file):
    """Process normal sized files"""
    try:
        if not analyze_stl:
            logger.error("analyze_stl function not available")
            return jsonify(success=False, message="Module phân tích file không khả dụng."), 500
        
        logger.info("Analyzing STL file...")
        result = analyze_stl(file)
        logger.info(f"Analysis result: {result}")
        return jsonify({"success": True, **result})
        
    except Exception as e:
        logger.error(f"Error in normal file processing: {e}")
        logger.error(f"Normal processing traceback: {traceback.format_exc()}")
        return jsonify(success=False, message=f"Lỗi phân tích file: {str(e)}"), 500

@app.route('/analyze', methods=['POST'])
def analyze():
    """Enhanced analyze endpoint"""
    logger.info("Analyze endpoint called")
    
    try:
        if 'file' not in request.files:
            return jsonify(success=False, message="Không có file được upload."), 400
        
        file = request.files['file']
        if not file or not file.filename:
            return jsonify(success=False, message="Không có file được chọn."), 400
        
        if not allowed_file or not allowed_file(file.filename):
            return jsonify(success=False, message="Chỉ hỗ trợ file STL hoặc OBJ."), 400
        
        if not analyze_stl:
            return jsonify(success=False, message="Module phân tích file không khả dụng."), 500
        
        result = analyze_stl(file)
        return jsonify({"success": True, **result})
        
    except Exception as e:
        logger.error(f"Error in analyze endpoint: {e}")
        logger.error(f"Analyze traceback: {traceback.format_exc()}")
        return jsonify(success=False, message=f"Lỗi phân tích: {str(e)}"), 500

@app.route('/price', methods=['POST'])
def price():
    """Enhanced price endpoint"""
    logger.info("Price endpoint called")
    
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
        logger.error(f"Error in price endpoint: {e}")
        logger.error(f"Price traceback: {traceback.format_exc()}")
        return jsonify(success=False, message=f"Lỗi tính giá: {str(e)}"), 500

@app.route('/order', methods=['POST'])
def order():
    """Enhanced order endpoint"""
    logger.info("Order endpoint called")
    
    try:
        data = request.get_json()
        if not data:
            return jsonify(success=False, message="Không có dữ liệu JSON."), 400
        
        if not handle_order:
            return jsonify(success=False, message="Module xử lý đơn hàng không khả dụng."), 500
        
        result = handle_order(data, db_conn, emailer, zalo_bot)
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error in order endpoint: {e}")
        logger.error(f"Order traceback: {traceback.format_exc()}")
        return jsonify(success=False, message=f"Lỗi xử lý đơn hàng: {str(e)}"), 500

@app.errorhandler(413)
def too_large(e):
    """Handle file too large errors"""
    logger.warning("File too large error")
    return jsonify(success=False, message="File quá lớn. Kích thước tối đa là 200MB."), 413

@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors"""
    logger.error(f"Internal server error: {e}")
    logger.error(f"500 error traceback: {traceback.format_exc()}")
    return jsonify(success=False, message="Lỗi máy chủ nội bộ."), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True) 
