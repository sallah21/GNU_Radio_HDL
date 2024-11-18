import argparse
from verilog_parser import Verilog_parser, port_type, Port
from gnu_radio_block_generator import c_server_block
def main():
    parser = argparse.ArgumentParser(prog="GNU Radio HDL parser",
                                     description="Parser for HDL module used to implement GNU Radio OOT object",
                                     epilog="Dawid Salamon Mikroinformatyka 2024/2025")
    
    parser.add_argument("filename")

    args = parser.parse_args()
    
    v_parser = Verilog_parser(args.filename)

    params = v_parser.parse_parameters()
    print(f"params\n {params}")

    ports = v_parser.parse_ports()
    input_ports = [port for port in ports if port.type == port_type.IN]
    output_ports = [port for port in ports if port.type == port_type.OUT]
    inout_ports = [port for port in ports if port.type == port_type.INOUT]
    print(f"in_ports\n {input_ports} \n")
    print(f"out_ports\n {output_ports} \n")
    print(f"inout_ports\n {inout_ports} \n")

    gnu_server = c_server_block(c_server_path="./a.out",input_ports=input_ports, output_ports=output_ports)
    data =[]
    gnu_server.work([1],data)
    print(f"DATA: {data}")
    
if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()