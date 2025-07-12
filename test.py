#!/usr/bin/env python3
"""
Simple test script to verify the upload endpoint is working
"""

import requests
import os
import tempfile
import numpy as np

def create_test_stl():
    """Create a simple test STL file"""
    try:
        import trimesh
        
        # Create a simple cube mesh
        vertices = np.array([
            [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
            [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]
        ])
        faces = np.array([
            [0, 1, 2], [0, 2, 3],  # bottom
            [4, 6, 5], [4, 7, 6],  # top
            [0, 4, 1], [1, 4, 5],  # front
            [2, 6, 3], [3, 6, 7],  # back
            [0, 3, 4], [3, 7, 4],  # left
            [1, 5, 2], [2, 5, 6]   # right
        ])
        
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        
        # Save as STL
        temp_file = tempfile.NamedTemporaryFile(suffix='.stl', delete=False)
        mesh.export(temp_file.name)
        return temp_file.name
        
    except ImportError:
        print("trimesh not available, creating a dummy file")
        # Create a dummy STL file
        temp_file = tempfile.NamedTemporaryFile(suffix='.stl', delete=False)
        with open(temp_file.name, 'w') as f:
            f.write("solid test\n")
            f.write("  facet normal 0 0 1\n")
            f.write("    outer loop\n")
            f.write("      vertex 0 0 0\n")
            f.write("      vertex 1 0 0\n")
            f.write("      vertex 1 1 0\n")
            f.write("    endloop\n")
            f.write("  endfacet\n")
            f.write("endsolid test\n")
        return temp_file.name

def test_upload_endpoint():
    """Test the upload endpoint"""
    url = "https://inne-production.up.railway.app/upload"
    
    print("Testing upload endpoint...")
    print(f"URL: {url}")
    
    # Create test file
    test_file_path = create_test_stl()
    file_size = os.path.getsize(test_file_path)
    print(f"Test file created: {test_file_path}")
    print(f"File size: {file_size / 1024:.2f} KB")
    
    try:
        # Test upload
        with open(test_file_path, 'rb') as f:
            files = {'file': ('test_cube.stl', f, 'application/octet-stream')}
            response = requests.post(url, files=files, timeout=30)
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✓ Upload successful!")
            print(f"Response: {result}")
        elif response.status_code == 413:
            print("✗ File too large (413 error)")
            print(f"Response: {response.text}")
        else:
            print(f"✗ Upload failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("✗ Request timed out")
    except requests.exceptions.ConnectionError:
        print("✗ Connection error - server might be down")
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        # Clean up
        try:
            os.unlink(test_file_path)
            print("Test file cleaned up")
        except:
            pass

def test_health_endpoint():
    """Test the health endpoint if available"""
    url = "https://inne-production.up.railway.app/health"
    
    print("\nTesting health endpoint...")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✓ Health check successful!")
            print(f"Status: {result}")
        else:
            print(f"✗ Health check failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("✗ Health check timed out")
    except requests.exceptions.ConnectionError:
        print("✗ Health check connection error")
    except Exception as e:
        print(f"✗ Health check error: {e}")

if __name__ == "__main__":
    print("3D Pricing App - Upload Endpoint Test")
    print("=" * 40)
    
    test_health_endpoint()
    test_upload_endpoint()
    
    print("\n" + "=" * 40)
    print("Test completed!") 
