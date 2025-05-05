# Model class
import subprocess
from verilog_parser import Port, port_type, Verilog_parser
import os
class model:
    def __init__(self, model_file, output_dir):
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
        always @({always_at}) begin
            $display({outputs_print});
        end
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
            model_instance=instance_wrapper,
            always_at=self.generate_always_at(),
            outputs_print=self.generate_display()
        )
        pass

    def compile_model(self):
        parameters_values = []
        # TODO: add parameters values passing 
        for param in self.params:
            parameters_values.append(f"-G{param}=0")
        cmd_compile = ["verilator", "--binary", self.model_file_wrapper,"--exe", *parameters_values]
        print(f"cmd_compile: {cmd_compile} \n")
        subprocess.run(cmd_compile, check=True)
        cmd_make = [
            "make", "-C", "obj_dir",
            "-f", f"V{self.module_name}_wrapper.mk",
            f"V{self.module_name}_wrapper"
        ]
        print(f"cmd_make: {cmd_make} \n")
        subprocess.run(cmd_make, check=True)
        self.exe_file = os.path.join(self.output_dir, "obj_dir", f"V{self.module_name}_wrapper")
        pass


    def parse_model(self):
        v_parser = Verilog_parser(self.model_file)
        v_parser.parse_module()
        self.module_name = v_parser.get_module_name()
        self.params = v_parser.get_parameters()
        self.ports = v_parser.get_ports()
        pass


    def dump_wrapper(self):
        with open(f"{self.module_name}_wrapper.v", "w") as f:
            f.write(self.wrapper_output)
        self.model_file_wrapper = os.path.join(self.output_dir, f"{self.module_name}_wrapper.v")
        pass


    def start_process(self):
        if self.process is not None:
            print("Process is already running")
            return
        cmd = [self.exe_file]
        self.process = subprocess.Popen(
            cmd,
            cwd=os.path.join(self.output_dir, "obj_dir"),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        pass


    # Run C++ model

    def run_model(self, inputs):
        if self.process is None:
            raise RuntimeError("Simulation process not started. Call start_process() first.")
        # Prepare input string, e.g., "1 2\n"
        input_str = " ".join(str(x) for x in inputs) + "\n"
        self.process.stdin.write(input_str)
        self.process.stdin.flush()
        # Read output line
        print("Waiting for output")
        output = self.process.stdout.readline().strip()
        print(f"Output: {output}")
        return output

    def stop_process(self):
        if self.process is None:
            print("Process is not running")
            return
        self.process.terminate()
        self.process.wait()
        self.process = None
        pass

if __name__ == "__main__":
    model = model("/Users/salsamon/Documents/Magisterka/adder.v", "/Users/salsamon/Documents/Magisterka/gr-OOT_HDL/python/OOT_HDL")
    model.parse_model()
    model.generate_wrapper()
    model.dump_wrapper()
    model.compile_model()
    model.start_process()
    model.run_model([1, 2])
    model.run_model([3, 4])
    model.run_model([5, 6])
    model.stop_process()