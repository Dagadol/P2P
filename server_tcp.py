import socket
import threading
import protocol
import pickle
import os
import file_class
import time
import udp_protocol

PATH = f'shared_files'

write_lock = threading.Lock()
active_writers = 0
IP = "10.0.0.15"
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

def data_update(file_path, new_data):
    global active_writers  # writing in database
    with write_lock:
        active_writers += 1

    with write_lock:
        #try:
        with open(file_path, "rb") as db_file:
            data = pickle.load(db_file)
        #except EOFError:
        #    print("empty file")

        data += new_data

        with open(file_path, "wb") as db_file:
            pickle.dump(data, db_file)

    with write_lock:
        active_writers -= 1


# old way to append
"""
def append_to_pickle_file(file_path, new_data): 
    try:
        # Open the file in read-write mode
        with open(file_path, 'rb+') as file:
            try:
                # Try to load existing data
                data = pickle.load(file)[0]
            except IndexError:
                print("index error")
                data = pickle.load(file)
            except EOFError:
                data = []

            # Append the new data
            print("data:", data)
            data.append(new_data)

            for f in data:
                print("name:", f.name)


            file.seek(0)
            pickle.dump(data, file)

    except FileNotFoundError:
        # If the file doesn't exist, create a new one and dump the data
        with open(file_path, 'wb') as file:
            pickle.dump([new_data], file)  # Start with a list containing the new data
"""


def get_local_files_and_sizes(directory):
    files = []
    sizes = []

    for root, dirs, filenames in os.walk(directory):
        for filename in filenames:
            filepath = os.path.join(root, filename)
            files.append(filepath)
            sizes.append(os.path.getsize(filepath))

    return files, sizes


def handle_dir(a):
    try:
        with open("database", "rb") as read_file:
            data = pickle.load(read_file)  # data is a list of classes of file_class
        print("data:", data)
        print("data type:", type(data))

        connect_files = ""
        for file in data:
            connect_files += file.path  # between file `~` between parameters `^`
            connect_files += "^" + file.size + "~"  # separated by `name^space_taken~`
    except EOFError:
        print("no data?")
        connect_files = ""

    directory = PATH
    files, sizes = get_local_files_and_sizes(directory)

    for filename, size in zip(files, sizes):  # connect local files
        connect_files += filename + "^"
        connect_files += str(size) + "~"

    return connect_files


def handle_shr(data):  # get IP, and file data
    #  files = data.split("~")  # ["name^space_taken", ...]
    files = pickle.loads(data)

    print("files:", files)
    data_update("database", files)

    return "SHR"


def handle_lnk(data):  # get IP, and file data
    path, size = data.decode().split('~')
    print(path)
    while active_writers > 0:
        time.sleep(0.01)

    with write_lock:

        with open("database", "rb") as db_file:
            data = pickle.load(db_file)
            for s in data:
                print(str(s))

        file = [x.owner_ip for x in data if x.path == os.path.normpath(path) and x.size == size]  # get the file with the same name
        print(file)
        if len(file) > 0:
            file = file[0]
            return file
        else:
            files, sizes = get_local_files_and_sizes(PATH)
            for filename, size in zip(files, sizes):
                if os.path.normpath(filename) == os.path.normpath(path) and size == int(size):
                    return IP
    return "not found"


def handle_cmd(cmd, data):
    if protocol.check_cmd(cmd):
        functions = {"DIR": handle_dir,
                     "SHR": handle_shr,
                     "LNK": handle_lnk}
        return functions[cmd](data)
    else:
        return "err"


def handle_client(client_socket, addr):
    while True:
        cmd, data = protocol.get_msg(client_socket)
        print("cmd:", cmd)
        print("data:", data)
        info = handle_cmd(cmd, data)
        print("info", info)
        client_socket.send(protocol.create_msg(cmd, info))


def main():
    threads = []
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 5500))
    server_socket.listen()

    if not os.path.exists('database'):  # if db not exist create empty db
        with open("database", 'wb') as f:
            pickle.dump([], f)

    print("server is up and running")
    while True:
        client_socket, addr = server_socket.accept()
        print("client is connected from:", addr)
        t = threading.Thread(target=handle_client, args=[client_socket, addr])
        t.start()
        threads.append(t)
    print("should never get here")


if __name__ == "__main__":
    threading.Thread(target=udp_server).start()
    main()
