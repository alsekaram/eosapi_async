import asyncio
from eosapi import EosApi


account_name = "consumer1111"
private_key = "You_key_here"


async def main() -> None:

    wax_api = EosApi(timeout=60)
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
    trx = await wax_api.make_transaction_async(trx)
    packed_trx = list(trx.pack())
    print("packed_trx: {0}".format(packed_trx))

    trx_2 = {
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
                    "quantity": "0.00000002 WAX",
                    "memo": "by eosapi_async",
                },
            }
        ]
    }

    resp = await wax_api.push_transaction_async(trx_2)
    print(resp)


if __name__ == "__main__":
    asyncio.run(main())
