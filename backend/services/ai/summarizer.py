"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Summarizer Service
Serviço simplificado de geração de resumos
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
class SummarizerConfig:
    """Configuração do summarizer"""
    max_summary_length: int = 2000
    min_sentence_length: int = 10
    max_sentences: int = 15
    include_key_insights: bool = True
    include_statistics: bool = True
    language: str = "pt"

class SummarizerService:
    """Serviço de geração de resumos"""
    
    def __init__(self, config: Optional[SummarizerConfig] = None):
        self.config = config or SummarizerConfig()
        
        # Stop words em português
        self.stop_words_pt = {
            'o', 'a', 'os', 'as', 'de', 'do', 'da', 'dos', 'das', 'em', 'no', 'na',
            'nos', 'nas', 'por', 'para', 'com', 'sem', 'como', 'mas', 'que', 'se',
            'um', 'uma', 'uns', 'umas', 'e', 'ou', 'mais', 'menos', 'muito', 'pouco',
            'foi', 'foram', 'ser', 'estar', 'está', 'estão', 'este', 'esta', 'esteve',
            'também', 'já', 'ainda', 'só', 'apenas', 'assim', 'então', 'porque', 'pois'
        }
        
        # Stop words em inglês
        self.stop_words_en = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'between', 'among', 'is', 'are',
            'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
            'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can'
        }
        
        logger.info("📝 Summarizer Service inicializado")
    
    async def summarize_results(self, query: str, results: List[SearchResult]) -> str:
        """
        Gera resumo dos resultados de busca
        
        Args:
            query: Query original
            results: Lista de resultados
            
        Returns:
            Resumo gerado
        """
        if not results:
            return f"Nenhum resultado encontrado para '{query}'."
        
        logger.info(f"📝 Gerando resumo para: '{query}' ({len(results)} resultados)")
        
        try:
            # Análise estatística
            stats = await self._analyze_statistics(results)
            
            # Extração de insights chave
            insights = await self._extract_key_insights(results, query)
            
            # Identificação de temas principais
            themes = await self._identify_main_themes(results)
            
            # Construir resumo estruturado
            summary = await self._build_structured_summary(
                query, stats, insights, themes, results
            )
            
            logger.info(f"✅ Resumo gerado: {len(summary)} caracteres")
            return summary
            
        except Exception as e:
            logger.error(f"❌ Erro gerando resumo: {str(e)}")
            return await self._generate_fallback_summary(query, results)
    
    async def _analyze_statistics(self, results: List[SearchResult]) -> Dict[str, Any]:
        """Analisa estatísticas dos resultados"""
        stats = {
            'total_results': len(results),
            'sources': {},
            'relevance_distribution': {'high': 0, 'medium': 0, 'low': 0},
            'average_relevance': 0.0,
            'temporal_analysis': {},
            'content_analysis': {}
        }
        
        # Análise de fontes
        for result in results:
            source = result.source
            stats['sources'][source] = stats['sources'].get(source, 0) + 1
        
        # Análise de relevância
        relevance_scores = [r.relevance_score for r in results if r.relevance_score]
        if relevance_scores:
            stats['average_relevance'] = sum(relevance_scores) / len(relevance_scores)
            
            for score in relevance_scores:
                if score >= 0.8:
                    stats['relevance_distribution']['high'] += 1
                elif score >= 0.5:
                    stats['relevance_distribution']['medium'] += 1
                else:
                    stats['relevance_distribution']['low'] += 1
        
        # Análise temporal
        timestamps = [r.timestamp for r in results if r.timestamp]
        if timestamps:
            stats['temporal_analysis'] = {
                'newest': max(timestamps),
                'oldest': min(timestamps),
                'time_span': max(timestamps) - min(timestamps),
                'recent_24h': len([t for t in timestamps if time.time() - t <= 86400]),
                'recent_week': len([t for t in timestamps if time.time() - t <= 604800])
            }
        
        # Análise de conteúdo
        all_titles = [r.title for r in results if r.title]
        all_descriptions = [r.description for r in results if r.description]
        
        if all_titles or all_descriptions:
            content_text = ' '.join(all_titles + all_descriptions)
            stats['content_analysis'] = {
                'total_words': len(content_text.split()),
                'unique_words': len(set(content_text.lower().split())),
                'avg_title_length': sum(len(t) for t in all_titles) / len(all_titles) if all_titles else 0,
                'has_extracted_data': len([r for r in results if r.extracted_data])
            }
        
        return stats
    
    async def _extract_key_insights(self, results: List[SearchResult], 
                                   query: str) -> List[str]:
        """Extrai insights chave dos resultados"""
        insights = []
        
        # Insights sobre fontes
        sources = [r.source for r in results]
        source_counts = Counter(sources)
        if source_counts:
            top_source = source_counts.most_common(1)[0]
            insights.append(f"Fonte predominante: {top_source[0]} ({top_source[1]} ocorrências)")
        
        # Insights sobre relevância
        high_relevance = [r for r in results if r.relevance_score >= 0.8]
        if high_relevance:
            insights.append(f"{len(high_relevance)} resultados com alta relevância (>0.8)")
        
        # Insights sobre dados extraídos
        results_with_data = [r for r in results if r.extracted_data]
        if results_with_data:
            total_emails = sum(len(r.extracted_data.get('emails', [])) for r in results_with_data)
            total_phones = sum(len(r.extracted_data.get('phones', [])) for r in results_with_data)
            total_companies = sum(len(r.extracted_data.get('companies', [])) for r in results_with_data)
            
            if total_emails > 0:
                insights.append(f"Encontrados {total_emails} endereços de email")
            if total_phones > 0:
                insights.append(f"Encontrados {total_phones} números de telefone")
            if total_companies > 0:
                insights.append(f"Identificadas {total_companies} empresas")
        
        # Insights temporais
        recent_results = [r for r in results if r.timestamp and time.time() - r.timestamp <= 86400]
        if recent_results:
            insights.append(f"{len(recent_results)} resultados das últimas 24 horas")
        
        # Insights sobre a query
        query_lower = query.lower()
        titles_with_query = [r for r in results if r.title and query_lower in r.title.lower()]
        if titles_with_query:
            insights.append(f"{len(titles_with_query)} títulos contêm a query exata")
        
        return insights
    
    async def _identify_main_themes(self, results: List[SearchResult]) -> List[Dict[str, Any]]:
        """Identifica temas principais nos resultados"""
        # Combinar todo o texto
        all_text = []
        for result in results:
            if result.title:
                all_text.append(result.title)
            if result.description:
                all_text.append(result.description)
        
        combined_text = ' '.join(all_text).lower()
        
        # Remover pontuação e tokenizar
        words = re.findall(r'\b\w+\b', combined_text)
        
        # Remover stop words
        stop_words = self.stop_words_pt if self.config.language == 'pt' else self.stop_words_en
        filtered_words = [w for w in words if w not in stop_words and len(w) > 3]
        
        # Contar frequência
        word_freq = Counter(filtered_words)
        
        # Identificar temas (palavras mais frequentes)
        themes = []
        for word, freq in word_freq.most_common(10):
            # Verificar se a palavra aparece em múltiplos resultados
            results_with_word = sum(1 for r in results 
                                 if ((r.title and word in r.title.lower()) or 
                                     (r.description and word in r.description.lower())))
            
            if results_with_word >= 2:  # Aparece em pelo menos 2 resultados
                themes.append({
                    'theme': word,
                    'frequency': freq,
                    'coverage': results_with_word,
                    'percentage': (results_with_word / len(results)) * 100
                })
        
        return themes[:5]  # Top 5 temas
    
    async def _build_structured_summary(self, query: str, stats: Dict[str, Any],
                                       insights: List[str], themes: List[Dict[str, Any]],
                                       results: List[SearchResult]) -> str:
        """Constrói resumo estruturado"""
        summary = f"# Análise de Resultados para: \"{query}\"\n\n"
        
        # Estatísticas gerais
        summary += "## 📊 Estatísticas Gerais\n"
        summary += f"- **Total de resultados**: {stats['total_results']}\n"
        summary += f"- **Relevância média**: {stats['average_relevance']:.2f}\n"
        summary += f"- **Fontes utilizadas**: {len(stats['sources'])}\n"
        
        # Distribuição de relevância
        if stats['relevance_distribution']['high'] > 0:
            summary += f"- **Alta relevância**: {stats['relevance_distribution']['high']} resultados\n"
        if stats['relevance_distribution']['medium'] > 0:
            summary += f"- **Relevância média**: {stats['relevance_distribution']['medium']} resultados\n"
        
        # Fontes principais
        summary += "\n## 🔍 Fontes Principais\n"
        top_sources = sorted(stats['sources'].items(), key=lambda x: x[1], reverse=True)[:5]
        for source, count in top_sources:
            percentage = (count / stats['total_results']) * 100
            summary += f"- **{source}**: {count} resultados ({percentage:.1f}%)\n"
        
        # Insights chave
        if insights:
            summary += "\n## 💡 Insights Principais\n"
            for insight in insights:
                summary += f"- {insight}\n"
        
        # Temas identificados
        if themes:
            summary += "\n## 🎯 Temas Identificados\n"
            for theme in themes:
                summary += f"- **{theme['theme'].title()}**: aparece em {theme['coverage']} resultados "
                summary += f"({theme['percentage']:.1f}% de cobertura)\n"
        
        # Análise temporal
        if stats['temporal_analysis']:
            temp = stats['temporal_analysis']
            summary += "\n## ⏰ Análise Temporal\n"
            if temp.get('recent_24h', 0) > 0:
                summary += f"- **Últimas 24h**: {temp['recent_24h']} resultados\n"
            if temp.get('recent_week', 0) > 0:
                summary += f"- **Última semana**: {temp['recent_week']} resultados\n"
            if temp.get('time_span', 0) > 0:
                days = temp['time_span'] / 86400
                summary += f"- **Período coberto**: {days:.1f} dias\n"
        
        # Top resultados
        summary += "\n## 🌟 Resultados Mais Relevantes\n"
        top_results = sorted(results, key=lambda x: x.relevance_score, reverse=True)[:5]
        for i, result in enumerate(top_results, 1):
            summary += f"\n{i}. **{result.title}**\n"
            summary += f"   - Fonte: {result.source} (Relevância: {result.relevance_score:.2f})\n"
            summary += f"   - URL: {result.url}\n"
            if result.description:
                desc = result.description[:200] + "..." if len(result.description) > 200 else result.description
                summary += f"   - Descrição: {desc}\n"
        
        # Recomendações
        summary += "\n## 🎯 Recomendações\n"
        
        if stats['relevance_distribution']['high'] >= 3:
            summary += "- **Analisar profundamente** os resultados de alta relevância para obter informações detalhadas\n"
        
        if stats['content_analysis'].get('has_extracted_data', 0) > 0:
            summary += "- **Investigar dados extraídos** para encontrar contatos e entidades relevantes\n"
        
        if themes:
            top_theme = themes[0]
            summary += f"- **Explorar o tema principal** \"{top_theme['theme']}\" para descobrir mais informações relacionadas\n"
        
        if stats['temporal_analysis'].get('recent_24h', 0) > 0:
            summary += "- **Priorizar resultados recentes** para informações mais atualizadas\n"
        
        return summary
    
    async def _generate_fallback_summary(self, query: str, results: List[SearchResult]) -> str:
        """Gera resumo de fallback (básico)"""
        summary = f"# Resumo de Resultados para: \"{query}\"\n\n"
        
        if not results:
            summary += "Nenhum resultado encontrado.\n"
            return summary
        
        summary += f"**Total de resultados**: {len(results)}\n\n"
        
        # Estatísticas básicas
        sources = list(set(r.source for r in results))
        summary += f"**Fontes**: {', '.join(sources)}\n\n"
        
        # Top 5 resultados
        summary += "**Principais Resultados**:\n\n"
        top_results = sorted(results, key=lambda x: x.relevance_score, reverse=True)[:5]
        
        for i, result in enumerate(top_results, 1):
            summary += f"{i}. {result.title}\n"
            summary += f"   Fonte: {result.source}\n"
            summary += f"   {result.description[:150]}...\n\n"
        
        return summary
    
    async def extract_key_sentences(self, text: str, max_sentences: int = 5) -> List[str]:
        """
        Extrai sentenças chave de um texto
        
        Args:
            text: Texto para analisar
            max_sentences: Número máximo de sentenças
            
        Returns:
            Lista de sentenças mais importantes
        """
        try:
            # Dividir em sentenças
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if len(s.strip()) >= self.config.min_sentence_length]
            
            if not sentences:
                return []
            
            # Calcular score para cada sentença
            sentence_scores = []
            words = text.lower().split()
            word_freq = Counter(words)
            
            for sentence in sentences:
                sentence_words = sentence.lower().split()
                
                # Remover stop words
                stop_words = self.stop_words_pt if self.config.language == 'pt' else self.stop_words_en
                content_words = [w for w in sentence_words if w not in stop_words]
                
                if not content_words:
                    continue
                
                # Calcular score baseado na frequência das palavras
                score = sum(word_freq.get(word, 0) for word in content_words) / len(content_words)
                
                # Bônus para sentenças mais longas (até certo ponto)
                length_bonus = min(len(content_words) / 20, 1.0)
                score += length_bonus
                
                sentence_scores.append((sentence, score))
            
            # Ordenar por score e retornar as melhores
            sentence_scores.sort(key=lambda x: x[1], reverse=True)
            
            return [s[0] for s in sentence_scores[:max_sentences]]
            
        except Exception as e:
            logger.error(f"❌ Erro extraindo sentenças chave: {str(e)}")
            return []
    
    async def generate_bullets_summary(self, text: str, max_bullets: int = 10) -> List[str]:
        """
        Gera resumo em formato de bullet points
        
        Args:
            text: Texto para resumir
            max_bullets: Número máximo de bullets
            
        Returns:
            Lista de bullet points
        """
        try:
            # Extrair sentenças chave
            key_sentences = await self.extract_key_sentences(text, max_bullets * 2)
            
            # Converter para bullets
            bullets = []
            for sentence in key_sentences:
                if len(bullets) >= max_bullets:
                    break
                
                # Limpar e formatar
                bullet = sentence.strip()
                if not bullet.endswith(('.', '!', '?')):
                    bullet += '.'
                
                # Limitar tamanho
                if len(bullet) > 150:
                    bullet = bullet[:147] + '...'
                
                bullets.append(bullet)
            
            return bullets
            
        except Exception as e:
            logger.error(f"❌ Erro gerando bullets: {str(e)}")
            return []
    
    async def compare_results(self, results1: List[SearchResult], 
                            results2: List[SearchResult]) -> Dict[str, Any]:
        """
        Compara dois conjuntos de resultados
        
        Args:
            results1: Primeiro conjunto de resultados
            results2: Segundo conjunto de resultados
            
        Returns:
            Análise comparativa
        """
        try:
            comparison = {
                'set1_stats': await self._analyze_statistics(results1),
                'set2_stats': await self._analyze_statistics(results2),
                'overlap_analysis': {},
                'differences': []
            }
            
            # Análise de sobreposição
            urls1 = set(r.url for r in results1)
            urls2 = set(r.url for r in results2)
            
            overlap = urls1 & urls2
            unique_to_1 = urls1 - urls2
            unique_to_2 = urls2 - urls1
            
            comparison['overlap_analysis'] = {
                'total_overlap': len(overlap),
                'unique_to_set1': len(unique_to_1),
                'unique_to_set2': len(unique_to_2),
                'overlap_percentage': (len(overlap) / len(urls1 | urls2)) * 100 if urls1 | urls2 else 0
            }
            
            # Análise de diferenças
            if comparison['set1_stats']['average_relevance'] > comparison['set2_stats']['average_relevance']:
                comparison['differences'].append("Conjunto 1 tem maior relevância média")
            else:
                comparison['differences'].append("Conjunto 2 tem maior relevância média")
            
            sources1 = set(comparison['set1_stats']['sources'].keys())
            sources2 = set(comparison['set2_stats']['sources'].keys())
            
            if sources1 != sources2:
                comparison['differences'].append(f"Fontes diferentes: {sources1 ^ sources2}")
            
            return comparison
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificação de saúde do serviço"""
        return {
            'status': 'healthy',
            'component': 'summarizer_service',
            'timestamp': time.time(),
            'max_summary_length': self.config.max_summary_length,
            'language': self.config.language
        }
            
        except Exception as e:
            logger.error(f"❌ Erro comparando resultados: {str(e)}")
            return {}
