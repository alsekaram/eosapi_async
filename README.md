# eosapi
![version](https://img.shields.io/badge/version-1.0.0-blue)
![license](https://img.shields.io/badge/license-MIT-brightgreen)
![python_version](https://img.shields.io/badge/python-%3E%3D%203.6-brightgreen)
![coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)
[![](https://img.shields.io/badge/blog-@encoderlee-red)](https://encoderlee.blog.csdn.net)
[![](https://img.shields.io/badge/github-@i--am--Vasya-red)](https://github.com/i-am-Vasya)

A simple, high-level and lightweight eosio sdk write by python
with async features developed by i-am-Vasya.

# What is it?
eosapi is a python library to interact with EOSIO blockchains.

its main focus are bot applications on the blockchain.

# Install
```$ pip install eosapi_async```

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
