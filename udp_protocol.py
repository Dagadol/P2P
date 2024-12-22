import hashlib
import socket

LENGTH = 3
CHECKSUM = 32
CMD = 3
COMMANDS = ["GET"]


def clac_checksum(data):
    m = hashlib.md5()
    m.update(data.encode())
    checksum = m.hexdigest()
    return checksum


def create_msg(cmd, data):
    length = len(data)
    length = str(length).zfill(LENGTH)
    msg = length + clac_checksum(cmd + data) + cmd + data
    return msg.encode()


def get_msg(other_socket):
    try:
        length = other_socket.recv(LENGTH)
        checksum = other_socket.recv(CHECKSUM)
        cmd = other_socket.recv(CMD)
        data = other_socket.recv(length)

        if clac_checksum(cmd + data) != checksum:
            return False, "RDO", "checksum error"
        return True, cmd, data
    except:
        return False, "ERR", "error recieving the information"
