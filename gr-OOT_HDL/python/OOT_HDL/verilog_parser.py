import re
from pathlib import Path
from dataclasses import dataclass
import string
from enum import Enum

class port_type(Enum):
    IN="input"
    OUT="output"
    INOUT="inout"

@dataclass
class Port:
    name:string
    size: string
    type: port_type


def read_file_content(file_path):
    temp_file_content = ""
    with open(file_path, "r") as f:
        temp_file_content += f.read()
    return temp_file_content


class Verilog_parser:
    def __init__(self, path = None):
        if (path == None):
            self.filename = None
            self.file_conent = ""
        else:
            self.filename = Path(path)
            self.file_conent = read_file_content(self.filename)
        self.moudule_name = "default_module_name"
        self.parameters = {}
        self.ports = []
        pass
    

    def parse_parameters(self):
        pattern = r"parameter\s+(?:(?:signed|unsigned)\s+)?(?:[a-zA-Z_][a-zA-Z0-9_$]*\s+)?(?:logic|bit|reg|integer|real|time|int|shortint|longint)?\s*(?:\[\s*\d+\s*:\s*\d+\s*\])?\s*([a-zA-Z_][a-zA-Z0-9_$]*)"
        matches = re.findall(pattern, self.file_conent)
        for match in matches:
            self.parameters[match] = 0
        

    def parse_ports(self):
        # More precise pattern that only matches port declarations in module header
        # This pattern looks for ports specifically in the module declaration section
        
        # First, extract just the module declaration section (between module name and first semicolon or begin)
        module_pattern = r"module\s+[a-zA-Z_][a-zA-Z0-9_$]*\s*(?:#\([^)]*\))?\s*\((.*?)\);"
        module_match = re.search(module_pattern, self.file_conent, re.DOTALL)
        
        if not module_match:
            # Fallback: look for module declaration without semicolon
            module_pattern = r"module\s+[a-zA-Z_][a-zA-Z0-9_$]*\s*(?:#\([^)]*\))?\s*\((.*?)\)\s*;"
            module_match = re.search(module_pattern, self.file_conent, re.DOTALL)
        
        if module_match:
            port_section = module_match.group(1)
            print(f"Debug: Port section found: {port_section[:200]}...")  # Debug output
        else:
            print("Debug: No module port section found, using entire file")
            port_section = self.file_conent
        
        # More precise pattern for port declarations
        pattern = r"\b(input|output|inout)\s+(?:(wire|reg|logic)\s+)?(?:\[\s*(\d+)\s*:\s*\d+\s*\])?\s*([a-zA-Z_][a-zA-Z0-9_$]*)"
        matches = re.findall(pattern, port_section)
        
        print(f"Debug: Found {len(matches)} port matches")  # Debug output
        
        for match in matches:
            print(f"Debug: Processing match: {match}")  # Debug output
            port_direction, wire_type, size_str, name = match
            port = None
            type = port_type(port_direction)
            
            # Convert size string to int, default to 1 if no size specified
            size = int(size_str) + 1 if size_str else 1
            port = Port(name, size, type)
            self.ports.append(port)
            print(f"Debug: Added port: {name} ({type.value}) size {size}")  # Debug output


    def parse_module_name(self):
        pattern = r"module\s+([a-zA-Z_][a-zA-Z0-9_$]*)"
        match = re.search(pattern, self.file_conent)
        if match:
            self.moudule_name = match.group(1)
        else:
            raise ValueError("Module name not found")


    def change_module(self, new_file):
        self.filename = Path(new_file)
        self.file_conent = read_file_content(self.filename)
        self.parse_module()
        pass


    def parse_module(self):
        self.parse_parameters()
        self.parse_ports()
        self.parse_module_name()
        pass


    def get_module_name(self):
        return self.moudule_name


    def get_parameters(self):
        return self.parameters


    def get_ports(self):
        return self.ports

    def cleanup(self):
        self.filename = None
        self.file_conent = ""
        self.moudule_name = "default_module_name"
        self.parameters = {}
        self.ports = []

    # Output instance information
    def dump(self):
        print(f"Module name: {self.moudule_name}")
        print(f"Parameters: {self.parameters}")
        print(f"Ports: {self.ports}")


    # Save instance information to a file
    def save(self, filename):
        with open(filename, "w") as f:
            f.write(f"Module name: {self.moudule_name}\n")
            f.write(f"Parameters: {self.parameters}\n")
            f.write(f"Ports: {self.ports}\n")