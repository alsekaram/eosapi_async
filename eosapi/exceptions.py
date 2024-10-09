import requests
from aiohttp import ClientResponse
from requests import Response


class EosApiException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class NodeException(EosApiException):
    def __init__(self, msg: str, resp: requests.Response | ClientResponse | None):
        super().__init__(msg)
        self.resp = resp
        print(self.resp)


class TransactionException(EosApiException):
    def __init__(self, msg, resp: dict | Response | None):
        super().__init__(msg)
        self.resp = resp
