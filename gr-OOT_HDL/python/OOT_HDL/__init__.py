#
# Copyright 2008,2009 Free Software Foundation, Inc.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

# The presence of this file turns this directory into a Python package

'''
This is the GNU Radio OOT_HDL module. Place your Python package
description here (python/__init__.py).
'''
import os

# import pybind11 generated symbols into the OOT_HDL namespace
try:
    # this might fail if the module is python-only
    from .OOT_HDL_python import *
except ModuleNotFoundError:
    pass

# import any pure python here
from .HDL_module import HDL_module
from .verilog_parser import Verilog_parser
from .model_class import model
from .model_generator import model_generator
from .YAML_generator import yml_generator
from .module_creator import module_creator
from .adder import adder
from .multiplier import multiplier










#


