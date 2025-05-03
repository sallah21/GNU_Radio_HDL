# Model class
import subprocess
from verilog_parser import Port, port_type, Verilog_parser
class model:
    def __init__(self, model_file, output_dir):
        self.model_file = model_file
        self.output_dir = output_dir
        self.module_name = None
        self.params = None
        self.ports = None
        # Verilog wrapper for returning output values
        self.wrapper_template = """
        module {module_name}_wrapper
        {parameters}
        (
            {inputs},
            {outputs}
        );
        {model_instance}
        always @(*) begin
            $display({outputs_print});
        end
        endmodule
        """
        self.module_instance_template = """
        {module_name} {module_name}_inst
        {instance_parameters}
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
        print(f"Inputs: {inputs}")
        print(f"Outputs: {outputs}")
        
        # Generate instance inputs and outputs for template replacement
        instance_inputs = ",\n ".join([f" .{port.name}({port.name})" for port in self.ports if port.type != port_type.OUT])
        instance_outputs = ",\n ".join([f" .{port.name}({port.name})" for port in self.ports if port.type == port_type.OUT])
        print(f"Instance inputs: {instance_inputs}")
        print(f"Instance outputs: {instance_outputs}")
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
        print(f"Display: {display}")
        return display
        pass

    def generate_parameters(self):
        if self.params is None:
            return ""
        param_template = "#(\n{params}\n)\n"
        parameters = []
        for param in self.params:
            parameters.append(param)
        parameters = ",\n".join(parameters)
        param_template = param_template.format(params=parameters)
        print(f"Parameters: {param_template}")
        return param_template
        pass

    def generate_instance_parameters(self):
        # TODO: make it work 
        if self.params is None:
            return ""
        param_template = "#({params})"
        parameters = []
        for param in self.params:
            parameters.append(param)
        parameters = ",\n".join(parameters)
        param_template = param_template.format(params=parameters)
        print(f"Instance parameters: {param_template}")
        return param_template
        pass


    def generate_wrapper(self):
        inputs, outputs, instance_inputs, instance_outputs = self.generate_ports()
        parameters = self.generate_parameters()
        instance_parameters = self.generate_instance_parameters()
        instance_wrapper = self.module_instance_template.format(
            module_name=self.module_name,
            parameters=parameters,
            instance_parameters=instance_parameters,
            instance_inputs=instance_inputs,
            instance_outputs=instance_outputs
        )
        self.wrapper_output = self.wrapper_template.format(
            inputs=inputs,
            outputs=outputs,
            module_name=self.module_name,
            model_instance=instance_wrapper,
            outputs_print=self.generate_display()
        )
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
        pass

    # Run C++ model
    def run_model(self):
        cmd = [self.model_file]
        subprocess.run(cmd, cwd=self.output_dir, check=True)
        pass

if __name__ == "__main__":
    model = model("/Users/salsamon/Documents/Magisterka/adder.v", "/Users/salsamon/Documents/Magisterka")
    model.parse_model()
    model.generate_wrapper()
    model.dump_wrapper()
    # model.run_model()