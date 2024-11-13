import os
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
    size: int
    type: port_type


class Verilog_parser:
    def __init__(self, path):
        # TODO: create data type for port 
        self.filename = Path(path)
        self.file_conent = ""
        self.parameters = {}
        self.ports = []

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
        # print(f"Matches {matches} \n")
        for match in matches:
            port =  None
            type = port_type(match[0])
            if (match[1] == ''):
                port = Port(match[2], 1 , type)
            elif (match[1] < 1):
                raise ValueError(" Size negative or zero")
            else :
                # print(f"NAME: {match[2]} , SIZE: {match[1]}, TYPE: {match[0]}\n")
                port = Port(match[2], match[1] , type)
            self.ports.append(port)
        return self.ports


    def get_parameters(self):
        pass


    def get_ports(self):
        pass