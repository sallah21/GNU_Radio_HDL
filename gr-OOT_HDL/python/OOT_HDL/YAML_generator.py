
from verilog_parser import Verilog_parser, Port, port_type

class yml_generator:
    def __init__(self):
        self.module_name = "default_module_name"
        self.parameters = {}
        self.input_ports = []
        self.output_ports = []
        self.yml_content = ""
        self.template = '''
        id: ${module_name}
        label: ${module_name}
        category: '[OOT_HDL]'

        templates:
          imports: from gnuradio import OOT_HDL
          make: OOT_HDL.${module_name}(${file})

        parameters:
${parameters}

        inputs:
${input_ports}

        outputs:
${output_ports}
        '''

        pass

    def generate(self, module_name, parameters, input_ports, output_ports):
        # Format parameters from input ports
        parameters_yaml = ''
        for port in parameters:
            parameters_yaml += f'''        - id: {port}
          label: {port}
          dtype: int
          default: 0

'''

        # Format input ports
        input_ports_yaml = ''
        for i, port in enumerate(input_ports):
            input_ports_yaml += f'''        - label: {port.name}
          domain: stream
          dtype: {"raw" if port.size > 1 else "bool"}

'''

        # Format output ports
        output_ports_yaml = ''
        for i, port in enumerate(output_ports):
            output_ports_yaml += f'''        - label: {port.name}
          domain: stream
          dtype: {"raw" if port.size > 1 else "bool"}

'''

        # Create YAML content with the template
        yaml_content = self.template.replace('${module_name}', module_name)
        yaml_content = yaml_content.replace('${parameters}', parameters_yaml)
        yaml_content = yaml_content.replace('${input_ports}', input_ports_yaml)
        yaml_content = yaml_content.replace('${output_ports}', output_ports_yaml)
        
        self.yml_content = yaml_content


    def get_yml_content(self):
        return self.yml_content

    def save_to_file(self, filename):
        with open(filename, "w") as f:
            f.write(self.yml_content)

if __name__ == "__main__":
    import verilog_parser
    generator = yml_generator()
    verilog_file = "/Users/salsamon/Library/Mobile Documents/com~apple~CloudDocs/Magisterka/GNU_Radio_HDL/multiplier.v"
    verilog_parser = Verilog_parser(verilog_file)
    verilog_parser.parse_module()
    ports = verilog_parser.get_ports()  
    input_ports = [port for port in ports if port.type == port_type.IN]
    output_ports = [port for port in ports if port.type == port_type.OUT]
    inout_ports = [port for port in ports if port.type == port_type.INOUT]
    parameters = verilog_parser.get_parameters()
    verilog_parser.dump()
    yaml_content = generator.generate(verilog_parser.get_module_name(), parameters, input_ports, output_ports).get_yml_content()
    print(yaml_content) 