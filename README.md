# OBSOLETE DESCRIPTION

# GNU Radio HDL Integration Project

This project demonstrates the integration of hardware description language (HDL) modules with GNU Radio, enabling signal processing applications to leverage hardware acceleration through custom HDL implementations.

## Project Overview

The project consists of several key components:

1. **GNU Radio Out-of-Tree Module (gr-OOT_HDL)**: A custom GNU Radio module that provides blocks for interfacing with HDL implementations.
2. **HDL Modules**: Verilog implementations of signal processing functions (adder, multiplier).
3. **C Server**: A TCP server that acts as a bridge between GNU Radio and the HDL modules.

## Directory Structure

```
.
├── gr-OOT_HDL/             # GNU Radio Out-of-Tree Module
│   ├── python/             # Python implementations of GNU Radio blocks
│   ├── grc/                # GNU Radio Companion block definitions
│   ├── include/            # C++ header files
│   ├── lib/                # C++ implementations
│   ├── apps/               # Standalone applications
│   ├── examples/           # Example flowgraphs
│   └── docs/               # Documentation
├── adder.v                 # Verilog implementation of an adder
├── multiplier.v            # Verilog implementation of a multiplier
├── server.c                # C implementation of the TCP server
├── test.grc                # GNU Radio Companion test flowgraph
└── untitled.grc            # GNU Radio Companion example flowgraph
```

## Installation

### Prerequisites

- GNU Radio (3.8 or later)
- GCC compiler
- Verilog simulator or FPGA development tools (depending on deployment method)

### Building the GNU Radio OOT Module

```bash
cd gr-OOT_HDL
mkdir build
cd build
cmake ..
make
sudo make install
sudo ldconfig
```

### Compiling the C Server

```bash
gcc -o hdl_server server.c
```

## Running the Project

### 1. Start the HDL Server

```bash
./hdl_server
```

This will start the TCP server on port 5000 that processes data for the HDL modules.

### 2. Run GNU Radio Flowgraph

You can run the example flowgraphs using GNU Radio Companion:

```bash
gnuradio-companion test.grc
```

Or run the Python script directly:

```bash
python untitled.py
```

## Project Logic

### Data Flow

1. **GNU Radio Block**: The custom `adder` block in GNU Radio receives input signals.
2. **Socket Communication**: The block establishes a TCP socket connection to the C server.
3. **HDL Processing**: The C server processes the data according to the HDL module logic (addition or multiplication).
4. **Results**: Processed data is returned to the GNU Radio block and continues through the flowgraph.

### HDL Modules

- **adder.v**: A 32-bit adder that takes two input values and outputs their sum.
- **multiplier.v**: A 32-bit multiplier that multiplies the input by 2.

### C Server

The server listens on port 5000 and processes messages in the format:

```
module1:val1,val2,val3;module2:val1,val2;...
```

For example, to process data with the adder module:

```
adder:2.5,3.7;
```

The server will return:

```
adder:5.00,7.40;
```

## Development

To add new HDL modules:

1. Create a new Verilog file with your module implementation
2. Add a corresponding block in the GNU Radio OOT module
3. Update the C server to handle the new module type

## License

This project is licensed under the GPL-3.0 License - see the LICENSE file for details.

## Author

Dawid Salamon, 2025
