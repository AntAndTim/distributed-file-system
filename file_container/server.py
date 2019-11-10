class FileServer:
    def __init__(self, address: str) -> None:
        super().__init__()
        self.address = address

    def download(self, file_path: str):
        return open(file_path).read()
