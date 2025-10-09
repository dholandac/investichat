from typing import Dict, List, Optional
from datetime import datetime
import requests


class StockQuote:
    # Representa uma cotação de ativo individual (mapeada a partir do Finnhub /quote).

    def __init__(self, symbol: str, data: Dict):
        self.symbol = symbol or ''
        # Finnhub: c (current), d (change), dp (percent), h (high), l (low), o (open), pc (previous close), t (timestamp)
        self.open_price = float(data.get('o') or 0)
        self.high_price = float(data.get('h') or 0)
        self.low_price = float(data.get('l') or 0)
        self.current_price = float(data.get('c') or 0)
        self.volume = 0  # Finnhub /quote não retorna volume; manter 0 para compatibilidade
        ts = data.get('t')
        self.latest_trading_day = (
            datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d') if ts else ''
        )
        self.previous_close = float(data.get('pc') or 0)
        self.change = float(data.get('d') or (self.current_price - self.previous_close))
        dp = data.get('dp')
        # Monta percentual como string com % no final para compatibilidade
        if dp is None and self.previous_close:
            dp = (self.change / self.previous_close) * 100
        self.change_percent = f"{dp:.2f}%" if dp is not None else '0%'

    def to_dict(self) -> Dict:
        return {
            'symbol': self.symbol,
            'open_price': self.open_price,
            'high_price': self.high_price,
            'low_price': self.low_price,
            'current_price': self.current_price,
            'volume': self.volume,
            'latest_trading_day': self.latest_trading_day,
            'previous_close': self.previous_close,
            'change': self.change,
            'change_percent': self.change_percent,
        }


class TimeSeriesData:
    """
    Representa um ponto de dados em uma série temporal (mapeada do Finnhub /stock/candle).
    """

    def __init__(self, timestamp: int, open_p: float, high_p: float, low_p: float, close_p: float, volume: int):
        self.timestamp = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        self.open_price = float(open_p)
        self.high_price = float(high_p)
        self.low_price = float(low_p)
        self.close_price = float(close_p)
        self.volume = int(volume)

    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp,
            'open_price': self.open_price,
            'high_price': self.high_price,
            'low_price': self.low_price,
            'close_price': self.close_price,
            'volume': self.volume,
        }


