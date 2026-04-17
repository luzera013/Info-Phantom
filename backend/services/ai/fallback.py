"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Fallback AI Service
Serviço de IA de emergência quando os principais falham
"""

import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import time
import logging
import re
from collections import Counter
from datetime import datetime

from ...core.pipeline import SearchResult
from ...utils.logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class FallbackConfig:
    """Configuração do serviço fallback"""
    max_summary_length: int = 1500
    enable_basic_analysis: bool = True
    enable_pattern_detection: bool = True
    enable_entity_extraction: bool = True
    language: str = "pt"

class FallbackAIService:
    """Serviço de IA fallback"""
    
    def __init__(self, config: Optional[FallbackConfig] = None):
        self.config = config or FallbackConfig()
        
        # Padrões para análise
        self.patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b\d{2,4}[-.\s]?\d{2,4}[-.\s]?\d{4,}\b',
            'url': r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?',
            'date': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
            'price': r'\b[R$€£$]\s*\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?\b',
            'cnpj': r'\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b',
            'cpf': r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b'
        }
        
        # Indicadores de importância
        self.importance_indicators = {
            'critical': ['urgente', 'emergência', 'crítico', 'grave', 'importante', 'essencial'],
            'high': ['novo', 'recente', 'atualizado', 'principal', 'destaque', 'oficial'],
            'medium': ['informação', 'detalhe', 'guia', 'tutorial', 'ajuda', 'suporte'],
            'low': ['antigo', 'desatualizado', 'arquivo', 'histórico', 'legado']
        }
        
        logger.info("🛡️ Fallback AI Service inicializado")
    
    async def generate_summary(self, query: str, results: List[SearchResult]) -> str:
        """
        Gera resumo usando métodos básicos
        
        Args:
            query: Query original
            results: Lista de resultados
            
        Returns:
            Resumo gerado
        """
        if not results:
            return f"Nenhum resultado encontrado para '{query}'."
        
        logger.info(f"🛡️ Gerando resumo fallback: '{query}' ({len(results)} resultados)")
        
        try:
            # Análise básica
            basic_stats = await self._basic_statistics(results)
            
            # Detecção de padrões
            pattern_analysis = await self._detect_patterns(results)
            
            # Extração de entidades
            entities = await self._extract_entities(results)
            
            # Análise de importância
            importance_analysis = await self._analyze_importance(results, query)
            
            # Construir resumo
            summary = await self._build_fallback_summary(
                query, basic_stats, pattern_analysis, entities, importance_analysis, results
            )
            
            logger.info(f"✅ Resumo fallback gerado: {len(summary)} caracteres")
            return summary
            
        except Exception as e:
            logger.error(f"❌ Erro resumo fallback: {str(e)}")
            return await self._emergency_summary(query, results)
    
    async def _basic_statistics(self, results: List[SearchResult]) -> Dict[str, Any]:
        """Gera estatísticas básicas"""
        stats = {
            'total_results': len(results),
            'unique_sources': len(set(r.source for r in results)),
            'average_relevance': 0.0,
            'high_relevance_count': 0,
            'medium_relevance_count': 0,
            'low_relevance_count': 0,
            'temporal_spread': 0,
            'content_volume': 0
        }
        
        # Análise de relevância
        relevance_scores = [r.relevance_score for r in results if r.relevance_score is not None]
        if relevance_scores:
            stats['average_relevance'] = sum(relevance_scores) / len(relevance_scores)
            
            for score in relevance_scores:
                if score >= 0.8:
                    stats['high_relevance_count'] += 1
                elif score >= 0.5:
                    stats['medium_relevance_count'] += 1
                else:
                    stats['low_relevance_count'] += 1
        
        # Análise temporal
        timestamps = [r.timestamp for r in results if r.timestamp]
        if timestamps and len(timestamps) > 1:
            stats['temporal_spread'] = max(timestamps) - min(timestamps)
        
        # Volume de conteúdo
        total_chars = sum(len(r.title or '') + len(r.description or '') for r in results)
        stats['content_volume'] = total_chars
        
        return stats
    
    async def _detect_patterns(self, results: List[SearchResult]) -> Dict[str, Any]:
        """Detecta padrões nos resultados"""
        patterns_found = {
            'emails': [],
            'phones': [],
            'urls': [],
            'dates': [],
            'prices': [],
            'documents': [],  # CNPJ, CPF
            'keywords': []
        }
        
        # Combinar todo o texto
        all_text = []
        for result in results:
            if result.title:
                all_text.append(result.title)
            if result.description:
                all_text.append(result.description)
            if result.extracted_data:
                # Extrair dados estruturados
                for key, values in result.extracted_data.items():
                    if isinstance(values, list):
                        all_text.extend(str(v) for v in values)
        
        combined_text = ' '.join(all_text)
        
        # Aplicar padrões
        for pattern_name, pattern in self.patterns.items():
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            if matches:
                if pattern_name == 'email':
                    patterns_found['emails'] = list(set(matches))
                elif pattern_name == 'phone':
                    patterns_found['phones'] = list(set(matches))
                elif pattern_name == 'url':
                    patterns_found['urls'] = list(set(matches))
                elif pattern_name == 'date':
                    patterns_found['dates'] = list(set(matches))
                elif pattern_name == 'price':
                    patterns_found['prices'] = list(set(matches))
                elif pattern_name in ['cnpj', 'cpf']:
                    patterns_found['documents'].extend(matches)
        
        # Extrair palavras-chave
        words = re.findall(r'\b\w+\b', combined_text.lower())
        
        # Remover stop words básicas
        stop_words = {'o', 'a', 'os', 'as', 'de', 'do', 'da', 'dos', 'das', 'em', 'no', 'na', 
                      'nos', 'nas', 'por', 'para', 'com', 'sem', 'como', 'mas', 'que', 'se', 
                      'um', 'uma', 'uns', 'umas', 'e', 'ou', 'mais', 'menos', 'muito', 'pouco'}
        
        filtered_words = [w for w in words if w not in stop_words and len(w) > 3]
        word_freq = Counter(filtered_words)
        
        patterns_found['keywords'] = [word for word, freq in word_freq.most_common(10)]
        
        return patterns_found
    
    async def _extract_entities(self, results: List[SearchResult]) -> Dict[str, List[str]]:
        """Extrai entidades básicas"""
        entities = {
            'people': [],
            'organizations': [],
            'locations': [],
            'technologies': [],
            'brands': []
        }
        
        # Combinar texto para análise
        all_text = []
        for result in results:
            if result.title:
                all_text.append(result.title)
            if result.description:
                all_text.append(result.description)
        
        combined_text = ' '.join(all_text)
        
        # Padrões simples para entidades
        entity_patterns = {
            'people': [
                r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',  # Nome completo
                r'\b[A-Z][a-z]+\s+[A-Z]\.\s+[A-Z][a-z]+\b',  # Nome com inicial
            ],
            'organizations': [
                r'\b[A-Z][a-z]+\s+(?:Ltda|S\.A|ME|EPP|Inc|Corp|LLC)\b',
                r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\s+(?:Company|Technologies|Solutions)\b'
            ],
            'locations': [
                r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2}\b',  # Cidade, Estado
                r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z][a-z]+\b'  # Cidade, País
            ],
            'technologies': [
                r'\b(?:Python|Java|JavaScript|React|Angular|Vue|Node\.js|Django|Flask|Spring|\.NET|PHP|Ruby|Go|Rust|Swift|Kotlin)\b',
                r'\b(?:MySQL|PostgreSQL|MongoDB|Redis|Elasticsearch|Docker|Kubernetes|AWS|Azure|GCP)\b'
            ],
            'brands': [
                r'\b(?:Google|Microsoft|Apple|Amazon|Facebook|Meta|Twitter|Tesla|Netflix|Spotify|Uber|Airbnb)\b',
                r'\b(?:Samsung|LG|Sony|Nike|Adidas|Coca-Cola|McDonald\'s|Burger\sKing)\b'
            ]
        }
        
        # Aplicar padrões
        for entity_type, patterns in entity_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, combined_text)
                entities[entity_type].extend(matches)
        
        # Remover duplicatas e limpar
        for entity_type in entities:
            entities[entity_type] = list(set(entities[entity_type]))
            entities[entity_type] = [e.strip() for e in entities[entity_type] if e.strip()]
        
        return entities
    
    async def _analyze_importance(self, results: List[SearchResult], 
                                 query: str) -> Dict[str, Any]:
        """Analisa importância dos resultados"""
        importance = {
            'critical_count': 0,
            'high_count': 0,
            'medium_count': 0,
            'low_count': 0,
            'query_matches': 0,
            'recent_count': 0,
            'priority_results': []
        }
        
        query_lower = query.lower()
        
        for result in results:
            result_importance = 'low'
            
            # Analisar texto para indicadores de importância
            text_to_analyze = f"{result.title or ''} {result.description or ''}".lower()
            
            # Verificar indicadores críticos
            if any(indicator in text_to_analyze for indicator in self.importance_indicators['critical']):
                result_importance = 'critical'
                importance['critical_count'] += 1
            
            # Verificar indicadores altos
            elif any(indicator in text_to_analyze for indicator in self.importance_indicators['high']):
                result_importance = 'high'
                importance['high_count'] += 1
            
            # Verificar indicadores médios
            elif any(indicator in text_to_analyze for indicator in self.importance_indicators['medium']):
                result_importance = 'medium'
                importance['medium_count'] += 1
            
            else:
                importance['low_count'] += 1
            
            # Verificar correspondência com query
            if query_lower in text_to_analyze:
                importance['query_matches'] += 1
                if result_importance != 'critical':
                    result_importance = 'high'
            
            # Verificar se é recente
            if result.timestamp and (time.time() - result.timestamp) <= 86400:  # 24 horas
                importance['recent_count'] += 1
                if result_importance in ['low', 'medium']:
                    result_importance = 'high'
            
            # Adicionar a resultados prioritários
            if result_importance in ['critical', 'high']:
                importance['priority_results'].append({
                    'title': result.title,
                    'url': result.url,
                    'importance': result_importance,
                    'relevance': result.relevance_score
                })
        
        return importance
    
    async def _build_fallback_summary(self, query: str, stats: Dict[str, Any],
                                     patterns: Dict[str, Any], entities: Dict[str, List[str]],
                                     importance: Dict[str, Any], results: List[SearchResult]) -> str:
        """Constrói resumo fallback estruturado"""
        summary = f"# Resumo Analítico para: \"{query}\"\n\n"
        
        # Estatísticas básicas
        summary += "## 📊 Estatísticas Gerais\n"
        summary += f"- **Total de resultados**: {stats['total_results']}\n"
        summary += f"- **Fontes únicas**: {stats['unique_sources']}\n"
        summary += f"- **Relevância média**: {stats['average_relevance']:.2f}\n"
        
        if stats['high_relevance_count'] > 0:
            summary += f"- **Alta relevância**: {stats['high_relevance_count']} resultados\n"
        if stats['temporal_spread'] > 0:
            days = stats['temporal_spread'] / 86400
            summary += f"- **Período coberto**: {days:.1f} dias\n"
        
        # Análise de importância
        summary += "\n## 🎯 Análise de Importância\n"
        if importance['critical_count'] > 0:
            summary += f"- **Críticos**: {importance['critical_count']} resultados\n"
        if importance['high_count'] > 0:
            summary += f"- **Alta prioridade**: {importance['high_count']} resultados\n"
        if importance['query_matches'] > 0:
            summary += f"- **Correspondência direta**: {importance['query_matches']} resultados\n"
        if importance['recent_count'] > 0:
            summary += f"- **Recentes (24h)**: {importance['recent_count']} resultados\n"
        
        # Padrões detectados
        summary += "\n## 🔍 Padrões Detectados\n"
        
        if patterns['emails']:
            summary += f"- **Emails encontrados**: {len(patterns['emails'])}\n"
        if patterns['phones']:
            summary += f"- **Telefones encontrados**: {len(patterns['phones'])}\n"
        if patterns['urls']:
            summary += f"- **URLs únicas**: {len(patterns['urls'])}\n"
        if patterns['dates']:
            summary += f"- **Datas identificadas**: {len(patterns['dates'])}\n"
        if patterns['prices']:
            summary += f"- **Preços encontrados**: {len(patterns['prices'])}\n"
        if patterns['documents']:
            summary += f"- **Documentos (CNPJ/CPF)**: {len(patterns['documents'])}\n"
        
        if patterns['keywords']:
            summary += f"- **Palavras-chave principais**: {', '.join(patterns['keywords'][:5])}\n"
        
        # Entidades identificadas
        summary += "\n## 🏢 Entidades Identificadas\n"
        
        if entities['people']:
            summary += f"- **Pessoas**: {', '.join(entities['people'][:3])}\n"
        if entities['organizations']:
            summary += f"- **Organizações**: {', '.join(entities['organizations'][:3])}\n"
        if entities['locations']:
            summary += f"- **Locais**: {', '.join(entities['locations'][:3])}\n"
        if entities['technologies']:
            summary += f"- **Tecnologias**: {', '.join(entities['technologies'][:3])}\n"
        if entities['brands']:
            summary += f"- **Marcas**: {', '.join(entities['brands'][:3])}\n"
        
        # Resultados prioritários
        if importance['priority_results']:
            summary += "\n## 🌟 Resultados Prioritários\n"
            for i, result in enumerate(importance['priority_results'][:5], 1):
                priority_icon = "🔴" if result['importance'] == 'critical' else "🟡"
                summary += f"{i}. {priority_icon} **{result['title']}**\n"
                summary += f"   - Importância: {result['importance']}\n"
                summary += f"   - Relevância: {result['relevance']:.2f}\n"
                summary += f"   - URL: {result['url']}\n\n"
        
        # Top resultados por relevância
        summary += "## 🏆 Top Resultados por Relevância\n"
        top_results = sorted(results, key=lambda x: x.relevance_score or 0, reverse=True)[:5]
        
        for i, result in enumerate(top_results, 1):
            summary += f"{i}. **{result.title}**\n"
            summary += f"   - Fonte: {result.source}\n"
            summary += f"   - Relevância: {result.relevance_score:.2f}\n"
            summary += f"   - URL: {result.url}\n"
            if result.description:
                desc = result.description[:200] + "..." if len(result.description) > 200 else result.description
                summary += f"   - Descrição: {desc}\n"
            summary += "\n"
        
        # Insights e recomendações
        summary += "## 💡 Insights e Recomendações\n"
        
        # Gerar insights baseados na análise
        insights = []
        
        if stats['average_relevance'] > 0.8:
            insights.append("- **Alta qualidade geral**: Os resultados têm alta relevância média")
        elif stats['average_relevance'] < 0.5:
            insights.append("- **Qualidade moderada**: Considere refinar a busca para melhores resultados")
        
        if importance['critical_count'] > 0:
            insights.append("- **Priorize resultados críticos**: Existem informações urgentes que requerem atenção imediata")
        
        if patterns['emails'] or patterns['phones']:
            insights.append(f"- **Dados de contato disponíveis**: {len(patterns['emails'] + patterns['phones'])} contatos encontrados")
        
        if entities['technologies']:
            insights.append(f"- **Contexto tecnológico**: {len(entities['technologies'])} tecnologias identificadas")
        
        if importance['recent_count'] > 0:
            insights.append("- **Informações atualizadas**: Existem resultados muito recentes")
        
        summary += "\n".join(insights) if insights else "- Nenhum insight específico identificado\n"
        
        summary += "\n\n## 🎯 Próximos Passos Sugeridos\n"
        summary += "- Analise detalhadamente os resultados de alta prioridade\n"
        summary += "- Verifique os dados de contato e entidades identificadas\n"
        summary += "- Considere buscas adicionais baseadas nas palavras-chave encontradas\n"
        
        if stats['unique_sources'] > 3:
            summary += "- Explore diferentes fontes para obter perspectivas variadas\n"
        
        return summary
    
    async def _emergency_summary(self, query: str, results: List[SearchResult]) -> str:
        """Gera resumo de emergência (mínimo)"""
        summary = f"# Resumo de Emergência para: \"{query}\"\n\n"
        
        if not results:
            return summary + "Nenhum resultado encontrado.\n"
        
        summary += f"**Resultados encontrados**: {len(results)}\n\n"
        
        # Estatísticas mínimas
        sources = list(set(r.source for r in results))
        summary += f"**Fontes**: {', '.join(sources)}\n\n"
        
        # Top 3 resultados
        summary += "**Principais resultados**:\n"
        top_results = sorted(results, key=lambda x: x.relevance_score or 0, reverse=True)[:3]
        
        for i, result in enumerate(top_results, 1):
            summary += f"{i}. {result.title}\n"
            summary += f"   Fonte: {result.source}\n"
            summary += f"   URL: {result.url}\n\n"
        
        return summary
    
    async def simple_analyze(self, text: str) -> Dict[str, Any]:
        """
        Análise simples de texto
        
        Args:
            text: Texto para analisar
            
        Returns:
            Análise básica
        """
        try:
            analysis = {
                'word_count': len(text.split()),
                'char_count': len(text),
                'sentence_count': len(re.split(r'[.!?]+', text)),
                'patterns': {},
                'keywords': []
            }
            
            # Detectar padrões
            for pattern_name, pattern in self.patterns.items():
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    analysis['patterns'][pattern_name] = len(matches)
            
            # Extrair palavras-chave
            words = re.findall(r'\b\w+\b', text.lower())
            stop_words = {'o', 'a', 'os', 'as', 'de', 'do', 'da', 'dos', 'das', 'em', 'no', 'na'}
            filtered_words = [w for w in words if w not in stop_words and len(w) > 3]
            word_freq = Counter(filtered_words)
            analysis['keywords'] = [word for word, freq in word_freq.most_common(5)]
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Erro análise simples: {str(e)}")
            return {'error': str(e)}
    
    async def extract_contacts(self, text: str) -> Dict[str, List[str]]:
        """
        Extrai informações de contato
        
        Args:
            text: Texto para analisar
            
        Returns:
            Contatos encontrados
        """
        contacts = {
            'emails': [],
            'phones': [],
            'urls': []
        }
        
        # Extrair emails
        email_matches = re.findall(self.patterns['email'], text, re.IGNORECASE)
        contacts['emails'] = list(set(email_matches))
        
        # Extrair telefones
        phone_matches = re.findall(self.patterns['phone'], text)
        contacts['phones'] = list(set(phone_matches))
        
        # Extrair URLs
        url_matches = re.findall(self.patterns['url'], text)
        contacts['urls'] = list(set(url_matches))
        
        return contacts
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificação de saúde do serviço"""
        return {
            'status': 'healthy',
            'component': 'fallback_ai_service',
            'timestamp': time.time(),
            'patterns_loaded': len(self.patterns) > 0,
            'language': self.config.language
        }
