# eosapi
![version](https://img.shields.io/badge/version-2.0.1-blue)
![license](https://img.shields.io/badge/license-MIT-brightgreen)
![python_version](https://img.shields.io/badge/python-%3E%3D%203.12-brightgreen)
![coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)
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



# Install
```$ pip install eosapi-async```

# Using
```python
import asyncio
from eosapi import EosApi


account_name = "consumer1111"
private_key = "you_key"


async def main() -> None:

    wax_api = EosApi()
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
