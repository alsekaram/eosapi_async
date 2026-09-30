from typing import Callable, Optional, ClassVar

import struct
import calendar
import datetime
from .exceptions import EosApiException
import re
from typing import List, Tuple
import hashlib
from Crypto.Hash import RIPEMD160
from cryptos import (
    hash_to_int,
    encode_privkey,
    decode,
    encode,
    hmac,
    fast_multiply,
    G,
    inv,
    N,
    decode_privkey,
    get_privkey_format,
)

try:
    from coincurve import PublicKey as _Secp256k1PublicKey
except ImportError:  # the optional "fast" extra is not installed: pure Python
    _Secp256k1PublicKey = None


class EosType:
    size: int = None
    fmt: str = None

    @classmethod
    def pack(cls, value: int) -> bytes:
        return struct.pack(cls.fmt, value)

    @classmethod
    def unpack(cls, value: bytes) -> int:
        return struct.unpack(cls.fmt, value[: cls.size])[0]

    @classmethod
    def pack_array(cls, items: list) -> bytes:
        mbytes = b""
        mbytes += VarUint32.pack(len(items))
        for item in items:
            mbytes += cls.pack(item)
        return mbytes

    @classmethod
    def unpack_array(cls, packed_bytes: bytes) -> List:
        size, array_len = VarUint32.unpack(packed_bytes)
        packed_bytes = packed_bytes[size:]
        values = []
        for i in range(0, array_len):
            value = cls.unpack(packed_bytes)
            values.append(value)
            packed_bytes = packed_bytes[cls.size :]
        return values


class Bytes(EosType):

    @classmethod
    def pack(cls, value: bytes) -> bytes:
        return value

    @classmethod
    def unpack(cls, value: bytes) -> bytes:
        return value


class Time(EosType):
    size = 4

    @classmethod
    def pack(cls, value: datetime.datetime) -> bytes:
        seconds = calendar.timegm(value.timetuple())
        return Uint32.pack(seconds)

    @classmethod
    def unpack(cls, value: bytes) -> datetime.datetime:
        seconds = Uint32.unpack(value)
        utc = datetime.datetime.fromtimestamp(seconds, datetime.UTC)
        return utc.replace(tzinfo=None)


class Name(EosType):
    size = 8

    @classmethod
    def pack(cls, value: str) -> bytes:
        if len(value) > 13 or not re.match(r"^[\.a-z1-5]*[a-z1-5]+[\.a-z1-5]*$", value):
            raise EosApiException("invalid name")
        value_uint64 = string_to_uint64(value)
        return Uint64.pack(value_uint64)

    @classmethod
    def unpack(cls, value: bytes) -> str:
        value_uint64 = Uint64.unpack(value)
        return uint64_to_string(value_uint64)


class Int8(EosType):
    size = 1
    fmt = "<b"


class Uint8(EosType):
    size = 1
    fmt = "<B"


class Uint16(EosType):
    size = 2
    fmt = "<H"


class Uint32(EosType):
    size = 4
    fmt = "<I"


class Uint64(EosType):
    size = 8
    fmt = "<Q"


class VarUint32(EosType):

    @classmethod
    def pack(cls, value: int) -> bytes:
        mbytes = b""
        val = value
        while True:
            b = val & 0x7F
            val >>= 7
            b |= (val > 0) << 7
            uint8 = Uint8.pack(b)
            mbytes += bytes(uint8)
            if not val:
                break
        return mbytes

    @classmethod
    def unpack(value: bytes) -> Tuple[int, int]:
        offset = 0
        value = 0
        size = 0
        for n, byte in enumerate(value):
            # only the 7 first bits matter
            partial_value = byte & 0x7F
            partial_value_offset = partial_value << offset
            value |= partial_value_offset
            offset += 7
            size = n
            if n >= 8:
                break
            # first bit (carry) off
            if not byte & 0x80:
                break
        return size, value


def string_to_uint64(s: str):
    if len(s) > 13:
        raise EosApiException("invalid string length")
    name = 0
    for i in range(0, min(len(s), 12)):
        name |= (char_to_symbol(ord(s[i])) & 0x1F) << (64 - 5 * (i + 1))
    if len(s) == 13:
        name |= char_to_symbol(ord(s[12])) & 0x0F
    return name


def uint64_to_string(n, strip_dots=False):
    charmap = ".12345abcdefghijklmnopqrstuvwxyz"
    s = bytearray(13 * b".")
    tmp = n
    for i in range(0, 13):
        c = charmap[tmp & (0x0F if i == 0 else 0x1F)]
        s[12 - i] = ord(c)
        tmp >>= 4 if i == 0 else 5
    s = s.decode("utf8")
    if strip_dots:
        s = s.strip(".")
    return s


def char_to_symbol(c):
    if ord("a") <= c <= ord("z"):
        return (c - ord("a")) + 6
    if ord("1") <= c <= ord("5"):
        return (c - ord("1")) + 1
    return 0


