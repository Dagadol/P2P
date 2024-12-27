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


def handle_frq(sock, addr, file):
    send_file(file, sock, addr)


def handle_rdo():
    pass

def get_files(my_skt, name, ip):  # doesn`t work on larger than 10 bits files
    my_skt.sendto(udp_protocol.create_msg("FRQ", name), (ip, UDP_PORT))
    chunks = []
    # error_no = []  # old way
    try:
        while True:
            valid, cmd, chunk, addr = udp_protocol.get_msg(my_skt)
            if cmd == b"END":
                break
            if not valid:
                raise Exception
            chunks.append(chunk.split(b"~")[1])

    except Exception as e:
        print(e, end="")
        clear_socket_data(my_skt)
        get_files(my_skt, name, ip)

    with open(name.split('/')[-1], 'wb') as f:
        f.write(b''.join(chunks))


def send_file(file, sock, addr):
    """"chunkim send and if didnt recieve good"""
    data = []
    with open(file, "rb") as f:
        chunk = f.read(1024)
        while len(chunk) > 0:
            data.append(chunk)
            chunk = f.read(1024)
        data.append(chunk)

    for i, chunk in enumerate(data):
        sock.sendto(b"FRQ" + str(i).encode() + chunk, addr)  # decode the chuck it'd be possible to add together


def udp_server():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_sock.bind(("0.0.0.0", UDP_PORT))
    threads = []
    while True:
        valid, cmd, data, addr = udp_protocol.get_msg(server_sock)
        if valid:
            if cmd == "FRQ":
                t = threading.Thread(target=send_file, args=[data, server_sock, addr])
                t.start()
                threads.append(t)


def get_files_list(directory, ip):
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
    return protocol.create_msg('LNK', f"{name}~{size}"), name


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

        if cmd == "LNK":
            udp_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            get_files(udp_skt, req_name, data)


def main():
    t1 = threading.Thread(target=tcp_client)
    t2 = threading.Thread(target=udp_server)
    t1.start()
    t2.start()
    t1.join()
    t2.join()


if __name__ == "__main__":
    main()
