# Class for generating and handling C++ generated models from verilator 
import os 
import subprocess
from model_class import model
from verilog_parser import Port, port_type

class model_generator:
    def __init__(self):
        self.hdl_file   = None
        self.model_file = None
        self.output_dir = None
        pass
    # TODO; switch file with wrapper
    # Compile HDL module into C++ model with verilator
    def generate_model(self, hdl_file):
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
        # Create output directory
        file_name = self.hdl_file.split("/")[-1].split(".")[0]
        os.makedirs(f"model_{file_name}", exist_ok=True)
        
        results = subprocess.run(["verilator", "--binary", self.hdl_file, "-o", f"model_{file_name}", "--exe"], 
        cwd=f"model_{file_name}", 
        check=True,
        capture_output=True,
        text=True)
        # Check if model was generated
        if not os.path.exists(f"model_{file_name}/obj_dir/model_{file_name}"):
            print(f"Model {file_name} was not generated")
            return
        self.output_dir = os.path.abspath(f"model_{file_name}/obj_dir/")
        self.model_file = f"model_{file_name}"
        model_instance = model(self.model_file, self.output_dir)
        return model_instance

    def get_model_file(self):
        return self.model_file


    def get_output_dir(self):
        return self.output_dir


if __name__ == "__main__":
    generator = model_generator()
    generated_model = generator.generate_model()
    print(generated_model.get_model_file())
    print(generated_model.get_output_dir())
    generated_model.generate_ports([Port("a",1, port_type.IN), Port("b",1, port_type.IN), Port("c",2, port_type.OUT)])
    
    