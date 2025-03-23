/**
 * TCP Server for HDL Module Data Processing
 * 
 * This program implements a simple TCP server that receives data in a specific format,
 * processes it, and sends back the results. It's designed to work with hardware modules
 * by receiving input values, processing them, and returning the processed values.
 */

/* Required header files */
#include <stdio.h>      /* Standard I/O functions */
#include <stdlib.h>     /* Standard library functions like atof() */
#include <string.h>     /* String manipulation functions */
#include <unistd.h>     /* UNIX standard functions like read(), close() */
#include <arpa/inet.h>  /* Internet operations, socket structures */

/* Configuration constants */
#define PORT 5000         /* TCP port number the server listens on */
#define BUFFER_SIZE 1024  /* Maximum size of message buffer */

int main() {
    /* Socket variables */
    int server_fd;                /* Server socket file descriptor */
    int new_socket;              /* Client connection socket descriptor */
    struct sockaddr_in address;  /* Socket address structure */
    int opt = 1;                 /* Option value for socket configuration */
    int addrlen = sizeof(address); /* Size of address structure */
    char buffer[BUFFER_SIZE] = {0}; /* Buffer for incoming messages */

    /* Create TCP socket */
    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    
    /* Set socket options to reuse address and port */
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR | SO_REUSEPORT, &opt, sizeof(opt));
    
    /* Configure server address */
    address.sin_family = AF_INET;           /* IPv4 */
    address.sin_addr.s_addr = INADDR_ANY;   /* Accept connections on any interface */
    address.sin_port = htons(PORT);         /* Set port in network byte order */
    
    /* Bind socket to the configured address and port */
    bind(server_fd, (struct sockaddr *)&address, sizeof(address));
    
    /* Start listening for incoming connections with a backlog queue of 3 */
    listen(server_fd, 3);

    printf("C Server listening on port %d...\n", PORT);

    /* Main server loop - continuously accept and process connections */
    while (1) {
        /* Accept a new client connection */
        new_socket = accept(server_fd, (struct sockaddr *)&address, (socklen_t *)&addrlen);
        
        /* Read data from the client into the buffer */
        read(new_socket, buffer, BUFFER_SIZE);
        printf("Received: %s\n", buffer);

        /* Prepare response buffer */
        char response[BUFFER_SIZE] = "";
        
        /* Parse incoming data format: "module1:val1,val2,val3;module2:val1,val2;..." */
        char *message = strtok(buffer, ";");  /* Split by semicolon to get each module section */
        
        /* Process each module section */
        while (message) {
            /* Extract module name and its values */
            char *name = strtok(message, ":");     /* Get module name before colon */
            char *values = strtok(NULL, ":");      /* Get all values after colon */
            char *value = strtok(values, ",");    /* Split values by comma */
            
            /* Start building response with module name */
            strcat(response, name);
            strcat(response, ":");

            /* Process each value for this module */
            while (value) {
                /* Convert string to float and perform processing (example: multiply by 2) */
                float processed = atof(value) * 2;  // Example processing
                
                /* Format the processed value as a string with 2 decimal places */
                char processed_value[32];
                snprintf(processed_value, sizeof(processed_value), "%.2f,", processed);
                
                /* Add processed value to response */
                strcat(response, processed_value);
                
                /* Move to next value */
                value = strtok(NULL, ",");
            }
            
            /* Replace the trailing comma with a semicolon to separate modules */
            response[strlen(response) - 1] = ';';  
            
            /* Move to next module section */
            message = strtok(NULL, ";");
        }

        /* Remove the trailing semicolon from the final response */
        response[strlen(response) - 1] = '\0';  
        
        /* Send the processed response back to the client */
        send(new_socket, response, strlen(response), 0);
        
        /* Close the client connection socket */
        close(new_socket);
    }

    /* Program should never reach here due to infinite loop */
    return 0;
}
