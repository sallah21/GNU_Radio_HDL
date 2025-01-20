#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 Dawid Salamon.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy
from gnuradio import gr
from verilog_parser import Verilog_parser, port_type, Port

class HDL_module(gr.basic_block):
    """
    docstring for block HDL_module
    """
    def __init__(self, file):
        # Saving HDL file for later use
        self.file = file
        # Creating Verilog parser with proviced HDL file
        v_parser = Verilog_parser(file)
        # Parsing and saving parameters 
        self.params = v_parser.parse_parameters().get_parameters()
        # Parsing and saving ports
        self.ports = v_parser.parse_ports().get_ports()
        # Parsing and saving module name
        self.module_name = v_parser.parse_module_name()

        # TODO: create parser for module name and parse size of ports to most fitable value
        gr.basic_block.__init__(self,
            name="HDL_module",
            in_sig=[Port(port_type.IN, numpy.int32) for port in self.ports],
            out_sig=[Port(port_type.OUT, numpy.int32) for port in self.ports])

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

