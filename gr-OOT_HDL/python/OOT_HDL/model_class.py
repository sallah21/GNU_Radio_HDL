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
        self.process_output_queue = queue.Queue()
        self.data_ready = threading.Event()
        self.wait_cycles_complete = threading.Event()  # Event for wait_n_cycles synchronization
        self.expected_cycles = 0  # Track expected number of cycles
        self.data = None
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
        self.has_clock = None

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

    def detect_clock_signals(self):
        """Detect if module uses clock signals"""
        clock_patterns = ['clk', 'clock', 'CLK', 'CLOCK']
        self.has_clock = False
        self.clock_ports = []
        if self.ports is None:
            return False
        for port in self.ports:
            if any(pattern in port.name for pattern in clock_patterns):
                self.has_clock = True
                self.clock_ports.append(port)
        return self.has_clock

    def wait_n_cycles(self, n):
        """Wait for n clock cycles"""
        if not self.has_clock:
            raise Exception("Model does not have clock ports")
        
        if not self.process or self.process.poll() is not None:
            raise Exception("Model process is not running")
        
        # Send special command to wait for n clock cycles
        # Format: "WAIT_CYCLES <n>\n"
        command = f"WAIT_CYCLES {n}\n"
        print(f"Waiting for {n} clock cycles...")
        
        try:
            # Set up synchronization before sending command
            self.expected_cycles = n
            self.wait_cycles_complete.clear()
            
            # Send the command
            self.process.stdin.write(command.encode())
            self.process.stdin.flush()
            
            # Wait for the event to be set by the processing thread
            # This is much more efficient than busy waiting
            if self.wait_cycles_complete.wait(timeout=10.0):
                print(f"Clock cycles completed: {n}")
                return
            else:
                raise Exception(f"Timeout waiting for {n} clock cycles to complete")
            
        except Exception as e:
            print(f"Error sending wait_n_cycles command: {e}")
            raise


    def get_model_file(self):
        """Get model file"""
        return self.model_file

    def get_output_dir(self):
        """Get output directory"""
        return self.output_dir

    def generate_ports(self):
        """Generate ports for template replacement"""
        port_type_map = {
            port_type.IN: "input",
            port_type.OUT: "output",
            port_type.INOUT: "inout"
        }
        self.has_clock = self.detect_clock_signals()
        print(f"Has clock ports: {self.has_clock}")
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
        """Generate display for template replacement"""
        if not self.ports:
            return '"OUTPUT_CHANGE: (no outputs)"'
        
        # Get output ports
        output_ports = [port for port in self.ports if port.type == port_type.OUT]
        
        if not output_ports:
            return '"OUTPUT_CHANGE: (no outputs)"'
        
        # Create format string for proper comma-separated output
        # For 3 outputs: "data_out=" << data_out << ", state_out=" << state_out << ", done=" << done
        display_parts = []
        for i, port in enumerate(output_ports):
            if i == 0:
                # First port: no leading comma
                display_parts.append(f'"{port.name}=", {port.name}')
            else:
                # Subsequent ports: add comma and space before port name
                display_parts.append(f'", {port.name}=", {port.name}')
        
        # Join all parts
        display = ', '.join(display_parts)
        display = f'"OUTPUT_CHANGE: ", {display}'
        
        print(f"DEBUG - Generated display: {display}")
        return display


    def generate_parameters(self):
        """Generate parameters for template replacement"""
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
        """Generate instance parameters for template replacement"""
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
        """Generate always at for template replacement"""
        if self.ports is None:
            return ""
        ports = []
        for port in self.ports:
            if port.type == port_type.OUT:
                ports.append(port.name)
        ports = ", ".join(ports)
        return ports

    def generate_wrapper(self):
        """Generate wrapper for template replacement"""
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
        """Compile model with verilator"""
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
            input_var_declarations = "; ".join([f"int {port.name} = 0" for port in input_ports])
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
                output_parts.append(f'<< "{port.name}=" << (int) top->{port.name} << ","')
            
            output_print = " ".join(output_parts)
            output_printing.append(f'            std::cout {output_print}<< std::endl;')
        
        # Dynamically generate a custom C++ testbench for the model based on its ports
        cpp_testbench_template = """
        // Automatically generated testbench for {module_name}
        #include <iostream>
        #include <string>
        #include <sstream>
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
                // Check for special WAIT_CYCLES command
                if (line.find("WAIT_CYCLES") == 0) {{
                    std::istringstream iss(line);
                    std::string command;
                    int cycles;
                    if (iss >> command >> cycles) {{
                        // Execute n clock cycles for clocked modules
                        for (int i = 0; i < cycles; i++) {{
                            {clock_cycle_code}
                        }}
                        std::cout << "WAIT_CYCLES_COMPLETE: " << cycles << std::endl;
                        std::cout.flush();
                    }}
                    continue;
                }}
                
                // Parse regular input values
        {input_declarations_code}
        {input_parsing_code}
        {input_setting_code}
                    // Evaluate model (run one clock cycle)
        {eval_statement}
                    
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

        eval_statement = None 

        if self.has_clock:
            eval_statement = """
                    // Clock cycle simulation
                    //top->clk = 0;
                    //top->eval();
            
                    //top->clk = 1;
                    top->eval();
            """
        else:
            eval_statement = "            top->eval();"

        clock_cycle_code = """
                    top->clk = 0;
                    top->eval();
                    top->clk = 1;
                    top->eval();
        """
        
        # Create the testbench file with dynamic port handling
        cpp_testbench_content = cpp_testbench_template.format(
            module_name=self.module_name,
            input_declarations_code="\n".join(input_declarations),
            input_parsing_code="\n".join(input_parsing),
            input_setting_code="\n".join(input_setting),
            output_printing_code="\n".join(output_printing),
            eval_statement=eval_statement,
            clock_cycle_code=clock_cycle_code   
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
        # print("Processing thread started")
        while self.running:
            try:
                if self.process and self.process.poll() is None:
                    line = self.process.stdout.readline().decode().strip()
                    if line:
                        # Check for WAIT_CYCLES_COMPLETE message
                        if line.startswith("WAIT_CYCLES_COMPLETE:"):
                            # Extract the number of cycles from the message
                            try:
                                cycles = int(line.split(":")[1].strip())
                                if cycles == self.expected_cycles:
                                    self.wait_cycles_complete.set()
                                else:
                                    print(f"Warning: Expected {self.expected_cycles} cycles, got {cycles}")
                            except (ValueError, IndexError):
                                print(f"Warning: Invalid WAIT_CYCLES_COMPLETE format: {line}")
                        else:
                            # Regular output, put in queue for normal processing
                            self.process_output_queue.put(line)
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
                        if isinstance(data, list) and len(data) > 0:
                            # Get list of input ports
                            input_ports = [port for port in self.ports if port.type != port_type.OUT]
                            
                            # Validate data length matches number of input ports
                            if len(data) == len(input_ports):
                                # Build command dynamically based on available inputs
                                command_parts = []
                                
                                # Log for debugging
                                log_parts = []
                                
                                # Process each input port with corresponding data
                                for i, port in enumerate(input_ports):
                                    # Convert input according to port specifications
                                    # This might need adjustment based on actual port types
                                    value = int(data[i])
                                    command_parts.append(str(value))
                                    log_parts.append(f"{port.name}={value}")
                                    # print(f"Setting {port.name}={value}")
                                print(f"Log parts: {log_parts}")
                                
                                # Create the command string with all inputs
                                command = " ".join(command_parts) + "\n"
                                print(f"Setting {', '.join(log_parts)}")
                                
                                # Send the command to the process
                                self.process.stdin.write(command.encode())
                                self.process.stdin.flush()
                            else:
                                print(f"Warning: Invalid data length. Expected {len(input_ports)} inputs for ports {[port.name for port in input_ports]}, got {len(data)} values: {data}")
                        else:
                            print(f"Warning: Invalid data format. Expected a list of values, got {data}")
                time.sleep(0.01)
            except Exception as e:
                print(f"Input thread error: {e}")
                exit(1)
                
        pass


    def _output_thread(self):
        while self.running:
            try:
                if not self.process_output_queue.empty():
                    self.data = self.process_output_queue.get()
                    self.data_ready.set()
                    # print(f"Output data: {self.data}")
            except Exception as e:
                print(f"Output thread error: {e}")
            time.sleep(0.01)
        pass


    def run_model(self,data):
        self.data_ready.clear()
        self.input_queue.put(data)
        # Wait for the output thread to process the data
        self.data_ready.wait()
        result_dict = {}
        
        # Handle multiple output parsing
        # Expected format: "OUTPUT_CHANGE: data_out=10, state_out=3, done=0"
        output_line = self.data
        
        # Remove "OUTPUT_CHANGE: " prefix if present
        if "OUTPUT_CHANGE:" in output_line:
            output_line = output_line.split("OUTPUT_CHANGE:")[1].strip()
        
        print(f"Output line: {output_line}")
        # Split by comma to get individual key=value pairs
        pairs = output_line.split(",")
        
        for pair in pairs:
            pair = pair.strip()
            if "=" in pair:
                key, value = pair.split("=", 1)  # Split only on first "="
                key = key.strip()
                value = value.strip()
                
                # Try to convert to int if possible, otherwise keep as string
                try:
                    result_dict[key] = int(value)
                except ValueError:
                    result_dict[key] = value
        
        return result_dict


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
        print(f"Starting process: {self.exe_file}")
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