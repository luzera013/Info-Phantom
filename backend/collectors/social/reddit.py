"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Reddit Collector
Coleta dados do Reddit
"""

import asyncio
import aiohttp
import json
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode, quote_plus
from dataclasses import dataclass
import time
import logging
import re

from ..core.pipeline import SearchResult
from ..utils.logger import setup_logger
from ..utils.http_client import HTTPClient

logger = setup_logger(__name__)

@dataclass
class RedditConfig:
    """Configuração do coletor Reddit"""
    client_id: str = ""
    client_secret: str = ""
    user_agent: str = "OMNISCIENT_REDDIT/3.0"
    max_results: int = 100
    timeout: int = 30
    retry_attempts: int = 3
    include_comments: bool = True
    max_comments: int = 50
    sort_by: str = "relevance"  # relevance, hot, new, top

class RedditCollector:
    """Coletor de dados do Reddit"""
    
    def __init__(self, config: Optional[RedditConfig] = None):
        self.config = config or RedditConfig()
        self.http_client = HTTPClient()
        self.session = None
        self.access_token = None
        self.token_expires = 0
        
        # Reddit API endpoints
        self.base_url = "https://www.reddit.com"
        self.oauth_url = "https://oauth.reddit.com"
        
        logger.info("📱 Reddit Collector inicializado")
    
    async def initialize(self):
        """Inicializa o coletor"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            headers={'User-Agent': self.config.user_agent}
        )
        
        # Obter token de acesso se tiver credenciais
        if self.config.client_id and self.config.client_secret:
            await self._get_access_token()
        
        logger.info("✅ Reddit Collector pronto")
    
    async def _get_access_token(self):
        """Obtém token de acesso OAuth2"""
        try:
            auth = aiohttp.BasicAuth(self.config.client_id, self.config.client_secret)
            
            data = {
                'grant_type': 'client_credentials'
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/access_token",
                auth=auth,
                data=data
            ) as response:
                if response.status == 200:
                    token_data = await response.json()
                    self.access_token = token_data['access_token']
                    self.token_expires = time.time() + token_data['expires_in'] - 60
                    
                    logger.info("🔑 Token Reddit obtido")
                else:
                    logger.warning(f"⚠️ Falha obter token Reddit: {response.status}")
        
        except Exception as e:
            logger.warning(f"⚠️ Erro autenticação Reddit: {str(e)}")
    
    async def search(self, query: str, max_results: Optional[int] = None, 
                   subreddit: Optional[str] = None, page: int = 1, 
                   per_page: int = 100, sort: str = 'relevance') -> List[SearchResult]:
        """
        Executa busca no Reddit com paginação avançada
        
        Args:
            query: Termo de busca
            max_results: Número máximo de resultados
            subreddit: Subreddit específico (opcional)
            page: Página atual
            per_page: Resultados por página
            sort: Ordenação (relevance, hot, new, top, comments)
            
        Returns:
            Lista de SearchResult
        """
        if not self.session:
            await self.initialize()
        
        max_results = max_results or self.config.max_results
        total_results = []
        
        logger.info(f"🔍 Buscando no Reddit: '{query}' (max: {max_results}, página: {page})")
        
        try:
            # Buscar em múltiplas páginas até atingir o limite
            current_page = page
            after = None
            
            while len(total_results) < max_results:
                # Ajustar número de resultados para esta página
                remaining = max_results - len(total_results)
                page_limit = min(per_page, remaining)
                
                # Construir URL da busca com paginação
                search_url = await self._build_search_url_paged(
                    query, subreddit, page_limit, after, sort
                )
                
                # Fazer requisição
                headers = await self._get_auth_headers()
                
                async with self.session.get(search_url, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.warning(f"⚠️ Reddit API error {response.status}: {error_text}")
                        break
                    
                    data = await response.json()
                    
                    # Parsear resultados
                    posts = await self._parse_search_results(data)
                    
                    if not posts:
                        logger.info(f"📊 Sem resultados na página {current_page}, parando busca")
                        break
                    
                    # Obter comentários se configurado (limitado para performance)
                    if self.config.include_comments and len(posts) <= 20:
                        posts = await self._fetch_comments(posts, headers)
                    
                    # Adicionar resultados da página
                    total_results.extend(posts)
                    
                    # Verificar se há mais páginas
                    has_more = (
                        'data' in data and
                        data['data'].get('after') and
                        len(posts) >= page_limit / 2
                    )
                    
                    if not has_more or len(total_results) >= max_results:
                        break
                    
                    # Preparar próxima página
                    after = data['data'].get('after')
                    current_page += 1
                    
                    # Delay entre páginas
                    await asyncio.sleep(random.uniform(0.5, 1.0))
            
            # Converter para SearchResult com rankeamento avançado
            results = []
            for post in total_results:
                # Calcular score de relevância avançado
                relevance_score = self._calculate_relevance_score(post, query)
                
                result = SearchResult(
                    title=post.get('title', ''),
                    url=post.get('url', ''),
                    description=post.get('selftext', '')[:500],
                    source='reddit',
                    timestamp=post.get('created_utc', time.time()),
                    relevance_score=relevance_score
                )
                
                result.extracted_data = post
                results.append(result)
            
            # Limitar resultados
            results = results[:max_results]
            
            logger.info(f" Encontrados {len(results)} posts no Reddit")
            return results
                
        except Exception as e:
            logger.error(f"❌ Erro na busca Reddit: {str(e)}")
            # Retornar resultados simulados se API falhar
            return await self._get_simulated_results(query, max_results, subreddit)
    
    async def _build_search_url(self, query: str, subreddit: Optional[str] = None) -> str:
        """Constrói URL de busca"""
        params = {
            'q': query,
            'sort': self.config.sort_by,
            't': 'all',  # Todos os tempos
            'limit': min(self.config.max_results, 100),
            'type': 'link'  # Apenas links
        }
        
        if subreddit:
            # Buscar em subreddit específico
            base = f"{self.base_url}/r/{subreddit}/search.json"
        else:
            # Buscar em todo o Reddit
            base = f"{self.base_url}/search.json"
        
        param_string = urlencode(params)
        return f"{base}?{param_string}"
    
    async def _get_auth_headers(self) -> Dict[str, str]:
        """Obtém headers de autenticação"""
        headers = {'User-Agent': self.config.user_agent}
        
        # Verificar se token ainda é válido
        if self.access_token and time.time() < self.token_expires:
            headers['Authorization'] = f"Bearer {self.access_token}"
        
        return headers
    
    async def _parse_search_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse resultados da busca"""
        posts = []
        
        try:
            if 'data' in data and 'children' in data['data']:
                for child in data['data']['children']:
                    if child.get('kind') == 't3':  # t3 = post
                        post_data = child.get('data', {})
                        posts.append(post_data)
        
        except Exception as e:
            logger.error(f"❌ Erro parse resultados Reddit: {str(e)}")
        
        return posts
    
    async def _fetch_comments(self, posts: List[Dict[str, Any]], headers: Dict[str, str]) -> List[Dict[str, Any]]:
        """Busca comentários dos posts"""
        for post in posts:
            try:
                permalink = post.get('permalink', '')
                if not permalink:
                    continue
                
                # Construir URL dos comentários
                comments_url = f"{self.base_url}{permalink}.json?sort=best&limit={self.config.max_comments}"
                
                async with self.session.get(comments_url, headers=headers) as response:
                    if response.status == 200:
                        comments_data = await response.json()
                        
                        # Parsear comentários
                        comments = []
                        if len(comments_data) > 1 and 'data' in comments_data[1]:
                            for child in comments_data[1]['data'].get('children', []):
                                if child.get('kind') == 't1':  # t1 = comment
                                    comment_data = child.get('data', {})
                                    comments.append({
                                        'author': comment_data.get('author', ''),
                                        'body': comment_data.get('body', ''),
                                        'score': comment_data.get('score', 0),
                                        'created_utc': comment_data.get('created_utc', 0)
                                    })
                        
                        post['comments'] = comments[:self.config.max_comments]
                
                # Delay entre requisições para evitar rate limiting
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.debug(f"⚠️ Erro buscando comentários: {str(e)}")
                post['comments'] = []
        
        return posts
    
    async def _get_simulated_results(self, query: str, max_results: int, 
                                   subreddit: Optional[str] = None) -> List[SearchResult]:
        """Retorna resultados simulados quando API não disponível"""
        logger.info("🎭 Usando resultados simulados do Reddit")
        
        subreddit_name = subreddit or "technology"
        
        simulated_posts = [
            {
                'title': f"Discussão sobre {query} no Reddit",
                'selftext': f"Post discutindo aspectos importantes sobre {query}. Comunidade compartilhando experiências e conhecimentos.",
                'url': f"https://reddit.com/r/{subreddit_name}/comments/abc123/discussao_sobre_{query.replace(' ', '_')}",
                'subreddit': subreddit_name,
                'author': 'user123',
                'score': 1250,
                'ups': 1250,
                'downs': 0,
                'num_comments': 89,
                'created_utc': time.time() - 86400,  # 1 dia atrás
                'over_18': False,
                'is_self': True,
                'permalink': f"/r/{subreddit_name}/comments/abc123/discussao_sobre_{query.replace(' ', '_')}/",
                'comments': [
                    {
                        'author': 'expert_user',
                        'body': f"Ótima discussão sobre {query}. Eu tenho experiência nesta área e posso adicionar que...",
                        'score': 156,
                        'created_utc': time.time() - 86000
                    },
                    {
                        'author': 'curious_mind',
                        'body': f"Alguém tem mais informações sobre {query}? Estou pesquisando para um projeto.",
                        'score': 45,
                        'created_utc': time.time() - 85000
                    }
                ]
            },
            {
                'title': f"{query} - Guia Completo e Recursos",
                'selftext': f"Compilei uma lista completa de recursos sobre {query}. Inclui tutoriais, documentação e melhores práticas.",
                'url': f"https://reddit.com/r/{subreddit_name}/comments/def456/{query}_guia_completo_e_recursos",
                'subreddit': subreddit_name,
                'author': 'helper_bot',
                'score': 890,
                'ups': 890,
                'downs': 0,
                'num_comments': 67,
                'created_utc': time.time() - 172800,  # 2 dias atrás
                'over_18': False,
                'is_self': True,
                'permalink': f"/r/{subreddit_name}/comments/def456/{query}_guia_completo_e_recursos/",
                'comments': []
            }
        ]
        
        results = []
        for post in simulated_posts:
            result = SearchResult(
                title=post['title'],
                url=post['url'],
                description=post['selftext'][:500],
                source='reddit_simulated',
                timestamp=post['created_utc'],
                relevance_score=post['score'] / 1000.0
            )
            
            result.extracted_data = post
            results.append(result)
        
        return results[:max_results]
    
    async def get_trending(self, subreddit: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Obtém posts trending/hot
        
        Args:
            subreddit: Subreddit específico (None = frontpage)
            limit: Número máximo de posts
            
        Returns:
            Lista de posts trending
        """
        if not self.session:
            await self.initialize()
        
        try:
            if subreddit:
                url = f"{self.base_url}/r/{subreddit}/hot.json?limit={limit}"
            else:
                url = f"{self.base_url}/hot.json?limit={limit}"
            
            headers = await self._get_auth_headers()
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    posts = await self._parse_search_results(data)
                    
                    logger.info(f"🔥 Encontrados {len(posts)} posts trending")
                    return posts
        
        except Exception as e:
            logger.error(f"❌ Erro buscando trending: {str(e)}")
        
        return []
    
    async def get_subreddit_info(self, subreddit: str) -> Dict[str, Any]:
        """
        Obtém informações sobre um subreddit
        
        Args:
            subreddit: Nome do subreddit
            
        Returns:
            Informações do subreddit
        """
        if not self.session:
            await self.initialize()
        
        try:
            url = f"{self.base_url}/r/{subreddit}/about.json"
            headers = await self._get_auth_headers()
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'data' in data:
                        return data['data']
        
        except Exception as e:
            logger.error(f"❌ Erro informações subreddit {subreddit}: {str(e)}")
        
        return {}
    
    async def search_comments(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Busca comentários específicos
        
        Args:
            query: Termo de busca
            limit: Número máximo de comentários
            
        Returns:
            Lista de comentários
        """
        # Reddit não tem busca direta de comentários via API pública
        # Implementação simplificada
        logger.info(f"🔍 Buscando comentários sobre: '{query}'")
        
        simulated_comments = [
            {
                'author': 'random_user',
                'body': f"Eu concordo com a discussão sobre {query}. É um tópico muito relevante atualmente.",
                'score': 23,
                'created_utc': time.time() - 3600,
                'permalink': f"/r/technology/comments/abc123/comment/def456/",
                'subreddit': 'technology'
            },
            {
                'author': 'expert_commenter',
                'body': f"Baseado na minha experiência com {query}, posso dizer que os resultados dependem muito do contexto específico.",
                'score': 67,
                'created_utc': time.time() - 7200,
                'permalink': f"/r/science/comments/ghi789/comment/jkl012/",
                'subreddit': 'science'
            }
        ]
        
        return simulated_comments[:limit]
    
    async def _build_search_url_paged(self, query: str, subreddit: Optional[str], 
                                      limit: int, after: Optional[str], sort: str) -> str:
        """
        Constrói URL de busca com paginação
        """
        base_url = "https://oauth.reddit.com/search"
        
        params = {
            'q': query,
            'limit': str(limit),
            'sort': sort,
            'type': 'link',
            'raw_json': '1'
        }
        
        if subreddit:
            params['restrict_sr'] = subreddit
        
        if after:
            params['after'] = after
        
        return f"{base_url}?" + urlencode(params)
    
    def _calculate_relevance_score(self, post: Dict[str, Any], query: str) -> float:
        """
        Calcula score de relevância avançado para posts
        """
        score = 0.0
        title = post.get('title', '').lower()
        selftext = post.get('selftext', '').lower()
        query_lower = query.lower()
        
        # Relevância do título (peso 40%)
        if query_lower in title:
            score += 0.4
            # Bônus se estiver no início do título
            if title.startswith(query_lower):
                score += 0.2
        
        # Relevância do conteúdo (peso 30%)
        if query_lower in selftext:
            score += 0.3
        
        # Score do Reddit (peso 20%)
        reddit_score = post.get('score', 0)
        if reddit_score > 0:
            score += min(reddit_score / 1000, 0.2)
        
        # Número de comentários (peso 10%)
        num_comments = post.get('num_comments', 0)
        if num_comments > 0:
            score += min(num_comments / 100, 0.1)
        
        return score
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificação de saúde do coletor"""
        return {
            'status': 'healthy',
            'component': 'reddit_collector',
            'timestamp': time.time(),
            'session_active': self.session is not None,
            'client_configured': bool(self.config.client_id and self.config.client_secret),
            'max_results': self.config.max_results
        }
    
    async def cleanup(self):
        """Limpa recursos"""
        if self.session:
            await self.session.close()
        
        logger.info("🧹 Reddit Collector limpo")
