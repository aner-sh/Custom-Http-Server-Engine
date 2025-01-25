import os
import socket

# constants
IP = '127.0.0.1'
PORT = 8080
SOCKET_TIMEOUT = 30

DEFAULT_URL = 'webroot/index.html'

# Define redirection paths
REDIRECTION_DICTIONARY = {
    'webroot/redirect': 'webroot/index.html'
}

# Forbidden resources
FORBIDDEN_RESOURCES = ["webroot/forbidden"]


# Function to extract a number from a string (used for calculation)
def extract_number(value):
    """ Extract number from string, considering negative and decimal values """
    number = ""
    decimal = False
    for char in value:
        if char.isdigit():
            number += char
        elif char == ".":
            decimal = True
            number += char

    return float(number) if decimal else int(number)


# Function to process calculations (calculate next number or area)
def perform_calculations(param1, param2=None):
    if param2:
        return (param1 * param2) / 2
    return param1 + 1


# Function to retrieve file content
def get_file_data(file_path):
    """ Read file and return its data or None if not found """
    try:
        with open(file_path, 'rb') as f:
            return f.read()
    except FileNotFoundError:
        return None


# Handle file upload for POST requests
def handle_file_upload(client_socket, resource, task):
    """ Handle file upload via POST request with enhanced error handling """
    try:
        if task == "upload":
            # try:
            #     to_name = resource.split('=')
            #     filename = to_name[1]
            #     file_path = os.path.join("uploads/", filename)
            #     file = open(file_path, 'rb')
            #     file_read = file.read()
            #     file.close()
            #     return file_read
            # except:
            #     return "File does not exist"
            variable = resource.split('=')[-1]
            try:
                with open('uploads/' + variable, 'rb') as f:
                    data = f.read()
                http_header = "HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n"
                client_socket.send(http_header.encode())
                client_socket.send(data)
            except FileNotFoundError:
                http_response = "HTTP/1.1 404 Not Found\r\n\r\n"
                data = get_file_data('404_show.html')
                client_socket.send(http_response.encode())
                client_socket.send(data)
        elif task == "download":
            parts = resource.split('?')
            to_name = parts[1].split('=')
            filename = to_name[1]
            binary_data = b''

            while True:
                try:
                    packet = client_socket.recv(1024)
                    binary_data += packet
                    client_socket.settimeout(2)
                except Exception:
                    break

            folder_path = "uploads/"
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

            file_path = os.path.join(folder_path, filename)

            # Write binary data to the file
            with open(file_path, 'wb') as file:
                file.write(binary_data)

            # Verify file was saved
            return generate_success_response(200, f"File '{filename}' uploaded successfully")
        else:
            return generate_error_response(500, "Upload failed")
    except Exception as e:
        return e


# Generate successful HTTP response
def generate_success_response(status_code, body):
    """ Generate HTTP response with the given status and body """
    return (
        f"HTTP/1.1 {status_code} OK\r\n"
        f"Content-Type: text/plain; charset=utf-8\r\n"
        f"Content-Length: {len(body)}\r\n\r\n"
        f"{body}"
    )


# Generate error HTTP response
def generate_error_response(status_code, message):
    """ Generate HTTP error response with the given status and message """
    return (
        f"HTTP/1.1 {status_code} Error\r\n"
        f"Content-Type: text/plain; charset=utf-8\r\n"
        f"Content-Length: {len(message)}\r\n\r\n"
        f"{message}"
    )


