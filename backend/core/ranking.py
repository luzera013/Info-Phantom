"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Ranking Engine
Ordena resultados por relevância usando múltiplos algoritmos
"""

import asyncio
import re
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

from ..core.pipeline import SearchResult
from utils.logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class RankingFactors:
    """Fatores para cálculo de relevância"""
    title_relevance: float = 0.0
    content_relevance: float = 0.0
    source_authority: float = 0.0
    freshness: float = 0.0
    popularity: float = 0.0
    extracted_data_value: float = 0.0
    diversity_bonus: float = 0.0

class RankingEngine:
    """Motor de rankeamento de resultados"""
    
    def __init__(self):
        self.source_authority_scores = {
            'wikipedia': 0.95,
            'github': 0.90,
            'stackoverflow': 0.85,
            'reddit': 0.70,
            'news': 0.80,
            'academic': 0.92,
            'government': 0.94,
            'web': 0.60,
            'tor': 0.30,
            'social': 0.65
        }
        
        self.popularity_indicators = [
            'views', 'likes', 'shares', 'comments', 'stars', 'forks',
            'downloads', 'subscribers', 'followers'
        ]
        
        logger.info("🏆 Ranking Engine inicializado")
    
    async def initialize(self):
        """Inicializa componentes do ranking engine"""
        logger.info("🔧 Inicializando Ranking Engine...")
        # Aqui poderíamos carregar modelos ML, dados históricos, etc.
        logger.info("✅ Ranking Engine pronto")
    
    async def rank_results(self, query: str, results: List[SearchResult]) -> List[SearchResult]:
        """
        Rankea resultados baseado em múltiplos fatores
        
        Args:
            query: Query original
            results: Lista de resultados para rankear
            
        Returns:
            Lista de resultados rankeados
        """
        if not results:
            return results
        
        logger.info(f"🏆 Rankeando {len(results)} resultados para: '{query}'")
        
        # Calcular fatores para cada resultado
        ranked_results = []
        for i, result in enumerate(results):
            factors = await self._calculate_ranking_factors(query, result, i)
            final_score = await self._calculate_final_score(factors)
            
            result.relevance_score = final_score
            result.ranking_factors = factors
            ranked_results.append(result)
        
        # Aplicar diversificação
        diversified_results = await self._apply_diversification(ranked_results)
        
        # Ordenar por score final
        final_results = sorted(diversified_results, key=lambda x: x.relevance_score, reverse=True)
        
        logger.info(f"✅ Rankeamento concluído")
        return final_results
    
    async def _calculate_ranking_factors(self, query: str, result: SearchResult, 
                                       position: int) -> RankingFactors:
        """Calcula fatores de rankeamento para um resultado"""
        factors = RankingFactors()
        
        # Relevância do título
        factors.title_relevance = await self._calculate_title_relevance(query, result.title)
        
        # Relevância do conteúdo
        factors.content_relevance = await self._calculate_content_relevance(query, result)
        
        # Autoridade da fonte
        factors.source_authority = self.source_authority_scores.get(
            result.source.lower(), 0.50
        )
        
        # Freshness (novidade)
        factors.freshness = await self._calculate_freshness(result.timestamp)
        
        # Popularidade
        factors.popularity = await self._calculate_popularity(result)
        
        # Valor dos dados extraídos
        factors.extracted_data_value = await self._calculate_extracted_data_value(result)
        
        # Bônus de diversificação (será ajustado depois)
        factors.diversity_bonus = 0.0
        
        return factors
    
    async def _calculate_title_relevance(self, query: str, title: str) -> float:
        """Calcula relevância do título em relação à query"""
        if not title:
            return 0.0
        
        title_lower = title.lower()
        query_lower = query.lower()
        
        # Exact match bonus
        if query_lower in title_lower:
            return 1.0
        
        # Palavras da query no título
        query_words = set(query_lower.split())
        title_words = set(title_lower.split())
        
        if not query_words:
            return 0.0
        
        # Jaccard similarity
        intersection = len(query_words & title_words)
        union = len(query_words | title_words)
        
        return intersection / union if union > 0 else 0.0
    
    async def _calculate_content_relevance(self, query: str, result: SearchResult) -> float:
        """Calcula relevância do conteúdo/descrição"""
        content = result.description or ""
        
        if result.extracted_data and 'scraped_content' in result.extracted_data:
            content += " " + result.extracted_data['scraped_content'][:1000]
        
        if not content:
            return 0.0
        
        content_lower = content.lower()
        query_lower = query.lower()
        
        # Contagem de ocorrências
        query_words = query_lower.split()
        word_matches = sum(1 for word in query_words if word in content_lower)
        
        return min(word_matches / len(query_words), 1.0) if query_words else 0.0
    
    async def _calculate_freshness(self, timestamp: float) -> float:
        """Calcula score de frescor baseado na idade"""
        if not timestamp:
            return 0.5  # Neutro se não tiver timestamp
        
        now = datetime.now().timestamp()
        age_hours = (now - timestamp) / 3600
        
        # Mais novo = mais fresco
        if age_hours < 1:
            return 1.0
        elif age_hours < 24:
            return 0.9
        elif age_hours < 168:  # 1 semana
            return 0.7
        elif age_hours < 720:  # 1 mês
            return 0.5
        elif age_hours < 8760:  # 1 ano
            return 0.3
        else:
            return 0.1
    
    async def _calculate_popularity(self, result: SearchResult) -> float:
        """Calcula score de popularidade baseado em indicadores"""
        if not result.extracted_data:
            return 0.0
        
        popularity_score = 0.0
        content = str(result.extracted_data).lower()
        
        # Procurar por indicadores de popularidade
        for indicator in self.popularity_indicators:
            pattern = rf'{indicator}[:\s]*(\d+)'
            matches = re.findall(pattern, content)
            if matches:
                # Normalizar para 0-1
                count = max(matches, key=int)
                count_int = int(count)
                popularity_score += min(count_int / 1000, 1.0) * 0.1
        
        return min(popularity_score, 1.0)
    
    async def _calculate_extracted_data_value(self, result: SearchResult) -> float:
        """Calcula valor dos dados extraídos"""
        if not result.extracted_data:
            return 0.0
        
        value_score = 0.0
        
        # Emails têm alto valor
        emails = result.extracted_data.get('emails', [])
        if emails:
            value_score += len(emails) * 0.2
        
        # Telefones têm alto valor
        phones = result.extracted_data.get('phones', [])
        if phones:
            value_score += len(phones) * 0.15
        
        # Nomes têm valor médio
        names = result.extracted_data.get('names', [])
        if names:
            value_score += len(names) * 0.1
        
        # Links têm valor baixo
        links = result.extracted_data.get('links', [])
        if links:
            value_score += min(len(links) / 100, 0.3)
        
        # Conteúdo extraído tem valor
        if 'scraped_content' in result.extracted_data:
            content_length = len(result.extracted_data['scraped_content'])
            value_score += min(content_length / 10000, 0.5)
        
        return min(value_score, 1.0)
    
    async def _calculate_final_score(self, factors: RankingFactors) -> float:
        """Calcula score final combinando todos os fatores"""
        # Pesos para cada fator
        weights = {
            'title_relevance': 0.25,
            'content_relevance': 0.20,
            'source_authority': 0.20,
            'freshness': 0.10,
            'popularity': 0.10,
            'extracted_data_value': 0.10,
            'diversity_bonus': 0.05
        }
        
        score = (
            factors.title_relevance * weights['title_relevance'] +
            factors.content_relevance * weights['content_relevance'] +
            factors.source_authority * weights['source_authority'] +
            factors.freshness * weights['freshness'] +
            factors.popularity * weights['popularity'] +
            factors.extracted_data_value * weights['extracted_data_value'] +
            factors.diversity_bonus * weights['diversity_bonus']
        )
        
        return min(score, 1.0)
    
    async def _apply_diversification(self, results: List[SearchResult]) -> List[SearchResult]:
        """Aplica algoritmo de diversificação para evitar agrupamento"""
        if len(results) <= 10:
            return results
        
        # Agrupar por fonte
        source_groups = {}
        for result in results:
            source = result.source.lower()
            if source not in source_groups:
                source_groups[source] = []
            source_groups[source].append(result)
        
        # Selecionar resultados diversificados
        diversified = []
        sources_used = set()
        results_per_source = max(1, len(results) // len(source_groups))
        
        # Iterar até preencher todos ou esgotar
        while len(diversified) < len(results) and len(sources_used) < len(source_groups):
            for source, source_results in source_groups.items():
                if source not in sources_used and len(diversified) < len(results):
                    # Pegar até N resultados desta fonte
                    take_count = min(results_per_source, len(source_results))
                    for i in range(take_count):
                        if i < len(source_results):
                            # Aplicar bônus de diversificação
                            source_results[i].ranking_factors.diversity_bonus = 0.2
                            diversified.append(source_results[i])
                    
                    sources_used.add(source)
            
            # Reduzir limite para próxima rodada
            results_per_source = max(1, results_per_source // 2)
        
        # Adicionar resultados restantes
        for result in results:
            if result not in diversified:
                diversified.append(result)
        
        return diversified
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificação de saúde do ranking engine"""
        return {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'source_authority_scores': len(self.source_authority_scores),
            'popularity_indicators': len(self.popularity_indicators)
        }
