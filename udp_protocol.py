import hashlib
import socket
import time

LENGTH = 4
CHECKSUM = 32
CMD = 3
COMMANDS = ["FRQ", "RDO", "END"]


def calc_checksum(data):
    m = hashlib.md5()
    m.update(data.encode())
    checksum = m.hexdigest()
    return checksum


def create_msg(cmd, data=''):
    length = len(data)
    length = str(length).zfill(LENGTH)

    msg = length + cmd + calc_checksum(cmd + data) + data
    return msg.encode()


def get_msg(udp_socket):
    try:
        # Receive the message and the sender's address
        msg, addr = udp_socket.recvfrom(1024)
        print(msg)

        # Parse the length header
        length_header = msg[:LENGTH]
        if not length_header:
            return False, "ERR", "Empty message", addr

        length = int(length_header.decode())

        # Parse the command header
        cmd = msg[LENGTH:LENGTH + CMD].decode()


        # Parse the checksum
        checksum_start = LENGTH + CMD
        checksum_end = checksum_start + CHECKSUM
        checksum = msg[checksum_start:checksum_end].decode()

        # Parse the data if the command requires it
        data_start = checksum_end
        data = msg[data_start:data_start + length].decode()  # if contains_data(cmd) else ""

        # Validate the checksum
        print(cmd + data)
        print(checksum)
        if checksum != calc_checksum(cmd + data):
            return False, "ERR", "Checksum mismatch", addr

        return True, cmd, data, addr
    except Exception as e:
        return False, "ERR", str(e), None
