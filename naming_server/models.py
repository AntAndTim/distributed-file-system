from json import JSONEncoder


class Server:
    def __init__(self, address: str, port: int) -> None:
        super().__init__()
        self.address = address
        self.port = port

    def __str__(self) -> str:
        return '{' + f'"address":"{self.address}", "port":{self.port}' + '}'

    def __repr__(self) -> str:
        return '{' + f'"address":"{self.address}", "port":{self.port}' + '}'

    def __eq__(self, o: object) -> bool:
        if isinstance(o, Server):
            return self.address == o.address and self.port == o.port
        return False

    def __hash__(self) -> int:
        return hash((self.address, self.port))


class Encoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Server):
            return str(obj)
        return JSONEncoder.default(self, obj)
