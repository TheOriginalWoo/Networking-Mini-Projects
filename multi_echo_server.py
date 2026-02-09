import socket
import threading
import time
import argparse
import pprint


connections = []
BUFFER_SIZE = 1024


def print_raw_response(raw_response: bytes):
    split_response = raw_response.split(b'\r\n')
    [print(i) for i in split_response]


def echo(client_connection: socket.socket, addr):
    client_connection.settimeout(10)
    with client_connection:
        # headers
        raw = b""
        while b"\r\n\r\n" not in raw:
            raw += client_connection.recv(BUFFER_SIZE)

        headers, body = raw.split(b"\r\n\r\n", 1)
        headers = headers.split(b"\r\n")
        headers_key_val_pairs = {}
        for header_val_pair in headers:
            try:
                k, v = header_val_pair.split(b':', 1)
                headers_key_val_pairs[k] = v
            except ValueError:
                continue

        print(f"received the following from {addr}\n{headers}")

        # body
        try:
            remaining_content_length = int(headers_key_val_pairs[b'Content-Length']) - len(body)
            while remaining_content_length > 0:
                body += client_connection.recv(BUFFER_SIZE)
                remaining_content_length -= BUFFER_SIZE
        except KeyError:
            pass

        print(f'received data from {addr}. echoing back..')
        pprint.pp(headers_key_val_pairs)

        client_connection.sendall(b'HTTP/1.1 503 service unavailable\r\n\r\n')



if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--port", type=int, default=8080, help="listening port")
    argparser.add_argument("--host", type=str, default='0.0.0.0', help="server ip")
    args = argparser.parse_args()

    socket_serverside = (args.host, args.port)
    my_socket = socket.socket()
    my_socket.bind(socket_serverside)
    my_socket.listen(5)

    print(f"server started. Listening on {socket_serverside[0]}:{socket_serverside[1]}")

    try:
        while True:
            client_connection, address = my_socket.accept()
            connections.append(threading.Thread(target=echo, args=[client_connection, address]))
            connections[-1].start()
    except KeyboardInterrupt:
        for connection_thread in connections:
            connection_thread.join(timeout=0.1)
        print("Server closed successfully")
    finally:
        my_socket.close()



