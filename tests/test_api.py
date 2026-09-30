import asyncio
import copy
import warnings

import pytest

from eosapi import EosApi, EosApiException, NodeException, TransactionException
from conftest import CHAIN_ID, PRIVATE_KEY, TRANSFER_ABI, arun, transfer_trx


def packed_cpu_usage(body):
    # expiration (4) + ref_block_num (2) + ref_block_prefix (4) + net words (1)
    return bytes.fromhex(body["packed_trx"])[11]


def pushed(servers):
    return [body for _, endpoint, body in servers.hits if endpoint == "push_transaction"]


# rpc_host


def test_rpc_host_needs_scheme():
    with pytest.raises(ValueError):
        EosApi(rpc_host="wax.greymass.com")


def test_plain_http_warns_except_loopback():
    with pytest.warns(UserWarning, match="plain HTTP"):
        EosApi(rpc_host="http://wax.greymass.com")
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        EosApi(rpc_host="http://127.0.0.1:8888")
        EosApi(rpc_host="http://localhost:8888")


# node errors


def test_sync_node_errors(api, servers):
    servers.reply("get_info", {"error": "bad"}, status=400)
    with pytest.raises(NodeException):
        api.get_info()
    api.cache.clear()
    servers.reply("get_info", {"error": "bad"}, status=500)
    with pytest.raises(TransactionException):
        api.get_info()


@pytest.mark.parametrize(
    "mode, outcome",
    [(None, "warn"), (False, "return"), (True, "raise")],
)
def test_async_node_error_modes(servers, mode, outcome):
    api = EosApi(rpc_host=servers.node_url, raise_on_node_error=mode)
    servers.reply("get_info", {"error": "bad"}, status=429)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        if outcome == "raise":
            with pytest.raises(NodeException) as exc_info:
                arun(api, api.get_info_async)
            assert exc_info.value.resp.status == 429
        else:
            assert arun(api, api.get_info_async) == {"error": "bad"}
    future = [w for w in caught if issubclass(w.category, FutureWarning)]
    assert len(future) == (1 if outcome == "warn" else 0)


def test_async_500_raises_transaction_exception(servers):
    api = EosApi(rpc_host=servers.node_url, raise_on_node_error=False)
    servers.reply("get_info", {"error": {"what": "boom"}}, status=500)
    with pytest.raises(TransactionException) as exc_info:
        arun(api, api.get_info_async)
    assert exc_info.value.resp == {"error": {"what": "boom"}}


def test_async_get_info_error_is_not_cached(servers):
    api = EosApi(rpc_host=servers.node_url, raise_on_node_error=False)
    api.import_key("alice", PRIVATE_KEY)
    api.set_abi("eosio.token", TRANSFER_ABI)
    servers.reply("get_info", {"error": "overloaded"}, status=503)
    with pytest.raises(NodeException, match="bad get_info response"):
        arun(api, lambda: api.make_transaction_async(transfer_trx()))

    servers.reset()
    trx = arun(api, lambda: api.make_transaction_async(transfer_trx()))
    assert trx.chain_id == CHAIN_ID


# proxy


def test_sync_and_async_use_proxy(servers):
    host, port = servers.urls["proxy"]
    api = EosApi(rpc_host=servers.node_url, proxy=(host, port, 1))
    api.get_info()
    api.cache.clear()
    arun(api, api.get_info_async)
    assert [e for e, _ in servers.hits_of("proxy")] == ["get_info", "get_info"]
    assert servers.hits_of("node") == []


def test_yeomen_proxy_was_removed(servers):
    with pytest.raises(TypeError, match="yeomen_proxy was removed"):
        EosApi(rpc_host=servers.node_url, yeomen_proxy=("127.0.0.1", 1, 1))
    with pytest.raises(TypeError, match="yeomen_proxy was removed"):
        EosApi(servers.node_url, 120, None, ("127.0.0.1", 1, 1))


# aiohttp session


def test_works_across_event_loops(servers):
    api = EosApi(rpc_host=servers.node_url)
    for _ in range(3):
        api.cache.clear()
        assert asyncio.run(api.get_info_async())["chain_id"] == CHAIN_ID
    asyncio.run(api.close())


def test_context_manager_closes_session(servers):
    api = EosApi(rpc_host=servers.node_url)

    async def main():
        async with api:
            await api.get_info_async()
            session = EosApi._global_aio_session
        return session

    assert asyncio.run(main()).closed
    assert EosApi._global_aio_session is None


def test_async_timeout(servers):
    api = EosApi(rpc_host=servers.node_url, timeout=1)
    servers.delay = 3
    with pytest.raises(TimeoutError):
        arun(api, api.get_info_async)


# transactions


def test_cpu_payer_does_not_modify_callers_dict(api, servers):
    api.set_cpu_payer("payer", PRIVATE_KEY)
    trx = transfer_trx()
    original = copy.deepcopy(trx)
    for _ in range(3):
        api.push_transaction(trx)
    assert trx == original
    assert len(pushed(servers)) == 3


def test_chain_id_mismatch_refuses_to_sign(servers):
    api = EosApi(rpc_host=servers.node_url, expected_chain_id="ab" * 32)
    api.set_abi("eosio.token", TRANSFER_ABI)
    api.import_key("alice", PRIVATE_KEY)
    with pytest.raises(EosApiException, match="chain_id mismatch"):
        api.push_transaction(transfer_trx())
    assert pushed(servers) == []


def test_expected_chain_id_is_case_insensitive(servers):
    api = EosApi(rpc_host=servers.node_url, expected_chain_id=CHAIN_ID.upper())
    api.set_abi("eosio.token", TRANSFER_ABI)
    api.import_key("alice", PRIVATE_KEY)
    assert api.push_transaction(transfer_trx()) == {"transaction_id": "abc"}


def test_account_without_contract(servers):
    api = EosApi(rpc_host=servers.node_url)
    servers.reply("get_abi", {"account_name": "nocontract"})
    with pytest.raises(NodeException, match="no ABI for account 'nocontract'"):
        api.abi_json_to_bin("nocontract", "transfer", {})
    with pytest.raises(NodeException, match="no ABI for account 'nocontract'"):
        arun(api, lambda: api.abi_json_to_bin_async("nocontract", "transfer", {}))


def test_sync_push_transaction_cpu_usage(api, servers):
    api.push_transaction(transfer_trx(), cpu_usage=5)
    assert packed_cpu_usage(pushed(servers)[0]) == 5


def test_async_push_accepts_signatures_as_second_argument(api, servers):
    with pytest.warns(FutureWarning, match="extra_signatures="):
        arun(api, lambda: api.push_transaction_async(transfer_trx(), "SIG_K1_extra"))
    body = pushed(servers)[0]
    assert "SIG_K1_extra" in body["signatures"]
    assert packed_cpu_usage(body) == 1


def test_async_push_cpu_usage_positional(api, servers):
    arun(api, lambda: api.push_transaction_async(transfer_trx(), 7))
    assert packed_cpu_usage(pushed(servers)[0]) == 7
