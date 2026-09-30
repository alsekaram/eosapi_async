# eosapi
![version](https://img.shields.io/badge/version-2.2.1-blue)
![license](https://img.shields.io/badge/license-MIT-brightgreen)
![python_version](https://img.shields.io/badge/python-%3E%3D%203.12-brightgreen)
[![](https://img.shields.io/badge/github-@alsekaram-red)](https://github.com/alsekaram)

A simple, high-level and lightweight eosio sdk write by python
with async features developed by alsekaram.

# What is it?
eosapi is a python library to interact with EOSIO blockchains.

its main focus are bot applications on the blockchain.

In version 2.0.0:
- Complete rework with modern Python support
- Enhanced async implementation
- Performance optimizations and improved error handling
- Support for Antelope's Leap 3.1 (modified abi_json_to_bin methods)
- Proxy support functionality
- Custom headers for Alien Worlds interaction
- Cache implementation for get_info and get_info_async
- Updated RPC host conditions for Alien Worlds platform

In version 2.0.2:
Added new dependencies: cryptos, base58, cachetools, pydantic, and antelopy.

In version 2.0.3:
Add `cpu_usage` parameter to `push_transaction_async`
This change introduces an optional `cpu_usage` parameter to the `push_transaction_async` method, defaulting to 1. 
It is also passed to the `make_transaction_async` function to allow more control over CPU resource allocation.

In version 2.1.0:
- Implemented shared HTTP session for asynchronous requests
- Added connection pooling and reuse, significantly reducing request latency (3-5x faster for multiple requests)
- Improved resource usage through TCP/TLS connection reuse
- Enhanced performance for high-frequency API interactions

In version 2.1.1:
- Fixed RIPEMD160 compatibility issues by adding support for pycryptodome
- Improved cross-platform compatibility for cryptographic operations
- Enhanced error handling for hash algorithms

In version 2.2.0 (security fixes):
- The sync client now really uses the configured proxy (it was silently bypassed before, exposing the real IP)
- New `expected_chain_id` parameter: transactions are signed only if the node reports this chain id
- New `set_abi(code, abi)` method to use a trusted local ABI instead of the one served by the node
- `rpc_host` must be an `http(s)` URL; plain HTTP to a non-local host emits a warning
- Private keys are no longer shown in `repr(Account)`
- Async requests now raise `NodeException` on any non-2xx response (like the sync ones) instead of returning the error body; request data is no longer logged
- Raised minimum versions: `aiohttp>=3.12.14`, `requests>=2.32.4`, `pycryptodome>=3.19.1`

In version 2.2.1:
- Restored the pre-2.2.0 behavior of async requests: a non-2xx, non-500 node response returns the error body again instead of raising, now with a `FutureWarning`. `NodeException` is not a subclass of `TransactionException`, so code catching only `TransactionException` broke in 2.2.0
- New `raise_on_node_error` parameter: `True` raises `NodeException` (the 3.0 default), `False` keeps returning the error body without a warning
- `proxy` now applies to async requests too (before, they ignored it and went out directly). The `yeomen_proxy` parameter was removed: passing it raises `TypeError`
- Transaction signing is about 27x faster with the optional `fast` extra (`pip install "eosapi-async[fast]"`): the elliptic curve multiplication runs in C via `coincurve` (libsecp256k1). Without it the pure Python path is used, as before. Signatures are byte-for-byte the same either way. The private key is now parsed once per signature
- Async requests work across event loops: a second `asyncio.run()` no longer fails with `Event loop is closed`. New `await api.close()` and `async with EosApi(...) as api` close the shared aiohttp session
- `timeout` now applies to async requests too (before, aiohttp's 5 minute default was used)
- With a CPU payer set, the transaction dict passed in is no longer modified, so pushing the same dict again works
- A failed `get_info` in async code is no longer cached for 5 minutes, and a bad `get_info` response raises `NodeException` instead of `KeyError`
- An account without a contract raises `NodeException` ("no ABI for account") instead of `TypeError`
- `push_transaction` accepts `cpu_usage=` like the async version; `push_transaction_async(trx, signatures)` in the sync argument order works, with a `FutureWarning`
- No more `DeprecationWarning` from `datetime.utcnow()` on Python 3.12+
- Dependencies are version ranges instead of exact pins (`pydantic`, `cachetools` and others no longer conflict with your project's versions); `python_requires=">=3.12"` is declared
- Added a test suite: `pip install -e .[test]` and `pytest`

# Install
```$ pip install eosapi-async```

For about 27x faster transaction signing (C implementation via `coincurve`):

```$ pip install "eosapi-async[fast]"```

Without it everything works the same, signing is just slower (~4 ms instead of ~0.16 ms per signature). `coincurve` has no wheel for Python 3.14 yet, so use the plain install there.

# Using
```python
import asyncio
from eosapi import EosApi


account_name = "consumer1111"
private_key = "you_key"


async def main() -> None:

    # WAX mainnet chain id: refuse to sign for any other chain
    wax_api = EosApi(
        expected_chain_id="1064487b3cd1a897ce03ae5b6a865651747e2e152090f99c1d19d44e01aea5a4"
    )
    wax_api.import_key(account_name, private_key)

    print(await wax_api.get_info_async())
    trx = {
        "actions": [
            {
                "account": "eosio.token",
                "name": "transfer",
                "authorization": [
                    {
                        "actor": account_name,
                        "permission": "active",
                    },
                ],
                "data": {
                    "from": account_name,
                    "to": "pink.gg",
                    "quantity": "0.00000001 WAX",
                    "memo": "by eosapi_async",
                },
            }
        ]
    }
    resp = await wax_api.push_transaction_async(trx)
    print(resp)


if __name__ == "__main__":
    asyncio.run(main())

```
