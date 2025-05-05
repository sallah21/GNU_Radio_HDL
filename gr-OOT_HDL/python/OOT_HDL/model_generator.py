# Class for generating and handling C++ generated models from verilator 
import os 
import subprocess
from model_class import model
from verilog_parser import Port, port_type
import time

class model_generator:
    def __init__(self):
        self.hdl_file   = None
        pass
    # Compile HDL module into C++ model with verilator
    def generate_model(self, hdl_file, output_dir):
        if hdl_file is None:
            print("HDL file not specified")
            return
        self.hdl_file = hdl_file
        # Check if verilator is installed
        if os.system("verilator --version") != 0:
            print("Verilator is not installed")
            return
        # Check if HDL file exists
        if not os.path.exists(self.hdl_file):
            print(f"HDL file {self.hdl_file} does not exist")
            return
        
        model_instance = model(self.hdl_file, output_dir)
        # model_instance.generate_model()
        return model_instance




if __name__ == "__main__":
    generator = model_generator()
    generated_model = generator.generate_model("/Users/salsamon/Documents/Magisterka/multiplier.v", "/Users/salsamon/Documents/Magisterka/gr-OOT_HDL/python/OOT_HDL")
    generated_model.run_model([1,2])
    time.sleep(1)
    generated_model.stop_process()


    
    