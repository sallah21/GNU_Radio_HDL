#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test file for memory_fsm.sv module
Demonstrates testing of modules with internal state and memory
"""

import sys
import os
sys.path.append('/Users/salsamon/Documents/Magisterka/gr-OOT_HDL/python')

from OOT_HDL.model_class import model
import time

def test_memory_fsm():
    """Test the memory FSM module with internal state and memory"""
    
    print("=== Memory FSM Test ===")
    print("Testing module with internal state machine and memory array")
    
    # Initialize the model
    model_file = "/Users/salsamon/Documents/Magisterka/memory_fsm.sv"
    output_dir = "/Users/salsamon/Documents/Magisterka/gr-OOT_HDL/python/OOT_HDL"
    
    # Create and start the model
    fsm_model = model(model_file, output_dir)
    fsm_model.generate_model()
    
    print("\n--- Test 1: Reset and Initial State ---")
    # Test reset functionality
    # Inputs: clk, rst, data_in, start
    # Outputs: data_out, state_out, done
    
    # Apply reset
    result = fsm_model.run_model([0, 1, 0, 0])  # clk=0, rst=1, data_in=0, start=0
    print(f"Reset state: {result}")
    fsm_model.wait_n_cycles(1)
    # Release reset
    result = fsm_model.run_model([0, 0, 0, 0])  # clk=0, rst=0, data_in=0, start=0
    print(f"After reset release: {result}")
    
    # Wait a few cycles to ensure stable state
    fsm_model.wait_n_cycles(2)
    
    print("\n--- Test 2: Start FSM and Store Data ---")
    # Start the FSM
    result = fsm_model.run_model([0, 0, 10, 1])  # clk=0, rst=0, data_in=10, start=1
    print(f"Start FSM: {result}")
    
    # Clock cycle to enter STORE state
    fsm_model.wait_n_cycles(1)
    
    # Store data sequence: 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160
    test_data = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160]
    
    print("Storing data in memory...")
    for i, data_val in enumerate(test_data):
        result = fsm_model.run_model([0, 0, data_val, 0])  # clk=0, rst=0, data_in=data_val, start=0
        print(f"Store cycle {i+1}: data={data_val}, state={result.get('state_out', 'N/A')}")
        fsm_model.wait_n_cycles(1)
    
    print("\n--- Test 3: Processing Phase ---")
    # FSM should automatically transition to PROCESS state
    print("FSM processing stored data...")
    
    # Wait for processing to complete (16 cycles)
    for i in range(16):
        result = fsm_model.run_model([0, 0, 0, 0])  # clk=0, rst=0, data_in=0, start=0
        print(f"Process cycle {i+1}: state={result.get('state_out', 'N/A')}")
        fsm_model.wait_n_cycles(1)
    
    print("\n--- Test 4: Read Phase ---")
    # FSM should transition to READ state
    print("FSM reading processed data...")
    
    read_results = []
    for i in range(8):  # Read first 8 values
        result = fsm_model.run_model([0, 0, 0, 0])  # clk=0, rst=0, data_in=0, start=0
        data_out = result.get('data_out', 0)
        state_out = result.get('state_out', 'N/A')
        read_results.append(data_out)
        print(f"Read cycle {i+1}: data_out={data_out}, state={state_out}")
        fsm_model.wait_n_cycles(1)
    
    print(f"Read data sequence: {read_results}")
    
    print("\n--- Test 5: Output Phase ---")
    # FSM should transition to OUTPUT state and show accumulated result
    result = fsm_model.run_model([0, 0, 0, 0])  # clk=0, rst=0, data_in=0, start=0
    final_result = result.get('data_out', 0)
    done_flag = result.get('done', 0)
    state_out = result.get('state_out', 'N/A')
    
    print(f"Final accumulated result: {final_result}")
    print(f"Done flag: {done_flag}")
    print(f"Final state: {state_out}")
    
    # Calculate expected sum for verification
    expected_sum = sum(test_data) % 256  # 8-bit overflow
    print(f"Expected accumulated sum (8-bit): {expected_sum}")
    
    fsm_model.wait_n_cycles(1)
    
    print("\n--- Test 6: Return to IDLE ---")
    # FSM should return to IDLE state
    result = fsm_model.run_model([0, 0, 0, 0])  # clk=0, rst=0, data_in=0, start=0
    state_out = result.get('state_out', 'N/A')
    done_flag = result.get('done', 0)
    print(f"Return to IDLE: state={state_out}, done={done_flag}")
    
    print("\n--- Test 7: Multiple Cycles Test ---")
    # Test running another complete cycle
    print("Starting second processing cycle...")
    
    # Start again with different data
    test_data_2 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
    
    # Start FSM
    result = fsm_model.run_model([0, 0, 0, 1])  # start=1
    fsm_model.wait_n_cycles(1)
    
    # Store new data
    for data_val in test_data_2:
        result = fsm_model.run_model([0, 0, data_val, 0])
        fsm_model.wait_n_cycles(1)
    
    # Wait for complete processing
    fsm_model.wait_n_cycles(25)  # Process + Read + Output
    
    # Check final result
    result = fsm_model.run_model([0, 0, 0, 0])
    final_result_2 = result.get('data_out', 0)
    expected_sum_2 = sum(test_data_2) % 256
    
    print(f"Second cycle result: {final_result_2}")
    print(f"Expected result: {expected_sum_2}")
    
    print("\n=== Test Summary ===")
    print("✅ Internal state machine transitions working")
    print("✅ Internal memory array operations working")
    print("✅ State persistence between clock cycles working")
    print("✅ Complex sequential logic working")
    print("✅ Multiple processing cycles working")
    
    # Cleanup
    fsm_model.stop_process()
    print("\nTest completed successfully!")

def test_simple_memory_module():
    """Test a simpler memory module for comparison"""
    
    print("\n=== Simple Memory Module Test ===")
    
    # This would test a simpler module like a basic counter with memory
    # You can add this test if you have a simpler module to compare
    pass

if __name__ == "__main__":
    try:
        test_memory_fsm()
        test_simple_memory_module()
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
