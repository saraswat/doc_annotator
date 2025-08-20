#!/usr/bin/env python3

import subprocess
import sys
import os

def run_backend_tests():
    """Run backend tests"""
    print("🧪 Running Backend Tests...")
    print("=" * 50)
    
    os.chdir('backend')
    
    # Install dependencies if needed
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                   capture_output=True)
    
    # Run specific tests for the new unified LLM system
    test_files = [
        'tests/test_unified_llm_service.py',
        'tests/test_chat_api.py::TestModelsAPI', 
        # Skip integration tests that might need real database
    ]
    
    for test_file in test_files:
        print(f"\n📋 Running {test_file}...")
        result = subprocess.run([
            sys.executable, '-m', 'pytest', test_file, '-v'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {test_file} - PASSED")
        else:
            print(f"❌ {test_file} - FAILED")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
    
    os.chdir('..')

def main():
    """Run all tests"""
    print("🚀 Testing Unified LLM System")
    print("=" * 50)
    
    try:
        # Test backend
        run_backend_tests()
        
        print("\n🎉 Test run completed!")
        
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
