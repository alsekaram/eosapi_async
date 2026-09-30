import pytest
from antelopy.exceptions.exceptions import SerializationError

from eosapi.abi import Abi
from conftest import PRIVATE_KEY, arun

# Shape of m.federation::mine: nonce is `bytes`, sent as a hex string
MINE_ABI = {
    "version": "eosio::abi/1.1",
    "types": [{"new_type_name": "nonce_t", "type": "bytes"}],
    "structs": [
        {
            "name": "mine",
            "base": "",
            "fields": [
                {"name": "miner", "type": "name"},
                {"name": "nonce", "type": "bytes"},
            ],
        },
        {
            "name": "many",
            "base": "",
            "fields": [
                {"name": "nonces", "type": "bytes[]"},
                {"name": "alias", "type": "nonce_t"},
            ],
        },
    ],
    "actions": [
        {"name": "mine", "type": "mine", "ricardian_contract": ""},
        {"name": "many", "type": "many", "ricardian_contract": ""},
    ],
}
ALICE = "0000000000855c34"  # name "alice", little-endian uint64


@pytest.fixture
def abi():
    return Abi("m.federation", **MINE_ABI)


def serialize(abi, action, data):
    return abi.serialize(abi.get_action(action), data).hex()


def test_bytes_from_hex_string(abi):
    packed = serialize(abi, "mine", {"miner": "alice", "nonce": "a1b2c3d4e5f60718"})
    assert packed == ALICE + "08" + "a1b2c3d4e5f60718"


def test_bytes_from_bytes(abi):
    nonce = bytes.fromhex("a1b2c3d4e5f60718")
    assert serialize(abi, "mine", {"miner": "alice", "nonce": nonce}) == serialize(
        abi, "mine", {"miner": "alice", "nonce": nonce.hex()}
    )


def test_empty_bytes(abi):
    assert serialize(abi, "mine", {"miner": "alice", "nonce": ""}) == ALICE + "00"


def test_bytes_list_and_alias(abi):
    packed = serialize(abi, "many", {"nonces": ["aa", b"\xbb\xcc"], "alias": "dd"})
    assert packed == "02" + "01aa" + "02bbcc" + "01dd"


def test_invalid_hex_raises_serialization_error(abi):
    with pytest.raises(SerializationError, match="nonce of type bytes"):
        serialize(abi, "mine", {"miner": "alice", "nonce": "not hex"})


def test_mine_transaction_async(servers):
    from eosapi import EosApi

    api = EosApi(rpc_host=servers.node_url)
    api.set_abi("m.federation", MINE_ABI)
    api.import_key("alice", PRIVATE_KEY)
    trx = {
        "actions": [
            {
                "account": "m.federation",
                "name": "mine",
                "authorization": [{"actor": "alice", "permission": "active"}],
                "data": {"miner": "alice", "nonce": "a1b2c3d4e5f60718"},
            }
        ]
    }
    result = arun(api, lambda: api.push_transaction_async(trx))
    assert result == {"transaction_id": "abc"}
