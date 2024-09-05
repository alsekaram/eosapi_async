import binascii
from collections import defaultdict

import aiohttp
import requests
import functools
from typing import List, Dict, Union

from antelopy import AbiCache

from .transaction import Account, Authorization, Action, Transaction
from .exceptions import TransactionException, NodeException

from .abi import Abi


class EosApi:
    """
    A class to interact with the EOS blockchain via the EOSIO API.
    """

    def __init__(self, rpc_host: str = "https://wax.pink.gg", timeout: int = 120):
        """
        Initialize the EosApi instance.

        :param rpc_host: The RPC host URL for the EOSIO API.
        :param timeout: Timeout for the HTTP requests.
        """
        self.rpc_host = rpc_host
        self.accounts: Dict[str, Account] = {}
        self.cpu_payer: Account | None = None
        self._abi_cache: defaultdict[str, Abi] = defaultdict()

        self.headers = {
            "accept": "*/*",
            "accept-language": "en-US;q=0.5,en;q=0.3",
            "referer": "https://waxbloks.io/",
            "accept-encoding": "gzip, deflate, br",
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:128.0) Gecko/20100101 Firefox/128.0",
            "origin": "https://waxbloks.io",
            "dnt": "1",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
        }
        self.warder_headers = {
            "accept": "*/*",
            "accept-language": "en-US;q=0.5,en;q=0.3",
            "referer": "https://play.alienworlds.io/",
            "accept-encoding": "gzip, deflate",
            "content-type": "text/plain;charset=UTF-8",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:128.0) Gecko/20100101 Firefox/128.0",
            "origin": "https://play.alienworlds.io",
            "dnt": "1",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "priority": "u=4",
            "te": "trailers",
        }
        if "yeomen" in self.rpc_host:
            self.headers = self.warder_headers
        self.session = requests.Session()
        self.session.trust_env = False
        self.session.headers = self.headers
        self.session.request = functools.partial(self.session.request, timeout=timeout)

    def import_key(self, account: str, private_key: str, permission: str = "active"):
        """
        Import a single key for an account.

        :param account: The account name.
        :param private_key: The private key for the account.
        :param permission: The permission level (default is "active").
        """
        account = Account(account, private_key, permission)
        self.accounts[account.index()] = account

    def import_keys(self, accounts: Union[List[Dict], List[Account]]):
        """
        Import multiple keys for accounts.

        :param accounts: A list of account dictionaries or Account objects.
        """
        for item in accounts:
            if isinstance(item, dict):
                account = Account(
                    item["account"], item["private_key"], item["permission"]
                )
            elif isinstance(item, Account):
                account = item
            else:
                raise TypeError("Unknown account type")
            self.accounts[account.index()] = account

    def set_cpu_payer(self, account: str, private_key: str, permission: str = "active"):
        """
        Set the CPU payer account.

        :param account: The account name.
        :param private_key: The private key for the account.
        :param permission: The permission level (default is "active").
        """
        self.cpu_payer = Account(account, private_key, permission)

    def remove_cpu_payer(self):
        """Remove the CPU payer account."""
        self.cpu_payer = None

    def _build_url(self, endpoint: str) -> str:
        """
        Build the full URL for a given endpoint.

        :param endpoint: The endpoint to append to the base URL.
        :return: The full URL.
        """
        return f"{self.rpc_host}/v1/chain/{endpoint}"

    def _post(self, url: str, post_data: Dict = None) -> requests.Response:
        """
        Make a POST request to the given URL.

        :param url: The URL to post to.
        :param post_data: The data to post.
        :return: The response from the request.
        """
        resp = self.session.post(url, json=post_data)

        if resp.status_code == 500:
            raise TransactionException(f"Transaction error: {resp.text}", resp)

        if resp.status_code >= 300 or resp.status_code < 200:
            raise NodeException(
                f"EOS node error, bad HTTP status code: {resp.status_code}", resp
            )

        return resp

    async def _post_async(self, url: str, post_data: Dict = None) -> Dict:
        """
        Asynchronously make a POST request to the given URL.

        :param url: The URL to post to.
        :param post_data: The data to post.
        :return: The response data as a dictionary.
        """
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=post_data, headers=self.headers) as resp:
                if resp.status >= 203:
                    if resp.status == 500:
                        raise TransactionException(
                            f"Transaction error: {await resp.json()}", resp
                        )

                    raise NodeException(
                        f"EOS node error, bad HTTP status code: {resp.status}",
                        resp,
                    )
                return await resp.json()

    def abi_json_to_bin(self, code: str, action: str, args: Dict) -> bytes:
        """
        Convert ABI JSON to binary format.

        :param code: The contract code.
        :param action: The action name.
        :param args: The arguments for the action.
        :return: The binary arguments.
        """
        url = self._build_url("abi_json_to_bin")
        post_data = {"code": code, "action": action, "args": args}
        resp = self._post(url, post_data)
        binargs = resp.json().get("binargs")
        if binargs is None:
            raise NodeException("EOS node error, 'binargs' not found", resp)
        return bytes.fromhex(binargs)

    async def abi_json_to_bin_async(self, code: str, action: str, args: Dict) -> bytes:
        """
        Asynchronously convert ABI JSON to binary format.

        :param code: The contract code.
        :param action: The action name.
        :param args: The arguments for the action.
        :return: The binary arguments.
        """

        if self._abi_cache.get(code) is None:
            url = self._build_url("get_abi")
            post_data = {"account_name": code}
            resp_json = await self._post_async(url, post_data)
            abi = Abi(code, **resp_json.get("abi"))
            self._abi_cache[code] = abi
        else:
            abi = self._abi_cache.get(code)

        actions = abi.get_action(action)
        binargs = abi.serialize(actions, args)

        if binargs is None:
            raise NodeException("EOS node error, 'binargs' not found", None)
        return binargs

    def get_info(self) -> Dict:
        """
        Retrieve blockchain information.

        :return: A dictionary containing blockchain information.
        """
        url = self._build_url("get_info")
        resp = self._post(url)
        return resp.json()

    async def get_info_async(self) -> Dict:
        """
        Asynchronously retrieve blockchain information.

        :return: A dictionary containing blockchain information.
        """
        url = self._build_url("get_info")
        return await self._post_async(url)

    def post_transaction(
        self,
        trx: Transaction,
        compression: bool = False,
        packed_context_free_data: str = "",
    ) -> Dict:
        """
        Post a transaction to the blockchain.

        :param trx: The transaction to post.
        :param compression: Whether to use compression.
        :param packed_context_free_data: Packed context-free data.
        :return: A dictionary with the result of the transaction.
        """
        url = self._build_url("push_transaction")
        post_data = {
            "signatures": trx.signatures,
            "compression": compression,
            "packed_context_free_data": packed_context_free_data,
            "packed_trx": trx.pack().hex(),
        }
        resp = self._post(url, post_data)
        return resp.json()

    async def post_transaction_async(
        self,
        trx: Transaction,
        compression: bool = False,
        packed_context_free_data: str = "",
    ) -> Dict:
        """
        Post a transaction to the blockchain.

        :param trx: The transaction to post.
        :param compression: Whether to use compression.
        :param packed_context_free_data: Packed context-free data.
        :return: A dictionary with the result of the transaction.
        """
        url = self._build_url("push_transaction")
        post_data = {
            "signatures": trx.signatures,
            "compression": compression,
            "packed_context_free_data": packed_context_free_data,
            "packed_trx": trx.pack().hex(),
        }
        resp = await self._post_async(url, post_data)
        return resp

    def get_table_rows(self, post_data: Dict) -> Dict:
        """
        Retrieve table rows from a smart contract.

        :param post_data: The data to post.
        :return: A dictionary with the table rows.
        """
        url = self._build_url("get_table_rows")
        resp = self._post(url, post_data)
        return resp.json()

    def _prepare_transaction(
        self, trx: Dict, cpu_usage: int = 1
    ) -> tuple[Transaction, list]:
        """
        Prepare a transaction for signing and sending.

        :param trx: The transaction data.
        :param cpu_usage: The CPU usage for the transaction.
        :return: The prepared transaction.
        """
        if self.cpu_payer:
            trx["actions"][0]["authorization"].insert(
                0,
                {
                    "actor": self.cpu_payer.account,
                    "permission": self.cpu_payer.permission,
                },
            )

        actors = []
        actions = []
        for item in trx["actions"]:
            authorization = []
            for auth in item["authorization"]:
                authorization.append(
                    Authorization(actor=auth["actor"], permission=auth["permission"])
                )
                actor_permission = f"{auth['actor']}-{auth['permission']}"
                if actor_permission not in actors:
                    actors.append(actor_permission)
            actions.append(
                Action(
                    account=item["account"],
                    name=item["name"],
                    authorization=authorization,
                    data=item["data"],
                )
            )
        trx = Transaction(actions=actions)
        trx.max_cpu_usage_ms = cpu_usage
        return trx, actors

    def make_transaction(self, trx: Dict, cpu_usage: int = 1) -> Transaction:
        """
        Create a transaction.

        :param trx: The transaction data.
        :param cpu_usage: The CPU usage for the transaction.
        :return: The created transaction.
        """
        trx, actors = self._prepare_transaction(trx, cpu_usage)

        for item in trx.actions:
            binargs = self.abi_json_to_bin(item.account, item.name, item.data)
            item.link(binargs)

        net_info = self.get_info()
        trx.link(net_info["last_irreversible_block_id"], net_info["chain_id"])

        signed_keys = []
        for actor_permission in actors:
            if actor_permission in self.accounts:
                private_key = self.accounts[actor_permission].private_key
            elif self.cpu_payer and actor_permission == self.cpu_payer.index():
                private_key = self.cpu_payer.private_key
            else:
                continue
            if private_key not in signed_keys:
                trx.sign(private_key)
                signed_keys.append(private_key)

        return trx

    async def make_transaction_async(
        self, trx: Dict, cpu_usage: int = 1
    ) -> Transaction:
        """
        Asynchronously create a transaction.

        :param trx: The transaction data.
        :param cpu_usage: The CPU usage for the transaction.
        :return: The created transaction.
        """
        trx, actors = self._prepare_transaction(trx, cpu_usage)

        for item in trx.actions:
            binargs = await self.abi_json_to_bin_async(
                item.account, item.name, item.data
            )
            item.link(binargs)

        net_info = await self.get_info_async()
        trx.link(net_info["last_irreversible_block_id"], net_info["chain_id"])

        signed_keys = []
        for actor_permission in actors:
            if actor_permission in self.accounts:
                private_key = self.accounts[actor_permission].private_key
            elif self.cpu_payer and actor_permission == self.cpu_payer.index():
                private_key = self.cpu_payer.private_key
            else:
                continue
            if private_key not in signed_keys:
                trx.sign(private_key)
                signed_keys.append(private_key)

        return trx

    def push_transaction(
        self,
        trx: Union[Dict, Transaction],
        extra_signatures: Union[str, List[str]] = None,
    ) -> Dict:
        """
        Push a transaction to the blockchain.

        :param trx: The transaction to push.
        :param extra_signatures: Any extra signatures to add to the transaction.
        :return: The result of the transaction.
        """
        if isinstance(trx, dict):
            trx = self.make_transaction(trx)
        if extra_signatures:
            if isinstance(extra_signatures, str):
                extra_signatures = [extra_signatures]
            for item in extra_signatures:
                if item not in trx.signatures:
                    trx.signatures.append(item)

        print(f"{trx=}")

        return self.post_transaction(trx)

    async def push_transaction_async(
        self,
        trx: Union[Dict, Transaction],
        extra_signatures: Union[str, List[str]] = None,
    ) -> Dict:
        """
        Push a transaction to the blockchain.

        :param trx: The transaction to push.
        :param extra_signatures: Any extra signatures to add to the transaction.
        :return: The result of the transaction.
        """
        if isinstance(trx, dict):
            trx = await self.make_transaction_async(trx)
        if extra_signatures:
            if isinstance(extra_signatures, str):
                extra_signatures = [extra_signatures]
            for item in extra_signatures:
                if item not in trx.signatures:
                    trx.signatures.append(item)

        return await self.post_transaction_async(trx)
