"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Advanced Search Engine
Motor de busca avançado com inteligência artificial e otimização extrema
"""

import asyncio
import time
import hashlib
import re
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import logging
import json

from ..collectors.massive_collector_factory import MassiveCollectorFactory, UnifiedSearchResult
from ..utils.logger import setup_logger
from ..utils.metrics import MetricsCollector
from ..utils.ttl_cache import TTLCache

logger = setup_logger(__name__)
metrics = MetricsCollector()

@dataclass
class SearchQuery:
    """Estrutura avançada para queries de busca"""
    original: str
    processed: str
    keywords: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    intent: str = "general"  # general, news, academic, technical, etc.
    language: str = "pt"
    filters: Dict[str, Any] = field(default_factory=dict)
    boost_terms: List[str] = field(default_factory=list)
    exclude_terms: List[str] = field(default_factory=list)

@dataclass
class SearchContext:
    """Contexto de busca para personalização"""
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    search_history: List[str] = field(default_factory=list)
    location: Optional[str] = None
    time_context: str = "current"  # current, recent, historical
    domain_preferences: List[str] = field(default_factory=list)
    quality_threshold: float = 0.5

@dataclass
class SearchResultCluster:
    """Cluster de resultados similares"""
    cluster_id: str
    centroid: UnifiedSearchResult
    members: List[UnifiedSearchResult] = field(default_factory=list)
    similarity_score: float = 0.0
    topic_label: str = ""
    confidence: float = 0.0

class AdvancedSearchEngine:
    """Motor de busca avançado com IA e otimização extrema"""
    
    def __init__(self):
        self.factory = MassiveCollectorFactory()
        self.cache = TTLCache(ttl=3600)  # 1 hora
        self.query_cache = TTLCache(ttl=1800)  # 30 minutos
        self.search_history: List[SearchQuery] = []
        self.performance_stats = {
            'total_searches': 0,
            'avg_response_time': 0.0,
            'cache_hit_rate': 0.0,
            'cluster_accuracy': 0.0
        }
        
        # Configurações de otimização
        self.optimization_config = {
            'max_concurrent_searches': 12,
            'result_deduplication_threshold': 0.8,
            'clustering_enabled': True,
            'semantic_search_enabled': True,
            'personalization_enabled': True,
            'quality_filter_enabled': True
        }
        
        logger.info(" Advanced Search Engine inicializado")
    
    async def initialize(self):
        """Inicializa o motor de busca avançado"""
        await self.factory.initialize()
        logger.info(" Advanced Search Engine pronto")
    
    async def intelligent_search(self, 
                               query: str, 
                               context: Optional[SearchContext] = None,
                               max_results: int = 100) -> Dict[str, Any]:
        """
        Busca inteligente com processamento avançado de query
        
        Args:
            query: Query de busca original
            context: Contexto de busca para personalização
            max_results: Número máximo de resultados
            
        Returns:
            Resultados processados com inteligência artificial
        """
        start_time = time.time()
        search_id = hashlib.md5(f"{query}_{time.time()}".encode()).hexdigest()[:8]
        
        logger.info(f" Iniciando busca inteligente #{search_id}: '{query}'")
        
        try:
            # Verificar cache
            cache_key = f"intelligent_search:{hashlib.md5(query.encode()).hexdigest()}:{max_results}"
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                logger.info(f" Cache hit para busca #{search_id}")
                metrics.increment_cache_hit()
                return cached_result
            
            # Processar query com NLP avançado
            processed_query = await self._process_query(query, context)
            
            # Executar busca massiva com otimização
            raw_results = await self._execute_optimized_search(processed_query, max_results)
            
            # Aplicar filtros inteligentes
            filtered_results = await self._apply_intelligent_filters(raw_results, processed_query, context)
            
            # Clustering de resultados
            clustered_results = await self._cluster_results(filtered_results) if self.optimization_config['clustering_enabled'] else filtered_results
            
            # Ranking avançado com machine learning
            ranked_results = await self._advanced_ranking(clustered_results, processed_query, context)
            
            # Enriquecimento de resultados
            enriched_results = await self._enrich_results(ranked_results, processed_query)
            
            # Gerar insights e estatísticas
            insights = await self._generate_search_insights(enriched_results, processed_query)
            
            # Construir resposta final
            response = {
                'search_id': search_id,
                'query': {
                    'original': query,
                    'processed': processed_query.processed,
                    'keywords': processed_query.keywords,
                    'intent': processed_query.intent
                },
                'results': [self._format_result(r) for r in enriched_results],
                'clusters': self._format_clusters(clustered_results) if self.optimization_config['clustering_enabled'] else [],
                'insights': insights,
                'stats': {
                    'total_results': len(enriched_results),
                    'processing_time': time.time() - start_time,
                    'sources_used': list(set(r.source for r in enriched_results)),
                    'quality_score': self._calculate_overall_quality(enriched_results),
                    'diversity_score': self._calculate_diversity_score(enriched_results)
                },
                'timestamp': datetime.now().isoformat()
            }
            
            # Salvar em cache
            await self.cache.set(cache_key, response)
            
            # Atualizar estatísticas
            self._update_performance_stats(time.time() - start_time)
            
            logger.info(f" Busca inteligente #{search_id} concluída em {time.time() - start_time:.2f}s")
            return response
            
        except Exception as e:
            logger.error(f" Erro na busca inteligente #{search_id}: {str(e)}")
            # Retornar resultado de fallback
            return await self._generate_fallback_response(query, search_id, str(e))
    
    async def _process_query(self, query: str, context: Optional[SearchContext]) -> SearchQuery:
        """Processa query com NLP avançado"""
        processed_query = SearchQuery(
            original=query,
            processed=query.lower().strip(),
            keywords=self._extract_keywords(query),
            entities=self._extract_entities(query),
            intent=self._detect_intent(query),
            language=self._detect_language(query),
            filters=self._extract_filters(query),
            boost_terms=self._extract_boost_terms(query),
            exclude_terms=self._extract_exclude_terms(query)
        )
        
        # Aplicar contexto se disponível
        if context:
            processed_query = self._apply_context_to_query(processed_query, context)
        
        logger.debug(f" Query processada: {processed_query.keywords} (intent: {processed_query.intent})")
        return processed_query
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extrai palavras-chave da query"""
        # Remover stop words e extrair termos importantes
        stop_words = {'o', 'a', 'os', 'as', 'de', 'do', 'da', 'em', 'para', 'com', 'sem', 'por', 'sobre', 'como', 'que', 'qual'}
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        # Adicionar termos compostos
        compound_terms = re.findall(r'\b\w+\s+\w+\b', query.lower())
        keywords.extend(compound_terms)
        
        return list(set(keywords))
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extrai entidades nomeadas da query"""
        entities = []
        
        # Padrões para entidades comuns
        patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b\d{2,4}[-.\s]?\d{4,5}[-.\s]?\d{4}\b',
            'url': r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?',
            'date': r'\b\d{1,2}/\d{1,2}/\d{4}\b|\b\d{4}-\d{2}-\d{2}\b'
        }
        
        for entity_type, pattern in patterns.items():
            matches = re.findall(pattern, query)
            entities.extend(matches)
        
        return entities
    
    def _detect_intent(self, query: str) -> str:
        """Detecta a intenção da busca"""
        query_lower = query.lower()
        
        # Padrões de intenção
        intent_patterns = {
            'news': ['notícia', 'notícias', 'jornal', 'reportagem', 'últimas', 'hoje', 'recente'],
            'academic': ['pesquisa', 'estudo', 'artigo', 'científico', 'acadêmico', 'tese', 'dissertação'],
            'technical': ['tutorial', 'como', 'implementar', 'código', 'programação', 'desenvolvimento'],
            'commercial': ['preço', 'comprar', 'vender', 'promoção', 'desconto', 'oferta'],
            'location': ['onde', 'endereço', 'localização', 'próximo', 'região']
        }
        
        for intent, keywords in intent_patterns.items():
            if any(keyword in query_lower for keyword in keywords):
                return intent
        
        return 'general'
    
    def _detect_language(self, query: str) -> str:
        """Detecta o idioma da query"""
        # Implementação simplificada - em produção usar bibliotecas como langdetect
        pt_indicators = ['que', 'de', 'a', 'o', 'em', 'para', 'com', 'um', 'uma', 'dos', 'das']
        en_indicators = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with']
        
        query_lower = query.lower()
        pt_count = sum(1 for word in pt_indicators if word in query_lower)
        en_count = sum(1 for word in en_indicators if word in query_lower)
        
        if pt_count > en_count:
            return 'pt'
        elif en_count > pt_count:
            return 'en'
        
        return 'pt'  # Default para português
    
    def _extract_filters(self, query: str) -> Dict[str, Any]:
        """Extrai filtros da query"""
        filters = {}
        
        # Filtro de site
        site_match = re.search(r'site:(\S+)', query)
        if site_match:
            filters['site'] = site_match.group(1)
        
        # Filtro de filetype
        filetype_match = re.search(r'filetype:(\S+)', query)
        if filetype_match:
            filters['filetype'] = filetype_match.group(1)
        
        # Filtro de data
        date_match = re.search(r'after:(\S+)|before:(\S+)', query)
        if date_match:
            filters['date'] = date_match.group(0)
        
        return filters
    
    def _extract_boost_terms(self, query: str) -> List[str]:
        """Extrai termos de boost da query"""
        # Termos entre aspas recebem boost
        quoted_terms = re.findall(r'"([^"]+)"', query)
        return quoted_terms
    
    def _extract_exclude_terms(self, query: str) -> List[str]:
        """Extrai termos de exclusão da query"""
        # Termos precedidos por - ou NOT
        exclude_patterns = [r'-(\w+)', r'NOT\s+(\w+)', r'!(\w+)']
        exclude_terms = []
        
        for pattern in exclude_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            exclude_terms.extend(matches)
        
        return exclude_terms
    
    def _apply_context_to_query(self, query: SearchQuery, context: SearchContext) -> SearchQuery:
        """Aplica contexto à query para personalização"""
        # Adicionar preferências de domínio
        if context.domain_preferences:
            query.filters['preferred_domains'] = context.domain_preferences
        
        # Ajustar threshold de qualidade
        if context.quality_threshold != 0.5:
            query.filters['quality_threshold'] = context.quality_threshold
        
        # Adicionar termos do histórico
        if context.search_history:
            # Adicionar termos relevantes do histórico como boost
            recent_terms = []
            for hist_query in context.search_history[-5:]:  # Últimas 5 buscas
                recent_terms.extend(self._extract_keywords(hist_query))
            
            query.boost_terms.extend(recent_terms[:3])  # Top 3 termos recentes
        
        return query
    
    async def _execute_optimized_search(self, query: SearchQuery, max_results: int) -> List[UnifiedSearchResult]:
        """Executa busca otimizada usando a factory"""
        try:
            # Construir query otimizada
            optimized_query = self._build_optimized_query(query)
            
            # Executar busca massiva
            results = await self.factory.search_all(optimized_query, max_results // len(self.factory.collectors))
            
            logger.debug(f" Busca otimizada retornou {len(results)} resultados")
            return results
            
        except Exception as e:
            logger.error(f" Erro na busca otimizada: {str(e)}")
            return []
    
    def _build_optimized_query(self, query: SearchQuery) -> str:
        """Constrói query otimizada para os coletores"""
        query_parts = []
        
        # Adicionar termos principais
        if query.boost_terms:
            query_parts.extend(query.boost_terms)
        else:
            query_parts.append(query.processed)
        
        # Adicionar keywords
        if query.keywords:
            query_parts.extend(query.keywords[:3])  # Top 3 keywords
        
        # Construir query final
        if len(query_parts) > 1:
            optimized_query = ' '.join(query_parts[:2])  # Primeiros 2 termos
        else:
            optimized_query = query_parts[0]
        
        return optimized_query
    
    async def _apply_intelligent_filters(self, 
                                       results: List[UnifiedSearchResult], 
                                       query: SearchQuery,
                                       context: Optional[SearchContext]) -> List[UnifiedSearchResult]:
        """Aplica filtros inteligentes aos resultados"""
        filtered_results = []
        
        for result in results:
            # Verificar termos de exclusão
            if self._should_exclude_result(result, query.exclude_terms):
                continue
            
            # Verificar qualidade
            if self.optimization_config['quality_filter_enabled']:
                quality_score = self._calculate_result_quality(result)
                threshold = context.quality_threshold if context else 0.5
                if quality_score < threshold:
                    continue
            
            # Verificar relevância semântica
            if self.optimization_config['semantic_search_enabled']:
                semantic_score = self._calculate_semantic_relevance(result, query)
                if semantic_score < 0.3:  # Threshold mínimo
                    continue
            
            filtered_results.append(result)
        
        logger.debug(f" Filtros inteligentes: {len(results)} -> {len(filtered_results)} resultados")
        return filtered_results
    
    def _should_exclude_result(self, result: UnifiedSearchResult, exclude_terms: List[str]) -> bool:
        """Verifica se o resultado deve ser excluído"""
        if not exclude_terms:
            return False
        
        content_lower = f"{result.title} {result.content}".lower()
        
        for term in exclude_terms:
            if term.lower() in content_lower:
                return True
        
        return False
    
    def _calculate_result_quality(self, result: UnifiedSearchResult) -> float:
        """Calcula score de qualidade do resultado"""
        score = 0.0
        
        # Título e conteúdo relevantes
        if result.title and len(result.title) > 10:
            score += 0.2
        
        if result.content and len(result.content) > 50:
            score += 0.2
        
        # Fonte confiável
        trusted_sources = ['wikipedia', 'github', 'reddit', 'news_api']
        if any(source in result.source.lower() for source in trusted_sources):
            score += 0.3
        
        # Relevância existente
        score += result.relevance_score * 0.3
        
        return min(score, 1.0)
    
    def _calculate_semantic_relevance(self, result: UnifiedSearchResult, query: SearchQuery) -> float:
        """Calcula relevância semântica (simplificado)"""
        content = f"{result.title} {result.content}".lower()
        query_lower = query.processed.lower()
        
        # Jaccard similarity simplificado
        content_words = set(content.split())
        query_words = set(query_lower.split())
        
        if not content_words or not query_words:
            return 0.0
        
        intersection = len(content_words & query_words)
        union = len(content_words | query_words)
        
        return intersection / union if union > 0 else 0.0
    
    async def _cluster_results(self, results: List[UnifiedSearchResult]) -> List[UnifiedSearchResult]:
        """Agrupa resultados similares usando clustering"""
        if len(results) < 2:
            return results
        
        clusters = []
        processed = set()
        
        for i, result in enumerate(results):
            if i in processed:
                continue
            
            # Encontrar resultados similares
            similar_results = [result]
            similar_indices = {i}
            
            for j, other_result in enumerate(results):
                if j in processed or i == j:
                    continue
                
                similarity = self._calculate_similarity(result, other_result)
                if similarity > self.optimization_config['result_deduplication_threshold']:
                    similar_results.append(other_result)
                    similar_indices.add(j)
            
            # Criar cluster
            if len(similar_results) > 1:
                cluster = SearchResultCluster(
                    cluster_id=f"cluster_{len(clusters)}",
                    centroid=self._find_centroid(similar_results),
                    members=similar_results,
                    similarity_score=sum(self._calculate_similarity(result, other_result) 
                                      for other_result in similar_results[1:]) / len(similar_results),
                    topic_label=self._extract_topic_label(similar_results),
                    confidence=0.8
                )
                clusters.append(cluster)
            
            processed.update(similar_indices)
        
        # Adicionar resultados não clusterizados
        unclustered = [result for i, result in enumerate(results) if i not in processed]
        
        logger.debug(f" Clustering: {len(clusters)} clusters, {len(unclustered)} individuais")
        return results  # Por agora, retornar todos os resultados
    
    def _calculate_similarity(self, result1: UnifiedSearchResult, result2: UnifiedSearchResult) -> float:
        """Calcula similaridade entre dois resultados"""
        # Similaridade de título
        title1_words = set(result1.title.lower().split())
        title2_words = set(result2.title.lower().split())
        
        if not title1_words or not title2_words:
            return 0.0
        
        title_intersection = len(title1_words & title2_words)
        title_union = len(title1_words | title2_words)
        title_similarity = title_intersection / title_union if title_union > 0 else 0.0
        
        # Similaridade de URL (mesmo domínio)
        url_similarity = 0.0
        if result1.link and result2.link:
            domain1 = result1.link.split('/')[2] if len(result1.link.split('/')) > 2 else ''
            domain2 = result2.link.split('/')[2] if len(result2.link.split('/')) > 2 else ''
            url_similarity = 1.0 if domain1 == domain2 and domain1 else 0.0
        
        # Combinar similaridades
        overall_similarity = title_similarity * 0.7 + url_similarity * 0.3
        
        return overall_similarity
    
    def _find_centroid(self, results: List[UnifiedSearchResult]) -> UnifiedSearchResult:
        """Encontra o centróide de um cluster"""
        # Simplificação: retornar o resultado com maior relevância
        return max(results, key=lambda r: r.relevance_score)
    
    def _extract_topic_label(self, results: List[UnifiedSearchResult]) -> str:
        """Extrai rótulo do tópico do cluster"""
        # Simplificação: usar palavras mais comuns nos títulos
        all_words = []
        for result in results:
            all_words.extend(result.title.lower().split())
        
        word_counts = Counter(all_words)
        most_common = word_counts.most_common(1)
        
        return most_common[0][0] if most_common else "unknown"
    
    async def _advanced_ranking(self, 
                              results: List[UnifiedSearchResult], 
                              query: SearchQuery,
                              context: Optional[SearchContext]) -> List[UnifiedSearchResult]:
        """Ranking avançado usando múltiplos fatores"""
        for result in results:
            # Score base existente
            base_score = result.relevance_score
            
            # Fator de frescor
            freshness_factor = self._calculate_freshness_factor(result)
            
            # Fator de autoridade da fonte
            authority_factor = self._calculate_authority_factor(result)
            
            # Fator de personalização
            personalization_factor = self._calculate_personalization_factor(result, context)
            
            # Fator de diversidade
            diversity_factor = self._calculate_diversity_factor(result, results)
            
            # Combinar fatores
            final_score = (
                base_score * 0.4 +
                freshness_factor * 0.2 +
                authority_factor * 0.2 +
                personalization_factor * 0.1 +
                diversity_factor * 0.1
            )
            
            result.relevance_score = min(final_score, 1.0)
        
        # Ordenar por score final
        return sorted(results, key=lambda r: r.relevance_score, reverse=True)
    
    def _calculate_freshness_factor(self, result: UnifiedSearchResult) -> float:
        """Calcula fator de frescor"""
        if not result.timestamp:
            return 0.5
        
        age_hours = (time.time() - result.timestamp) / 3600
        
        if age_hours < 24:
            return 1.0
        elif age_hours < 168:  # 1 semana
            return 0.8
        elif age_hours < 720:  # 1 mês
            return 0.6
        else:
            return 0.4
    
    def _calculate_authority_factor(self, result: UnifiedSearchResult) -> float:
        """Calcula fator de autoridade da fonte"""
        authority_scores = {
            'wikipedia': 0.95,
            'github': 0.90,
            'news_api': 0.85,
            'reddit': 0.75,
            'rss': 0.70,
            'bing': 0.80,
            'web_search': 0.60,
            'onion': 0.30
        }
        
        return authority_scores.get(result.source.lower(), 0.5)
    
    def _calculate_personalization_factor(self, result: UnifiedSearchResult, context: Optional[SearchContext]) -> float:
        """Calcula fator de personalização"""
        if not context:
            return 0.5
        
        factor = 0.5
        
        # Preferências de domínio
        if context.domain_preferences:
            for domain in context.domain_preferences:
                if domain in result.link.lower():
                    factor += 0.2
                    break
        
        # Histórico de busca
        if context.search_history:
            for hist_query in context.search_history[-3:]:  # Últimas 3 buscas
                if hist_query.lower() in result.title.lower():
                    factor += 0.1
                    break
        
        return min(factor, 1.0)
    
    def _calculate_diversity_factor(self, result: UnifiedSearchResult, all_results: List[UnifiedSearchResult]) -> float:
        """Calcula fator de diversidade"""
        # Verificar diversidade de fontes
        sources = [r.source for r in all_results]
        source_counts = Counter(sources)
        
        # Dar boost para fontes menos representadas
        current_source_count = source_counts.get(result.source, 0)
        total_results = len(all_results)
        
        if total_results == 0:
            return 0.5
        
        source_ratio = current_source_count / total_results
        diversity_factor = 1.0 - source_ratio  # Fontes mais raras recebem mais boost
        
        return max(diversity_factor, 0.3)
    
    async def _enrich_results(self, results: List[UnifiedSearchResult], query: SearchQuery) -> List[UnifiedSearchResult]:
        """Enriquece resultados com informações adicionais"""
        for result in results:
            # Extrair entidades do conteúdo
            result.metadata['entities'] = self._extract_content_entities(result.content)
            
            # Detectar sentimento
            result.metadata['sentiment'] = self._detect_sentiment(result.content)
            
            # Extrair tópicos
            result.metadata['topics'] = self._extract_topics(result.content)
            
            # Calcular legibilidade
            result.metadata['readability_score'] = self._calculate_readability(result.content)
        
        return results
    
    def _extract_content_entities(self, content: str) -> List[str]:
        """Extrai entidades do conteúdo"""
        entities = []
        
        # Padrões simplificados para entidades
        patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b\d{2,4}[-.\s]?\d{4,5}[-.\s]?\d{4}\b',
            'url': r'https?://[^\s]+',
            'money': r'R\$\s*\d+(?:\.\d{2})?|\$\s*\d+(?:\.\d{2})?',
            'date': r'\b\d{1,2}/\d{1,2}/\d{4}\b'
        }
        
        for pattern in patterns.values():
            matches = re.findall(pattern, content)
            entities.extend(matches)
        
        return entities[:5]  # Limitar a 5 entidades
    
    def _detect_sentiment(self, content: str) -> str:
        """Detecta sentimento do conteúdo (simplificado)"""
        positive_words = ['bom', 'ótimo', 'excelente', 'maravilhoso', 'positivo', 'sucesso', 'feliz']
        negative_words = ['ruim', 'péssimo', 'horrível', 'terrível', 'negativo', 'falha', 'triste']
        
        content_lower = content.lower()
        
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        
        return 'neutral'
    
    def _extract_topics(self, content: str) -> List[str]:
        """Extrai tópicos do conteúdo"""
        # Simplificação: extrair palavras mais frequentes
        words = re.findall(r'\b\w+\b', content.lower())
        stop_words = {'o', 'a', 'os', 'as', 'de', 'do', 'da', 'em', 'para', 'com', 'que', 'e', 'é', 'um', 'uma'}
        
        filtered_words = [w for w in words if w not in stop_words and len(w) > 3]
        word_counts = Counter(filtered_words)
        
        return [word for word, count in word_counts.most_common(3)]
    
    def _calculate_readability(self, content: str) -> float:
        """Calcula score de legibilidade (simplificado)"""
        if not content:
            return 0.0
        
        sentences = content.split('.')
        words = content.split()
        
        if not sentences or not words:
            return 0.0
        
        avg_sentence_length = len(words) / len(sentences)
        
        # Score simplificado baseado no comprimento médio das sentenças
        if avg_sentence_length < 15:
            return 0.9  # Fácil leitura
        elif avg_sentence_length < 25:
            return 0.7  # Leitura moderada
        else:
            return 0.5  # Leitura difícil
    
    async def _generate_search_insights(self, 
                                      results: List[UnifiedSearchResult], 
                                      query: SearchQuery) -> Dict[str, Any]:
        """Gera insights da busca"""
        insights = {
            'query_analysis': {
                'complexity': len(query.keywords),
                'intent_confidence': 0.8,
                'language_detected': query.language
            },
            'result_analysis': {
                'source_distribution': Counter(r.source for r in results),
                'avg_relevance': sum(r.relevance_score for r in results) / len(results) if results else 0,
                'temporal_distribution': self._analyze_temporal_distribution(results),
                'topic_clusters': self._analyze_topic_clusters(results)
            },
            'quality_metrics': {
                'high_quality_results': len([r for r in results if r.relevance_score > 0.7]),
                'duplicate_rate': self._estimate_duplicate_rate(results),
                'coverage_score': self._calculate_coverage_score(results, query)
            },
            'recommendations': self._generate_recommendations(results, query)
        }
        
        return insights
    
    def _analyze_temporal_distribution(self, results: List[UnifiedSearchResult]) -> Dict[str, int]:
        """Analisa distribuição temporal dos resultados"""
        distribution = {
            'last_hour': 0,
            'last_day': 0,
            'last_week': 0,
            'last_month': 0,
            'older': 0
        }
        
        now = time.time()
        
        for result in results:
            if not result.timestamp:
                distribution['older'] += 1
                continue
            
            age_hours = (now - result.timestamp) / 3600
            
            if age_hours < 1:
                distribution['last_hour'] += 1
            elif age_hours < 24:
                distribution['last_day'] += 1
            elif age_hours < 168:
                distribution['last_week'] += 1
            elif age_hours < 720:
                distribution['last_month'] += 1
            else:
                distribution['older'] += 1
        
        return distribution
    
    def _analyze_topic_clusters(self, results: List[UnifiedSearchResult]) -> List[str]:
        """Analisa clusters de tópicos"""
        all_topics = []
        for result in results:
            all_topics.extend(result.metadata.get('topics', []))
        
        topic_counts = Counter(all_topics)
        return [topic for topic, count in topic_counts.most_common(5)]
    
    def _estimate_duplicate_rate(self, results: List[UnifiedSearchResult]) -> float:
        """Estima taxa de duplicados"""
        if len(results) < 2:
            return 0.0
        
        similar_pairs = 0
        total_pairs = 0
        
        for i in range(len(results)):
            for j in range(i + 1, len(results)):
                total_pairs += 1
                similarity = self._calculate_similarity(results[i], results[j])
                if similarity > 0.8:
                    similar_pairs += 1
        
        return similar_pairs / total_pairs if total_pairs > 0 else 0.0
    
    def _calculate_coverage_score(self, results: List[UnifiedSearchResult], query: SearchQuery) -> float:
        """Calcula score de cobertura da query"""
        if not results or not query.keywords:
            return 0.0
        
        covered_keywords = set()
        all_content = ' '.join(f"{r.title} {r.content}" for r in results).lower()
        
        for keyword in query.keywords:
            if keyword.lower() in all_content:
                covered_keywords.add(keyword)
        
        return len(covered_keywords) / len(query.keywords)
    
    def _generate_recommendations(self, results: List[UnifiedSearchResult], query: SearchQuery) -> List[str]:
        """Gera recomendações baseadas nos resultados"""
        recommendations = []
        
        # Se poucos resultados, sugerir expandir busca
        if len(results) < 10:
            recommendations.append("Tente usar termos mais genéricos ou remover filtros")
        
        # Se muitos resultados de baixa qualidade, sugerir refinar
        low_quality_count = len([r for r in results if r.relevance_score < 0.5])
        if low_quality_count > len(results) * 0.7:
            recommendations.append("Tente adicionar termos mais específicos para melhorar a qualidade")
        
        # Se resultados muito antigos, sugerir busca por recência
        old_results = len([r for r in results if r.timestamp and (time.time() - r.timestamp) > 86400 * 30])
        if old_results > len(results) * 0.8:
            recommendations.append("Tente adicionar filtros de data para resultados mais recentes")
        
        # Se resultados de poucas fontes, sugerir expandir fontes
        unique_sources = len(set(r.source for r in results))
        if unique_sources < 3:
            recommendations.append("Considere buscar em diferentes tipos de fontes")
        
        return recommendations
    
    def _format_result(self, result: UnifiedSearchResult) -> Dict[str, Any]:
        """Formata resultado para saída"""
        return {
            'source': result.source,
            'title': result.title,
            'link': result.link,
            'content': result.content,
            'timestamp': result.timestamp,
            'relevance_score': result.relevance_score,
            'metadata': result.metadata
        }
    
    def _format_clusters(self, results: List[UnifiedSearchResult]) -> List[Dict[str, Any]]:
        """Formata clusters para saída (simplificado)"""
        # Por enquanto, retorna lista vazia - clustering será implementado posteriormente
        return []
    
    def _calculate_overall_quality(self, results: List[UnifiedSearchResult]) -> float:
        """Calcula qualidade geral dos resultados"""
        if not results:
            return 0.0
        
        total_quality = sum(r.relevance_score for r in results)
        return total_quality / len(results)
    
    def _calculate_diversity_score(self, results: List[UnifiedSearchResult]) -> float:
        """Calcula score de diversidade das fontes"""
        if not results:
            return 0.0
        
        unique_sources = len(set(r.source for r in results))
        max_possible_sources = 8  # Número máximo de fontes diferentes
        
        return unique_sources / max_possible_sources
    
    def _update_performance_stats(self, response_time: float):
        """Atualiza estatísticas de performance"""
        self.performance_stats['total_searches'] += 1
        
        # Atualizar tempo médio de resposta
        old_avg = self.performance_stats['avg_response_time']
        total_searches = self.performance_stats['total_searches']
        new_avg = (old_avg * (total_searches - 1) + response_time) / total_searches
        self.performance_stats['avg_response_time'] = new_avg
    
    async def _generate_fallback_response(self, query: str, search_id: str, error: str) -> Dict[str, Any]:
        """Gera resposta de fallback em caso de erro"""
        return {
            'search_id': search_id,
            'query': {
                'original': query,
                'processed': query.lower(),
                'keywords': query.split(),
                'intent': 'general'
            },
            'results': [],
            'clusters': [],
            'insights': {
                'error': error,
                'fallback_used': True
            },
            'stats': {
                'total_results': 0,
                'processing_time': 0.0,
                'sources_used': [],
                'quality_score': 0.0,
                'diversity_score': 0.0
            },
            'timestamp': datetime.now().isoformat()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificação de saúde do motor de busca"""
        try:
            factory_health = await self.factory.get_collector_health()
            
            return {
                'status': 'healthy',
                'component': 'advanced_search_engine',
                'timestamp': datetime.now().isoformat(),
                'factory_health': factory_health,
                'performance_stats': self.performance_stats,
                'cache_status': {
                    'cache_size': len(self.cache.cache),
                    'query_cache_size': len(self.query_cache.cache)
                },
                'optimization_config': self.optimization_config
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'component': 'advanced_search_engine',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    async def cleanup(self):
        """Limpa recursos"""
        await self.factory.cleanup()
        self.cache.clear()
        self.query_cache.clear()
        logger.info(" Advanced Search Engine limpo")
