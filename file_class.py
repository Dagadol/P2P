import hashlib


class FileInfo:
    def __init__(self, size, ip, path):
        self.size = size
        self.owner_ip = ip
        self.path = path

        #  self.hash = hashlib.sha256((path + size + ip).encode()).digest()
    def __str__(self):
        return f"{self.path}&{self.size}&{self.owner_ip}"

