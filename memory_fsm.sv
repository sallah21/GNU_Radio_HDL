module memory_fsm (
    input wire clk,
    input wire rst,
    input wire [7:0] data_in,
    input wire start,
    output reg [7:0] data_out,
    output reg [2:0] state_out,
    output reg done
);

    // FSM States
    typedef enum logic [2:0] {
        IDLE    = 3'b000,
        STORE   = 3'b001,
        PROCESS = 3'b010,
        READ    = 3'b011,
        OUTPUT  = 3'b100
    } state_t;
    
    state_t current_state, next_state;
    
    // Internal memory array (16 bytes)
    reg [7:0] memory [0:15];
    
    // Internal registers for state
    reg [3:0] address_counter;
    reg [3:0] read_address;
    reg [7:0] accumulator;
    reg [3:0] process_counter;
    
    // State register
    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            current_state <= IDLE;
            address_counter <= 0;
            read_address <= 0;
            accumulator <= 0;
            process_counter <= 0;
            data_out <= 0;
            done <= 0;
            
            // Initialize memory to zero
            for (int i = 0; i < 16; i++) begin
                memory[i] <= 8'h00;
            end
        end else begin
            current_state <= next_state;
            
            case (current_state)
                IDLE: begin
                    done <= 0;
                    address_counter <= 0;
                    read_address <= 0;
                    accumulator <= 0;
                    process_counter <= 0;
                end
                
                STORE: begin
                    // Store input data in memory
                    memory[address_counter] <= data_in;
                    address_counter <= address_counter + 1;
                end
                
                PROCESS: begin
                    // Process data: accumulate values from memory
                    accumulator <= accumulator + memory[process_counter];
                    process_counter <= process_counter + 1;
                end
                
                READ: begin
                    // Read processed data from memory
                    data_out <= memory[read_address];
                    read_address <= read_address + 1;
                end
                
                OUTPUT: begin
                    // Output the accumulated result
                    data_out <= accumulator;
                    done <= 1;
                end
                
                default: begin
                    // Default case to handle any undefined states
                    current_state <= IDLE;
                    done <= 0;
                    address_counter <= 0;
                    read_address <= 0;
                    accumulator <= 0;
                    process_counter <= 0;
                end
            endcase
        end
    end
    
    // Next state logic
    always_comb begin
        next_state = current_state;
        
        case (current_state)
            IDLE: begin
                if (start)
                    next_state = STORE;
            end
            
            STORE: begin
                if (address_counter == 15)
                    next_state = PROCESS;
            end
            
            PROCESS: begin
                if (process_counter == 15)
                    next_state = READ;
            end
            
            READ: begin
                if (read_address == 7)  // Read first 8 values
                    next_state = OUTPUT;
            end
            
            OUTPUT: begin
                next_state = IDLE;
            end
            
            default: begin
                // Default case to handle any undefined states
                next_state = IDLE;
            end
        endcase
    end
    
    // Output current state for debugging
    assign state_out = current_state;
    
endmodule
