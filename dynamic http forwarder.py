import socket
# import argparse
import threading


BUFFER_SIZE = 4096
BACKLOG = 20
# change it to 20 later when actually using it
TIMEOUT = 3
# ConnectionResetError:


def forward(source_sock: socket.socket, dest_sock: socket.socket):
    source_peername = source_sock.getpeername()
    dest_peername = dest_sock.getpeername()
    try:
        while True:
            data = source_sock.recv(BUFFER_SIZE)
            print(f"sent 1 chunk from {source_peername} -> {dest_peername}. len: {len(data)}")
            if not data:
                break
            dest_sock.sendall(data)
    except TimeoutError:
        pass

    print(f"{source_peername} -> {dest_peername} successful")
    source_sock.shutdown(socket.SHUT_WR)


def handle_client(client: socket.socket):
    # get remote address
    # possible that host will be down the line
    # data = client.recv(BUFFER_SIZE)
    data = b''
    while b'\r\n\r\n' not in data:
        chunk = client.recv(BUFFER_SIZE)
        if not chunk:
            break
        else:
            data += chunk

    headers, rest = data.split(b'\r\n\r\n')
    header_list = headers.split(b'\r\n')
    header_list.pop(0)
    header_dict = {}
    for header in header_list:
        k, v = header.split(b':')
        header_dict[k] = v

    host = header_dict[b'Host']
    print(host)
    host_str = host.decode("utf-8").lstrip()
    print(host_str)

    remote = socket.create_connection((host_str, 80))
    print(f"conneted to remote {host_str}:80")
    client.settimeout(TIMEOUT)
    remote.settimeout(TIMEOUT)
    remote.sendall(data)
    threads.append(threading.Thread(target=forward, args=(client, remote)))
    threads[-1].start()
    threads.append(threading.Thread(target=forward, args=(remote, client)))
    threads[-1].start()


if __name__ == "__main__":
    # argparser = argparse.ArgumentParser()
    # argparser.add_argument("--remote", type=str)
    # args = argparser.parse_args()

    # remote_ip, remote_port = args.remote.split(':', maxsplit=1)
    # socket.setdefaulttimeout(10)

    exit_code = 0
    threads = []
    source = ('0.0.0.0', 8080)

    local_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    local_sock.bind(source)
    local_sock.listen(BACKLOG)

    print(f"forwarder started. listening in on {source[0]}:{source[1]}")

    try:
        while True:
            client_sock, client_addr = local_sock.accept()
            print(f"Established connection with client {client_addr}")
            threads.append(threading.Thread(target=handle_client, args=[client_sock]))
            threads[-1].start()

    # except KeyboardInterrupt:
    #     pass

    except Exception as e:
        if e != KeyboardInterrupt:
            print(e)
            exit_code = 1

    finally:
        for thread in threads:
            thread.join()
        local_sock.close()
        # remote_sock.close()
        print(f"Forwarder closed with exit code {exit_code}")


