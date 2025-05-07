#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 Dawid Salamon.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
TEST_DIR = "/Users/salsamon/Documents/Magisterka"

import os
from gnuradio import gr
from .verilog_parser import Verilog_parser, port_type, Port
from .YAML_generator import yml_generator
from .model_generator import model_generator
class module_creator(gr.basic_block):
    """
    docstring for block module_creator
    """
    def __init__(self):
        gr.basic_block.__init__(self,
            name="module_creator",
            in_sig=[],
            out_sig=[])
        self.parser = Verilog_parser()
        self.yml_generator = yml_generator()
        self.model_generator = model_generator()
        self.file = None
        self.module_name = None
        self.params = None
        self.ports = None
        print("Module creator created")

    def generate_python_module(self):
        input_ports = [f"numpy.float32" for port in self.ports if port.type == port_type.IN]
        output_ports = [f"numpy.float32" for port in self.ports if port.type == port_type.OUT]
        input_ports_str = ", ".join(input_ports)
        output_ports_str = ", ".join(output_ports)
        python_template = f"""
#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 Dawid Salamon.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy
from gnuradio import gr
import os
import socket
import threading 
class {self.module_name}(gr.basic_block):
    \"\"\"
    docstring for block {self.module_name}
    \"\"\"
    def __init__(self,{', '.join(self.params)}):
        gr.basic_block.__init__(self,
            name="{self.module_name}",
            in_sig=[{input_ports_str}],
            out_sig=[{output_ports_str}])
        self.socket = None
        self.server = None
        # Create server socket  
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(('', 12345))
        self.socket.listen(1)
        with open("{TEST_DIR}/OOT_HDL_{self.module_name}.txt", "w") as f:
            f.write("SOCKET STARTED")
        #self.server = self.socket.accept()[0]
        self.server_Thread = threading.Thread(target=self.handle_connection)
        self.server_Thread.daemon = True
        self.server_Thread.start()

    def handle_connection(self):
        with open("{TEST_DIR}/OOT_HDL_{self.module_name}.txt", "w") as f:
            f.write("SERVER STARTED")
        while True:
            try:
                with open("{TEST_DIR}/OOT_HDL_{self.module_name}.txt", "w") as f:
                    f.write("Wait for connection from server")
                client, addr = self.socket.accept()
                print(f"Connection from server")
                with open("{TEST_DIR}/OOT_HDL_{self.module_name}.txt", "w") as f:
                    f.write("Connection from server")
                while True:
                    if len(self.data_buffer) > 0:
                        data = self.data_buffer.popleft()
                        client.send(json.dumps(data).encode() + b'\\n')
            except Exception as e:
                print(f"Server error: ")
                with open("{TEST_DIR}/OOT_HDL_{self.module_name}.txt", "w") as f:
                    f.write("CAN'T CONNECT")
                continue

    

    def forecast(self, noutput_items, ninputs):
        # ninputs is the number of input connections
        # setup size of input_items[i] for work call
        # the required number of input items is returned
        #   in a list where each element represents the
        #   number of required items for each input
        ninput_items_required = [noutput_items] * ninputs
        return ninput_items_required

    def general_work(self, input_items, output_items):
        # For this sample code, the general block is made to behave like a sync block
        ninput_items = min([len(items) for items in input_items])
        noutput_items = min(len(output_items[0]), ninput_items)
        output_items[0][:noutput_items] = input_items[0][:noutput_items]
        self.consume_each(noutput_items)
        return noutput_items
        """
        return python_template
        pass

    def forecast(self, noutput_items, ninputs):
        # ninputs is the number of input connections
        # setup size of input_items[i] for work call
        # the required number of input items is returned
        #   in a list where each element represents the
        #   number of required items for each input
        ninput_items_required = [noutput_items] * ninputs
        return ninput_items_required



    def generate_new_module(self):
        self.module_name = self.parser.get_module_name()
        self.params = self.parser.get_parameters()
        self.ports = self.parser.get_ports()            
        input_ports = [port for port in self.ports if port.type == port_type.IN]
        output_ports = [port for port in self.ports if port.type == port_type.OUT]
        inout_ports = [port for port in self.ports if port.type == port_type.INOUT] # XXX: Not implemented yet

        print(f"Changing directory to {TEST_DIR}/gr-OOT_HDL/")
        if os.system(f"cd {TEST_DIR}/gr-OOT_HDL/") != 0:
            print("Failed to change directory")
            return
        param_names = ",".join(self.params.keys())
        # Check if module already exists
        module_path = f"{TEST_DIR}/gr-OOT_HDL/python/OOT_HDL/{self.module_name}.py"
        module_yml_path = f"{TEST_DIR}/gr-OOT_HDL/grc/OOT_HDL_{self.module_name}.block.yml"
        
        if not os.path.exists(module_path) and not os.path.exists(module_yml_path):
            print(f"Adding module to GNU_Radio \n command: gr_modtool add -t general --copyright \"Dawid Salamon\" --argument-list {param_names} --skip-lib --skip-pybind --add-python-qa -l python --yes {self.module_name}")
            if os.system(f"cd {TEST_DIR}/gr-OOT_HDL/ && gr_modtool add -t general --copyright \"Dawid Salamon\" --argument-list {param_names} --skip-lib --skip-pybind --add-python-qa -l python --yes {self.module_name}") != 0:
                print("Failed to add module")
                print("Current directory:")
                os.system("pwd")
                return
        else:
            print(f"Module {self.module_name} already exists, skipping gr_modtool add")

        print("Generating YAML")
        self.yml_generator.generate(self.module_name, self.params, input_ports, output_ports)
        print("YAML generated")
        self.yml_generator.save_to_file(f"{TEST_DIR}/gr-OOT_HDL/grc/OOT_HDL_{self.module_name}.block.yml")
        print("YAML saved")
        print("Generating GNU_Radio module")

        #Delete init file
        if os.path.exists(f"{TEST_DIR}/gr-OOT_HDL/python/OOT_HDL/{self.module_name}.py"):
            os.remove(f"{TEST_DIR}/gr-OOT_HDL/python/OOT_HDL/{self.module_name}.py")
        else:
            print("Init file not found")

        python_module = self.generate_python_module()
        with open(f"{TEST_DIR}/gr-OOT_HDL/python/OOT_HDL/{self.module_name}.py", "w") as f:
            f.write(python_module)

        # Update init file
        init_file_path = f"{TEST_DIR}/gr-OOT_HDL/python/OOT_HDL/__init__.py"
        import_line = f"from .{self.module_name} import {self.module_name}"
        
        # Read existing content
        with open(init_file_path, 'r') as f:
            content = f.read()
        
        # Only append if import doesn't exist
        if import_line not in content:
            with open(init_file_path, 'a') as f:
                f.write(f"{import_line}\n")

        print("Running CMake")
        if os.system(f" cd {TEST_DIR}/gr-OOT_HDL/build && cmake -DCMAKE_INSTALL_PREFIX=$(gnuradio-config-info --prefix) ..") != 0:
            print("Failed to configure GNU Radio")
            return

        print("Running make")
        if os.system(f"cd {TEST_DIR}/gr-OOT_HDL/build && make") != 0:
            print("Failed to build GNU Radio")
            return

        print("Running make install")
        if os.system(f"cd {TEST_DIR}/gr-OOT_HDL/build && make install") != 0:
            print("Failed to install GNU Radio")
            return
        print("Generating model")

    
    def generate_model(self, file=None):
        if file is None:
            file = self.file
        generated_model = self.model_generator.generate_model(file, TEST_DIR)
        if generated_model is None:
            raise Exception("Failed to generate model")
        print("Module generated")
        return generated_model


    def cleanup(self):
        self.parser.cleanup()
        self.yml_generator.cleanup()
        self.file = None
        self.actual_file = False
        self.module_name = None
        self.params = None
        self.ports = None
        pass


    def general_work(self, filename=None, **kwargs):
        self.cleanup()
        print("File changed")
        self.file = filename
        
        if not filename or not os.path.exists(filename):
            print(f"Error: File {filename} does not exist")
            return None
            
        print("Changing module")
        try:
            self.parser.change_module(filename)
            self.ports = self.parser.get_ports()
            self.params = self.parser.get_parameters()
            self.module_name = self.parser.get_module_name()
            
            if not self.module_name:
                print("Error: Could not determine module name")
                return None
                
            print(f"Module name: {self.module_name}")
            print(f"Ports: {len(self.ports) if self.ports else 0}")
            print(f"Parameters: {len(self.params) if self.params else 0}")
            
            # Generate new module and model
            return self.generate_new_module()
        except Exception as e:
            print(f"Error processing module: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
