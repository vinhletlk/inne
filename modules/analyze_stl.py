import trimesh
from werkzeug.utils import secure_filename

DENSITY_G_CM3 = 1.24  # PLA mặc định
ALLOWED_EXTENSIONS = {'stl', 'obj'}

def allowed_file(filename):
    return filename and '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def analyze_stl(file):
    ext = file.filename.rsplit('.', 1)[1].lower()
    mesh = trimesh.load(file.stream, file_type=ext, process=False)
    if isinstance(mesh, trimesh.Scene):
        if not mesh.geometry:
            raise ValueError("Không tìm thấy mesh trong file.")
        mesh = list(mesh.geometry.values())[0]
    if not isinstance(mesh, trimesh.Trimesh) or mesh.volume is None:
        raise ValueError("Không thể tính thể tích từ file này.")
    volume_cm3 = mesh.volume / 1000
    bounds = mesh.bounds
    length = bounds[1][0] - bounds[0][0]
    width = bounds[1][1] - bounds[0][1]
    height = bounds[1][2] - bounds[0][2]
    mass_grams = volume_cm3 * DENSITY_G_CM3
    return {
        "filename": secure_filename(file.filename),
        "volume_cm3": round(volume_cm3, 2),
        "dimensions_mm": {
            "length": round(length, 2),
            "width": round(width, 2),
            "height": round(height, 2)
        },
        "mass_grams": round(mass_grams, 2),
        "density_g_cm3": DENSITY_G_CM3
    }