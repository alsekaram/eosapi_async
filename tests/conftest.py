import asyncio
import threading

import pytest
from aiohttp import web

from eosapi import EosApi

CHAIN_ID = "1064487b3cd1a897ce03ae5b6a865651747e2e152090f99c1d19d44e01aea5a4"
BLOCK_ID = "0a1b2c3d" * 8
# Well-known EOSIO development key, not a secret
PRIVATE_KEY = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"

TRANSFER_ABI = {
    "version": "eosio::abi/1.1",
    "structs": [
        {
            "name": "transfer",
            "base": "",
            "fields": [
                {"name": "from", "type": "name"},
                {"name": "to", "type": "name"},
                {"name": "quantity", "type": "asset"},
                {"name": "memo", "type": "string"},
            ],
        }
    ],
    "actions": [{"name": "transfer", "type": "transfer", "ricardian_contract": ""}],
}


def transfer_trx(actor="alice"):
    return {
        "actions": [
            {
                "account": "eosio.token",
                "name": "transfer",
                "authorization": [{"actor": actor, "permission": "active"}],
                "data": {
                    "from": actor,
                    "to": "bob",
                    "quantity": "1.00000000 WAX",
                    "memo": "test",
                },
            }
        ]
    }


class FakeServers:
    """An EOS node and an HTTP proxy on localhost, served from one thread."""

    def __init__(self):
        self.replies = {}
        self.hits = []  # (server name, endpoint, request json)
        self.delay = 0
        self.urls = {}
        started = threading.Event()
        threading.Thread(target=asyncio.run, args=(self._serve(started),), daemon=True).start()
        started.wait()

    def reset(self):
        self.replies.clear()
        self.hits.clear()
        self.delay = 0
        self.reply(
            "get_info",
            {"chain_id": CHAIN_ID, "last_irreversible_block_id": BLOCK_ID},
        )
        self.reply("push_transaction", {"transaction_id": "abc"})

    def reply(self, endpoint, body, status=200):
        self.replies[endpoint] = (status, body)

    def hits_of(self, server):
        return [(endpoint, body) for name, endpoint, body in self.hits if name == server]

    async def _serve(self, started):
        for name in ("node", "proxy"):
            app = web.Application()
            app.router.add_route("*", "/{tail:.*}", self._handler(name))
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, "127.0.0.1", 0)
            await site.start()
            port = site._server.sockets[0].getsockname()[1]
            self.urls[name] = ("127.0.0.1", port)
        started.set()
        await asyncio.Event().wait()

    def _handler(self, name):
        async def handle(request):
            endpoint = request.url.path.rsplit("/", 1)[-1]
            body = await request.json() if request.can_read_body else None
            self.hits.append((name, endpoint, body))
            if self.delay:
                await asyncio.sleep(self.delay)
            status, payload = self.replies.get(endpoint, (404, {"error": "unknown"}))
            return web.json_response(payload, status=status)

        return handle

    @property
    def node_url(self):
        host, port = self.urls["node"]
        return f"http://{host}:{port}"


@pytest.fixture(scope="session")
def _servers():
    return FakeServers()


@pytest.fixture
def servers(_servers):
    _servers.reset()
    return _servers


@pytest.fixture
def api(servers):
    api = EosApi(rpc_host=servers.node_url)
    api.set_abi("eosio.token", TRANSFER_ABI)
    api.import_key("alice", PRIVATE_KEY)
    return api


def arun(api, coro_fn):
    """Run coro_fn() in a fresh event loop and close the shared session."""

    async def main():
        async with api:
            return await coro_fn()

    return asyncio.run(main())
