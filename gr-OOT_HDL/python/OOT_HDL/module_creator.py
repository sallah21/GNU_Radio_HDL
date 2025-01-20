#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 Dawid Salamon.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
TEST_DIR = "/Users/salsamon/Documents/Magisterka"

import numpy
import os
from gnuradio import gr
from .verilog_parser import Verilog_parser, port_type, Port
from .YAML_generator import yml_generator
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
        self.generator = yml_generator()
        self.file = None
        self.actual_file = False
        self.module_name = None
        self.params = None
        self.ports = None
        print("Module creator created")

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
        print("Generating YAML")
        self.generator.generate(self.module_name, self.params, input_ports, output_ports)
        print("YAML generated")
        self.generator.save_to_file(f"{TEST_DIR}/gr-OOT_HDL/grc/OOT_HDL_HDL_module.block_gen.yml")
        print("YAML saved")
        print("Generating GNU_Radio module")
        # Create new GNU_Radio module
        print(f"Module name: {self.module_name}")
        print(f"Parameters: {self.params}")
        print(f"Ports: {self.ports}")
        print(f"Changing directory to {TEST_DIR}/gr-OOT_HDL/")
        if os.system(f"cd {TEST_DIR}/gr-OOT_HDL/") != 0:
            print("Failed to change directory")
            return
        param_names = ",".join(self.params.keys())
        print(f"Param names: {param_names}")
        print(f"Adding module to GNU_Radio \n command: gr_modtool add -t general --copyright \"Dawid Salamon\" --argument-list {param_names} -l python --yes {self.module_name}")
        if os.system(f"gr_modtool add -t general --copyright \"Dawid Salamon\" --argument-list {param_names} -l python --yes {self.module_name}") != 0:
            print("Failed to add module")
            return
        print("Changing directory to GNU_Radio build")
        if os.system(f"cd {TEST_DIR}/gr-OOT_HDL/build") != 0:
            print("Failed to change directory")
            return
        
        print("Running CMake")
        if os.system(f"cmake -DCMAKE_INSTALL_PREFIX=$(gnuradio-config-info --prefix) ..") != 0:
            print("Failed to configure GNU Radio")
            return

        print("Running make")
        if os.system(f"make") != 0:
            print("Failed to build GNU Radio")
            return

        print("Running make install")
        if os.system(f"make install") != 0:
            print("Failed to install GNU Radio")
            return

        pass

    def general_work(self, filename=None, **kwargs):
        if (not self.actual_file and filename != None):
            self.file = filename
            print("Changing module")
            self.parser.change_module(filename)
            self.generate_new_module()
            self.actual_file = True
            pass
        if (filename != self.file):
            self.actual_file = False
        else:  
            pass
        pass
