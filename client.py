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


def clear_socket_data(sock, buffer_size=1024):
    sock.setblocking(False)  # Set the socket to non-blocking mode
    try:
        while True:
            data, address = sock.recvfrom(buffer_size)
            print(f"Cleared data from {address}: {data.decode('utf-8')}")
    except BlockingIOError:
        # No more data to read
        pass
    finally:
        sock.setblocking(True)  # Restore the socket to blocking mode


def handle_frq(sock, addr, file):
    send_file(file, sock, addr)


def get_files(my_skt, name, ip):  # doesn`t work on larger than 10 bits files
    print(f"Requesting file: {name} from {ip}:{UDP_PORT}")
    my_skt.sendto(udp_protocol.create_msg("FRQ", name), (ip, UDP_PORT))
    chunks = []
    # error_no = []  # old way
    try:
        while True:
            valid, cmd, chunk, addr = udp_protocol.get_msg(my_skt)
            print(f"Received: valid={valid}, cmd={cmd}, chunk={chunk[:50]}... from {addr}")
            if cmd == "END":
                break
            if not valid:
                raise Exception
            chunks.append(chunk.split("~")[1])

    except Exception as e:
        print(f"Error while receiving file: {e}")
        clear_socket_data(my_skt)
        get_files(my_skt, name, ip)
    print("maam", name)
    with open(name.split('\\')[-1], 'wb') as f:
        f.write(''.join(chunks).encode())
    print(f"File {name} received and written successfully.")


def send_file(file, sock, addr):
    print(f"Sending file: {file} to {addr}")
    data = []
    with open(file, "rb") as f:
        chunk = f.read(10)
        while len(chunk) > 0:
            data.append(chunk)
            chunk = f.read(10)
        data.append(chunk)

    for i, chunk in enumerate(data):
        print(f"Sending chunk {i} of size {len(chunk)} to {addr}")
        sock.sendto(udp_protocol.create_msg("FRQ", (str(i) + "~") + chunk.decode()), addr)
    sock.sendto(udp_protocol.create_msg("END"), addr)
    print(f"File {file} sent successfully.")


def udp_server():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_sock.bind(("0.0.0.0", UDP_PORT))
    print(f"UDP server listening on port {UDP_PORT}")
    threads = []
    while True:
        valid, cmd, data, addr = udp_protocol.get_msg(server_sock)
        print(f"UDP Server received: valid={valid}, cmd={cmd}, data={data[:50]}... from {addr}")
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
    path = input("Enter a path of a folder: ").strip()
    files = []
    if os.path.isdir(path) and os.path.exists(path):
        files = get_files_list(path, ip)

    return protocol.create_msg('SHR', pickle.dumps(files))


def handle_dir():
    return protocol.create_msg('DIR', "dir")  # no data is needed


def handle_lnk():
    name = input("Enter the file name: ")
    size = input("Enter the size of the file: ")
    return protocol.create_msg('LNK', f"{name}~{size}"), name


def tcp_client():  # connected to main server only
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((IP, TCP_PORT))
    print("Connected to server")

    while True:
        command = input("Enter command ('SHR' or 'DIR' or 'LNK'): ").strip().upper()

        match command:
            case "SHR":
                msg = handle_share(socket.gethostbyname(socket.gethostname()))

            case "DIR":
                msg = handle_dir()

            case "LNK":
                msg, req_name = handle_lnk()

            case _:  # default gateway
                print("Invalid command! Please enter 'SHR' or 'DIR' or 'LNK'.")
                continue

        print(f"Sending TCP message: {msg}")
        sock.send(msg)

        cmd, data = protocol.get_msg(sock)
        print(f"Received response: cmd={cmd}, data={data}")

        if cmd == "LNK":
            udp_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            if data != "not found":
                get_files(udp_skt, req_name, data)


def main():
    print("Starting client...")
    t1 = threading.Thread(target=tcp_client)
    t2 = threading.Thread(target=udp_server)
    t1.start()
    t2.start()
    t1.join()
    t2.join()


if __name__ == "__main__":
    main()
