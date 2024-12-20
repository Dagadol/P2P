import socket

COMMANDS = ['DIR', 'SHR', 'LNK']
LENGTH_HEADER = 4
CMD_HEADER = 3


def check_cmd(cmd):
    return cmd in COMMANDS


def create_msg(cmd, data):
    if type(data) is not bytes:
        data = data.encode()
    print(data)
    length = str(len(data)).zfill(LENGTH_HEADER)
    msg = length.encode() + cmd.encode() + data
    print(msg)
    return msg


def get_msg(other_socket):
    try:
        length = other_socket.recv(LENGTH_HEADER)
        print("l1:", length)
        length = int(length.decode())
        print("l2:", length)
        cmd = other_socket.recv(CMD_HEADER).decode()
        print("3")
        data = other_socket.recv(length)
        print("4")
        return cmd, data
    except ValueError as e:
        return "ER1", f"error recieving the information: {e}"
