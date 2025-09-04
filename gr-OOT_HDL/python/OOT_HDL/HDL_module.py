#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 Dawid Salamon.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

import numpy  # Operacje na typach całkowitych o określonej szerokości (int8/int16/int32/int64)
import os  # Praca ze ścieżkami i systemem plików
from .verilog_parser import Verilog_parser, port_type, Port  # Parser Verilog do ekstrakcji nazwy modułu, portów i parametrów
from .YAML_generator import yml_generator  # Generator pliku YAML dla edytora GRC (GNU Radio Companion)
from gnuradio import gr  # API do tworzenia bloków GNU Radio
YAML_BLOCK_DIR="/Users/salsamon/radioconda/share/gnuradio/grc/blocks"  # Ścieżka do katalogu z plikami bloków GRC (YAML)
YAML_BLOCK_FILE="OOT_HDL_HDL_module.block.yml"  # Nazwa pliku YAML opisującego blok GRC
class HDL_module(gr.basic_block):  # Klasa bloku GNU Radio integrującego moduł HDL
    """
    Blok GNU Radio integrujący symulowany model HDL (Verilog) z przepływem danych GNU Radio.

    Kroki działania:
    1. Parsowanie pliku Verilog i pobranie parametrów/portów.
    2. Budowa sygnatur wejściowych/wyjściowych na podstawie szerokości portów.
    3. Inicjalizacja bloku GNU Radio i utworzenie modelu HDL.
    4. (Opcjonalnie) Wygenerowanie pliku YAML dla edytora GRC.
    """
    def __init__(self, file, **kwargs):
        """
        Inicjalizacja bloku HDL_module.
        
        Argumenty:
            file (str): Ścieżka do pliku HDL (Verilog) do sparsowania.
            **kwargs: Wartości parametrów przekazywane z GNU Radio (nadpisują domyślne).
        """
        # Najpierw parsujemy plik HDL (Verilog), aby poznać nazwę modułu, parametry i porty
        v_parser = Verilog_parser(file)
        v_parser.parse_module()
        
        # Zachowanie podstawowych informacji o module do późniejszego użycia
        self.file = file
        self.module_name = v_parser.get_module_name()
        self.params = v_parser.get_parameters()
        self.ports = v_parser.get_ports()
        
        # Nadpisanie wartości parametrów tymi podanymi z poziomu GNU Radio (jeśli występują)
        for param_name, default_value in self.params.items():
            if param_name in kwargs:
                self.params[param_name] = kwargs[param_name]
        
        # Utworzenie sygnatur wejścia/wyjścia na podstawie szerokości portów
        in_sigs = []
        out_sigs = []
        
        for port in self.ports:
            # Konwersja szerokości portu Verilog na odpowiadający typ numpy
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
            # Porty inout pomijane – GNU Radio nie wspiera ich bezpośrednio
        
        # Inicjalizacja bazowego bloku GNU Radio z odpowiednimi sygnaturami
        gr.basic_block.__init__(self,
            name=self.module_name,
            in_sig=[(numpy.int32, vlen) for vlen in in_sigs],
            out_sig=[(numpy.int32, vlen) for vlen in out_sigs])
        

        self.model= model_generator(self.file, './')  # Utworzenie instancji modelu HDL (generator/verilator poza tym plikiem)


        # Wygenerowanie pliku konfiguracyjnego YAML dla GRC, jeśli jeszcze nie istnieje
        yaml_path = os.path.join(os.path.dirname(__file__), 
                               f'{YAML_BLOCK_DIR}/{YAML_BLOCK_FILE}')
        if not os.path.exists(yaml_path):
            self._generate_yaml_config(yaml_path)

    def start_simulation(self):  # Ręczne uruchomienie generacji/kompilacji modelu HDL
        self.model.generate_model()  # Generowanie modelu (np. wywołanie Verilatora i budowa testbencha)
        pass

    def _generate_yaml_config(self, yaml_path):
        """Generowanie pliku YAML opisującego blok dla GRC (interfejs parametrów i portów)."""
        generator = yml_generator()
        generator.generate(
            self.module_name, 
            self.params, 
            self.ports
        )
        generator.save_to_file(yaml_path)

    def forecast(self, noutput_items, ninputs):  # Określenie, ile próbek wejściowych potrzeba do wygenerowania n wyjściowych
        # ninputs – liczba podłączonych wejść
        # Konfiguracja wymaganej liczby elementów input_items[i] dla wywołania work
        # Funkcja zwraca listę z wymaganą liczbą elementów dla każdego wejścia
        #   Każdy element listy odpowiada jednemu portowi wejściowemu
        #   Ustawiamy zapotrzebowanie równe liczbie próbek wyjściowych
        ninput_items_required = [noutput_items] * ninputs
        return ninput_items_required

    def general_work(self, input_items, output_items):  # Główna pętla przetwarzania próbek przez model HDL
        # Przetwarzanie próbek przez model HDL (wczytywanie wejść, wywołanie modelu, pobranie wyjść)
        ninput_items = min([len(items) for items in input_items])  # Dostępna liczba próbek na wszystkich wejściach
        noutput_items = min(len(output_items[0]), ninput_items)  # Ilość próbek do wyprodukowania w tej iteracji
        
        # Przetwarzanie próbek pojedynczo (próba po próbie)
        for i in range(noutput_items):
            # Zebranie danych wejściowych ze wszystkich portów wejściowych
            input_data = []
            for j in range(len(input_items)):
                input_data.append(int(input_items[j][i]))  # Konwersja na int (dopasowanie do interfejsu modelu)
            
            # Przekazanie danych wejściowych do modelu
            self.model.run_model(input_data)  # Asynchroniczne uruchomienie kroku modelu z danymi
            
            # Krótkie odczekanie na przetworzenie (do optymalizacji/usunięcia – docelowo synchronizacja zdarzeniowa)
            import time  # Lokalny import, aby nie spowalniać importu modułu
            time.sleep(0.01)  # Sztuczne opóźnienie; w przyszłości zastąpić mechanizmem synchronizacji
            
            # Sprawdzenie, czy w kolejce wyjściowej pojawiły się dane z modelu
            if not self.model.output_queue.empty():
                # Pobranie surowego tekstowego wyniku z kolejki wyjścia modelu
                output_str = self.model.output_queue.get()
                
                # Ekstrakcja wartości liczbowej z napisu wyjściowego
                # Oczekiwany format: "OUTPUT_CHANGE: data_out= 3"
                try:
                    value_str = output_str.split("=")[1].strip()  # Pobranie fragmentu po znaku '='
                    output_value = int(value_str)  # Konwersja na liczbę całkowitą
                    output_items[0][i] = output_value  # Zapis wartości do bufora wyjściowego GNU Radio
                except (IndexError, ValueError) as e:
                    print(f"Error parsing output: {output_str}, {e}")  # Diagnostyka błędnego formatu
                    output_items[0][i] = 0  # Wartość domyślna w przypadku błędu parsowania
            else:
                # Brak gotowego wyjścia – wpisujemy wartość domyślną
                output_items[0][i] = 0
        
        # Informacja dla GNU Radio, ile próbek wejściowych zostało skonsumowanych
        self.consume_each(noutput_items)
        return noutput_items
