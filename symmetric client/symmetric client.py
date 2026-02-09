import socket
from cryptography.fernet import Fernet
import json
import threading


def encrypt(message: str, _key: bytes) -> bytes:
    engine = Fernet(_key)
    encrypted_message = engine.encrypt(message.encode())
    return encrypted_message


def decrypt(encrypted_message: bytes, _key: bytes) -> str:
    engine = Fernet(_key)
    decrypted_message: bytes = engine.decrypt(encrypted_message)
    return decrypted_message.decode("utf-8")


def listen(local: socket.socket):
    while run:
        client, address = local.accept()
        encrypted_message: bytes = client.recv(BUFFER_SIZE)
        decrypted_message: str = decrypt(encrypted_message, key)

        print(f"\nmessage received from {address}")
        print(f"encrypted message: {encrypted_message}")
        print(f"decrypted message: {decrypted_message}\n")

        client.shutdown(socket.SHUT_RDWR)

def send(message: str):
    target: socket.socket = socket.create_connection((target_details["ip"], target_details["port"]))
    encrypted_message: bytes = encrypt(message, key)

    print(f"\nyour message: {message}")
    print(f"encrypted message: {encrypted_message}")

    target.sendall(encrypted_message)


def main():
    local: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    local.bind((your_details["ip"], your_details["port"]))
    local.listen()

    listener_thread = threading.Thread(target=listen, args=(local,))
    listener_thread.start()

    try:
        while True:
            message: str = input("Enter your message: ")
            send(message)

    except KeyboardInterrupt:
        pass

    finally:
        global run
        run = False
        listener_thread.join(timeout=3.0)
        local.close()


if __name__ == '__main__':
    BUFFER_SIZE: int = 1024
    run: bool = True

    with open("config.json", "r") as config_file:
        config_dictionary: dict = json.load(config_file)

        key: bytes = config_dictionary["key"].encode()
        target_details: dict = config_dictionary["target details"]
        your_details: dict = config_dictionary["your details"]

    main()
