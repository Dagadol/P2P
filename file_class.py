import hashlib


class FileInfo:
    def __init__(self, size, ip, path):
        self.size = size
        self.owner_ip = ip
        self.path = path
        #  self.hash = hashlib.sha256((path + size + ip).encode()).digest()