class FinnhubAPIClient:
    """
    Cliente para interagir com a API do Finnhub, mantendo métodos compatíveis.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = 'https://finnhub.io/api/v1'
        self._symbol_cache: Dict[str, str] = {}

    def _get(self, path: str, params: Dict) -> Dict:
        params = {**params, 'token': self.api_key}
        url = f"{self.base_url}{path}"
        resp = requests.get(url, params=params, timeout=10)
        # Tentar extrair mensagem de erro útil
        try:
            resp.raise_for_status()
        except requests.HTTPError as e:
            detail = ''
            try:
                detail = resp.json().get('error', '')
            except Exception:
                detail = resp.text[:200]
            raise requests.HTTPError(f"{e} | Detalhe: {detail}")
        data = resp.json()
        # Finnhub sinaliza erros com mensagem ou campo s != 'ok' em alguns endpoints
        if isinstance(data, dict) and data.get('error'):
            raise ValueError(f"Erro da API Finnhub: {data['error']}")
        return data

    def _search_symbol(self, query: str) -> Optional[str]:
        """
        Busca o símbolo canônico no Finnhub a partir de um texto.
        Cacheia resultados para reduzir chamadas.
        """
        if query in self._symbol_cache:
            return self._symbol_cache[query]
        try:
            data = self._get('/search', {'q': query})
            # Preferir correspondências exatas, depois o primeiro resultado
            result = None
            for item in data.get('result', []):
                if item.get('symbol', '').upper() == query.upper():
                    result = item.get('symbol')
                    break
            if not result and data.get('result'):
                result = data['result'][0].get('symbol')
            if result:
                self._symbol_cache[query] = result
            return result
        except Exception:
            return None

    def get_global_quote(self, symbol: str) -> Optional[StockQuote]:
        # Tenta obter cotação direto; em caso de erro 4xx/zeros, tenta resolver símbolo via /search.
        try:
            data = self._get('/quote', {'symbol': symbol})
            if data and not (data.get('c') in (None, 0) and data.get('pc') in (None, 0)):
                return StockQuote(symbol, data)
        except requests.HTTPError:
            # Tentar resolução de símbolo em caso de 401/403/404
            pass
        except Exception:
            pass

        # Tenta buscar símbolo canônico
        resolved = self._search_symbol(symbol)
        if resolved and resolved != symbol:
            try:
                data = self._get('/quote', {'symbol': resolved})
                if data and not (data.get('c') in (None, 0) and data.get('pc') in (None, 0)):
                    return StockQuote(resolved, data)
            except Exception:
                pass

        # Fallback para cripto: tentar candles de cripto e montar uma "cotação" sintética
        if '-' in symbol or symbol.upper().endswith('USD'):
            synthetic = self._crypto_quote_fallback(symbol)
            if synthetic:
                return synthetic

        # Falhou
        print(f"Erro ao obter cotação (Finnhub) para {symbol}: sem dados ou acesso negado.")
        return None

    def _crypto_quote_fallback(self, symbol: str) -> Optional[StockQuote]:
        """
        Usa /crypto/candle para obter último candle e construir uma StockQuote sintética.
        Aceita formatos como BTC-USD ou BTCUSD.
        """
        try:
            candidates = self._crypto_symbol_candidates(symbol)
            now = int(datetime.utcnow().timestamp())
            _from = now - 60 * 60 * 24
            for inst in candidates:
                data = self._get('/crypto/candle', {
                    'symbol': inst,
                    'resolution': '5',
                    'from': _from,
                    'to': now,
                })
                if isinstance(data, dict) and data.get('s') == 'ok' and data.get('c'):
                    # último candle
                    i = -1
                    close = data['c'][i]
                    open_p = data['o'][i]
                    high = data['h'][i]
                    low = data['l'][i]
                    prev_close = data['c'][i-1] if len(data['c']) > 1 else open_p
                    ts = data['t'][i]
                    quote_data = {
                        'o': open_p,
                        'h': high,
                        'l': low,
                        'c': close,
                        'pc': prev_close,
                        't': ts,
                    }
                    return StockQuote(symbol, quote_data)
        except Exception:
            return None
        return None

    def _crypto_symbol_candidates(self, symbol: str) -> List[str]:
        """
        Gera candidatos de símbolo por exchange para pares populares.
        Exemplos: BTC-USD -> BINANCE:BTCUSDT, COINBASE:BTC-USD, KRAKEN:XBTUSD, BITSTAMP:BTCUSD
        """
        s = symbol.upper()
        if '-' in s:
            base, quote = s.split('-', 1)
        else:
            # separa heurística para ...USD / ...USDT
            if s.endswith('USDT'):
                base, quote = s[:-4], 'USDT'
            elif s.endswith('USD'):
                base, quote = s[:-3], 'USD'
            else:
                base, quote = s, 'USD'

        # Kraken usa XBT em vez de BTC
        kraken_base = 'XBT' if base == 'BTC' else base

        # Binance costuma usar USDT como quote
        binance_pair = f"{base}USDT" if quote == 'USD' else f"{base}{quote}"
        # Outros usam USD direto
        generic_pair = f"{base}{quote}"

        candidates = [
            f"BINANCE:{binance_pair}",
            f"COINBASE:{base}-{quote}",
            f"KRAKEN:{kraken_base}{quote}",
            f"BITSTAMP:{generic_pair}",
            f"BITFINEX:{generic_pair}",
        ]
        # Remover duplicatas mantendo ordem
        seen = set()
        uniq = []
        for c in candidates:
            if c not in seen:
                seen.add(c)
                uniq.append(c)
        return uniq

    def get_time_series_intraday(self, symbol: str, interval: str = '5min') -> List[TimeSeriesData]:
        mapping = {
            '1min': '1',
            '5min': '5',
            '15min': '15',
            '30min': '30',
            '60min': '60',
        }
        resolution = mapping.get(interval, '5')

        # Obter últimos 100 candles
        now = int(datetime.utcnow().timestamp())
        # Janela de ~2 dias para garantir 100 candles em mercados intraday
        _from = now - 60 * 60 * 24 * 3

        try:
            # Tentar ação/índice
            data = self._get('/stock/candle', {
                'symbol': symbol,
                'resolution': resolution,
                'from': _from,
                'to': now,
            })
            ok = isinstance(data, dict) and data.get('s') == 'ok'
        except Exception:
            ok = False
            data = None

        if not ok:
            # Tentar cripto
            try:
                candidates = self._crypto_symbol_candidates(symbol)
                for inst in candidates:
                    data = self._get('/crypto/candle', {
                        'symbol': inst,
                        'resolution': resolution,
                        'from': _from,
                        'to': now,
                    })
                    if isinstance(data, dict) and data.get('s') == 'ok':
                        ok = True
                        break
            except Exception:
                ok = False

        if not ok or not isinstance(data, dict):
            return []

        ts_list: List[TimeSeriesData] = []
        closes = data.get('c', [])
        highs = data.get('h', [])
        lows = data.get('l', [])
        opens = data.get('o', [])
        vols = data.get('v', [])
        times = data.get('t', [])

        for i in range(min(len(times), len(opens), len(highs), len(lows), len(closes), len(vols))):
            ts_list.append(
                TimeSeriesData(times[i], opens[i], highs[i], lows[i], closes[i], vols[i])
            )

        ts_list.sort(key=lambda x: x.timestamp, reverse=True)
        return ts_list
