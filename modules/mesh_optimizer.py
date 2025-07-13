"""
Mesh Optimization Module
Provides functionality to optimize large mesh files by reducing their size
"""

import os
import tempfile
import logging
from werkzeug.datastructures import FileStorage

# Configure logging
logger = logging.getLogger(__name__)

# Check library availability
TRIMESH_AVAILABLE = False
PYMESHLAB_AVAILABLE = False
OPEN3D_AVAILABLE = False

try:
    import trimesh
    TRIMESH_AVAILABLE = True
    logger.info("trimesh library is available")
except ImportError:
    logger.warning("trimesh library not available")

try:
    import pymeshlab
    PYMESHLAB_AVAILABLE = True
    logger.info("pymeshlab library is available")
except ImportError:
    logger.warning("pymeshlab library not available")

try:
    import open3d as o3d
    OPEN3D_AVAILABLE = True
    logger.info("open3d library is available")
except ImportError:
    logger.warning("open3d library not available")

# Configuration
MAX_FILE_SIZE_MB = 100  # Files larger than this will be optimized
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

def needs_optimization(file_size_bytes):
    """
    Check if a file needs optimization based on its size
    
    Args:
        file_size_bytes (int): Size of the file in bytes
        
    Returns:
        bool: True if file needs optimization, False otherwise
    """
    return file_size_bytes > MAX_FILE_SIZE_BYTES

def optimize_mesh_file(file_storage):
    """
    Optimize a mesh file to reduce its size
    
    Args:
        file_storage (FileStorage): The uploaded file
        
    Returns:
        tuple: (optimized_path, was_optimized, original_size, optimized_size)
    """
    if not isinstance(file_storage, FileStorage):
        raise ValueError("Expected FileStorage object")
    
    # Create temporary files
    temp_dir = tempfile.mkdtemp()
    original_path = os.path.join(temp_dir, f"original_{file_storage.filename}")
    optimized_path = os.path.join(temp_dir, f"optimized_{file_storage.filename}")
    
    # Save original file
    file_storage.save(original_path)
    original_size = os.path.getsize(original_path)
    
    # Check if optimization is needed
    if not needs_optimization(original_size):
        logger.info(f"File {file_storage.filename} ({original_size} bytes) does not need optimization")
        return original_path, False, original_size, original_size
    
    # Try different optimization methods
    optimized_size = original_size
    was_optimized = False
    
    try:
        if TRIMESH_AVAILABLE:
            was_optimized, optimized_size = _optimize_with_trimesh(original_path, optimized_path)
        elif PYMESHLAB_AVAILABLE:
            was_optimized, optimized_size = _optimize_with_pymeshlab(original_path, optimized_path)
        else:
            logger.warning("No optimization libraries available, returning original file")
            return original_path, False, original_size, original_size
            
    except Exception as e:
        logger.error(f"Optimization failed: {str(e)}")
        return original_path, False, original_size, original_size
    
    if was_optimized:
        logger.info(f"File optimized from {original_size} to {optimized_size} bytes")
        return optimized_path, True, original_size, optimized_size
    else:
        logger.info("Optimization was not successful, returning original file")
        return original_path, False, original_size, original_size

def _optimize_with_trimesh(input_path, output_path):
    """
    Optimize mesh using trimesh library
    
    Args:
        input_path (str): Path to input file
        output_path (str): Path to output file
        
    Returns:
        tuple: (was_optimized, optimized_size)
    """
    try:
        # Load the mesh
        mesh = trimesh.load_mesh(input_path)
        
        # Apply basic optimizations
        if hasattr(mesh, 'remove_duplicate_faces'):
            mesh.remove_duplicate_faces()
        if hasattr(mesh, 'remove_degenerate_faces'):
            mesh.remove_degenerate_faces()
        if hasattr(mesh, 'remove_unreferenced_vertices'):
            mesh.remove_unreferenced_vertices()
        
        # Simplify the mesh (reduce face count)
        if hasattr(mesh, 'simplify_quadratic_decimation'):
            # Reduce to 70% of original face count
            target_faces = int(len(mesh.faces) * 0.7)
            mesh = mesh.simplify_quadratic_decimation(target_faces)
        
        # Export optimized mesh
        mesh.export(output_path)
        optimized_size = os.path.getsize(output_path)
        
        return True, optimized_size
        
    except Exception as e:
        logger.error(f"Trimesh optimization failed: {str(e)}")
        return False, 0

def _optimize_with_pymeshlab(input_path, output_path):
    """
    Optimize mesh using pymeshlab library
    
    Args:
        input_path (str): Path to input file
        output_path (str): Path to output file
        
    Returns:
        tuple: (was_optimized, optimized_size)
    """
    try:
        # Create a new MeshSet
        ms = pymeshlab.MeshSet()
        
        # Load the mesh
        ms.load_new_mesh(input_path)
        
        # Apply optimizations
        ms.meshing_remove_duplicate_faces()
        ms.meshing_remove_duplicate_vertices()
        ms.meshing_remove_unreferenced_vertices()
        
        # Simplify the mesh
        ms.meshing_decimation_quadric_edge_collapse(targetfacenum=int(ms.current_mesh().face_number() * 0.7))
        
        # Save the optimized mesh
        ms.save_current_mesh(output_path)
        optimized_size = os.path.getsize(output_path)
        
        return True, optimized_size
        
    except Exception as e:
        logger.error(f"PyMeshLab optimization failed: {str(e)}")
        return False, 0

def cleanup_temp_files(file_path):
    """
    Clean up temporary files and directories
    
    Args:
        file_path (str): Path to the file to clean up
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up temporary file: {file_path}")
            
            # Try to remove the temporary directory if it's empty
            temp_dir = os.path.dirname(file_path)
            try:
                os.rmdir(temp_dir)
                logger.info(f"Cleaned up temporary directory: {temp_dir}")
            except OSError:
                # Directory not empty, that's fine
                pass
                
    except Exception as e:
        logger.warning(f"Could not clean up temporary file {file_path}: {str(e)}")

# Create a module-level instance for backward compatibility
class MeshOptimizer:
    """Mesh optimizer class for backward compatibility"""
    
    def __init__(self):
        self.TRIMESH_AVAILABLE = TRIMESH_AVAILABLE
        self.PYMESHLAB_AVAILABLE = PYMESHLAB_AVAILABLE
        self.OPEN3D_AVAILABLE = OPEN3D_AVAILABLE
    
    def needs_optimization(self, file_size_bytes):
        return needs_optimization(file_size_bytes)
    
    def optimize_mesh_file(self, file_storage):
        return optimize_mesh_file(file_storage)
    
    def cleanup_temp_files(self, file_path):
        return cleanup_temp_files(file_path)

# Create module instance
mesh_optimizer = MeshOptimizer()