import hashlib
import socket
import time

LENGTH = 3
CHECKSUM = 16
CMD = 3
COMMANDS = ["FRQ", "RDO", "END"]


def clac_checksum(data):
    m = hashlib.md5()
    m.update(data.encode())
    checksum = m.hexdigest()
    return checksum


def create_msg(cmd, data=b''):
    length = len(data)
    length = str(length).zfill(LENGTH)
    msg = length + clac_checksum(cmd + data) + cmd + data
    return msg.encode()


def get_msg(other_socket):
    try:
        print('1')
        print(other_socket.recvfrom(LENGTH))
        length, addr = other_socket.recvfrom(LENGTH)
        print('2')
        checksum, addr = other_socket.recvfrom(CHECKSUM)
        cmd, addr = other_socket.recvfrom(CMD)
        data, addr = other_socket.recvfrom(int(length))

        if clac_checksum(cmd + data) != checksum:
            return False, "RDO", "checksum error", addr
        return True, cmd, data, addr
    except Exception as e:
        print("reall shii error", e)
        return False, "ERR", "error recieving the information", addr