# Handle incoming client requests
def handle_client_request(resource, client_socket):
    """ Process and send the appropriate response for the given resource """
    try:
        # Redirect if necessary
        for key, redirect_to in REDIRECTION_DICTIONARY.items():
            if key in resource:
                http_response = (
                    f"HTTP/1.1 302 Found\r\n"
                    f"Location: /{redirect_to}\r\n"
                    f"Content-Length: 0\r\n\r\n"
                )
                client_socket.send(http_response.encode())
                return

        # Forbidden resource handling
        for forbidden in FORBIDDEN_RESOURCES:
            if forbidden in resource:
                http_response = generate_error_response(403, "Forbidden")
                client_socket.send(http_response.encode())
                return

        # Handle special case: calculate-next
        if "calculate-next" in resource:
            query_string = resource.split('?')[-1]
            num = extract_number(query_string)
            result = perform_calculations(num)
            http_response = generate_success_response(200, str(result))
            client_socket.send(http_response.encode())
            return

        # Handle special case: calculate-area
        if "calculate-area" in resource:
            query_string = resource.split('?')[-1]
            params = query_string.split('&')
            height = extract_number(params[0].split('=')[-1])
            width = extract_number(params[1].split('=')[-1])
            area = perform_calculations(height, width)
            http_response = generate_success_response(200, str(area))
            client_socket.send(http_response.encode())
            return

        # Handle file request (GET)
        if resource == '/' or resource == '':
            resource = DEFAULT_URL

        if not resource.startswith('webroot/'):
            resource = os.path.join('webroot', resource.lstrip('/'))

        data = get_file_data(resource)
        if data is None:
            http_response = generate_error_response(404, "File Not Found")
            client_socket.send(http_response.encode())
            return

        # Determine content type based on file extension
        file_extension = resource.split('.')[-1].lower()
        status = '200 OK'
        content_type = 'application/octet-stream'  # Default content type
        if file_extension == 'html' or file_extension == 'txt':
            content_type = 'text/html; charset=utf-8'
        elif file_extension == 'jpg':
            content_type = 'image/jpeg'
        elif file_extension == 'js':
            content_type = 'application/javascript; charset=UTF-8'
        elif file_extension == 'css':
            content_type = 'text/css'
        elif file_extension == 'ico':
            content_type = 'image/x-icon'
        else:
            status = '415 Unsupported Media Type'

        # Create the response header
        http_header = (
            f"HTTP/1.1 {status}\r\n"
            f"Content-Type: {content_type}\r\n"
            f"Content-Length: {len(data)}\r\n"
            "Connection: close\r\n\r\n"
        )

        # Send the response (header + data)
        client_socket.send(http_header.encode() + data)

    except Exception as e:
        # Handle unexpected errors gracefully
        print(f"Error processing request: {e}")
        error_message = "Internal Server Error"
        http_response = generate_error_response(500, error_message)
        client_socket.send(http_response.encode())


# Validate incoming HTTP request
def validate_http_request(request):
    """ Check if the incoming HTTP request is valid """
    print(request)
    lines = request.split('\r\n')
    if len(lines) < 1:
        return False, None

    method, url, version = lines[0].split()
    if method not in ['GET', 'POST'] or not url.startswith('/'):
        return False, None

    return True, url[1:]  # Strip leading '/' from the URL


# Main client handling function
def handle_client(client_socket):
    """ Manage client connection and process their requests with detailed logging """
    print('Client connected')
    client_socket.settimeout(SOCKET_TIMEOUT)

    try:
        # Increase buffer size for larger requests
        client_request = client_socket.recv(16384)
        request_str = client_request.decode('utf-8', 'replace')

        print("Full Request Received:")
        print("---REQUEST START---")
        print(request_str)
        print("---REQUEST END---")

        # Robust request parsing
        if '\r\n\r\n' in request_str:
            headers, body = request_str.split('\r\n\r\n', 1)
        else:
            headers, body = request_str, ''

        # Detailed header parsing
        headers_lines = headers.split('\r\n')
        if not headers_lines:
            print("Invalid request: No headers found")
            client_socket.send(generate_error_response(400, "Invalid Request").encode())
            return

        # Safely parse first line
        try:
            method, url, version = headers_lines[0].split()
            print(f"Parsed Method: {method}")
            print(f"Parsed URL: {url}")
        except ValueError:
            print("Could not parse request line")
            client_socket.send(generate_error_response(400, "Malformed Request").encode())
            return

        if method == 'POST':
            print("Processing POST request")
            print(f"POST URL: {url}")
            print(f"Request Body Length: {len(body)}")

            if '/upload' in url:
                response = handle_file_upload(client_socket, url, "download")
                print("Upload Response:", response)
                client_socket.send(response.encode())
            else:
                print("Unsupported POST endpoint")
                client_socket.send(generate_error_response(404, "Not Found").encode())

        elif method == 'GET':
            valid_http, resource = validate_http_request(request_str)
            if '/image' in url:
                try:
                    response = handle_file_upload(client_socket, url, "upload")
                    client_socket.send(response.encode())
                except Exception as e:
                    print(e)
            elif valid_http:
                handle_client_request(resource, client_socket)
            else:
                client_socket.send(generate_error_response(400, "Bad Request").encode())

    except Exception as e:
        print(f"CRITICAL ERROR handling client request: {e}")
        import traceback
        traceback.print_exc()
        client_socket.send(generate_error_response(500, "Internal Server Error").encode())

    finally:
        print('Closing connection')
        client_socket.close()


# Main server function to start accepting connections
def main():
    """ Start server and handle incoming client connections """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((IP, PORT))
    server_socket.listen(10)
    print(f"Server listening on port {PORT}")

    while True:
        client_socket, client_address = server_socket.accept()
        print(f"New connection received from {client_address}")
        handle_client(client_socket)


if __name__ == "__main__":
    main()
