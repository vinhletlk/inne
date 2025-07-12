#!/usr/bin/env python3
"""
Debug script to identify upload endpoint issues
"""

import os
import sys
import logging
import tempfile
from werkzeug.datastructures import FileStorage

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def test_dependencies():
    """Test if all required dependencies are available"""
    print("=== Testing Dependencies ===")
    
    # Test trimesh
    try:
        import trimesh
        print("✓ trimesh imported successfully")
        print(f"  Version: {trimesh.__version__}")
    except ImportError as e:
        print(f"✗ trimesh import failed: {e}")
        return False
    
    # Test pymeshlab
    try:
        import pymeshlab
        print("✓ pymeshlab imported successfully")
    except ImportError as e:
        print(f"✗ pymeshlab import failed: {e}")
    
    # Test open3d
    try:
        import open3d as o3d
        print("✓ open3d imported successfully")
    except ImportError as e:
        print(f"✗ open3d import failed: {e}")
    
    # Test numpy
    try:
        import numpy as np
        print("✓ numpy imported successfully")
        print(f"  Version: {np.__version__}")
    except ImportError as e:
        print(f"✗ numpy import failed: {e}")
        return False
    
    return True

def test_modules():
    """Test if all custom modules can be imported"""
    print("\n=== Testing Custom Modules ===")
    
    try:
        from modules.analyze_stl import analyze_stl, allowed_file
        print("✓ analyze_stl module imported successfully")
    except ImportError as e:
        print(f"✗ analyze_stl import failed: {e}")
        return False
    
    try:
        from modules.mesh_optimizer import mesh_optimizer
        print("✓ mesh_optimizer module imported successfully")
    except ImportError as e:
        print(f"✗ mesh_optimizer import failed: {e}")
        return False
    
    try:
        from modules.pricing import calculate_price
        print("✓ pricing module imported successfully")
    except ImportError as e:
        print(f"✗ pricing import failed: {e}")
    
    try:
        from modules.order_handler import handle_order
        print("✓ order_handler module imported successfully")
    except ImportError as e:
        print(f"✗ order_handler import failed: {e}")
    
    return True

def test_file_permissions():
    """Test file system permissions"""
    print("\n=== Testing File Permissions ===")
    
    try:
        temp_dir = tempfile.mkdtemp()
        print(f"✓ Created temp directory: {temp_dir}")
        
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test")
        print("✓ Can write to temp directory")
        
        os.remove(test_file)
        os.rmdir(temp_dir)
        print("✓ Can delete from temp directory")
        
    except Exception as e:
        print(f"✗ File permission test failed: {e}")
        return False
    
    return True

def test_mesh_processing():
    """Test basic mesh processing functionality"""
    print("\n=== Testing Mesh Processing ===")
    
    try:
        import trimesh
        import numpy as np
        
        # Create a simple test mesh
        vertices = np.array([
            [0, 0, 0],
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1]
        ])
        faces = np.array([
            [0, 1, 2],
            [0, 2, 3],
            [0, 3, 1],
            [1, 3, 2]
        ])
        
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        print("✓ Created test mesh")
        
        # Test volume calculation
        volume = mesh.volume
        print(f"✓ Volume calculation: {volume}")
        
        # Test bounds calculation
        bounds = mesh.bounds
        print(f"✓ Bounds calculation: {bounds}")
        
        # Test file export
        test_stl = "test_mesh.stl"
        mesh.export(test_stl)
        print("✓ STL export successful")
        
        # Clean up
        os.remove(test_stl)
        print("✓ Cleanup successful")
        
    except Exception as e:
        print(f"✗ Mesh processing test failed: {e}")
        return False
    
    return True

def test_analyze_stl_function():
    """Test the analyze_stl function with a simple mesh"""
    print("\n=== Testing analyze_stl Function ===")
    
    try:
        import trimesh
        import numpy as np
        from modules.analyze_stl import analyze_stl
        
        # Create a simple test mesh
        vertices = np.array([
            [0, 0, 0],
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1]
        ])
        faces = np.array([
            [0, 1, 2],
            [0, 2, 3],
            [0, 3, 1],
            [1, 3, 2]
        ])
        
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        
        # Save as STL
        test_stl = "test_analyze.stl"
        mesh.export(test_stl)
        
        # Create FileStorage object
        with open(test_stl, 'rb') as f:
            file_storage = FileStorage(
                stream=f,
                filename="test_analyze.stl",
                content_type="application/octet-stream"
            )
            
            # Test analyze_stl function
            result = analyze_stl(file_storage)
            print("✓ analyze_stl function successful")
            print(f"  Result: {result}")
        
        # Clean up
        os.remove(test_stl)
        
    except Exception as e:
        print(f"✗ analyze_stl test failed: {e}")
        return False
    
    return True

def main():
    """Run all diagnostic tests"""
    print("3D Pricing App - Upload Endpoint Diagnostic")
    print("=" * 50)
    
    tests = [
        ("Dependencies", test_dependencies),
        ("Custom Modules", test_modules),
        ("File Permissions", test_file_permissions),
        ("Mesh Processing", test_mesh_processing),
        ("analyze_stl Function", test_analyze_stl_function)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✓ All tests passed! The issue might be in the Flask app configuration or runtime environment.")
        print("\nAdditional debugging steps:")
        print("1. Check Flask app logs for detailed error messages")
        print("2. Verify the server has enough memory for large file processing")
        print("3. Check if the server is running in a restricted environment")
        print("4. Verify all environment variables are set correctly")
    else:
        print("✗ Some tests failed. Please fix the issues above before running the Flask app.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
