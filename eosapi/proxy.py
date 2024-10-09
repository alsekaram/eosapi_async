from random import randint, choice


class Proxy:

    def __init__(self, ip: str, port: int, quantity: int):
        self.ip = f"http://{ip}"
        self.port = port
        self.quantity = quantity
        self.current_index = randint(0, self.quantity - 1)

    def get_random_proxy(self):
        proxy_number = randint(self.port, self.port + self.quantity)
        proxy = f"{self.ip}:{proxy_number}"
        return proxy

    def get_sequential_proxy(self):
        proxy_number = self.port + (self.current_index % self.quantity)
        proxy = f"{self.ip}:{proxy_number}"
        self.current_index += 1  # увеличиваем индекс для следующего прокси
        return proxy
