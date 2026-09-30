from random import randint


class Proxy:

    def __init__(self, ip: str, port: int, quantity: int):
        self.ip = f"http://{ip}"
        self.port = port
        self.quantity = quantity

    def get_random_proxy(self):
        proxy_number = randint(self.port, self.port + self.quantity - 1)
        proxy = f"{self.ip}:{proxy_number}"
        return proxy
