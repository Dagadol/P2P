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


BUFFER_SIZE = 1024  # Optimal buffer size for UDP transfer


def clear_socket_data(sock, buffer_size=BUFFER_SIZE):
    sock.setblocking(False)  # Set the socket to non-blocking mode
    try:
        while True:
            data, address = sock.recvfrom(buffer_size)
            print(f"Cleared data from {address}: {data.decode('utf-8')}")
    except BlockingIOError:
        pass  # No more data to read
    finally:
        sock.setblocking(True)  # Restore the socket to blocking mode


def get_files(my_skt, name, ip):
    print(f"Requesting file: {name} from {ip}:{UDP_PORT}")
    my_skt.sendto(udp_protocol.create_msg(b"FRQ", name.encode()), (ip, UDP_PORT))
    chunks = []

    while True:
        valid, cmd, chunk, addr = udp_protocol.get_msg(my_skt)
        print(f"Received: valid={valid}, cmd={cmd}, chunk length={len(chunk)} from {addr}")
        if cmd == "END":
            break

        if not valid:
            print(f"Error while receiving file chunk: {chunk}")
            clear_socket_data(my_skt)
            return get_files(my_skt, name, ip)

        chunks.append(chunk.split(b"~", 1)[1])  # Append the data part of the chunk

    output_file = os.path.basename(name)
    with open(output_file, 'wb') as f:
        f.write(b"".join(chunks))
    print(f"File {output_file} received and written successfully.")


def send_file(file, sock, addr):
    print(f"Sending file: {file} to {addr}")
    try:
        with open(file, "rb") as f:
            chunk_id = 0
            while True:
                chunk = f.read(BUFFER_SIZE - len(f"{chunk_id}~".encode()))
                if not chunk:
                    break

                message = udp_protocol.create_msg(b"FRQ", f"{chunk_id}~".encode() + chunk)
                sock.sendto(message, addr)
                chunk_id += 1

        sock.sendto(udp_protocol.create_msg(b"END"), addr)
        print(f"File {file} sent successfully.")
    except Exception as e:
        print(f"Error while sending file {file}: {e}")


def udp_server():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_sock.bind(("0.0.0.0", UDP_PORT))
    print(f"UDP server listening on port {UDP_PORT}")

    while True:
        valid, cmd, data, addr = udp_protocol.get_msg(server_sock)
        print(f"UDP Server received: valid={valid}, cmd={cmd}, data={data[:50]}... from {addr}")
        if valid and cmd == "FRQ":
            filepath = data.decode()
            threading.Thread(target=send_file, args=(filepath, server_sock, addr)).start()


def get_files_list(directory, ip):
    files = []
    for root, _, filenames in os.walk(directory):
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
    return protocol.create_msg('DIR', "dir")


def handle_lnk():
    name = input("Enter the file name: ")
    size = input("Enter the size of the file: ")
    return protocol.create_msg('LNK', f"{name}~{size}"), name


def tcp_client():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((IP, TCP_PORT))
    print("Connected to server")

    while True:
        command = input("Enter command ('SHR' or 'DIR' or 'LNK'): ").strip().upper()

        if command == "SHR":
            msg = handle_share(socket.gethostbyname(socket.gethostname()))
        elif command == "DIR":
            msg = handle_dir()
        elif command == "LNK":
            msg, req_name = handle_lnk()
        else:
            print("Invalid command! Please enter 'SHR', 'DIR', or 'LNK'.")
            continue

        print(f"Sending TCP message: {msg}")
        sock.send(msg)

        cmd, data = protocol.get_msg(sock)
        print(f"Received response: cmd={cmd}, data={data}")

        if cmd == "LNK":
            udp_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            get_files(udp_skt, req_name, data.decode())
        print("Awaiting new command.")


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
