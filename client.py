import threading
import protocol
import udp_protocol
from file_class import FileInfo
import os
import socket
import pickle

IP = '127.0.0.1'
TCP_PORT = 5500
UDP_PORT = 5501

def udp_server():
    pass

def get_files(directory, ip):
    files = []
    for root, dirs, filenames in os.walk(directory):
        for filename in filenames:
            filepath = os.path.join(root, filename)
            file_object = FileInfo(str(os.path.getsize(filepath)), ip, filepath)
            files.append(file_object)

    return files


def handle_share(ip):
    path = input("enter a path of a folder ").strip()
    files = []
    if os.path.isdir(path) and os.path.exists(path):
        files = get_files(path, ip)

    return protocol.create_msg('SHR', pickle.dumps(files))


def handle_dir():
    return protocol.create_msg('DIR', "dir")  # no data is needed


def handle_lnk():
    name = input("enter the file name ")
    size = input("enter the size of the file ")
    return protocol.create_msg('LNK', f"{name}~{size}")



def tcp_client():  # connected to main server only
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((IP, TCP_PORT))
    print("connected to server")

    while True:
        command = input("Enter command ('SHR' or 'DIR' or 'LNK'): ").strip().upper()

        match command:
            case "SHR":
                msg = handle_share(socket.gethostbyname(socket.gethostname()))

            case "DIR":
                msg = handle_dir()

            case "LNK":
                msg = handle_lnk()

            case _:  # default getaway
                print("Invalid command! Please enter 'SHR' or 'DIR' or 'LNK'.")
                continue

        sock.send(msg)

        cmd, data = protocol.get_msg(sock)
        print(data.decode())




def main():
    tcp_client()


if __name__ == "__main__":
    main()
