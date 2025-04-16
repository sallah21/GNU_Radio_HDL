try:
    from .verilog_parser import Verilog_parser, Port, port_type
except ImportError:
    print("Verilog_parser not found, using local version")
    from verilog_parser import Verilog_parser, Port, port_type
from regex import regex

class testbench_generator:
    def __init__(self):
        self.module_name = "default_module_name"
        self.clock_format_regex = ""
        self.parameters = {}
        self.input_ports = []
        self.output_ports = []
        self.inout_ports = []
        self.module_type = None # None, combinational, sequential
        clock_pattern = r"(?i)^(clk|clock|clk_i|clock_i|clk_in|clock_in|sys_clk|system_clk|sys_clock|system_clock|pclk|aclk|bclk|clk_\w+|clock_\w+)$"
        for port in self.input_ports:
            if regex.match(port.name, clock_pattern):
                self.module_type = "sequential"
                break
        else:
            self.module_type = "combinational"
        
        self.comb_template = """
`timescale 1ns/1ps

module ${module_name}_tb;
    // Inputs
    ${input_ports}
    
    // Outputs
    ${output_ports}
    
    // Instantiate the Unit Under Test (UUT)
    ${module_name} uut (
        ${port_connections}
    );
    
    integer input_file, output_file, scan_file;
    
    initial begin
        // Initialize inputs 
        ${init_inputs}
        
        // Open files directly with the command line arguments
        input_file = $fopen("{module_name}_input.txt", "r");
        output_file = $fopen("{module_name}_output.txt", "w");
        
        if (input_file == 0) begin
            $display("Error: Could not open input file");
            $finish;
        end
        
        if (output_file == 0) begin
            $display("Error: Could not open output file");
            $finish;
        end
        
        // Process inputs
        while (!$feof(input_file)) begin
            ${fscanf_statement}
            
            #10; // Wait for combinational logic
            
            ${fwrite_statement}
            ${display_statement}
        end
        
        // Close files
        $fclose(input_file);
        $fclose(output_file);
        
        $finish;
    end
endmodule
        """
        self.seq_template = """
        """
        pass
    
    def generate(self, module_name, parameters, input_ports, output_ports):
        # Create testbench content with the template
        self.module_name = module_name
        self.parameters = parameters
        self.input_ports = input_ports
        self.output_ports = output_ports
        
        if self.module_type == "combinational":
            return self.generate_comb()
        elif self.module_type == "sequential":
            return self.generate_seq()
        pass

    def generate_port_syntax(self):
        port_syntax = ""
        for port in self.input_ports:
            port_syntax += f"input [{port.size - 1}:0] {port.name},\n"
        for port in self.output_ports:
            port_syntax += f"output [{port.size - 1}:0] {port.name},\n"
        return port_syntax
        

    def generate_comb(self):
        # Create testbench content with the template
        self.comb_template.replace('${module_name}', self.module_name)
        fscanf_statement = ''' 
                            
                           '''
        fwrite_statement = '''

                           '''
        display_statement = '''
                           '''
        pass

    def generate_seq(self):
        # Create testbench content with the template
        self.seq_template
        pass
        