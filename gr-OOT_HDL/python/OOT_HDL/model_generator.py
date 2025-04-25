# Class for generating and handling C++ generated models from verilator 
import os 
import subprocess


class model_generator:
    def __init__(self, hdl_file):
        self.hdl_file = hdl_file
        self.output_dir = None
        pass

    # Compile HDL module into C++ model with verilator
    def generate_model(self):
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
        
        verilator = subprocess.run(["verilator", "--binary", self.hdl_file, "-o", f"model_{file_name}", "--exe"], 
        cwd=f"model_{file_name}", 
        check=True,
        capture_output=True,
        text=True)
        # Check if model was generated
        if not os.path.exists(f"model_{file_name}/obj_dir/model_{file_name}"):
            print(f"Model {file_name} was not generated")
            return
        pass



if __name__ == "__main__":
    generator = model_generator("/Users/salsamon/Documents/Magisterka/multiplier.sv")
    generator.generate_model()
    