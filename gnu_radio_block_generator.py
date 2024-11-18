import os
import socket
import subprocess
from gnuradio import gr
from verilog_parser import Port
class c_server_block(gr.sync_block):
    """
    A GNU Radio block that connects to a C server process with configurable
    named input and output ports and variable sizes.
    """

    def __init__(self, c_server_path, input_ports, output_ports, host='127.0.0.1', port=5000):
        """
        :param c_server_path: Path to the compiled C server executable.
        :param input_ports: List of dictionaries defining input ports:
                            [{'name': 'input1', 'size': 3}, {'name': 'input2', 'size': 2}, ...]
        :param output_ports: List of dictionaries defining output ports:
                             [{'name': 'output1', 'size': 3}, {'name': 'output2', 'size': 2}, ...]
        :param host: Host address for the server connection.
        :param port: Port number for the server connection.
        """
        # Prepare input and output signatures based on sizes
        in_sig = [(int, port.size) for port in input_ports]
        out_sig = [(int, port.size) for port in output_ports]

        gr.sync_block.__init__(self, name="Dynamic Named C Server Block", in_sig=in_sig, out_sig=out_sig)

        self.c_server_path = c_server_path
        self.host = host
        self.port = port
        self.input_ports = input_ports
        self.output_ports = output_ports

        # Start the C server as a subprocess
        self.server_process = subprocess.Popen([self.c_server_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Started C server: {self.c_server_path}")

        # Create a socket to communicate with the C server
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))

    def work(self, input_items, output_items):
        """
        Processes data by sending it to the C server and receiving results.
        """
        num_iterations = min(len(input_items[0]), len(output_items[0]))  # Process based on minimum port size
        for i in range(num_iterations):
            # Prepare the message with input data (include names)
            input_message = []
            for idx, port in enumerate(self.input_ports):
                data = ",".join(str(input_items[idx][i]) for i in range(port['size']))
                input_message.append(f"{port['name']}:{data}")
            input_message = ";".join(input_message)

            self.client_socket.sendall(f"{input_message}\n".encode())

            # Receive and parse the processed data from the server
            response = self.client_socket.recv(1024).decode().strip()
            output_messages = response.split(";")

            # Map received data to output ports
            output_map = {msg.split(":")[0]: msg.split(":")[1] for msg in output_messages}
            for idx, port in enumerate(self.output_ports):
                output_data = output_map.get(port['name'], "").split(",")
                for j in range(port['size']):
                    try:
                        output_items[idx][j] = float(output_data[j])
                    except (IndexError, ValueError):
                        output_items[idx][j] = 0.0  # Default value on error

        return num_iterations

    def stop(self):
        """
        Cleanup on stop: terminates the server process and closes the socket.
        """
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait()
        self.client_socket.close()
        print("C server terminated.")
        return super().stop()
