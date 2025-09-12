"""
Módulo para interação com a API do Alpha Vantage.
Implementa classes para buscar dados de investimento em tempo real.
"""

import requests
import json
from typing import Dict, List, Optional
from datetime import datetime


class StockQuote:
    """
    Representa uma cotação de ativo individual.
    """
    
    def __init__(self, data: Dict):
        """
        Inicializa uma instância de StockQuote com dados da API.
        
        Args:
            data: Dicionário contendo os dados da cotação da API Alpha Vantage
        """
        self.symbol = data.get('01. symbol', '')
        self.open_price = float(data.get('02. open', 0))
        self.high_price = float(data.get('03. high', 0))
        self.low_price = float(data.get('04. low', 0))
        self.current_price = float(data.get('05. price', 0))
        self.volume = int(data.get('06. volume', 0))
        self.latest_trading_day = data.get('07. latest trading day', '')
        self.previous_close = float(data.get('08. previous close', 0))
        self.change = float(data.get('09. change', 0))
        self.change_percent = data.get('10. change percent', '0%')
    
    def to_dict(self) -> Dict:
        """
        Converte a instância para um dicionário.
        
        Returns:
            Dicionário com os dados da cotação
        """
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
            'change_percent': self.change_percent
        }


class TimeSeriesData:
    """
    Representa um ponto de dados em uma série temporal.
    """
    
    def __init__(self, timestamp: str, data: Dict):
        """
        Inicializa uma instância de TimeSeriesData.
        
        Args:
            timestamp: Data e hora do ponto de dados
            data: Dicionário contendo os dados do ponto temporal
        """
        self.timestamp = timestamp
        self.open_price = float(data.get('1. open', 0))
        self.high_price = float(data.get('2. high', 0))
        self.low_price = float(data.get('3. low', 0))
        self.close_price = float(data.get('4. close', 0))
        self.volume = int(data.get('5. volume', 0))
    
    def to_dict(self) -> Dict:
        """
        Converte a instância para um dicionário.
        
        Returns:
            Dicionário com os dados do ponto temporal
        """
        return {
            'timestamp': self.timestamp,
            'open_price': self.open_price,
            'high_price': self.high_price,
            'low_price': self.low_price,
            'close_price': self.close_price,
            'volume': self.volume
        }


class AlphaVantageAPIClient:
    """
    Cliente para interagir com a API do Alpha Vantage.
    """
    
    def __init__(self, api_key: str):
        """
        Inicializa o cliente da API.
        
        Args:
            api_key: Chave de API do Alpha Vantage
        """
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
    
    def _make_request(self, params: Dict) -> Dict:
        """
        Faz uma requisição para a API do Alpha Vantage.
        
        Args:
            params: Parâmetros da requisição
            
        Returns:
            Resposta JSON da API
            
        Raises:
            requests.RequestException: Se houver erro na requisição
            ValueError: Se a resposta não for válida
        """
        params['apikey'] = self.api_key
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Verifica se há erro na resposta da API
            if 'Error Message' in data:
                raise ValueError(f"Erro da API: {data['Error Message']}")
            
            if 'Note' in data:
                raise ValueError(f"Limite de requisições atingido: {data['Note']}")
            
            return data
            
        except requests.RequestException as e:
            raise requests.RequestException(f"Erro na requisição: {str(e)}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Erro ao decodificar JSON: {str(e)}")
    
    def get_global_quote(self, symbol: str) -> Optional[StockQuote]:
        """
        Obtém cotação global de um ativo.
        
        Args:
            symbol: Símbolo do ativo (ex: 'IBM', 'PETR4.SA')
            
        Returns:
            Instância de StockQuote ou None se houver erro
        """
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol
        }
        
        try:
            data = self._make_request(params)
            
            if 'Global Quote' in data:
                return StockQuote(data['Global Quote'])
            else:
                print(f"Dados não encontrados para o símbolo: {symbol}")
                return None
                
        except Exception as e:
            print(f"Erro ao obter cotação para {symbol}: {str(e)}")
            return None
    
    def get_time_series_intraday(self, symbol: str, interval: str = '5min') -> List[TimeSeriesData]:
        """
        Obtém dados de série temporal intraday de um ativo.
        
        Args:
            symbol: Símbolo do ativo
            interval: Intervalo dos dados ('1min', '5min', '15min', '30min', '60min')
            
        Returns:
            Lista de instâncias de TimeSeriesData
        """
        params = {
            'function': 'TIME_SERIES_INTRADAY',
            'symbol': symbol,
            'interval': interval,
            'outputsize': 'compact'  # Últimos 100 pontos de dados
        }
        
        try:
            data = self._make_request(params)
            
            time_series_key = f'Time Series ({interval})'
            
            if time_series_key in data:
                time_series_data = []
                for timestamp, values in data[time_series_key].items():
                    time_series_data.append(TimeSeriesData(timestamp, values))
                
                # Ordena por timestamp (mais recente primeiro)
                time_series_data.sort(key=lambda x: x.timestamp, reverse=True)
                return time_series_data
            else:
                print(f"Dados de série temporal não encontrados para: {symbol}")
                return []
                
        except Exception as e:
            print(f"Erro ao obter série temporal para {symbol}: {str(e)}")
            return []
    
    def get_top_gainers_losers(self) -> Dict:
        """
        Obtém os maiores ganhadores e perdedores do mercado.
        
        Returns:
            Dicionário com listas de ganhadores e perdedores
        """
        params = {
            'function': 'TOP_GAINERS_LOSERS'
        }
        
        try:
            data = self._make_request(params)
            
            result = {
                'top_gainers': [],
                'top_losers': [],
                'most_actively_traded': []
            }
            
            if 'top_gainers' in data:
                result['top_gainers'] = data['top_gainers'][:5]  # Top 5
            
            if 'top_losers' in data:
                result['top_losers'] = data['top_losers'][:5]  # Top 5
            
            if 'most_actively_traded' in data:
                result['most_actively_traded'] = data['most_actively_traded'][:5]  # Top 5
            
            return result
            
        except Exception as e:
            print(f"Erro ao obter top gainers/losers: {str(e)}")
            return {'top_gainers': [], 'top_losers': [], 'most_actively_traded': []}

