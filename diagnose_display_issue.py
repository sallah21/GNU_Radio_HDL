#!/usr/bin/env python3

import sys
import os
import shutil
sys.path.append('/Users/salsamon/Documents/Magisterka/gr-OOT_HDL/python')

from OOT_HDL.model_class import model

def diagnose_display_issue():
    """Comprehensive diagnosis of the display format issue"""
    
    print("=== Display Format Issue Diagnosis ===")
    
    # Paths
    model_file = "/Users/salsamon/Documents/Magisterka/memory_fsm.sv"
    output_dir = "/Users/salsamon/Documents/Magisterka/gr-OOT_HDL/python/OOT_HDL"
    testbench_file = os.path.join(output_dir, "memory_fsm_testbench.cpp")
    obj_dir = os.path.join(output_dir, "memory_fsm_obj_dir")
    
    print("Step 1: Testing generate_display() method directly")
    
    # Create model instance to test generate_display
    fsm_model = model(model_file, output_dir)
    fsm_model.parse_model()  # Parse to get ports
    
    # Test generate_display directly
    display_result = fsm_model.generate_display()
    print(f"Direct generate_display() result: {display_result}")
    
    # Analyze what this should produce in C++
    print(f"This should create C++ code like:")
    print(f"cout << {display_result};")
    
    print("\nStep 2: Clean and regenerate completely")
    
    # Clean everything
    for path in [obj_dir, testbench_file]:
        if os.path.exists(path):
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            print(f"Removed: {path}")
    
    # Force regeneration
    print("Regenerating testbench...")
    fsm_model.generate_model()
    
    print("\nStep 3: Check generated testbench content")
    
    if os.path.exists(testbench_file):
        print(f"Testbench file exists: {testbench_file}")
        try:
            with open(testbench_file, 'r') as f:
                content = f.read()
                
            # Find OUTPUT_CHANGE lines
            lines = content.split('\n')
            output_lines = [line for line in lines if 'OUTPUT_CHANGE' in line]
            
            if output_lines:
                print("Found OUTPUT_CHANGE lines in testbench:")
                for i, line in enumerate(output_lines):
                    print(f"  {i+1}: {line.strip()}")
            else:
                print("❌ No OUTPUT_CHANGE lines found in testbench!")
                
            # Check for our expected format
            expected_patterns = ['"data_out=", data_out', '"state_out=", state_out', '"done=", done']
            for pattern in expected_patterns:
                if pattern in content:
                    print(f"✅ Found expected pattern: {pattern}")
                else:
                    print(f"❌ Missing expected pattern: {pattern}")
                    
        except Exception as e:
            print(f"❌ Error reading testbench: {e}")
    else:
        print("❌ Testbench file not found!")
    
    print("\nStep 4: Test actual output")
    
    # Test the actual model
    result = fsm_model.run_model([0, 1, 0, 0])  # Reset state
    print(f"Actual test result: {result}")
    
    # Analyze the result
    if isinstance(result.get('data_out'), int):
        print("✅ Output parsing is working correctly!")
    else:
        print("❌ Output is still concatenated")
        print(f"Raw data received: '{fsm_model.data}'")
        
        # Check what the C++ process actually outputs
        print("\nStep 5: Debug the actual C++ output")
        
        # Try to capture raw output
        fsm_model.data_ready.clear()
        fsm_model.input_queue.put([0, 0, 0, 0])  # Test input
        fsm_model.data_ready.wait()
        
        print(f"Raw C++ output: '{fsm_model.data}'")
        
        # Manual parsing test
        output_line = fsm_model.data
        if "OUTPUT_CHANGE:" in output_line:
            after_prefix = output_line.split("OUTPUT_CHANGE:")[1].strip()
            print(f"After removing prefix: '{after_prefix}'")
            
            pairs = after_prefix.split(",")
            print(f"Split by comma: {pairs}")
    
    fsm_model.stop_process()
    
    print("\n=== Diagnosis Complete ===")

if __name__ == "__main__":
    diagnose_display_issue()