def endian_reverse_u32(x):
    x = x & 0xFFFFFFFF
    return (
        ((x >> 0x18) & 0xFF)
        | (((x >> 0x10) & 0xFF) << 0x08)
        | (((x >> 0x08) & 0xFF) << 0x10)
        | (((x) & 0xFF) << 0x18)
    )


def get_tapos_info(block_id):
    block_id_bin = bytes.fromhex(block_id)

    hash0 = struct.unpack("<Q", block_id_bin[0:8])[0]
    hash1 = struct.unpack("<Q", block_id_bin[8:16])[0]

    ref_block_num = endian_reverse_u32(hash0) & 0xFFFF
    ref_block_prefix = hash1 & 0xFFFFFFFF

    return ref_block_num, ref_block_prefix


def _decode_signing_key(priv) -> Tuple[int, bytes, bool]:
    """Parse a private key once: (secret, 32-byte secret, is compressed)."""
    secret = decode_privkey(priv)
    compressed = "compressed" in get_privkey_format(priv)
    return secret, secret.to_bytes(32, "big"), compressed


# Built-in int <-> bytes below: cryptos' encode/decode/inv are pure Python
# and were most of the signing time once k·G moved to C.
def _generate_k(z: int, secret_bin: bytes, nonce: int) -> int:
    v = b"\x01" * 32
    k = b"\x00" * 32
    zn = z + nonce
    msghash = zn.to_bytes(max(32, (zn.bit_length() + 7) // 8), "big")
    k = hmac.new(k, v + b"\x00" + secret_bin + msghash, hashlib.sha256).digest()
    v = hmac.new(k, v, hashlib.sha256).digest()
    k = hmac.new(k, v + b"\x01" + secret_bin + msghash, hashlib.sha256).digest()
    v = hmac.new(k, v, hashlib.sha256).digest()
    return int.from_bytes(hmac.new(k, v, hashlib.sha256).digest(), "big")


def deterministic_generate_k_nonce(msghash, priv, nonce):
    return _generate_k(hash_to_int(msghash), encode_privkey(priv, "bin"), nonce)


def _multiply_g(k: int) -> Tuple[int, int]:
    """k·G on secp256k1: in C via libsecp256k1 when coincurve is installed."""
    if _Secp256k1PublicKey is None:
        return fast_multiply(G, k)
    return _Secp256k1PublicKey.from_secret((k % N).to_bytes(32, "big")).point()


def _sign(z: int, key: Tuple[int, bytes, bool], nonce: int):
    secret, secret_bin, compressed = key
    k = _generate_k(z, secret_bin, nonce)

    r, y = _multiply_g(k)
    s = pow(k, -1, N) * (z + r * secret) % N

    v, r, s = 27 + ((y % 2) ^ (0 if s * 2 < N else 1)), r, s if s * 2 < N else N - s
    if compressed:
        v += 4
    return v, r, s


def ecdsa_raw_sign_nonce(msghash, priv, nonce):
    return _sign(hash_to_int(msghash), _decode_signing_key(priv), nonce)


def ecdsa_sign_canonical(msghash: bytes, priv) -> bytes:
    """Sign a 32-byte digest as v || r || s, retrying with the next nonce
    until the signature is canonical, as EOS requires."""
    z = int.from_bytes(msghash, "big")
    key = _decode_signing_key(priv)
    nonce = 0
    while True:
        v, r, s = _sign(z, key, nonce)
        signature = v.to_bytes(1, "big") + r.to_bytes(32, "big") + s.to_bytes(32, "big")
        if is_canonical(signature):
            return signature
        nonce += 1


# like https://github.com/EOSIO/eosjs-ecc/commit/09c823ac4c4fb4f7257d8ed2df45a34215a8c537#diff-e8c843fd1f732a963ec41decb2e69133R241
def is_canonical(c):
    return (
        not (c[1] & 0x80)
        and not (c[1] == 0 and not (c[2] & 0x80))
        and not (c[33] & 0x80)
        and not (c[33] == 0 and not (c[34] & 0x80))
    )


class RipemdHasher:
    _hasher: ClassVar[Optional[Callable[[bytes], bytes]]] = None

    @classmethod
    def hash(cls, data: bytes) -> bytes:
        if cls._hasher is None:
            cls._determine_hasher()

        return cls._hasher(data)

    @classmethod
    def _determine_hasher(cls) -> None:
        """
        Determines the most suitable RIPEMD-160 implementation.
        Tries to use hashlib first, falls back to Crypto.Hash.RIPEMD160 if not available.
        """
        try:
            test_hash = hashlib.new("ripemd160")
            test_hash.update(b"test")
            test_hash.digest()

            def hashlib_ripemd(data: bytes) -> bytes:
                h = hashlib.new("ripemd160")
                h.update(data)
                return h.digest()

            cls._hasher = hashlib_ripemd

        except (ValueError, ImportError):

            def crypto_ripemd(data: bytes) -> bytes:
                h = RIPEMD160.new()
                h.update(data)
                return h.digest()

            cls._hasher = crypto_ripemd


def ripemd160(data: bytes) -> bytes:
    return RipemdHasher.hash(data)
