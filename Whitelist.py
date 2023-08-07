from requests import Session
from time import sleep, time
from sys import stderr
from pyuseragents import random as random_ua
from config import Token, Chain
from json import loads
from loguru import logger


logger.remove()
logger.add(stderr,
           format="<white>{time:HH:mm:ss:SSS}</white> | <level>{level: <8}</level> | <level>{message}</level>")


def wallet():
    with open('wallet.txt', 'r') as file:
        file = file.read().splitlines()
        return [address.replace(",", "").replace(";", "") for address in file]


def check_whitelist(session: Session, chain_id: str, sub_id: int) -> list:
    response = session.get(f'https://www.okx.com/v2/asset/withdraw/address-by-type?t={int(time() * 1000)}&type=0&'
                           f'currencyId={chain_id}')
    response = loads(response.text)
    response_address = response['data']['addressList']
    list_address = []
    for data in response_address:
        if data['subCurrencyId'] == sub_id:
            list_address.append(data['address'].lower())
    add_wallet = []
    addresses = wallet()
    for address in addresses:
        if address.lower() not in list_address:
            add_wallet.append(address)
    return add_wallet


def add_whitelist(chain: str) -> None:
    session = Session()
    session.headers.update({
        'user-agent': random_ua(),
        'authorization': Token,
    })
    chain_id = {'polygon': "1696", 'zksync': '2', 'ethereum': '2', 'arbitrum': '2', 'optimism': '2', 'core': '2806',
                'fantom': "307", 'avalanche': '1532', 'bsc': '1896'}
    chain_id_sub = {'zksync': 409517, 'avalanche': 1790, 'polygon': 1787, 'arbitrum': 1917, 'optimism': 1999,
                    'fantom': 1782, 'ethereum': 2, 'core': 2806, 'bsc': 1896}

    addresses = check_whitelist(session, chain_id[chain], chain_id_sub[chain])
    x = lambda a: a // -20 * -1

    if addresses:
        completed = []
        for i in range(x(len(addresses))):
            start = i * 20
            end = (i + 1) * 20 if (i + 1) * 20 < len(addresses) else 0
            if end:
                addresses_input = addresses[start:end]
            else:
                addresses_input = addresses[start:]
            json_data = {
                'chooseChain': True,
                'formGroupIndexes': [i for i in range(len(addresses_input))],
                'authFlag': True,
                'subCurrencyId': chain_id_sub[chain],
                'generalType': 1,
                'targetType': -1,
                'currencyId': str(chain_id[chain]),
                'addressInfoList': [{'address': adr, 'validateName': f'addressInfoList.{i}.address'}for i, adr
                                    in enumerate(addresses_input)],
                'includeAuth': True,
                'validateOnly': True,
            }

            r = session.post(
                f'https://www.okx.com/v2/asset/withdraw/addressBatch?t={int(time() * 1000)}', json=json_data)
            try:
                response = loads(r.text)
                if response["error_code"] == '0':
                    logger.success(f'Эмайл код отправлен')
                else:
                    logger.error(f'{r.text}')
            except BaseException as error:
                logger.error(f'response : {r.text}')
                logger.error(f'error: {error}')
            sleep(1)

            session.get(f"https://www.okx.com/v2/asset/withdraw/add/address/sendEmailCode?t={int(time() * 1000)}&addressStr="
                        f"{','.join(addresses_input)}&includeAuth=true")
            sleep(5)
            json_data_end = json_data.copy()
            json_data_end['validateOnly'] = False
            json_data_end['_allow'] = True
            json_data_end['emailCode'] = input('Email code: ')
            json_data_end['totpCode'] = input('Google auth: ')

            r = session.post(
                f'https://www.okx.com/v2/asset/withdraw/addressBatch?t={int(time() * 1000)}', json=json_data_end)
            try:
                response = loads(r.text)
                if response["error_code"] == '0':
                    logger.success(f'Добавлены адреса: {"; ".join(addresses_input)}')
                    completed += addresses_input
                    logger.success(f'{len(completed)} / {len(addresses)}')
                    sleep(1)
                    if len(completed) != len(addresses):
                        input("Для дальнейшей раюоты нажми Enter")

                else:
                    logger.error(f'{r.text}')
            except BaseException as error:
                logger.error(f'response : {r.text}')
                logger.error(f'error: {error}')
    else:
        logger.success('Все адреса уже были в вайтлисте')


if __name__ == '__main__':
    add_whitelist(Chain)
