import argparse
from verilog_parser import Verilog_parser
def main():
    parser = argparse.ArgumentParser(prog="GNU Radio HDL parser",
                                     description="Parser for HDL module used to implement GNU Radio OOT object",
                                     epilog="Dawid Salamon Mikroinformatyka 2024/2025")
    
    parser.add_argument("filename")

    args = parser.parse_args()
    
    v_parser = Verilog_parser(args.filename)

    params = v_parser.parse_parameters()
    print(f"params\n {params}")

    in_ports, out_ports, inout_ports = v_parser.parse_ports()
    print(f"in_ports\n {in_ports} \n")
    print(f"out_ports\n {out_ports} \n")
    print(f"inout_ports\n {inout_ports} \n")

    

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()