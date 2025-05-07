# Model class
import subprocess
from .verilog_parser import Port, port_type, Verilog_parser
import os
import threading
import queue
import time

class model:
    def __init__(self, model_file, output_dir):
        self.input_queue = queue.Queue()
        self.output_queue = queue.Queue()
        self.running = False
        self.input_thread = None
        self.output_thread = None
        self.model_file = model_file
        self.output_dir = output_dir
        self.module_name = None
        self.params = None
        self.ports = None
        self.inputs = None
        self.outputs = None
        self.process = None
        self.exe_file = None
        self.model_file_wrapper = None
        # Verilog wrapper for returning output values
        self.wrapper_template = """
        module {module_name}_wrapper
        {parameters}
        (
            {inputs},
            {outputs}
        );
        {model_instance}
        endmodule
        """
        self.module_instance_template = """
        {module_name}
        {instance_parameters}
        {module_name}_inst
        (
            {instance_inputs},
            {instance_outputs}
        );
        """
        self.wrapper_output = None
        pass

    # Get model file
    def get_model_file(self):
        return self.model_file

    # Get output directory
    def get_output_dir(self):
        return self.output_dir

    def generate_ports(self):
        port_type_map = {
            port_type.IN: "input",
            port_type.OUT: "output",
            port_type.INOUT: "inout"
        }
        # Generate inputs and outputs for template replacement
        inputs = ",\n ".join([f" {port_type_map[port.type]} [{port.size-1}:0] {port.name}" for port in self.ports if port.type != port_type.OUT])
        outputs = ",\n ".join([f" {port_type_map[port.type]} [{port.size-1}:0] {port.name}" for port in self.ports if port.type == port_type.OUT])
        # print(f"Inputs: {inputs}")
        # print(f"Outputs: {outputs}")  
        
        # Generate instance inputs and outputs for template replacement
        instance_inputs = ",\n ".join([f" .{port.name}({port.name})" for port in self.ports if port.type != port_type.OUT])
        instance_outputs = ",\n ".join([f" .{port.name}({port.name})" for port in self.ports if port.type == port_type.OUT])
        # print(f"Instance inputs: {instance_inputs}")
        # print(f"Instance outputs: {instance_outputs}")
        return inputs, outputs, instance_inputs, instance_outputs
        pass


    def generate_display(self):
        display_parts = []
        for port in self.ports:
            if port.type == port_type.OUT:
                display_parts.append(f'"{port.name}="')
                display_parts.append(f'{port.name}')
        display = ', '.join(display_parts) if display_parts else '""'
        display = f'"OUTPUT_CHANGE: ", {display}'
        # print(f"Display: {display}")
        return display


    def generate_parameters(self):
        if self.params is None:
            return ""
        param_template = "#(\n{params}\n)\n"
        parameters = []
        for param in self.params:
            parameters.append(param)
        parameters = ",\n".join(parameters)
        param_template = param_template.format(params=parameters)
        return param_template


    def generate_instance_parameters(self):
        if self.params is None:
            return ""
        param_template = "#({params})"
        parameters = []
        for param in self.params:
            parameters.append(param)
        parameters = ",\n".join(f".{param}({param})" for param in parameters)
        param_template = param_template.format(params=parameters)
        return param_template


    def generate_always_at(self):
        if self.ports is None:
            return ""
        ports = []
        for port in self.ports:
            if port.type == port_type.OUT:
                ports.append(port.name)
        ports = ", ".join(ports)
        return ports

    def generate_wrapper(self):
        inputs, outputs, instance_inputs, instance_outputs = self.generate_ports()
        self.inputs = inputs
        self.outputs = outputs
        instance_wrapper = self.module_instance_template.format(
            module_name=self.module_name,
            instance_parameters=self.generate_instance_parameters(),
            instance_inputs=instance_inputs,
            instance_outputs=instance_outputs
        )
        self.wrapper_output = self.wrapper_template.format(
            parameters=self.generate_parameters(),
            inputs=self.inputs,
            outputs=self.outputs,
            module_name=self.module_name,
            model_instance=instance_wrapper
        )
        pass

    def compile_model(self):
        parameters_values = []
        # TODO: add parameters values passing 
        for param in self.params:
            parameters_values.append(f"-G{param}=0")
        
        # Generate dynamic input and output handling code based on actual ports
        input_declarations = []
        input_parsing = []
        input_setting = []
        output_printing = []
        
        # Get input and output ports
        input_ports = [port for port in self.ports if port.type != port_type.OUT]
        output_ports = [port for port in self.ports if port.type == port_type.OUT]
        
        # Generate input parsing code
        if input_ports:
            input_var_declarations = ", ".join([f"int {port.name} = 0" for port in input_ports])
            input_declarations.append(f"        {input_var_declarations};")
            
            input_scanf_format = " ".join(["%d" for _ in input_ports])
            input_scanf_vars = ", ".join([f"&{port.name}" for port in input_ports])
            input_parsing.append(f'        if (sscanf(line.c_str(), "{input_scanf_format}", {input_scanf_vars}) == {len(input_ports)}) {{')
            
            for port in input_ports:
                input_setting.append(f"            top->{port.name} = {port.name};")
        
        # Generate output printing code
        if output_ports:
            output_parts = []
            for port in output_ports:
                # Fix: Use stream insertion operator (<<) instead of comma
                output_parts.append(f'<< "{port.name}=" << top->{port.name} ')
            
            output_print = " ".join(output_parts)
            output_printing.append(f'            std::cout {output_print}<< std::endl;')
        
        # Dynamically generate a custom C++ testbench for the model based on its ports
        cpp_testbench_template = """
        // Automatically generated testbench for {module_name}
        #include <iostream>
        #include <string>
        #include "V{module_name}_wrapper.h"
        #include "verilated.h"

        // Main testbench code
        int main(int argc, char** argv) {{
            // Initialize Verilator
            Verilated::commandArgs(argc, argv);
            
            // Create an instance of the Verilator-generated module
            V{module_name}_wrapper* top = new V{module_name}_wrapper;
            
            // Process input/output in a loop
            std::string line;
            while (std::getline(std::cin, line)) {{
                // Parse input values
        {input_declarations_code}
        {input_parsing_code}
        {input_setting_code}
                    
                    // Evaluate model (run one clock cycle)
                    top->eval();
                    
                    // Print output value (this will be captured by our processing thread)
        {output_printing_code}
                    std::cout.flush();
                }}
            }}
            
            // Clean up
            top->final();
            delete top;
            
            return 0;
        }}
        """
        
        # Create the testbench file with dynamic port handling
        cpp_testbench_content = cpp_testbench_template.format(
            module_name=self.module_name,
            input_declarations_code="\n".join(input_declarations),
            input_parsing_code="\n".join(input_parsing),
            input_setting_code="\n".join(input_setting),
            output_printing_code="\n".join(output_printing)
        )
        
        cpp_testbench_file = os.path.join(self.output_dir, f"{self.module_name}_testbench.cpp")
        
        with open(cpp_testbench_file, "w") as f:
            f.write(cpp_testbench_content)
        
        # Use --cc instead of --binary to generate C++ output without the default main
        # Then we'll use our own main file
        cmd_compile = [
            "verilator", 
            "--cc", 
            self.model_file_wrapper,
            "--Mdir",
            os.path.join(self.output_dir, f"{self.module_name}_obj_dir"),
            "--exe",
            cpp_testbench_file,
            *parameters_values
        ]
        try:
            # print(f"cmd_compile: {cmd_compile} \n")
            subprocess.run(cmd_compile, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            print(f"Error compiling Verilator model: {e}")
            return
        
        cmd_make = [
            "make", 
            "-C", os.path.join(self.output_dir, f"{self.module_name}_obj_dir"),
            "-f", f"V{self.module_name}_wrapper.mk"
        ]
        # print(f"cmd_make: {cmd_make} \n")
        subprocess.run(cmd_make, check=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        self.exe_file = os.path.join(self.output_dir, f"{self.module_name}_obj_dir", f"V{self.module_name}_wrapper")
        pass


    def parse_model(self):
        v_parser = Verilog_parser(self.model_file)
        v_parser.parse_module()
        self.module_name = v_parser.get_module_name()
        self.params = v_parser.get_parameters()
        self.ports = v_parser.get_ports()
        pass


    def dump_wrapper(self):
        print(f"Wrapper output path: {os.path.join(self.output_dir, f"{self.module_name}_wrapper.v")}")
        with open(os.path.join(self.output_dir, f"{self.module_name}_wrapper.v"), "w") as f:
            f.write(self.wrapper_output)
        self.model_file_wrapper = os.path.join(self.output_dir, f"{self.module_name}_wrapper.v")
        pass


    def _processing_thread(self):
        print("Processing thread started")
        while self.running:
            try:
                if self.process and self.process.poll() is None:
                    line = self.process.stdout.readline().decode().strip()
                    if line:
                        self.output_queue.put(line)
                else:
                    # Only sleep if we're not actively reading
                    time.sleep(0.01)
            except Exception as e:
                print(f"Processing thread error: {e}")
                # Don't stop running on a single exception
                time.sleep(0.1)  # Brief pause before trying again
        print("Processing thread stopped")


    def _input_thread(self):
        while self.running:
            try:
                if not self.input_queue.empty():
                    data = self.input_queue.get()
                    print(f"Input data: {data}")
                    if self.process and self.process.poll() is None:
                        # Format the data for the Verilator model
                        # For Verilator with C++ testbench, we need to set top-level signals
                        if isinstance(data, list) and len(data) >= 2:
                            # Here's how Verilator C++ testbench expects commands
                            # The exact syntax depends on your model but this is common
                            data_in = int(data[0])
                            data_in2 = int(data[1])
                            print(f"Setting data_in={data_in}, data_in2={data_in2}")
                            
                            # Send command to set inputs (depends on your testbench implementation)
                            command = f"{data_in} {data_in2}\n"
                            self.process.stdin.write(command.encode())
                            self.process.stdin.flush()
                        else:
                            print(f"Warning: Invalid data format. Expected [data_in, data_in2], got {data}")
                time.sleep(0.01)
            except Exception as e:
                print(f"Input thread error: {e}")
                
        pass


    def _output_thread(self):
        while self.running:
            try:
                if not self.output_queue.empty():
                    data = self.output_queue.get()
                    print(f"Output data: {data}")
            except Exception as e:
                print(f"Output thread error: {e}")
            time.sleep(0.01)
        pass


    def run_model(self,data):
        self.input_queue.put(data)
        pass


    def stop_process(self):
        print("Stopping process...")
        self.running = False
        
        print("Waiting for threads to finish...")
        # Give the threads a chance to see that running is False
        time.sleep(0.5)
        
        if self.process and self.process.poll() is None:
            print("Terminating process...")
            try:
                self.process.terminate()
                self.process.wait(timeout=1.0)
            except:
                print("Force killing process...")
                self.process.kill()
                
        if self.input_thread and self.input_thread.is_alive():
            print("Joining input thread...")
            self.input_thread.join(timeout=1.0)
            
        if hasattr(self, 'processing_thread') and self.processing_thread and self.processing_thread.is_alive():
            print("Joining processing thread...")
            self.processing_thread.join(timeout=1.0)
            
        if self.output_thread and self.output_thread.is_alive():
            print("Joining output thread...")
            self.output_thread.join(timeout=1.0)
            
        print("Model process stopped")
        pass


    def start_process(self):
        self.running = True
        self.process = subprocess.Popen([self.exe_file],
         stdin=subprocess.PIPE, 
         stdout=subprocess.PIPE, 
         stderr=subprocess.PIPE)
        # print(f"Process started: {self.process}")
        self.input_thread = threading.Thread(target=self._input_thread)
        self.input_thread.daemon = True
        self.input_thread.start()
        # Start processing thread to read output from the process
        self.processing_thread = threading.Thread(target=self._processing_thread)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        # print(f"Input thread started: {self.input_thread}")
        self.output_thread = threading.Thread(target=self._output_thread)
        self.output_thread.daemon = True
        self.output_thread.start()
        # print(f"Output thread started: {self.output_thread}")
        pass

    def generate_model(self):
        self.parse_model()
        self.generate_wrapper()
        self.dump_wrapper()
        self.compile_model()
        self.start_process()
        pass

if __name__ == "__main__":
    model = model("/Users/salsamon/Documents/Magisterka/multiplier.v", "/Users/salsamon/Documents/Magisterka/gr-OOT_HDL/python/OOT_HDL")
    model.parse_model()
    model.generate_wrapper()
    model.dump_wrapper()
    model.compile_model()
    model.start_process()
    model.run_model([1,2])
    model.run_model([3,4])
    model.run_model([5,6])
    time.sleep(1)

    model.stop_process()