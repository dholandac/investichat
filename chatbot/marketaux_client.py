"""
Cliente para API Marketaux - Notícias de Mercado Financeiro
Documentação: https://www.marketaux.com/documentation
"""

from typing import Dict, List, Optional
from datetime import datetime
import requests


class MarketauxClient:
    """
    Cliente para interagir com a API do Marketaux.
    Fornece notícias de mercado financeiro em português e outros idiomas.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = 'https://api.marketaux.com/v1'

    def _get(self, endpoint: str, params: Dict) -> Dict:
        """Faz requisição GET para a API"""
        params['api_token'] = self.api_key
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            error_detail = ''
            try:
                error_detail = response.json().get('error', {}).get('message', '')
            except Exception:
                error_detail = response.text[:200]
            raise requests.HTTPError(f"{e} | Detalhe: {error_detail}")
        except Exception as e:
            raise Exception(f"Erro ao conectar com Marketaux API: {e}")

    def get_market_news(
        self, 
        languages: str = '',
        countries: str = '',
        limit: int = 10,
        filter_entities: bool = True
    ) -> List[Dict]:
        """
        Busca notícias do mercado financeiro.
        
        Args:
            languages: Idiomas das notícias (ex: 'pt', 'en', 'pt,en') - vazio para todos
            countries: Países das notícias (ex: 'br', 'us', 'br,us') - vazio para todos
            limit: Número máximo de notícias (máx: 100)
            filter_entities: Se True, retorna apenas notícias com símbolos/entidades relacionadas
            
        Returns:
            Lista de dicionários contendo as notícias formatadas
        """
        try:
            params = {
                'limit': min(limit, 100),  # API limita a 100
                'sort': 'published_at',
            }

            if languages:
                params['language'] = languages
            
            if countries:
                params['countries'] = countries
            
            if filter_entities:
                params['filter_entities'] = 'true'
            
            data = self._get('/news/all', params)
            
            if not data or 'data' not in data:
                return []
            
            # Formata as notícias
            news_list = []
            for item in data['data']:
                # Formata a data
                published_at = item.get('published_at', '')
                try:
                    dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    formatted_date = dt.strftime('%d/%m/%Y %H:%M')
                except Exception:
                    formatted_date = published_at
                
                # Extrai símbolos relacionados
                entities = item.get('entities', [])
                symbols = [e.get('symbol') for e in entities if e.get('symbol')]
                
                # Extrai sentimento
                sentiment = item.get('sentiment', {})
                sentiment_score = sentiment.get('polarity', 0) if sentiment else 0
                
                news_item = {
                    'uuid': item.get('uuid'),
                    'headline': item.get('title', ''),
                    'summary': item.get('description', ''),
                    'source': item.get('source', ''),
                    'url': item.get('url', ''),
                    'image': item.get('image_url', ''),
                    'datetime': formatted_date,
                    'published_at': published_at,
                    'symbols': symbols,
                    'sentiment_score': sentiment_score,
                    'language': item.get('language', ''),
                }
                news_list.append(news_item)
            
            return news_list
            
        except Exception as e:
            print(f"Erro ao buscar notícias do Marketaux: {e}")
            return []

    def get_news_by_symbols(
        self,
        symbols: List[str],
        languages: str = 'pt,en',
        limit: int = 10
    ) -> List[Dict]:
        """
        Busca notícias relacionadas a símbolos específicos (ações, crypto, etc).
        
        Args:
            symbols: Lista de símbolos (ex: ['AAPL', 'PETR4', 'BTC'])
            languages: Idiomas das notícias
            limit: Número máximo de notícias
            
        Returns:
            Lista de dicionários contendo as notícias formatadas
        """
        try:
            # Junta os símbolos com vírgula
            symbols_param = ','.join(symbols)
            
            params = {
                'symbols': symbols_param,
                'language': languages,  # SINGULAR, não 'languages'
                'limit': min(limit, 100),
                'sort': 'published_at',
            }
            
            data = self._get('/news/all', params)
            
            if not data or 'data' not in data:
                return []
            
            # Formata as notícias
            news_list = []
            for item in data['data']:
                published_at = item.get('published_at', '')
                try:
                    dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    formatted_date = dt.strftime('%d/%m/%Y %H:%M')
                except Exception:
                    formatted_date = published_at
                
                entities = item.get('entities', [])
                related_symbols = [e.get('symbol') for e in entities if e.get('symbol')]
                
                news_item = {
                    'uuid': item.get('uuid'),
                    'headline': item.get('title', ''),
                    'summary': item.get('description', ''),
                    'source': item.get('source', ''),
                    'url': item.get('url', ''),
                    'image': item.get('image_url', ''),
                    'datetime': formatted_date,
                    'symbols': related_symbols,
                }
                news_list.append(news_item)
            
            return news_list
            
        except Exception as e:
            print(f"Erro ao buscar notícias por símbolos do Marketaux: {e}")
            return []
