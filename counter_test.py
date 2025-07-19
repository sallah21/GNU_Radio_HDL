#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Not titled yet
# GNU Radio version: 3.10.10.0

from PyQt5 import Qt
from gnuradio import qtgui
from gnuradio import OOT_HDL
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
import time


class untitled(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "Not titled yet", catch_exceptions=True)
        # Qt.QWidget.__init__(self)
        # self.setWindowTitle("Not titled yet")
        # qtgui.util.check_set_qss()
        # try:
        #     self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        # except BaseException as exc:
        #     print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        # self.top_scroll_layout = Qt.QVBoxLayout()
        # self.setLayout(self.top_scroll_layout)
        # self.top_scroll = Qt.QScrollArea()
        # self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        # self.top_scroll_layout.addWidget(self.top_scroll)
        # self.top_scroll.setWidgetResizable(True)
        # self.top_widget = Qt.QWidget()
        # self.top_scroll.setWidget(self.top_widget)
        # self.top_layout = Qt.QVBoxLayout(self.top_widget)
        # self.top_grid_layout = Qt.QGridLayout()
        # self.top_layout.addLayout(self.top_grid_layout)

        # self.settings = Qt.QSettings("GNU Radio", "untitled")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 32000

        ##################################################
        # Blocks
        ##################################################

    """
    Comprehensive test for wait_n_cycles() functionality
    """
    print("=== wait_n_cycles() Test Suite ===\n")
    
    # Create module creator
    creator = OOT_HDL.module_creator()
    
    # Generate model from counter test module
    model = creator.generate_model("/Users/salsamon/Documents/Magisterka/counter.sv")
    if model is None:
        raise Exception("Failed to generate model")
    
    model.generate_model()
    
    print("1. Testing basic counter functionality...")
    
    # Test 1: Basic counter operation
    # Reset the counter
    rst = 1
    clk = 0
    enable = 0
    result = model.run_model([clk, rst, enable])
    print(f"   After reset: count = {result['count']}")
    
    # Release reset
    rst = 0
    result = model.run_model([clk, rst, enable])
    print(f"   Reset released: count = {result['count']}")
    
    print("\n2. Testing manual clock control...")
    
    # Enable counter
    enable = 1
    
    # Manual clock cycles to verify basic operation
    for i in range(3):
        clk = 1  # Rising edge
        result = model.run_model([clk, rst, enable])
        print(f"   Manual cycle {i+1}: count = {result['count']}")
        clk = 0  # Falling edge
        model.run_model([clk, rst, enable])
    
    print("\n3. Testing wait_n_cycles() functionality...")
    
    # Get current count
    current_count = int(result['count'])
    print(f"   Current count before wait_n_cycles(): {current_count}")
    
    # Test wait_n_cycles(5)
    print("   Calling wait_n_cycles(5)...")
    start_time = time.time()
    model.wait_n_cycles(5)
    end_time = time.time()
    
    # Check result after wait
    result = model.run_model([clk, rst, enable])
    final_count = int(result['count'])
    print(f"   Count after wait_n_cycles(5): {final_count}")
    print(f"   Time taken: {end_time - start_time:.3f} seconds")
    
    # Verify the count increased by 5
    expected_count = current_count + 5
    if final_count == expected_count:
        print(f"   ✅ SUCCESS: Count increased by exactly 5 cycles ({current_count} → {final_count})")
    else:
        print(f"   ❌ FAILURE: Expected {expected_count}, got {final_count}")
    
    print("\n4. Testing different cycle counts...")
    
    # Test different cycle counts
    test_cycles = [1, 3, 10]
    for cycles in test_cycles:
        current_count = int(result['count'])
        print(f"   Testing wait_n_cycles({cycles})...")
        
        start_time = time.time()
        model.wait_n_cycles(cycles)
        end_time = time.time()
        
        result = model.run_model([clk, rst, enable])
        new_count = int(result['count'])
        
        expected = current_count + cycles
        if new_count == expected:
            print(f"   ✅ wait_n_cycles({cycles}): {current_count} → {new_count} (time: {end_time - start_time:.3f}s)")
        else:
            print(f"   ❌ wait_n_cycles({cycles}): Expected {expected}, got {new_count}")
    
    print("\n5. Testing with counter disabled...")
    
    # Disable counter and test wait_n_cycles
    enable = 0
    current_count = int(result['count'])
    result = model.run_model([clk, rst, enable])
    
    print(f"   Counter disabled, current count: {current_count}")
    print("   Calling wait_n_cycles(3) with counter disabled...")
    
    model.wait_n_cycles(3)
    result = model.run_model([clk, rst, enable])
    final_count = int(result['count'])
    
    if final_count == current_count:
        print(f"   ✅ SUCCESS: Count unchanged when disabled ({current_count} → {final_count})")
    else:
        print(f"   ❌ FAILURE: Count should not change when disabled ({current_count} → {final_count})")
    
    print("\n6. Performance test...")
    
    # Performance test - measure timing accuracy
    enable = 1
    result = model.run_model([clk, rst, enable])
    
    cycles_to_test = [5, 10, 20]
    for cycles in cycles_to_test:
        times = []
        for _ in range(3):  # Run multiple times for average
            start_time = time.time()
            model.wait_n_cycles(cycles)
            end_time = time.time()
            times.append(end_time - start_time)
        
        avg_time = sum(times) / len(times)
        print(f"   wait_n_cycles({cycles}): avg time = {avg_time:.3f}s (samples: {len(times)})")
    
    # Cleanup
    model.stop_process()
    print("\n=== Test Complete ===")



    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "untitled")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate




def main(top_block_cls=untitled, options=None):

    # qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()

    # tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    # timer = Qt.QTimer()
    # timer.start(500)
    # timer.timeout.connect(lambda: None)

    # qapp.exec_()

if __name__ == '__main__':
    main()
