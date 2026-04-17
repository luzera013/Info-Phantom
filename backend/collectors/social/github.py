"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - GitHub Collector
Coleta dados do GitHub
"""

import asyncio
import aiohttp
import json
import random
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
class GitHubConfig:
    """Configuração do coletor GitHub"""
    token: str = ""  # Personal Access Token
    max_results: int = 100
    timeout: int = 30
    retry_attempts: int = 3
    include_readme: bool = True
    include_languages: bool = True
    include_contributors: bool = True
    sort_by: str = "updated"  # stars, forks, updated

class GitHubCollector:
    """Coletor de dados do GitHub"""
    
    def __init__(self, config: Optional[GitHubConfig] = None):
        self.config = config or GitHubConfig()
        self.http_client = HTTPClient()
        self.session = None
        
        # GitHub API endpoints
        self.api_url = "https://api.github.com"
        self.web_url = "https://github.com"
        
        logger.info("🐙 GitHub Collector inicializado")
    
    async def initialize(self):
        """Inicializa o coletor"""
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'OMNISCIENT_GITHUB/3.0'
        }
        
        if self.config.token:
            headers['Authorization'] = f"token {self.config.token}"
        
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            headers=headers
        )
        
        logger.info("✅ GitHub Collector pronto")
    
    async def search(self, query: str, max_results: Optional[int] = None, 
                   search_type: str = "repositories", page: int = 1, 
                   per_page: int = 100, sort: str = "updated") -> List[SearchResult]:
        """
        Executa busca no GitHub com paginação avançada
        
        Args:
            query: Termo de busca
            max_results: Número máximo de resultados
            search_type: Tipo de busca (repositories, users, code, issues)
            page: Página atual
            per_page: Resultados por página
            sort: Ordenação (updated, stars, forks, created)
            
        Returns:
            Lista de SearchResult
        """
        if not self.session:
            await self.initialize()
        
        max_results = max_results or self.config.max_results
        total_results = []
        
        logger.info(f"🔍 Buscando no GitHub: '{query}' (max: {max_results}, type: {search_type}, página: {page})")
        
        try:
            # Buscar em múltiplas páginas até atingir o limite
            current_page = page
            
            while len(total_results) < max_results:
                # Ajustar número de resultados para esta página
                remaining = max_results - len(total_results)
                page_limit = min(per_page, remaining)
                
                # Construir URL de busca com paginação
                search_url = await self._build_search_url_paged(
                    query, search_type, page_limit, current_page, sort
                )
                
                # Fazer requisição
                async with self.session.get(search_url) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.warning(f"⚠️ GitHub API error {response.status}: {error_text}")
                        break
                    
                    data = await response.json()
                    
                    # Parsear resultados baseado no tipo
                    if search_type == "repositories":
                        items = await self._parse_repositories(data)
                    elif search_type == "users":
                        items = await self._parse_users(data)
                    elif search_type == "code":
                        items = await self._parse_code(data)
                    elif search_type == "issues":
                        items = await self._parse_issues(data)
                    else:
                        items = []
                    
                    if not items:
                        logger.info(f"📊 Sem resultados na página {current_page}, parando busca")
                        break
                    
                    # Enriquecer resultados (limitado para performance)
                    if len(items) <= 50:
                        enriched_items = await self._enrich_results(items, search_type)
                    else:
                        enriched_items = items
                    
                    # Adicionar resultados da página
                    total_results.extend(enriched_items)
                    
                    # Verificar se há mais páginas
                    has_more = (
                        'items' in data and
                        len(items) >= page_limit / 2
                    )
                    
                    if not has_more or len(total_results) >= max_results:
                        break
                    
                    current_page += 1
                    
                    # Delay entre páginas
                    await asyncio.sleep(random.uniform(0.5, 1.0))
            
            # Remover duplicatas por ID/URL
            unique_results = []
            seen_ids = set()
            
            for item in total_results:
                item_id = item.get('id', item.get('html_url', ''))
                if item_id not in seen_ids:
                    seen_ids.add(item_id)
                    
                    # Calcular score de relevância avançado
                    relevance_score = self._calculate_github_relevance(item, query, search_type)
                    
                    result = SearchResult(
                        title=item.get('name', item.get('title', '')),
                        url=item.get('html_url', item.get('url', '')),
                        description=item.get('description', ''),
                        source=f'github_{search_type}',
                        timestamp=item.get('created_at', time.time()),
                        relevance_score=relevance_score
                    )
                    
                    result.extracted_data = item
                    unique_results.append(result)
            
            # Rankeamento final por relevância
            unique_results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            # Limitar ao máximo solicitado
            final_results = unique_results[:max_results]
            
            logger.info(f"✅ Encontrados {len(final_results)} resultados únicos no GitHub")
            return final_results
                
        except Exception as e:
            logger.error(f"❌ Erro busca GitHub: {str(e)}")
            return []
    
    async def _build_search_url_paged(self, query: str, search_type: str, per_page: int, page: int, sort: str) -> str:
        """Constrói URL de busca com paginação"""
        base_url = f"{self.api_url}/search/{search_type}"
        
        params = {
            'q': query,
            'sort': self.config.sort_by,
            'order': 'desc',
            'per_page': min(self.config.max_results, 100)
        }
        
        # Adicionar qualificadores específicos por tipo
        if search_type == "repositories":
            params['q'] += " is:public"
        elif search_type == "code":
            params['q'] += " in:file"
        elif search_type == "issues":
            params['q'] += " state:open"
        
        param_string = urlencode(params)
        return f"{base_url}?{param_string}"
    
    async def _parse_repositories(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse resultados de repositórios"""
        repositories = []
        
        try:
            if 'items' in data:
                for item in data['items']:
                    repo_data = {
                        'id': item.get('id'),
                        'name': item.get('name'),
                        'full_name': item.get('full_name'),
                        'description': item.get('description', ''),
                        'html_url': item.get('html_url'),
                        'url': item.get('url'),
                        'clone_url': item.get('clone_url'),
                        'ssh_url': item.get('ssh_url'),
                        'stargazers_count': item.get('stargazers_count', 0),
                        'watchers_count': item.get('watchers_count', 0),
                        'forks_count': item.get('forks_count', 0),
                        'open_issues_count': item.get('open_issues_count', 0),
                        'language': item.get('language'),
                        'created_at': item.get('created_at'),
                        'updated_at': item.get('updated_at'),
                        'pushed_at': item.get('pushed_at'),
                        'size': item.get('size', 0),
                        'default_branch': item.get('default_branch', 'main'),
                        'archived': item.get('archived', False),
                        'disabled': item.get('disabled', False),
                        'private': item.get('private', False),
                        'owner': item.get('owner', {}),
                        'license': item.get('license'),
                        'topics': item.get('topics', []),
                        'score': item.get('score', 0)
                    }
                    repositories.append(repo_data)
        
        except Exception as e:
            logger.error(f"❌ Erro parse repositórios: {str(e)}")
        
        return repositories
    
    async def _parse_users(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse resultados de usuários"""
        users = []
        
        try:
            if 'items' in data:
                for item in data['items']:
                    user_data = {
                        'id': item.get('id'),
                        'login': item.get('login'),
                        'name': item.get('name'),
                        'email': item.get('email'),
                        'bio': item.get('bio'),
                        'company': item.get('company'),
                        'location': item.get('location'),
                        'blog': item.get('blog'),
                        'html_url': item.get('html_url'),
                        'url': item.get('url'),
                        'followers': item.get('followers', 0),
                        'following': item.get('following', 0),
                        'public_repos': item.get('public_repos', 0),
                        'public_gists': item.get('public_gists', 0),
                        'created_at': item.get('created_at'),
                        'updated_at': item.get('updated_at'),
                        'type': item.get('type', 'User'),
                        'site_admin': item.get('site_admin', False),
                        'score': item.get('score', 0)
                    }
                    users.append(user_data)
        
        except Exception as e:
            logger.error(f"❌ Erro parse usuários: {str(e)}")
        
        return users
    
    async def _parse_code(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse resultados de código"""
        code_results = []
        
        try:
            if 'items' in data:
                for item in data['items']:
                    code_data = {
                        'name': item.get('name'),
                        'path': item.get('path'),
                        'sha': item.get('sha'),
                        'url': item.get('url'),
                        'git_url': item.get('git_url'),
                        'html_url': item.get('html_url'),
                        'repository': item.get('repository', {}),
                        'score': item.get('score', 0),
                        'text_matches': item.get('text_matches', [])
                    }
                    code_results.append(code_data)
        
        except Exception as e:
            logger.error(f"❌ Erro parse código: {str(e)}")
        
        return code_results
    
    async def _parse_issues(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse resultados de issues"""
        issues = []
        
        try:
            if 'items' in data:
                for item in data['items']:
                    issue_data = {
                        'id': item.get('id'),
                        'number': item.get('number'),
                        'title': item.get('title'),
                        'body': item.get('body', ''),
                        'html_url': item.get('html_url'),
                        'url': item.get('url'),
                        'state': item.get('state'),
                        'locked': item.get('locked', False),
                        'comments': item.get('comments', 0),
                        'created_at': item.get('created_at'),
                        'updated_at': item.get('updated_at'),
                        'closed_at': item.get('closed_at'),
                        'user': item.get('user', {}),
                        'assignee': item.get('assignee'),
                        'assignees': item.get('assignees', []),
                        'labels': item.get('labels', []),
                        'milestone': item.get('milestone'),
                        'repository': item.get('repository', {}),
                        'score': item.get('score', 0)
                    }
                    issues.append(issue_data)
        
        except Exception as e:
            logger.error(f"❌ Erro parse issues: {str(e)}")
        
        return issues
    
    async def _enrich_results(self, items: List[Dict[str, Any]], search_type: str) -> List[Dict[str, Any]]:
        """Enriquece resultados com dados adicionais"""
        enriched = []
        
        for item in items:
            try:
                if search_type == "repositories" and self.config.include_readme:
                    # Obter README
                    readme = await self._get_readme(item)
                    if readme:
                        item['readme'] = readme
                
                if search_type == "repositories" and self.config.include_languages:
                    # Obter linguagens
                    languages = await self._get_languages(item)
                    if languages:
                        item['languages'] = languages
                
                if search_type == "repositories" and self.config.include_contributors:
                    # Obter contributors
                    contributors = await self._get_contributors(item)
                    if contributors:
                        item['contributors'] = contributors
                
                enriched.append(item)
                
                # Delay para evitar rate limiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.debug(f"⚠️ Erro enriquecendo item: {str(e)}")
                enriched.append(item)
        
        return enriched
    
    async def _get_readme(self, repo: Dict[str, Any]) -> Optional[str]:
        """Obtém README do repositório"""
        try:
            if not repo.get('url'):
                return None
            
            readme_url = f"{repo['url']}/readme"
            
            async with self.session.get(readme_url) as response:
                if response.status == 200:
                    readme_data = await response.json()
                    content = readme_data.get('content', '')
                    
                    # Decodificar base64
                    import base64
                    try:
                        decoded_content = base64.b64decode(content).decode('utf-8')
                        return decoded_content[:5000]  # Limitar tamanho
                    except:
                        return content
        
        except Exception as e:
            logger.debug(f"⚠️ Erro obtendo README: {str(e)}")
        
        return None
    
    async def _get_languages(self, repo: Dict[str, Any]) -> Optional[Dict[str, int]]:
        """Obtém linguagens do repositório"""
        try:
            if not repo.get('url'):
                return None
            
            languages_url = f"{repo['url']}/languages"
            
            async with self.session.get(languages_url) as response:
                if response.status == 200:
                    return await response.json()
        
        except Exception as e:
            logger.debug(f"⚠️ Erro obtendo linguagens: {str(e)}")
        
        return None
    
    async def _get_contributors(self, repo: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Obtém contributors do repositório"""
        try:
            if not repo.get('url'):
                return None
            
            contributors_url = f"{repo['url']}/contributors"
            
            async with self.session.get(contributors_url) as response:
                if response.status == 200:
                    return await response.json()
        
        except Exception as e:
            logger.debug(f"⚠️ Erro obtendo contributors: {str(e)}")
        
        return None
    
    async def _get_simulated_results(self, query: str, max_results: int, 
                                   search_type: str) -> List[SearchResult]:
        """Retorna resultados simulados quando API não disponível"""
        logger.info("🎭 Usando resultados simulados do GitHub")
        
        if search_type == "repositories":
            return await self._simulate_repositories(query, max_results)
        elif search_type == "users":
            return await self._simulate_users(query, max_results)
        elif search_type == "code":
            return await self._simulate_code(query, max_results)
        elif search_type == "issues":
            return await self._simulate_issues(query, max_results)
        
        return []
    
    async def _simulate_repositories(self, query: str, max_results: int) -> List[SearchResult]:
        """Simula resultados de repositórios"""
        simulated_repos = [
            {
                'name': f'{query.replace(" ", "-")}-project',
                'full_name': f'user/{query.replace(" ", "-")}-project',
                'description': f'Amazing {query} project with modern features and best practices',
                'html_url': f'https://github.com/user/{query.replace(" ", "-")}-project',
                'stargazers_count': 1234,
                'forks_count': 567,
                'language': 'Python',
                'created_at': '2023-01-15T10:30:00Z',
                'updated_at': '2024-04-10T15:45:00Z',
                'size': 2048,
                'open_issues_count': 12,
                'topics': [query, 'awesome', 'modern'],
                'license': {'name': 'MIT'},
                'owner': {'login': 'user', 'type': 'User'},
                'score': 85.5
            },
            {
                'name': f'{query}-tutorial',
                'full_name': f'educator/{query}-tutorial',
                'description': f'Complete tutorial and examples for learning {query}',
                'html_url': f'https://github.com/educator/{query}-tutorial',
                'stargazers_count': 892,
                'forks_count': 234,
                'language': 'JavaScript',
                'created_at': '2022-08-20T09:15:00Z',
                'updated_at': '2024-04-08T11:20:00Z',
                'size': 512,
                'open_issues_count': 3,
                'topics': ['tutorial', 'education', query],
                'license': {'name': 'Apache-2.0'},
                'owner': {'login': 'educator', 'type': 'User'},
                'score': 72.3
            }
        ]
        
        results = []
        for repo in simulated_repos:
            result = SearchResult(
                title=repo['name'],
                url=repo['html_url'],
                description=repo['description'],
                source='github_simulated',
                timestamp=time.time(),
                relevance_score=repo['score'] / 100.0
            )
            
            result.extracted_data = repo
            results.append(result)
        
        return results[:max_results]
    
    async def _simulate_users(self, query: str, max_results: int) -> List[SearchResult]:
        """Simula resultados de usuários"""
        return []
    
    async def _simulate_code(self, query: str, max_results: int) -> List[SearchResult]:
        """Simula resultados de código"""
        return []
    
    async def _simulate_issues(self, query: str, max_results: int) -> List[SearchResult]:
        """Simula resultados de issues"""
        return []
    
    async def get_trending_repositories(self, language: Optional[str] = None, 
                                     since: str = "daily") -> List[Dict[str, Any]]:
        """
        Obtém repositórios trending
        
        Args:
            language: Linguagem específica
            since: Período (daily, weekly, monthly)
            
        Returns:
            Lista de repositórios trending
        """
        if not self.session:
            await self.initialize()
        
        try:
            # GitHub não tem API oficial para trending, usar busca com qualificadores
            query = "created:>" + {
                "daily": "1 day ago",
                "weekly": "1 week ago", 
                "monthly": "1 month ago"
            }.get(since, "1 day ago")
            
            if language:
                query += f" language:{language}"
            
            search_url = f"{self.api_url}/search/repositories?q={quote_plus(query)}&sort=stars&order=desc&per_page=50"
            
            async with self.session.get(search_url) as response:
                if response.status == 200:
                    data = await response.json()
                    repos = await self._parse_repositories(data)
                    
                    logger.info(f"🔥 Encontrados {len(repos)} repositórios trending")
                    return repos
        
        except Exception as e:
            logger.error(f"❌ Erro trending repositories: {str(e)}")
        
        return []
    
    async def get_repository_details(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Obtém detalhes completos de um repositório
        
        Args:
            owner: Nome do dono
            repo: Nome do repositório
            
        Returns:
            Detalhes do repositório
        """
        if not self.session:
            await self.initialize()
        
        try:
            url = f"{self.api_url}/repos/{owner}/{repo}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
        
        except Exception as e:
            logger.error(f"❌ Erro detalhes repositório {owner}/{repo}: {str(e)}")
        
        return {}
    
    def _calculate_github_relevance(self, item: Dict[str, Any], query: str, search_type: str) -> float:
        """
        Calcula score de relevância avançado para itens do GitHub
        """
        score = 0.0
        query_lower = query.lower()
        
        # Relevância baseada no tipo de busca
        if search_type == "repositories":
            name = item.get('name', '').lower()
            description = item.get('description', '').lower()
            
            # Nome do repositório (peso 40%)
            if query_lower in name:
                score += 0.4
                if name.startswith(query_lower):
                    score += 0.2
            
            # Descrição (peso 30%)
            if query_lower in description:
                score += 0.3
            
            # Stars (peso 20%)
            stars = item.get('stargazers_count', 0)
            if stars > 0:
                score += min(stars / 1000, 0.2)
            
            # Forks (peso 10%)
            forks = item.get('forks_count', 0)
            if forks > 0:
                score += min(forks / 500, 0.1)
        
        elif search_type == "users":
            login = item.get('login', '').lower()
            name = item.get('name', '').lower()
            bio = item.get('bio', '').lower()
            
            # Login (peso 50%)
            if query_lower in login:
                score += 0.5
                if login == query_lower:
                    score += 0.3
            
            # Nome (peso 30%)
            if query_lower in name:
                score += 0.3
            
            # Bio (peso 20%)
            if query_lower in bio:
                score += 0.2
            
            # Seguidores (peso 10%)
            followers = item.get('followers', 0)
            if followers > 0:
                score += min(followers / 1000, 0.1)
        
        # Atualização recente (bônus geral de 10%)
        updated_at = item.get('updated_at', '')
        if updated_at:
            try:
                from datetime import datetime
                updated_dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                days_old = (datetime.now() - updated_dt).days
                if days_old < 30:
                    score += 0.1
                elif days_old < 7:
                    score += 0.2
            except:
                pass
        
        return score
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificação de saúde do coletor"""
        return {
            'status': 'healthy',
            'component': 'github_collector',
            'timestamp': time.time(),
            'session_active': self.session is not None,
            'token_configured': bool(self.config.token),
            'max_results': self.config.max_results
        }
    
    async def cleanup(self):
        """Limpa recursos"""
        if self.session:
            await self.session.close()
        
        logger.info("🧹 GitHub Collector limpo")
