#!/usr/bin/env python3
"""
Test script for mesh optimization functionality
"""

import os
import sys
import tempfile
import logging
from werkzeug.datastructures import FileStorage

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.mesh_optimizer import mesh_optimizer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_test_file(size_mb=150):
    """Create a test file with specified size"""
    temp_dir = tempfile.mkdtemp()
    test_file_path = os.path.join(temp_dir, "test_large.stl")
    
    # Create a simple STL file content (this is a minimal valid STL)
    stl_content = """solid test
facet normal 0.0 0.0 1.0
    outer loop
        vertex 0.0 0.0 0.0
        vertex 1.0 0.0 0.0
        vertex 0.0 1.0 0.0
    endloop
endfacet
endsolid test
"""
    
    # Repeat content to reach desired size
    target_size = size_mb * 1024 * 1024
    content_size = len(stl_content.encode('utf-8'))
    repetitions = max(1, target_size // content_size)
    
    with open(test_file_path, 'w') as f:
        for _ in range(repetitions):
            f.write(stl_content)
    
    return test_file_path

def test_mesh_optimizer():
    """Test the mesh optimizer functionality"""
    print("🧪 Testing Mesh Optimizer...")
    
    # Test 1: Check if optimization libraries are available
    print("\n1. Checking available libraries:")
    print(f"   - trimesh: {'✅ Available' if hasattr(mesh_optimizer, 'TRIMESH_AVAILABLE') and mesh_optimizer.TRIMESH_AVAILABLE else '❌ Not available'}")
    print(f"   - pymeshlab: {'✅ Available' if hasattr(mesh_optimizer, 'PYMESHLAB_AVAILABLE') and mesh_optimizer.PYMESHLAB_AVAILABLE else '❌ Not available'}")
    print(f"   - open3d: {'✅ Available' if hasattr(mesh_optimizer, 'OPEN3D_AVAILABLE') and mesh_optimizer.OPEN3D_AVAILABLE else '❌ Not available'}")
    
    # Test 2: Create a large test file
    print("\n2. Creating test file...")
    test_file_path = create_test_file(150)  # 150MB file
    original_size = os.path.getsize(test_file_path)
    print(f"   Created test file: {original_size / 1024 / 1024:.2f} MB")
    
    # Test 3: Test file size detection
    print("\n3. Testing file size detection:")
    needs_opt = mesh_optimizer.needs_optimization(original_size)
    print(f"   File needs optimization: {'✅ Yes' if needs_opt else '❌ No'}")
    
    # Test 4: Test optimization (if libraries are available)
    if needs_opt:
        print("\n4. Testing mesh optimization:")
        try:
            # Create a FileStorage object from the test file
            with open(test_file_path, 'rb') as f:
                test_file = FileStorage(
                    stream=f,
                    filename="test_large.stl",
                    content_type="application/octet-stream"
                )
            
            # Test optimization
            optimized_path, was_optimized, orig_size, opt_size = mesh_optimizer.optimize_mesh_file(test_file)
            
            if was_optimized:
                compression_ratio = (1 - opt_size / orig_size) * 100
                print(f"   ✅ Optimization successful!")
                print(f"   Original size: {orig_size / 1024 / 1024:.2f} MB")
                print(f"   Optimized size: {opt_size / 1024 / 1024:.2f} MB")
                print(f"   Compression ratio: {compression_ratio:.1f}%")
                
                # Clean up optimized file
                mesh_optimizer.cleanup_temp_files(optimized_path)
            else:
                print("   ⚠️ Optimization failed or not needed")
                
        except Exception as e:
            print(f"   ❌ Optimization error: {str(e)}")
    
    # Clean up test file
    try:
        os.remove(test_file_path)
        os.rmdir(os.path.dirname(test_file_path))
    except:
        pass
    
    print("\n✅ Mesh optimizer test completed!")

def test_small_file():
    """Test with a small file that shouldn't need optimization"""
    print("\n🧪 Testing small file handling...")
    
    # Create a small test file
    test_file_path = create_test_file(10)  # 10MB file
    original_size = os.path.getsize(test_file_path)
    
    needs_opt = mesh_optimizer.needs_optimization(original_size)
    print(f"   Small file ({original_size / 1024 / 1024:.2f} MB) needs optimization: {'❌ Yes' if needs_opt else '✅ No'}")
    
    # Clean up
    try:
        os.remove(test_file_path)
        os.rmdir(os.path.dirname(test_file_path))
    except:
        pass

if __name__ == "__main__":
    print("🚀 Starting Mesh Optimizer Tests...")
    
    try:
        test_mesh_optimizer()
        test_small_file()
        print("\n🎉 All tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        sys.exit(1) 
