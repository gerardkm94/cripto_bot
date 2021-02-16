from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json


class CoinMarketApi:

    def __init__(self) -> None:
        self.url = 'https://min-api.cryptocompare.com/data/pricemulti?fsyms='
        self.session = Session()
        self.pairs = []
        self.criptos = {}

    def get_prices(self):

        try:
            str_pairs = ','.join(self.pairs)
            prices = json.loads(self.session.get(
                f'{self.url}{str_pairs}&tsyms=EUR').text)

            return prices

        except (ConnectionError, Timeout, TooManyRedirects) as e:
            print(e)
            return None

    def get_notifications(self):

        if not self.pairs:
            return None

        prices = self.get_prices()

        if not prices:
            return None

        messages = []

        for coin in self.pairs:
            if self.criptos.get(coin)[1] == 'comprar':
                if prices.get(coin).get('EUR') <= self.criptos.get(coin)[0]:
                    messages.append(f'Momento de comprar {coin}')
            else:
                if prices.get(coin).get('EUR') >= self.criptos.get(coin)[0]:
                    messages.append(f'Momento de vender {coin}')

        return messages
