#!/usr/bin/env python3

import sys
import os
import shutil
sys.path.append('/Users/salsamon/Documents/Magisterka/gr-OOT_HDL/python')

from OOT_HDL.model_class import model

print("=== Quick Fix Test ===")

# Clean old compiled files
output_dir = "/Users/salsamon/Documents/Magisterka/gr-OOT_HDL/python/OOT_HDL"
obj_dir = os.path.join(output_dir, "memory_fsm_obj_dir")

print("Removing old compiled files...")
if os.path.exists(obj_dir):
    shutil.rmtree(obj_dir)
    print("✅ Cleaned object directory")

# Regenerate with fix
model_file = "/Users/salsamon/Documents/Magisterka/memory_fsm.sv"
fsm_model = model(model_file, output_dir)
fsm_model.generate_model()

print("✅ Module regenerated with display fix")

# Quick test
result = fsm_model.run_model([0, 1, 0, 0])  # Reset
print(f"Test result: {result}")

if isinstance(result.get('data_out'), int):
    print("🎉 SUCCESS: Display format fix is working!")
else:
    print("⚠️ Still concatenated - checking testbench...")

fsm_model.stop_process()
