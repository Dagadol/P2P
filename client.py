import threading
import protocol
import udp_protocol
from file_class import FileInfo
import os
import  socket


def udp_server():
    pass


def get_files(directory, ip):
    files = []
    for root, dirs, filenames in os.walk(directory):
        for filename in filenames:
            filepath = os.path.join(root, filename)
            files.append(filepath)
            file_object = FileInfo()



    return files


def handle_share(ip):
    path = input("enter a path of a folder").strip()
    if os.path.isdir(path) and os.path.exists(path):
        files = get_files(path, ip)



def handle_dir():
    pass


def handle_lnk():
    pass


def tcp_client():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        command = input("Enter command ('SHR' or 'DIR' or 'LNK'): ").strip().upper()

        if not protocol.check_cmd(command):
            print("Invalid command! Please enter 'SHR' or 'DIR' or 'LNK'.")
            continue

        match command:
            case "SHR":
                handle_share(sock.gethostbyname(socket.gethostname()))

            case "DIR":
                handle_dir()

            case "LNK":
                handle_lnk()


def main():
    tcp_client()


if __name__ == "__main__":
    main()
