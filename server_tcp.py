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

    with write_lock:
        with open(file_path, "rb") as db_file:
            data = pickle.load(db_file)

        data.append(new_data)

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
        print("data:", data[0])
        print("data type:", type(data))

        connect_files = ""
        for file in data[0]:
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
    files = pickle.load(data)

    print("files:", files)
    data_update("database", files)

    return "SHR"


def handle_lnk(data):  # get IP, and file data
    path, size = data.split('~')
    while active_writers > 0:
        time.sleep(0.01)

    with write_lock:
        with open("database", "rb") as db_file:
            data = pickle.load(db_file)

            file = [x for x in data if x.path == path and x.size == size][0]  # get the file with the same name and size

            if file != "N/A":
                return file.owner_ip
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
        info = handle_cmd(cmd, addr, data)
        print("info", info)
        client_socket.send(protocol.create_msg(cmd, info))



def main():
    threads = []
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 5500))
    server_socket.listen()

    while True:
        client_socket, addr = server_socket.accept()
        t = threading.Thread(target=handle_client, args=[client_socket, addr])
        t.start()
        threads.append(t)


if __name__ == "__main__":
    main()
