import re  # Wyrażenia regularne używane do parsowania plików Verilog
from pathlib import Path  # Wygodne operacje na ścieżkach plików
from dataclasses import dataclass  # Automatyczne generowanie klas danych (Port)
import string  # Użyte w adnotacjach typów 
from enum import Enum  # Definicja typów wyliczeniowych (kierunek portu)

class port_type(Enum):
    """Typ wyliczeniowy określający kierunek portu w module Verilog."""
    IN="input"
    OUT="output"
    INOUT="inout"

@dataclass
class Port:
    """Struktura opisująca port modułu Verilog.

    Pola:
    - name: nazwa portu (ciąg znaków)
    - size: szerokość portu (liczba bitów); w praktyce traktowana jako int
    - type: kierunek portu (IN/OUT/INOUT)
    """
    name:string
    size: string
    type: port_type


def read_file_content(file_path):
    """Wczytuje i zwraca pełną zawartość pliku tekstowego.

    Argumenty:
    - file_path: ścieżka do pliku.
    """
    temp_file_content = ""
    with open(file_path, "r") as f:
        temp_file_content += f.read()
    return temp_file_content


class Verilog_parser:
    """Parser plików Verilog do ekstrakcji nazwy modułu, parametrów i portów.

    Przebieg działania:
    1) Wczytanie zawartości pliku.
    2) Parsowanie parametrów, portów oraz nazwy modułu (parse_module()).
    3) Udostępnienie wyników poprzez metody get_*.
    """
    def __init__(self, path = None):
        """Konstruktor parsera.

        Argumenty:
        - path: opcjonalna ścieżka do pliku Verilog; jeśli None, inicjalizacja pusta.
        """
        if (path == None):
            self.filename = None
            self.file_conent = ""
        else:
            self.filename = Path(path)
            self.file_conent = read_file_content(self.filename)
        self.moudule_name = "default_module_name"  # Domyślna nazwa, nadpisywana po parsowaniu
        self.parameters = {}  # Słownik parametrów (nazwa -> wartość domyślna 0)
        self.ports = []  # Lista obiektów Port
        pass
    

    def parse_parameters(self):
        """Wyszukuje i zapisuje nazwy parametrów z pliku Verilog.

        Używany wzorzec regex dopasowuje różne warianty deklaracji 'parameter'.
        Każdemu znalezionemu parametrowi przypisywana jest wartość 0 (placeholder).
        """
        pattern = r"parameter\s+(?:(?:signed|unsigned)\s+)?(?:[a-zA-Z_][a-zA-Z0-9_$]*\s+)?(?:logic|bit|reg|integer|real|time|int|shortint|longint)?\s*(?:\[\s*\d+\s*:\s*\d+\s*\])?\s*([a-zA-Z_][a-zA-Z0-9_$]*)"
        matches = re.findall(pattern, self.file_conent)
        for match in matches:
            self.parameters[match] = 0
        

    def parse_ports(self):
        """Parsuje porty z nagłówka deklaracji modułu Verilog.

        Krok 1: wyodrębnia sekcję deklaracji portów z nagłówka modułu.
        Krok 2: dopasowuje kierunek, typ oraz rozmiar portu i dodaje do listy ports.
        """
        # Dokładniejszy wzorzec dopasowujący tylko deklaracje portów w nagłówku modułu
        # Najpierw wyodrębniamy fragment między 'module ... (' a zamknięciem listy portów i średnikiem
        module_pattern = r"module\s+[a-zA-Z_][a-zA-Z0-9_$]*\s*(?:#\([^)]*\))?\s*\((.*?)\);"
        module_match = re.search(module_pattern, self.file_conent, re.DOTALL)
        
        if not module_match:
            # Fallback: alternatywna forma – ostrożność przy różnych stylach formatowania
            module_pattern = r"module\s+[a-zA-Z_][a-zA-Z0-9_$]*\s*(?:#\([^)]*\))?\s*\((.*?)\)\s*;"
            module_match = re.search(module_pattern, self.file_conent, re.DOTALL)
        
        if module_match:
            port_section = module_match.group(1)
        else:
            # Jeśli nie uda się wyodrębnić nagłówka, przeszukujemy cały plik jako fallback
            port_section = self.file_conent
        
        # Wzorzec dopasowujący deklaracje portów (kierunek, typ, rozmiar, nazwa)
        pattern = r"\b(input|output|inout)\s+(?:(wire|reg|logic)\s+)?(?:\[\s*(\d+)\s*:\s*\d+\s*\])?\s*([a-zA-Z_][a-zA-Z0-9_$]*)"
        matches = re.findall(pattern, port_section)
        
        for match in matches:
            port_direction, wire_type, size_str, name = match
            port = None
            type = port_type(port_direction)
            
            # Konwersja rozmiaru: jeśli brak, przyjmujemy 1 bit; dla [N:0] rozmiar to N+1
            size = int(size_str) + 1 if size_str else 1
            port = Port(name, size, type)
            self.ports.append(port)
            print(f"Debug: Added port: {name} ({type.value}) size {size}") 


    def parse_module_name(self):
        """Wyszukuje nazwę modułu ('module <nazwa>') i zapisuje ją w stanie parsera."""
        pattern = r"module\s+([a-zA-Z_][a-zA-Z0-9_$]*)"
        match = re.search(pattern, self.file_conent)
        if match:
            self.moudule_name = match.group(1)
        else:
            raise ValueError("Module name not found")


    def change_module(self, new_file):
        """Zmienia aktualnie analizowany plik modułu i ponownie wykonuje parsowanie."""
        self.filename = Path(new_file)
        self.file_conent = read_file_content(self.filename)
        self.parse_module()
        pass


    def parse_module(self):
        """Wykonuje pełne parsowanie: parametrów, portów oraz nazwy modułu."""
        self.parse_parameters()
        self.parse_ports()
        self.parse_module_name()
        pass


    def get_module_name(self):
        """Zwraca nazwę modułu wykrytą w pliku Verilog."""
        return self.moudule_name


    def get_parameters(self):
        """Zwraca słownik parametrów (nazwa -> wartość)."""
        return self.parameters


    def get_ports(self):
        """Zwraca listę obiektów Port wykrytych w nagłówku modułu."""
        return self.ports

    def cleanup(self):
        """Czyści stan parsera, przywracając wartości domyślne."""
        self.filename = None
        self.file_conent = ""
        self.moudule_name = "default_module_name"
        self.parameters = {}
        self.ports = []

    # Output instance information
    def dump(self):
        """Wypisuje podstawowe informacje o aktualnym stanie parsera (do debugowania)."""
        print(f"Module name: {self.moudule_name}")
        print(f"Parameters: {self.parameters}")
        print(f"Ports: {self.ports}")


    # Save instance information to a file
    def save(self, filename):
        """Zapisuje informacje o module, parametrach i portach do pliku tekstowego."""
        with open(filename, "w") as f:
            f.write(f"Module name: {self.moudule_name}\n")
            f.write(f"Parameters: {self.parameters}\n")
            f.write(f"Ports: {self.ports}\n")