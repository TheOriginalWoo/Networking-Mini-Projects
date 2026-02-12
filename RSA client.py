import rsa
import socket
import json
import threading
import argparse
import time
import random


def measure_excecution_time(function):
    def wrapper(*args, **kwargs):
        time_before = time.time()
        function(*args, **kwargs)
        time_after = time.time()
        execution_time_micros = (time_after - time_before) * 1e3
        print(f"excecution time for {function.__name__}: {execution_time_micros} ms")

    return wrapper


@ measure_excecution_time
def encrypt_and_send_RSA(cleartext_message: str, target_public_key: rsa.PublicKey, target: socket.socket):
    cyphertext = rsa.encrypt(cleartext_message.encode(), target_public_key)
    target.sendall(cyphertext)

@ measure_excecution_time
def decrypt_RSA(cyphertext: bytes, local_private_key: rsa.PrivateKey):
    cleartext: str = rsa.decrypt(cyphertext, local_private_key).decode()
    return cleartext


def reach_out_to_connect(target_details: dict[str, int]):
    # TODO: give this a timeout too so it loops a couple times and fucking give up
    while True:
        try:
            remote_socket = socket.create_connection((target_details["ip"], target_details["port"]))
            break
        except ConnectionRefusedError:
            time.sleep(20e-3)

    return remote_socket


def establish_connection(target_details: dict, local:socket.socket) -> socket.socket:
    print("connecting to remote...")
    randomized_delay: float = 0.1 * random.random() + 0.050

    try:
        local.settimeout(randomized_delay)
        remote_socket, remote_address = local.accept()
    except TimeoutError:
        remote_socket = reach_out_to_connect(target_details)

    print(f"connected to remote {remote_socket.getsockname()}")
    return remote_socket


        

# TODO: maybe make this able to accept data > BUFFER_SIZE
def listen(your_public_key: rsa.PublicKey, remote_connection: socket.socket, 
           your_private_key: rsa.PrivateKey):
    print("listening...")
    global target_closed

    while True:
        if target_closed:
            break

        incoming_data: bytes = remote_connection.recv(BUFFER_SIZE)
        if incoming_data == REQUEST_PUBLIC_KEY_KEYWORD:
            remote_connection.sendall(your_public_key.save_pkcs1("PEM"))
        elif b"-----BEGIN RSA PUBLIC KEY-----" in incoming_data:
            global target_public_key
            target_public_key = rsa.PublicKey.load_pkcs1(incoming_data)
            print(f"received target public key")
        elif not incoming_data:
            print("target disconnected. press enter to quit")
            target_closed = True
        else:
            print(f"target said: {decrypt_RSA(incoming_data, your_private_key)} \n")
            # Only for RSA. might have to change


def main(args):
    with open(args.home_dir + "public.pem", "rb") as public_key_file:
        your_public_key = rsa.PublicKey.load_pkcs1(public_key_file.read())

    with open(args.home_dir + "private.pem", "rb") as private_key_file:
        your_private_key = rsa.PrivateKey.load_pkcs1(private_key_file.read())

    with open(args.home_dir + "address_details.json", "r") as address_file:
        all_details: dict = json.load(address_file)
        your_details: dict = all_details["your details"]
        target_details: dict = all_details["target details"]

    random.seed(your_details["port"])

    local: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    local.bind((your_details["ip"], your_details["port"]))
    local.listen()

    try:
        remote_socket = establish_connection(target_details, local)
        listening_thread = threading.Thread(target=listen, args=(your_public_key, remote_socket, your_private_key), daemon=True)
        listening_thread.start()

        remote_socket.sendall(REQUEST_PUBLIC_KEY_KEYWORD)

        # didnt replace the True with target closed so that i can add more break statements if need be 
        while True:
            user_message_cleartext: str = input("enter a message: ")
            print(f"you said: {user_message_cleartext}\n")
            encrypt_and_send_RSA(user_message_cleartext, target_public_key, remote_socket)

            if target_closed:
                break
    except KeyboardInterrupt:
        pass
    finally:
        print("Shutting down client...")
        listening_thread.join(timeout=THREAD_TIMEOUT)
        remote_socket.close()
        local.close()
        print("Client shutdown successfully")


def test():
    public_key, private_key = rsa.newkeys(1024)
    print(public_key.save_pkcs1("PEM"))


if __name__ == "__main__":
    BUFFER_SIZE: int = 2048
    REQUEST_PUBLIC_KEY_KEYWORD: bytes = b"REQUEST PUBLIC\r\n"
    THREAD_TIMEOUT: float = 0.5
    target_public_key = None
    target_closed: bool = False

    parser = argparse.ArgumentParser()
    parser.add_argument("--home_dir", type=str, default="")
    args = parser.parse_args()
    
    main(args)
