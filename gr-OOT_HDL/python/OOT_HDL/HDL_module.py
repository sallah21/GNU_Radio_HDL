#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 Dawid Salamon.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

import numpy
import os
import multiprocessing
from .verilog_parser import Verilog_parser, port_type, Port
from .YAML_generator import yml_generator
from gnuradio import gr
SERVER_C_FILE="/Users/salsamon/Documents/Magisterka/serwer.c"
SERVER_OUTPUT_FILE="/Users/salsamon/Documents/Magisterka/serwer.out"
YAML_BLOCK_DIR="/Users/salsamon/radioconda/share/gnuradio/grc/blocks"
YAML_BLOCK_FILE="OOT_HDL_HDL_module.block.yml"
class HDL_module(gr.basic_block):
    """
    docstring for block HDL_module
    """
    def __init__(self, file, **kwargs):
        """
        Initialize the HDL module block.
        
        Args:
            file (str): Path to the HDL file to parse
            **kwargs: Parameter values passed from GNU Radio
        """
        # Parse the HDL file first
        v_parser = Verilog_parser(file)
        v_parser.parse_module()
        
        # Store module information
        self.file = file
        self.module_name = v_parser.get_module_name()
        self.params = v_parser.get_parameters()
        self.ports = v_parser.get_ports()
        
        # Update parameters with values from GNU Radio
        for param_name, default_value in self.params.items():
            if param_name in kwargs:
                self.params[param_name] = kwargs[param_name]
        
        # Create input/output signatures based on port sizes
        in_sigs = []
        out_sigs = []
        
        for port in self.ports:
            # Convert Verilog port size to numpy dtype
            if port.size <= 8:
                dtype = numpy.int8
            elif port.size <= 16:
                dtype = numpy.int16
            elif port.size <= 32:
                dtype = numpy.int32
            else:
                dtype = numpy.int64
                
            if port.type == port_type.IN:
                in_sigs.append(dtype)
            elif port.type == port_type.OUT:
                out_sigs.append(dtype)
            # Ignore inout ports for now as GNU Radio doesn't support them directly
        
        # Initialize the basic block
        gr.basic_block.__init__(self,
            name=self.module_name,
            in_sig=[(numpy.int32, vlen) for vlen in in_sigs],
            out_sig=[(numpy.int32, vlen) for vlen in out_sigs])
        
        # Start simulation in a separate process
        self.process = multiprocessing.Process(target=self.start_simulation)
        self.process.start()
  
        # Generate YAML configuration if it doesn't exist
        yaml_path = os.path.join(os.path.dirname(__file__), 
                               f'{YAML_BLOCK_DIR}/{YAML_BLOCK_FILE}')
        if not os.path.exists(yaml_path):
            self._generate_yaml_config(yaml_path)

    def start_simulation(self):
        # Compile C server
        # TODO: use in model class run_model
        pass

    def _generate_yaml_config(self, yaml_path):
        """Generate YAML configuration file for the HDL module."""
        generator = yml_generator()
        generator.generate(
            self.module_name, 
            self.params, 
            self.ports
        )
        generator.save_to_file(yaml_path)

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
