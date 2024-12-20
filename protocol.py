import socket

COMMANDS = ['DIR', 'SHR', 'LNK']
LENGTH_HEADER = 4
CMD_HEADER = 3


def check_cmd(cmd):
    return cmd in COMMANDS


def create_msg(cmd, data):
    length = len(data)
    length = str(length).zfill(LENGTH_HEADER)
    msg = length + cmd + data
    return msg.encode()


def get_msg(other_socket):
    try:
        length = other_socket.recv(LENGTH_HEADER)
        print("l1:", length)
        length = int(length.decode())
        print("l2:", length)
        cmd = other_socket.recv(CMD_HEADER).decode()
        data = other_socket.recv(length).decode()
        return cmd, data
    except:
        return "ERR", "error recieving the information"
