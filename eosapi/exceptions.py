import requests
from aiohttp import ClientResponse
from requests import Response


class EosApiException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class NodeException(EosApiException):
    def __init__(
        self,
        msg: str,
        resp: requests.Response | ClientResponse | None,
        status: int | None = None,
        body: dict | str | None = None,
    ):
        super().__init__(msg)
        self.resp = resp
        # an aiohttp response is closed by now: status and body stay readable
        self.status = status
        self.body = body


class TransactionException(EosApiException):
    def __init__(
        self,
        msg,
        resp: dict | Response | None,
        status: int | None = None,
        body: dict | str | None = None,
    ):
        super().__init__(msg)
        self.resp = resp
        self.status = status
        self.body = body
