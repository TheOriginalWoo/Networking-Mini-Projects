import rsa
import socket
import json
import threading
import argparse
import time
import random
from cryptography.fernet import Fernet


# class SynchronousEncryptionHandler:
#     def __init__(self):
#         self.SYMMETRIC_KEY_TAG: bytes = b"SESSION_KEY:"  # always keep a ":" on
#         self.SYMMETRIC_KEY_RECEIVED_SUCCESS: bytes = b"SESSION KEY RECEIVED"
#         self.session_symmetric_key: bytes = b""
#         self.sync_key_received: bool = False

    


def measure_excecution_time(function):
    def wrapper(*args, **kwargs):
        time_before = time.time()
        function_output = function(*args, **kwargs)
        time_after = time.time()
        execution_time_micros = (time_after - time_before) * 1e3
        print(f"excecution time for {function.__name__}: {execution_time_micros} ms")
        return function_output

    return wrapper


@ measure_excecution_time
def encrypt_sync(message: str, _key: bytes) -> bytes:
    engine = Fernet(_key)
    encrypted_message = engine.encrypt(message.encode())
    # print(f"encrypted message inside function: {encrypted_message}")
    return encrypted_message


@ measure_excecution_time
def decrypt_sync(encrypted_message: bytes, _key: bytes) -> str:
    engine = Fernet(_key)
    decrypted_message: bytes = engine.decrypt(encrypted_message)
    return decrypted_message.decode("utf-8")


@ measure_excecution_time
def encrypt_and_send_RSA(cleartext_message: str, target_public_key: rsa.PublicKey, target: socket.socket):
    cyphertext = rsa.encrypt(cleartext_message.encode(), target_public_key)
    target.sendall(cyphertext)


def reach_out_to_connect(target_details: dict[str, int]):
    # TODO: give this a timeout in time not in loops
    while True:
        try:
            remote_socket = socket.create_connection((target_details["ip"], target_details["port"]))
            break
        except ConnectionRefusedError:
            time.sleep(20e-3)

    return remote_socket


def establish_connection(target_details: dict, local:socket.socket, your_symmetric_key: bytes) -> tuple[socket.socket, bool]:
    global session_symmetric_key
    attacker: bool = False
    print("connecting to remote...")
    randomized_delay: float = 0.1 * random.random() + 0.050

    try:
        local.settimeout(randomized_delay)
        remote_socket, remote_address = local.accept()
    except TimeoutError:
        attacker = True
        remote_socket = reach_out_to_connect(target_details)

    if attacker:
        session_symmetric_key = your_symmetric_key

    print(f"connected to remote {remote_socket.getsockname()}")
    return remote_socket, attacker


        

# TODO: maybe make this able to accept data > BUFFER_SIZE
def listen(your_public_key: rsa.PublicKey, remote_connection: socket.socket, 
           your_private_key: rsa.PrivateKey, attacker: bool):
    # def tackle_symmetric_key_actions(remote_connection, _incoming_data: bytes, is_attacker):

    #     ...

    print("listening...")
    global target_closed
    global target_public_key
    global session_symmetric_key
    global sync_key_received

    init_progress: int = 0

    while True:
        if target_closed:
            break

        incoming_data: bytes = remote_connection.recv(BUFFER_SIZE)

        if init_progress < 3:
            # This aint the most efficient but you aint gonna be practically feeling the extra time anyways

            # public key handling (both will happen)
            if incoming_data == REQUEST_PUBLIC_KEY_KEYWORD:
                remote_connection.sendall(your_public_key.save_pkcs1("PEM"))
                print("sent your public key")
                init_progress += 1
            elif b"-----BEGIN RSA PUBLIC KEY-----" in incoming_data:
                target_public_key = rsa.PublicKey.load_pkcs1(incoming_data)
                print("received target public key")
                print(target_public_key.save_pkcs1("PEM")[:20])
                init_progress += 1

            # symmetric key handling (one or the other)
            elif not attacker and SYMMETRIC_KEY_TAG in incoming_data:    # cleatext SYMMETRIC_KEY_TAG + enc symmetric key
                encrypted_symmetric_key = incoming_data.split(b":", maxsplit=1)[1]
                session_symmetric_key = rsa.decrypt(encrypted_symmetric_key, your_private_key)  
                remote_connection.sendall(SYMMETRIC_KEY_RECEIVED_SUCCESS)
                print("sync key received")
                init_progress += 1
            elif attacker and SYMMETRIC_KEY_RECEIVED_SUCCESS in incoming_data:
                sync_key_received = True
                print("target received the sync key successfully")
                init_progress += 1


        else:
            if not incoming_data:   # might get this during init phase. if that happens,  we cooked. though init only takes like milliseconds so maybe not
                print("target disconnected. press enter to quit")
                target_closed = True
            else:
                print(f"target said: {decrypt_sync(incoming_data, session_symmetric_key)} \n")


def main(args):
    with open(args.home_dir + "public.pem", "rb") as public_key_file:
        your_public_key = rsa.PublicKey.load_pkcs1(public_key_file.read())

    with open(args.home_dir + "private.pem", "rb") as private_key_file:
        your_private_key = rsa.PrivateKey.load_pkcs1(private_key_file.read())

    with open(args.home_dir + "address_details.json", "r") as address_file:
        all_details: dict = json.load(address_file)
        your_details: dict = all_details["your details"]
        target_details: dict = all_details["target details"]
        your_symmetric_key: bytes = all_details["key"].encode()

    random.seed(your_details["port"])

    local: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    local.bind((your_details["ip"], your_details["port"]))
    local.listen()

    try:
        remote_socket, is_attacker = establish_connection(target_details, local, your_symmetric_key)
        listening_thread = threading.Thread(target=listen, args=(your_public_key, remote_socket, your_private_key, is_attacker), daemon=True)
        listening_thread.start()

        remote_socket.sendall(REQUEST_PUBLIC_KEY_KEYWORD)

        # send symmetric key
        global sync_key_received

        if is_attacker:
            while not sync_key_received:
                if target_public_key:
                    remote_socket.sendall(SYMMETRIC_KEY_TAG + rsa.encrypt(session_symmetric_key, target_public_key))
                time.sleep(50e-3)
        else:
            while not session_symmetric_key:
                time.sleep(50e-3)

                

        # didnt replace the True with target closed so that i can add more break statements if need be 
        while True:
            user_message_cleartext: str = input("enter a message: ")
            print(f"you said: {user_message_cleartext}\n")
            cyphertext = encrypt_sync(user_message_cleartext, session_symmetric_key)
            remote_socket.sendall(cyphertext)

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

    SYMMETRIC_KEY_TAG: bytes = b"SESSION_KEY:"  # always keep a ":" on
    SYMMETRIC_KEY_RECEIVED_SUCCESS: bytes = b"SESSION KEY RECEIVED"

    THREAD_TIMEOUT: float = 0.5
    target_public_key = None
    target_closed: bool = False

    session_symmetric_key: bytes = b""
    sync_key_received: bool = False

    parser = argparse.ArgumentParser()
    parser.add_argument("--home_dir", type=str, default="")
    args = parser.parse_args()
    
    main(args)
