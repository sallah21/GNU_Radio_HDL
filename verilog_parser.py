import os
import re
from pathlib import Path

class Verilog_parser:
    def __init__(self, path):
        self.filename = Path(path)
        self.file_conent = ""
        self.parameters = {}
        self.in_ports = {}
        self.out_ports = {}
        self.inout_ports = {}

        with open(self.filename, "r+") as f:
            for line in f:
                self.file_conent += line 
        pass
    

    def parse_parameters(self):
        pattern = r"parameter\s+(?:(?:signed|unsigned)\s+)?(?:[a-zA-Z_][a-zA-Z0-9_$]*\s+)?(?:logic|bit|reg|integer|real|time|int|shortint|longint)?\s*(?:\[\s*\d+\s*:\s*\d+\s*\])?\s*([a-zA-Z_][a-zA-Z0-9_$]*)"
        matches = re.findall(pattern, self.file_conent)
        for match in matches:
            self.parameters[match] = 0
        return self.parameters
        
    
    def parse_ports(self):
        pattern = r"\b(input|output|inout)\b\s*(?:(signed|unsigned)\s+)?(?:wire|reg|logic|bit|integer|real|time|int|shortint|longint)?\s*(?:\[\s*\d+\s*:\s*\d+\s*\])?\s*([a-zA-Z_][a-zA-Z0-9_$]*)"
        matches = re.findall(pattern, self.file_conent)
        for match in matches:
            if (match[0] == "input"):
                self.in_ports[match[2]] = 0
            elif (match[0] == "output"):
                self.out_ports[match[2]] = 0
            elif (match[0] == "inout"):
                self.inout_ports[match[2]] = 0
        return self.in_ports, self.out_ports, self.inout_ports


    def get_parameters(self):
        pass


    def get_ports(self):
        pass