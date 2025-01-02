import socket
import threading
import protocol
import pickle
import os
import file_class
import time

PATH = f'shared_files'

write_lock = threading.Lock()
active_writers = 0

def data_update(file_path, new_data):
    global active_writers
    with write_lock:
        active_writers += 1
        print(f"[DEBUG] Incremented active_writers: {active_writers}")

    try:
        with open(file_path, "rb") as db_file:
            data = pickle.load(db_file)
            print(f"[DEBUG] Data loaded from {file_path}: {data}")
    except (EOFError, FileNotFoundError) as e:
        print(f"[ERROR] Failed to read {file_path}: {e}")
        data = []

    data += new_data

    try:
        with open(file_path, "wb") as db_file:
            pickle.dump(data, db_file)
            print(f"[DEBUG] Data updated in {file_path}: {data}")
    except Exception as e:
        print(f"[ERROR] Failed to write to {file_path}: {e}")

    with write_lock:
        active_writers -= 1
        print(f"[DEBUG] Decremented active_writers: {active_writers}")

def get_local_files_and_sizes(directory):
    files = []
    sizes = []
    print(f"[DEBUG] Scanning directory: {directory}")

    for root, dirs, filenames in os.walk(directory):
        for filename in filenames:
            filepath = os.path.join(root, filename)
            files.append(filepath)
            sizes.append(os.path.getsize(filepath))

    print(f"[DEBUG] Found files: {files}")
    print(f"[DEBUG] File sizes: {sizes}")
    return files, sizes

def handle_dir(a):
    try:
        with open("database", "rb") as read_file:
            data = pickle.load(read_file)
            print(f"[DEBUG] Data loaded from database: {data}")

        connect_files = ""
        for file in data:
            connect_files += file.path
            connect_files += "^" + file.size + "~"
    except EOFError:
        print("[WARNING] Database is empty.")
        connect_files = ""

    directory = PATH
    files, sizes = get_local_files_and_sizes(directory)

    for filename, size in zip(files, sizes):
        connect_files += filename + "^"
        connect_files += str(size) + "~"

    print(f"[DEBUG] handle_dir output: {connect_files}")
    return connect_files

def handle_shr(data):
    print(f"[DEBUG] Received SHR data: {data}")
    files = pickle.loads(data)
    data_update("database", files)
    return "SHR"

def handle_lnk(data):
    path, size = data.decode().split('~')
    print(f"[DEBUG] Received LNK data: path={path}, size={size}")
    while active_writers > 0:
        print(f"[DEBUG] Waiting for active_writers to finish. Current count: {active_writers}")
        time.sleep(0.01)

    with write_lock:
        try:
            with open("database", "rb") as db_file:
                data = pickle.load(db_file)
                print(f"[DEBUG] Data loaded from database for LNK: {data}")

            file = [x.owner_ip for x in data if x.path == os.path.normpath(path) and x.size == size]
            file = file[0] if file else "N/A"

            if file != "N/A":
                print(f"[DEBUG] File found: {file}")
                return file
        except Exception as e:
            print(f"[ERROR] handle_lnk failed: {e}")
    return "not found"

def handle_cmd(cmd, data):
    print(f"[DEBUG] Handling command: {cmd}, data: {data}")
    if protocol.check_cmd(cmd):
        functions = {"DIR": handle_dir,
                     "SHR": handle_shr,
                     "LNK": handle_lnk}
        return functions[cmd](data)
    else:
        print(f"[ERROR] Invalid command: {cmd}")
        return "err"

def handle_client(client_socket, addr):
    print(f"[DEBUG] New client connected: {addr}")
    while True:
        try:
            cmd, data = protocol.get_msg(client_socket)
            print(f"[DEBUG] Received from client: cmd={cmd}, data={data}")
            info = handle_cmd(cmd, data)
            response = protocol.create_msg(cmd, info)
            client_socket.send(response)
            print(f"[DEBUG] Sent to client: {response}")
        except Exception as e:
            print(f"[ERROR] Error handling client {addr}: {e}")
            break

def main():
    threads = []
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 5500))
    server_socket.listen()

    if not os.path.exists('database'):
        with open("database", 'wb') as f:
            pickle.dump([], f)
            print("[DEBUG] Initialized empty database.")

    print("[INFO] Server is up and running")
    while True:
        try:
            client_socket, addr = server_socket.accept()
            print(f"[INFO] Client connected: {addr}")
            t = threading.Thread(target=handle_client, args=[client_socket, addr])
            t.start()
            threads.append(t)
        except Exception as e:
            print(f"[ERROR] Error accepting client: {e}")

if __name__ == "__main__":
    main()
