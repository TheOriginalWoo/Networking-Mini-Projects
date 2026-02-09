import socket
import threading
import argparse


BUFFER_SIZE = 4096
TIMEOUT = 10.0
LISTEN_MAX = 20
threads = []


def handle_client(client_connection: socket.socket):
    client_connection.settimeout(TIMEOUT)
    header_chunk = client_connection.recv(BUFFER_SIZE)
    if not header_chunk:
        client_connection.sendall(b'HTTP/1.1 400 Bad Request\r\n')
        print(f"improper request. dropped client {client_connection.getpeername()}")
        return

    header_list = header_chunk.split(b'\r\n')
    method, path, protocol_version = header_list[0].split(b' ')
    if method != b'CONNECT':
        client_connection.sendall(b'HTTP/1.1 400 Bad Request\r\n\r\n')
        print(f"improper request. dropped client {client_connection.getpeername()}")
        return

    remote_host, remote_port = path.split(b':')
    remote_sock = socket.create_connection((remote_host.decode(), int(remote_port.decode())))
    print(f"CONNECTED to remote {remote_host.decode()}:{remote_port.decode()}")
    client_connection.sendall(b'HTTP/1.1 200 Connection established\r\n\r\n')

    threads.append(threading.Thread(target=forward, args=(client_connection, remote_sock)))
    threads[-1].start()
    threads.append(threading.Thread(target=forward, args=(remote_sock, client_connection)))
    threads[-1].start()


def forward(source_sock: socket.socket, dest_sock: socket.socket):
    empty_amount = 0
    source_peername = source_sock.getpeername()
    dest_peername = dest_sock.getpeername()
    try:
        while True:
            data = source_sock.recv(BUFFER_SIZE)
            if not data:
                break
            dest_sock.sendall(data)

            print(f"sent 1 chunk from {source_peername} -> {dest_peername}. len: {len(data)}")
            if args.verbose:
                try:    print(data.decode("utf-8"))
                except UnicodeDecodeError:
                    print("undecodable chunk. printing raw bytes...")
                finally: print()
    except TimeoutError:
        pass

    except BrokenPipeError:
        pass

    print(f"{source_peername} -> {dest_peername} successful")
    try:
        source_sock.shutdown(socket.SHUT_WR)
    except OSError: # if the socket is already closed basically
        pass


if __name__ == "__main__":
    exit_code = 0

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=int, default=8080)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    local_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    local_sock.bind(('0.0.0.0', args.port))
    local_sock.listen(LISTEN_MAX)

    print(f"server initialization complete. Listening on 0.0.0.0:{args.port}")

    try:
        while True:
            client_sock, client_addr = local_sock.accept()
            print(f"Received connection from {client_addr[0]}:{client_addr[1]}")
            threads.append(threading.Thread(target=handle_client, args=[client_sock]))
            threads[-1].start()

    except KeyboardInterrupt:
        pass

    except Exception as e:
        print(e)
        exit_code = 1

    finally:
        print(f"\nserver shutdown in progress\nwrapping up all ongoing processes...")
        for t in threads:
            t.join(timeout=3)
        local_sock.close()
        print(f"server closed successfully with exit code {exit_code}")

