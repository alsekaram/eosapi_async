import datetime
import hashlib
import json
import random
from pathlib import Path

import pytest
from cryptos import N, decode_privkey, encode_privkey

import eosapi.packer as packer
from eosapi import Account, Action, Authorization, Transaction
from eosapi.packer import RipemdHasher, Time, ecdsa_sign_canonical

# Signatures made by eosapi 2.2.0 (pure Python ECDSA) for vectors() below
REFERENCE = json.loads(
    (Path(__file__).parent / "data" / "signatures_2_2_0.json").read_text()
)


def vectors(n=300, seed=42):
    rnd = random.Random(seed)
    out = []
    for i in range(n):
        fmt = "wif" if i % 5 else "wif_compressed"
        key = encode_privkey(rnd.randrange(1, N), fmt)
        binargs = rnd.randbytes(rnd.randrange(0, 200))
        trx = Transaction(
            actions=[
                Action(
                    "eosio.token",
                    "transfer",
                    [Authorization("alice")],
                    binargs=binargs,
                )
            ]
        )
        trx.chain_id = "1064487b3cd1a897ce03ae5b6a865651747e2e152090f99c1d19d44e01aea5a4"
        trx.ref_block_num = rnd.randrange(65536)
        trx.ref_block_prefix = rnd.randrange(2**32)
        trx.expiration = datetime.datetime(2026, 1, 1) + datetime.timedelta(seconds=i)
        out.append((key, trx))
    return out


def sign_all(n=300):
    signatures = []
    for key, trx in vectors(n):
        trx.sign(key)
        signatures.append(trx.signatures[0])
    return signatures


def test_signatures_match_2_2_0():
    # with coincurve if installed, else the pure Python path
    assert sign_all() == REFERENCE


def test_pure_python_fallback_matches_2_2_0(monkeypatch):
    monkeypatch.setattr(packer, "_Secp256k1PublicKey", None)
    assert sign_all(50) == REFERENCE[:50]


def test_signatures_recover_to_signer():
    coincurve = pytest.importorskip("coincurve")
    for key, trx in vectors(50):
        mbytes = bytes.fromhex(trx.chain_id) + trx.pack() + b"\x00" * 32
        msghash = hashlib.sha256(mbytes).digest()
        sig = ecdsa_sign_canonical(msghash, key)
        recid = (sig[0] - 27) & 3
        recovered = coincurve.PublicKey.from_signature_and_message(
            sig[1:] + bytes([recid]), msghash, hasher=None
        )
        secret = decode_privkey(key).to_bytes(32, "big")
        signer = coincurve.PrivateKey(secret).public_key
        assert recovered.format() == signer.format()


def test_ripemd160_without_hashlib_support(monkeypatch):
    # OpenSSL 3.0.0-3.0.6 has no RIPEMD160 in hashlib
    real_new = hashlib.new

    def new(name, *args, **kwargs):
        if name.lower() == "ripemd160":
            raise ValueError("unsupported hash type ripemd160")
        return real_new(name, *args, **kwargs)

    monkeypatch.setattr(hashlib, "new", new)
    monkeypatch.setattr(RipemdHasher, "_hasher", None)
    assert sign_all(20) == REFERENCE[:20]
    assert RipemdHasher._hasher.__name__ == "crypto_ripemd"


def test_account_repr_hides_private_key():
    account = Account("alice", "5Ksecret")
    assert "5Ksecret" not in repr(account)


def test_time_roundtrip_is_naive_utc():
    moment = datetime.datetime(2026, 9, 30, 12, 0, 0)
    assert Time.unpack(Time.pack(moment)) == moment


def test_link_sets_naive_utc_expiration():
    trx = Transaction(actions=[])
    trx.link("0a1b2c3d" * 8, "00" * 32)
    now = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
    assert trx.expiration.tzinfo is None
    assert abs((trx.expiration - now).total_seconds() - 300) < 5
