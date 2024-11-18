#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>

#define PORT 5000
#define BUFFER_SIZE 1024

int main() {
    int server_fd, new_socket;
    struct sockaddr_in address;
    int opt = 1;
    int addrlen = sizeof(address);
    char buffer[BUFFER_SIZE] = {0};

    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR | SO_REUSEPORT, &opt, sizeof(opt));
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(PORT);
    bind(server_fd, (struct sockaddr *)&address, sizeof(address));
    listen(server_fd, 3);

    printf("C Server listening on port %d...\n", PORT);

    while (1) {
        new_socket = accept(server_fd, (struct sockaddr *)&address, (socklen_t *)&addrlen);
        read(new_socket, buffer, BUFFER_SIZE);
        printf("Received: %s\n", buffer);

        char response[BUFFER_SIZE] = "";
        char *message = strtok(buffer, ";");
        while (message) {
            char *name = strtok(message, ":");
            char *values = strtok(NULL, ":");
            char *value = strtok(values, ",");
            strcat(response, name);
            strcat(response, ":");

            while (value) {
                float processed = atof(value) * 2;  // Example processing
                char processed_value[32];
                snprintf(processed_value, sizeof(processed_value), "%.2f,", processed);
                strcat(response, processed_value);
                value = strtok(NULL, ",");
            }
            response[strlen(response) - 1] = ';';  // Replace trailing comma with semicolon
            message = strtok(NULL, ";");
        }

        response[strlen(response) - 1] = '\0';  // Remove trailing semicolon
        send(new_socket, response, strlen(response), 0);
        close(new_socket);
    }

    return 0;
}
