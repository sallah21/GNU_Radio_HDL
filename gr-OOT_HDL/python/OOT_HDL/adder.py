
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
class adder(gr.basic_block):
    """
    docstring for block adder
    """
    def __init__(self,dupa, dupa2, dupa3):
        gr.basic_block.__init__(self,
            name="adder",
            in_sig=[numpy.float32, numpy.float32],
            out_sig=[numpy.float32])
        self.socket = None
        self.server = None
        # Create server socket  
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(('', 12345))
        self.socket.listen(1)
        with open("/Users/salsamon/Documents/Magisterka/OOT_HDL_adder.txt", "w") as f:
            f.write("SOCKET STARTED")
        #self.server = self.socket.accept()[0]
        self.server_Thread = threading.Thread(target=self.handle_connection)
        self.server_Thread.daemon = True
        self.server_Thread.start()

    def handle_connection(self):
        with open("/Users/salsamon/Documents/Magisterka/OOT_HDL_adder.txt", "w") as f:
            f.write("SERVER STARTED")
        while True:
            try:
                with open("/Users/salsamon/Documents/Magisterka/OOT_HDL_adder.txt", "w") as f:
                    f.write("Wait for connection from server")
                client, addr = self.socket.accept()
                print(f"Connection from server")
                with open("/Users/salsamon/Documents/Magisterka/OOT_HDL_adder.txt", "w") as f:
                    f.write("Connection from server")
                while True:
                    if len(self.data_buffer) > 0:
                        data = self.data_buffer.popleft()
                        client.send(json.dumps(data).encode() + b'\n')
            except Exception as e:
                print(f"Server error: ")
                with open("/Users/salsamon/Documents/Magisterka/OOT_HDL_adder.txt", "w") as f:
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
        