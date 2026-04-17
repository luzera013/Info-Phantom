"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Data Aggregator
Sistema centralizado de agregação e unificação de dados de múltiplas fontes
"""

import asyncio
import json
import time
import hashlib
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import Counter, defaultdict
import re
import logging

from ..core.pipeline import SearchResult
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class UnifiedResult:
    """Resultado unificado de múltiplas fontes"""
    source: str
    title: str
    link: str
    content: str
    analysis: Dict[str, Any]
    extra: Dict[str, Any]
    relevance_score: float
    timestamp: float
    trust_score: float
    freshness_score: float

class DataAggregator:
    """Agregador central de dados de múltiplas fontes"""
    
    def __init__(self):
        self.unified_results: List[UnifiedResult] = []
        self.source_stats: Dict[str, int] = defaultdict(int)
        self.entity_counts: Dict[str, int] = defaultdict(int)
        self.deduplication_cache: Set[str] = set()
        
    async def aggregate_all_sources(self, query: str, 
                                web_results: List[SearchResult] = None,
                                news_results: List[SearchResult] = None,
                                wikipedia_results: List[SearchResult] = None,
                                github_results: List[SearchResult] = None,
                                reddit_results: List[SearchResult] = None,
                                tor_results: List[SearchResult] = None,
                                **other_sources) -> Dict[str, Any]:
        """
        Agrega dados de TODAS as fontes em uma única estrutura unificada
        
        Args:
            query: Query original
            web_results: Resultados da busca web
            news_results: Resultados de notícias
            wikipedia_results: Resultados da Wikipedia
            github_results: Resultados do GitHub
            reddit_results: Resultados do Reddit
            tor_results: Resultados da rede Tor
            **other_sources: Outras fontes de dados
            
        Returns:
            Estrutura unificada completa com todos os dados
        """
        logger.info(f"🔄 Iniciando agregação unificada para: '{query}'")
        
        # Coletar todos os resultados de todas as fontes
        all_sources = {
            'web': web_results or [],
            'news': news_results or [],
            'wikipedia': wikipedia_results or [],
            'github': github_results or [],
            'reddit': reddit_results or [],
            'tor': tor_results or []
        }
        
        # Adicionar outras fontes dinamicamente
        for source_name, results in other_sources.items():
            if results:
                all_sources[source_name] = results
        
        # Processar cada fonte
        for source_name, results in all_sources.items():
            if results:
                logger.info(f"📊 Processando {len(results)} resultados da fonte: {source_name}")
                await self._process_source_results(source_name, results, query)
        
        # Eliminar duplicados e mesclar informações
        await self._deduplicate_and_merge()
        
        # Gerar resumo inteligente de tudo
        summary = await self._generate_unified_summary(query)
        
        # Construir resposta final unificada
        unified_response = {
            "query": query,
            "total": len(self.unified_results),
            "sources_analyzed": list(all_sources.keys()),
            "source_distribution": dict(self.source_stats),
            "data": [],
            "summary": summary,
            "generated_at": datetime.now().isoformat(),
            "aggregation_stats": {
                "total_raw_results": sum(len(results) for results in all_sources.values()),
                "unique_results": len(self.unified_results),
                "deduplication_rate": self._calculate_deduplication_rate(all_sources),
                "entity_extraction_count": dict(self.entity_counts)
            }
        }
        
        # Adicionar dados unificados à resposta
        for result in self.unified_results:
            unified_response["data"].append({
                "source": result.source,
                "title": result.title,
                "link": result.link,
                "content": result.content,
                "analysis": result.analysis,
                "extra": result.extra,
                "relevance_score": result.relevance_score,
                "trust_score": result.trust_score,
                "freshness_score": result.freshness_score
            })
        
        logger.info(f"✅ Agregação concluída: {len(self.unified_results)} resultados únicos")
        return unified_response
    
    async def _process_source_results(self, source_name: str, 
                                   results: List[SearchResult], 
                                   query: str):
        """Processa resultados de uma fonte específica"""
        for result in results:
            # Criar hash para deduplicação
            content_hash = self._generate_content_hash(result)
            
            if content_hash in self.deduplication_cache:
                logger.debug(f"🔄 Duplicado detectado: {result.title[:50]}...")
                continue
            
            self.deduplication_cache.add(content_hash)
            
            # Enriquecer análise do conteúdo
            enhanced_analysis = await self._enhance_content_analysis(result, query)
            
            # Criar resultado unificado
            unified_result = UnifiedResult(
                source=f"{source_name}_{result.source}" if source_name != result.source else result.source,
                title=result.title,
                link=result.url,
                content=self._extract_full_content(result),
                analysis=enhanced_analysis,
                extra=self._extract_extra_metadata(result),
                relevance_score=self._calculate_unified_relevance(result, query),
                timestamp=result.timestamp or time.time(),
                trust_score=self._calculate_trust_score(result),
                freshness_score=self._calculate_freshness_score(result)
            )
            
            self.unified_results.append(unified_result)
            self.source_stats[source_name] += 1
            
            # Contar entidades para estatísticas
            if enhanced_analysis.get('emails'):
                self.entity_counts['emails'] += len(enhanced_analysis['emails'])
            if enhanced_analysis.get('phones'):
                self.entity_counts['phones'] += len(enhanced_analysis['phones'])
            if enhanced_analysis.get('names'):
                self.entity_counts['names'] += len(enhanced_analysis['names'])
    
    async def _enhance_content_analysis(self, result: SearchResult, 
                                      query: str) -> Dict[str, Any]:
        """ Enriquece a análise de conteúdo com múltiplas técnicas"""
        analysis = {
            "emails": [],
            "phones": [],
            "names": [],
            "companies": [],
            "addresses": [],
            "keywords": [],
            "sentiment": "neutral",
            "topics": [],
            "quality_score": 0.0,
            "trust_indicators": []
        }
        
        # Combinar todo o conteúdo para análise
        full_content = f"{result.title} {result.description}"
        if result.extracted_data:
            # Extrair dados extraídos
            if isinstance(result.extracted_data, dict):
                for key, value in result.extracted_data.items():
                    if key in analysis and isinstance(value, list):
                        analysis[key].extend(value)
                    elif key not in analysis:
                        analysis[key] = value
        
        # Extração avançada de entidades
        content_text = full_content.lower()
        
        # Emails - múltiplos padrões
        email_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        ]
        for pattern in email_patterns:
            emails = re.findall(pattern, content_text)
            analysis["emails"].extend(emails)
        
        # Telefones - padrões internacionais
        phone_patterns = [
            r'\b\+?\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,4}\b',
            r'\b\(\d{2,3}\)\s?\d{4,5}[-.\s]?\d{4}\b',
            r'\b\d{4}[-.\s]?\d{4}[-.\s]?\d{4}\b'
        ]
        for pattern in phone_patterns:
            phones = re.findall(pattern, content_text)
            analysis["phones"].extend(phones)
        
        # Nomes - padrões de nomes próprios
        name_patterns = [
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',  # Nome completo
            r'\b[A-Z][a-z]+\s+[A-Z]\.\s+[A-Z][a-z]+\b',  # Nome com abreviação
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b'  # Nome completo com sobrenome composto
        ]
        for pattern in name_patterns:
            names = re.findall(pattern, full_content)
            analysis["names"].extend(names)
        
        # Empresas - indicadores
        company_indicators = ['ltda', 'sa', 'inc', 'mei', 'company', 'corporation', 'group', 's.a.']
        words = content_text.split()
        analysis["companies"] = [
            word for word in words 
            if any(indicator in word.lower() for indicator in company_indicators)
        ]
        
        # Endereços - padrões brasileiros
        address_patterns = [
            r'[A-Z][a-z]+,\s*[A-Z][a-z]+\s*\d{5}[-.\s]?\d{3}',
            r'[A-Z][a-z]+\s*\d{3}[-.\s]?\d{3}[-.\s]?\d{3}'
        ]
        for pattern in address_patterns:
            addresses = re.findall(pattern, full_content)
            analysis["addresses"].extend(addresses)
        
        # Palavras-chave - remover stopwords e extrair mais relevantes
        stopwords = {'o', 'a', 'os', 'as', 'da', 'de', 'do', 'em', 'um', 'para', 'com', 'na', 'no', 'por', 'se', 'mais', 'mas', 'ao', 'pelo', 'que', 'como', 'dos', 'das', 'à', 'às'}
        words_filtered = [
            word for word in words 
            if len(word) > 3 and word.lower() not in stopwords
        ]
        word_freq = Counter(words_filtered)
        analysis["keywords"] = [word for word, count in word_freq.most_common(15)]
        
        # Análise de sentimento
        positive_words = ['bom', 'ótimo', 'excelente', 'sucesso', 'feliz', 'positivo', 'cresceu', 'melhorou', 'avanço', 'conquista']
        negative_words = ['ruim', 'péssimo', 'falha', 'erro', 'problema', 'prejuízo', 'crise', 'fracasso']
        
        pos_count = sum(1 for word in positive_words if word in content_text)
        neg_count = sum(1 for word in negative_words if word in content_text)
        
        if pos_count > neg_count:
            analysis["sentiment"] = "positive"
        elif neg_count > pos_count:
            analysis["sentiment"] = "negative"
        
        # Tópicos baseados em palavras-chave
        topic_keywords = {
            'tecnologia': ['tecnologia', 'software', 'aplicativo', 'sistema', 'plataforma', 'digital'],
            'negócios': ['negócio', 'empresa', 'lucro', 'venda', 'cliente', 'mercado'],
            'educação': ['educação', 'escola', 'universidade', 'curso', 'aprendizado'],
            'saúde': ['saúde', 'médico', 'hospital', 'tratamento', 'doença'],
            'entretenimento': ['filme', 'música', 'jogo', 'esporte', 'show']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in content_text for keyword in keywords):
                analysis["topics"].append(topic)
        
        # Score de qualidade
        quality_score = 0.0
        if result.title and len(result.title) > 10:
            quality_score += 0.3
        if result.description and len(result.description) > 50:
            quality_score += 0.3
        if result.extracted_data:
            quality_score += 0.2
        if result.relevance_score > 0.5:
            quality_score += 0.2
        
        analysis["quality_score"] = min(quality_score, 1.0)
        
        # Indicadores de confiança
        trust_indicators = []
        if result.url.startswith('https://'):
            trust_indicators.append("secure_connection")
        if any(trusted in result.url.lower() for trusted in ['wikipedia', 'github', 'stackoverflow']):
            trust_indicators.append("trusted_source")
        if any(edu in result.url for edu in ['.edu', '.gov', '.org']):
            trust_indicators.append("authoritative_domain")
        
        analysis["trust_indicators"] = trust_indicators
        
        # Limpar e deduplicar listas
        for key in ['emails', 'phones', 'names', 'companies', 'addresses', 'keywords']:
            if key in analysis:
                analysis[key] = list(set(analysis[key]))[:10]  # Limitar para performance
        
        return analysis
    
    def _extract_full_content(self, result: SearchResult) -> str:
        """Extrai conteúdo completo combinando título, descrição e dados extraídos"""
        content_parts = []
        
        if result.title:
            content_parts.append(f"TÍTULO: {result.title}")
        
        if result.description:
            content_parts.append(f"DESCRIÇÃO: {result.description}")
        
        # Adicionar dados extraídos relevantes
        if result.extracted_data and isinstance(result.extracted_data, dict):
            for key, value in result.extracted_data.items():
                if value and key in ['emails', 'phones', 'companies', 'addresses']:
                    if isinstance(value, list) and value:
                        content_parts.append(f"{key.upper()}: {', '.join(str(v) for v in value[:5])}")
        
        return " | ".join(content_parts)
    
    def _extract_extra_metadata(self, result: SearchResult) -> Dict[str, Any]:
        """Extrai metadados extras do resultado"""
        metadata = {
            "source_type": self._classify_source_type(result.source),
            "content_length": len(result.description or ""),
            "has_extracted_data": bool(result.extracted_data),
            "extracted_data_types": [],
            "url_domain": self._extract_domain(result.url),
            "publication_date": result.timestamp,
            "relevance_category": self._categorize_relevance(result.relevance_score)
        }
        
        if result.extracted_data and isinstance(result.extracted_data, dict):
            metadata["extracted_data_types"] = [
                key for key, value in result.extracted_data.items() 
                if value and isinstance(value, (list, dict, str))
            ]
        
        return metadata
    
    def _generate_content_hash(self, result: SearchResult) -> str:
        """Gera hash único para deduplicação de conteúdo"""
        content = f"{result.title}{result.url}{result.source}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _calculate_unified_relevance(self, result: SearchResult, query: str) -> float:
        """Calcula score de relevância unificado considerando múltiplos fatores"""
        base_score = result.relevance_score or 0.0
        
        # Fator de correspondência exata
        query_lower = query.lower()
        title_lower = (result.title or "").lower()
        desc_lower = (result.description or "").lower()
        
        exact_match_bonus = 0.0
        if query_lower in title_lower:
            exact_match_bonus += 0.3
            if title_lower.startswith(query_lower):
                exact_match_bonus += 0.2  # Bônus por começar com a query
        if query_lower in desc_lower:
            exact_match_bonus += 0.2
        
        # Fator de qualidade do conteúdo
        quality_factor = 0.0
        if result.title and len(result.title) > 10:
            quality_factor += 0.2
        if result.description and len(result.description) > 100:
            quality_factor += 0.2
        if result.extracted_data:
            quality_factor += 0.1
        
        # Fator de confiança da fonte
        source_weights = {
            'wikipedia': 0.9,
            'github': 0.85,
            'reddit': 0.7,
            'news': 0.8,
            'web': 0.6,
            'bing': 0.75,
            'tor': 0.4
        }
        
        source_factor = source_weights.get(result.source.lower(), 0.5)
        
        # Combinar todos os fatores
        unified_score = (
            base_score * 0.5 +           # Score base (50%)
            exact_match_bonus * 0.3 +      # Correspondência exata (30%)
            quality_factor * 0.15 +          # Qualidade (15%)
            source_factor * 0.05              # Fonte (5%)
        )
        
        return min(unified_score, 1.0)
    
    def _calculate_trust_score(self, result: SearchResult) -> float:
        """Calcula score de confiança do resultado"""
        score = 0.5  # Base
        
        # HTTPS
        if result.url and result.url.startswith('https://'):
            score += 0.2
        
        # Fontes confiáveis
        trusted_sources = ['wikipedia', 'github', 'stackoverflow', 'w3', 'mozilla']
        if any(trusted in result.source.lower() for trusted in trusted_sources):
            score += 0.2
        
        # Domínios educacionais/governamentais
        edu_domains = ['.edu', '.gov', '.org']
        if any(domain in (result.url or "") for domain in edu_domains):
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_freshness_score(self, result: SearchResult) -> float:
        """Calcula score de frescor do resultado"""
        if not result.timestamp:
            return 0.0
        
        age_hours = (time.time() - result.timestamp) / 3600
        
        if age_hours < 1:
            return 1.0
        elif age_hours < 24:
            return 0.8
        elif age_hours < 168:  # 1 semana
            return 0.6
        elif age_hours < 720:  # 1 mês
            return 0.4
        else:
            return 0.2
    
    async def _deduplicate_and_merge(self):
        """Elimina duplicados e mescla informações semelhantes"""
        logger.info("🔄 Iniciando deduplicação e mesclagem...")
        
        # Agrupar resultados similares
        similarity_groups = []
        processed_indices = set()
        
        for i, result1 in enumerate(self.unified_results):
            if i in processed_indices:
                continue
                
            group = [i]
            processed_indices.add(i)
            
            for j, result2 in enumerate(self.unified_results[i+1:], i+1):
                if j in processed_indices:
                    continue
                    
                similarity = self._calculate_content_similarity(result1, result2)
                if similarity > 0.7:  # 70% de similaridade
                    group.append(j)
                    processed_indices.add(j)
            
            if len(group) > 1:
                similarity_groups.append(group)
        
        # Mesclar grupos similares
        for group in similarity_groups:
            if len(group) > 1:
                await self._merge_similar_results(group)
        
        # Ordenar por relevância final
        self.unified_results.sort(
            key=lambda x: (x.relevance_score * 0.5 + x.trust_score * 0.3 + x.freshness_score * 0.2),
            reverse=True
        )
        
        logger.info(f"✅ Deduplicação concluída: {len(similarity_groups)} grupos mesclados")
    
    def _calculate_content_similarity(self, result1: UnifiedResult, result2: UnifiedResult) -> float:
        """Calcula similaridade entre dois resultados"""
        # Similaridade de título
        title1_words = set(result1.title.lower().split())
        title2_words = set(result2.title.lower().split())
        title_similarity = len(title1_words & title2_words) / max(len(title1_words | title2_words), 1)
        
        # Similaridade de URL (domínio)
        domain1 = self._extract_domain(result1.link)
        domain2 = self._extract_domain(result2.link)
        url_similarity = 1.0 if domain1 and domain1 == domain2 else 0.0
        
        # Similaridade combinada
        return (title_similarity * 0.7 + url_similarity * 0.3)
    
    async def _merge_similar_results(self, indices: List[int]):
        """Mescla resultados similares mantendo o melhor"""
        if len(indices) < 2:
            return
        
        # Encontrar o melhor resultado (maior relevância)
        best_index = max(indices, key=lambda i: self.unified_results[i].relevance_score)
        best_result = self.unified_results[best_index]
        
        # Mesclar informações de todos os resultados do grupo
        merged_analysis = {
            "emails": [],
            "phones": [],
            "names": [],
            "companies": [],
            "addresses": [],
            "keywords": [],
            "sentiment": "neutral",
            "topics": [],
            "quality_score": 0.0,
            "trust_indicators": []
        }
        
        all_sources = []
        
        for idx in indices:
            result = self.unified_results[idx]
            all_sources.append(result.source)
            
            # Combinar análises
            for key in merged_analysis.keys():
                if key in result.analysis and isinstance(result.analysis[key], list):
                    merged_analysis[key].extend(result.analysis[key])
        
        # Limpar e deduplicar
        for key in merged_analysis.keys():
            merged_analysis[key] = list(set(merged_analysis[key]))[:10]
        
        # Atualizar o melhor resultado com informações mescladas
        best_result.analysis = merged_analysis
        best_result.extra["merged_sources"] = all_sources
        best_result.extra["merge_count"] = len(indices)
        
        # Remover outros resultados do grupo (manter apenas o melhor)
        indices_to_remove = [idx for idx in indices if idx != best_index]
        for idx in sorted(indices_to_remove, reverse=True):
            del self.unified_results[idx]
    
    async def _generate_unified_summary(self, query: str) -> str:
        """Gera resumo inteligente unificado de TODAS as fontes"""
        if not self.unified_results:
            return f"Não foram encontrados resultados para a query: '{query}'"
        
        # Estatísticas gerais
        total_results = len(self.unified_results)
        sources = list(set(result.source for result in self.unified_results))
        
        # Análise de sentimento geral
        sentiments = [result.analysis.get('sentiment', 'neutral') for result in self.unified_results]
        sentiment_counts = Counter(sentiments)
        overall_sentiment = sentiment_counts.most_common(1)[0][0] if sentiment_counts else 'neutral'
        
        # Tópicos mais comuns
        all_topics = []
        for result in self.unified_results:
            all_topics.extend(result.analysis.get('topics', []))
        topic_counts = Counter(all_topics)
        top_topics = [topic for topic, count in topic_counts.most_common(5)]
        
        # Entidades mais encontradas
        all_emails = []
        all_phones = []
        all_companies = []
        
        for result in self.unified_results:
            all_emails.extend(result.analysis.get('emails', []))
            all_phones.extend(result.analysis.get('phones', []))
            all_companies.extend(result.analysis.get('companies', []))
        
        # Qualidade média dos resultados
        avg_quality = sum(
            result.analysis.get('quality_score', 0.0) 
            for result in self.unified_results
        ) / total_results
        
        # Construir resumo inteligente
        summary_parts = [
            f"📊 ANÁLISE COMPLETA PARA: '{query}'",
            f"",
            f"🔍 ESTATÍSTICAS GERAIS:",
            f"• Total de resultados únicos: {total_results}",
            f"• Fontes analisadas: {', '.join(sources)}",
            f"• Qualidade média: {avg_quality:.2%}",
            f"",
            f"🎯 ANÁLISE DE CONTEÚDO:",
            f"• Sentimento predominante: {overall_sentiment}",
            f"• Tópicos principais: {', '.join(top_topics) if top_topics else 'Nenhum identificado'}",
            f"",
            f"📋 ENTIDADES EXTRAÍDAS:",
            f"• Emails únicos: {len(set(all_emails))}",
            f"• Telefones únicos: {len(set(all_phones))}",
            f"• Empresas identificadas: {len(set(all_companies))}",
        ]
        
        # Adicionar insights específicos baseados nos dados
        if len(set(all_emails)) > 5:
            summary_parts.append(f"• 📧 Alta concentração de emails detectada - possível lista de contatos")
        
        if len(set(all_companies)) > 3:
            summary_parts.append(f"• 🏢 Múltiplas empresas identificadas - contexto corporativo")
        
        if overall_sentiment == 'positive':
            summary_parts.append(f"• 😊 Conteúdo geralmente positivo - favorável para negócios")
        elif overall_sentiment == 'negative':
            summary_parts.append(f"• ⚠️ Conteúdo com tendências negativas - atenção necessária")
        
        # Top resultados por relevância
        if self.unified_results:
            summary_parts.extend([
                f"",
                f"🏆 RESULTADOS PRINCIPAIS (por relevância):"
            ])
            
            for i, result in enumerate(self.unified_results[:5], 1):
                summary_parts.append(
                    f"{i}. {result.title[:80]}{'...' if len(result.title) > 80 else ''} "
                    f"[Fonte: {result.source} | Relevância: {result.relevance_score:.2%}]"
                )
        
        # Recomendações baseadas na análise
        summary_parts.extend([
            f"",
            f"💡 RECOMENDAÇÕES INTELIGENTES:",
        ])
        
        if len(sources) > 3:
            summary_parts.append("• Alta diversidade de fontes - informações bem fundamentadas")
        
        if avg_quality > 0.7:
            summary_parts.append("• Alta qualidade geral dos resultados - dados confiáveis")
        elif avg_quality < 0.4:
            summary_parts.append("• Qualidade moderada - verificação recomendada")
        
        return "\n".join(summary_parts)
    
    def _classify_source_type(self, source: str) -> str:
        """Classifica o tipo da fonte"""
        source_lower = source.lower()
        
        if 'wikipedia' in source_lower:
            return 'knowledge_base'
        elif 'github' in source_lower:
            return 'code_repository'
        elif 'reddit' in source_lower:
            return 'social_forum'
        elif 'news' in source_lower or 'rss' in source_lower:
            return 'news'
        elif 'tor' in source_lower:
            return 'anonymous_network'
        else:
            return 'web_search'
    
    def _extract_domain(self, url: str) -> str:
        """Extrai domínio da URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except:
            return ""
    
    def _categorize_relevance(self, score: float) -> str:
        """Categoriza o nível de relevância"""
        if score >= 0.8:
            return 'alta'
        elif score >= 0.5:
            return 'media'
        elif score >= 0.3:
            return 'baixa'
        else:
            return 'muito_baixa'
    
    def _calculate_deduplication_rate(self, all_sources: Dict[str, List[SearchResult]]) -> float:
        """Calcula taxa de deduplicação"""
        total_raw = sum(len(results) for results in all_sources.values())
        total_unique = len(self.unified_results)
        
        if total_raw == 0:
            return 0.0
        
        return ((total_raw - total_unique) / total_raw) * 100
