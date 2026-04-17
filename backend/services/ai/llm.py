"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - LLM Service
Serviço principal de Inteligência Artificial
"""

import asyncio
import aiohttp
import json
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
import time
import logging
from datetime import datetime

from ...core.pipeline import SearchResult
from ...utils.logger import setup_logger
from ...utils.http_client import HTTPClient

logger = setup_logger(__name__)

@dataclass
class LLMConfig:
    """Configuração do serviço LLM"""
    provider: str = "openai"  # openai, anthropic, huggingface, local
    api_key: str = ""
    model: str = "gpt-4"
    max_tokens: int = 4000
    temperature: float = 0.7
    timeout: int = 120
    retry_attempts: int = 3
    system_prompt: str = ""
    
    def __post_init__(self):
        if not self.system_prompt:
            self.system_prompt = """
            Você é um sistema avançado de análise de informações chamado OMNISCIENT_ULTIMATE_SYSTEM_FINAL.
            Sua tarefa é analisar grandes volumes de dados e gerar insights valiosos.
            Seja objetivo, preciso e forneça informações úteis e acionáveis.
            """

class LLMService:
    """Serviço de Language Model"""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        self.http_client = HTTPClient()
        self.session = None
        
        # URLs das APIs
        self.api_endpoints = {
            'openai': 'https://api.openai.com/v1/chat/completions',
            'anthropic': 'https://api.anthropic.com/v1/messages',
            'huggingface': 'https://api-inference.huggingface.co/models',
            'local': 'http://localhost:8000/v1/chat/completions'
        }
        
        logger.info(f"🤖 LLM Service inicializado (provider: {self.config.provider})")
    
    async def initialize(self):
        """Inicializa o serviço LLM"""
        headers = {
            'User-Agent': 'OMNISCIENT_LLM/3.0',
            'Content-Type': 'application/json'
        }
        
        # Adicionar headers específicos por provider
        if self.config.provider == 'openai':
            headers['Authorization'] = f'Bearer {self.config.api_key}'
        elif self.config.provider == 'anthropic':
            headers['x-api-key'] = self.config.api_key
            headers['anthropic-version'] = '2023-06-01'
        elif self.config.provider == 'huggingface':
            headers['Authorization'] = f'Bearer {self.config.api_key}'
        
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            headers=headers
        )
        
        logger.info("✅ LLM Service pronto")
    
    async def generate_summary(self, query: str, results: List[SearchResult], 
                             extracted_data: Dict[str, Any]) -> str:
        """
        Gera resumo inteligente dos resultados
        
        Args:
            query: Query original
            results: Lista de resultados
            extracted_data: Dados extraídos
            
        Returns:
            Resumo gerado pela IA
        """
        if not self.session:
            await self.initialize()
        
        logger.info(f"🧠 Gerando resumo para: '{query}' ({len(results)} resultados)")
        
        try:
            # Preparar contexto
            context = await self._prepare_context(query, results, extracted_data)
            
            # Construir prompt
            prompt = await self._build_summary_prompt(query, context)
            
            # Gerar resposta
            summary = await self._generate_response(prompt)
            
            logger.info(f"✅ Resumo gerado: {len(summary)} caracteres")
            return summary
            
        except Exception as e:
            logger.error(f"❌ Erro gerando resumo: {str(e)}")
            return await self._generate_fallback_summary(query, results, extracted_data)
    
    async def _prepare_context(self, query: str, results: List[SearchResult], 
                              extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepara contexto avançado para a IA"""
        # Limitar número de resultados para não exceder tokens
        max_results = 50
        limited_results = results[:max_results]
        
        # Análise avançada dos resultados
        sources_count = {}
        for result in limited_results:
            source = result.source
            sources_count[source] = sources_count.get(source, 0) + 1
        
        # Extrair entidades e padrões
        all_entities = set()
        entities_count = {'emails': 0, 'phones': 0, 'companies': 0, 'people': 0}
        
        for result in limited_results:
            if result.extracted_data:
                for key in ['emails', 'phones', 'companies', 'people']:
                    entities = result.extracted_data.get(key, [])
                    if entities:
                        all_entities.update(entities)
                        entities_count[key] += len(entities)
        
        # Análise de sentimento e tópicos
        all_text = ' '.join([r.title + ' ' + r.description for r in limited_results])
        sentiment = self._analyze_sentiment(all_text)
        topics = self._extract_topics(all_text)
        
        # Identificar padrões e tendências
        patterns = self._identify_patterns(limited_results)
        trends = self._identify_trends(limited_results)
        
        context = {
            'query': query,
            'total_results': len(results),
            'analyzed_results': len(limited_results),
            'sources_distribution': sources_count,
            'top_sources': sorted(sources_count.items(), key=lambda x: x[1], reverse=True)[:5],
            'top_results': [],
            'key_insights': [],
            'extracted_entities': {
                'total_unique': len(all_entities),
                'by_type': entities_count,
                'most_common': self._get_most_common_entities(all_entities)
            },
            'sentiment_analysis': sentiment,
            'topics': topics,
            'patterns': patterns,
            'trends': trends,
            'quality_score': self._calculate_quality_score(limited_results),
            'timestamp': datetime.now().isoformat()
        }
        
        # Processar top resultados com metadados avançados
        for i, result in enumerate(limited_results[:15]):
            result_info = {
                'rank': i + 1,
                'title': result.title,
                'url': result.url,
                'description': result.description[:500],
                'source': result.source,
                'relevance_score': result.relevance_score,
                'extracted_data': result.extracted_data or {},
                'content_quality': self._assess_content_quality(result),
                'trust_score': self._calculate_trust_score(result),
                'freshness': self._calculate_freshness(result)
            }
            context['top_results'].append(result_info)
        
        # Gerar insights automáticos
        context['key_insights'] = self._generate_insights(
            query, limited_results, extracted_data, sentiment, topics
        )
        
        return context
        context['key_insights'] = await self._extract_key_insights(limited_results, extracted_data)
        
        return context
    
    async def _extract_key_insights(self, results: List[SearchResult], 
                                   extracted_data: Dict[str, Any]) -> List[str]:
        """Extrai insights chave dos dados"""
        insights = []
        
        # Análise de fontes
        sources = [r.source for r in results]
        source_counts = {}
        for source in sources:
            source_counts[source] = source_counts.get(source, 0) + 1
        
        if source_counts:
            top_source = max(source_counts, key=source_counts.get)
            insights.append(f"Fonte mais comum: {top_source} ({source_counts[top_source]} ocorrências)")
        
        # Análise de dados extraídos
        if extracted_data.get('emails'):
            insights.append(f"Encontrados {len(extracted_data['emails'])} emails")
        
        if extracted_data.get('phones'):
            insights.append(f"Encontrados {len(extracted_data['phones'])} telefones")
        
        if extracted_data.get('companies'):
            insights.append(f"Identificadas {len(extracted_data['companies'])} empresas")
        
        # Análise de relevância
        high_relevance = [r for r in results if r.relevance_score > 0.8]
        if high_relevance:
            insights.append(f"{len(high_relevance)} resultados com alta relevância (>0.8)")
        
        # Análise temporal
        timestamps = [r.timestamp for r in results if r.timestamp]
        if timestamps:
            latest = max(timestamps)
            oldest = min(timestamps)
            time_span = latest - oldest
            if time_span > 0:
                insights.append(f"Período de resultados: {time_span/86400:.1f} dias")
        
        return insights
    
    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Análise de sentimento simplificada"""
        positive_words = ['bom', 'ótimo', 'excelente', 'sucesso', 'feliz', 'alegria', 'satisfeito', 'positivo', 'cresceu', 'melhorou', 'avanço', 'conquista', 'vitória', 'ganhou', 'lucro', 'lucrativo', 'rentável', 'eficiente', 'eficaz', 'funciona', 'perfeito', 'ideal', 'maravilhoso']
        negative_words = ['ruim', 'péssimo', 'terrível', 'falha', 'erro', 'problema', 'dificuldade', 'prejuízo', 'perda', 'derrota', 'fracasso', 'crise', 'quebra', 'defeito', 'falência', 'insucesso', 'ineficiente', 'ineficaz', 'não funciona', 'quebrado', 'defeituoso', 'horrível', 'pior']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            sentiment = 'positive'
        elif negative_count > positive_count:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {
            'sentiment': sentiment,
            'positive_score': positive_count,
            'negative_score': negative_count,
            'confidence': max(positive_count, negative_count) / max(positive_count + negative_count, 1)
        }
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extrai tópicos do texto"""
        # Palavras-chave por área
        topic_keywords = {
            'tecnologia': ['tecnologia', 'software', 'aplicativo', 'sistema', 'plataforma', 'digital', 'online', 'web', 'site', 'app', 'programa', 'código', 'desenvolvimento', 'api', 'banco de dados', 'nuvem', 'servidor'],
            'negócios': ['negócio', 'empresa', 'lucro', 'venda', 'cliente', 'mercado', 'produto', 'serviço', 'comércio', 'varejo', 'atacado', 'investimento', 'receita', 'despesa', 'custo', 'preço', 'orçamento', 'financeiro', 'econômico'],
            'educação': ['educação', 'escola', 'universidade', 'curso', 'aprendizado', 'ensino', 'aluno', 'professor', 'disciplina', 'graduação', 'pós-graduação', 'mestrado', 'doutorado', 'pesquisa', 'estudo', 'livro', 'material', 'aula'],
            'saúde': ['saúde', 'médico', 'hospital', 'tratamento', 'doença', 'remédio', 'farmácia', 'consulta', 'exame', 'diagnóstico', 'terapia', 'cirurgia', 'prevenção', 'vacina'],
            'entretenimento': ['entretenimento', 'filme', 'música', 'jogo', 'esporte', 'show', 'festa', 'férias', 'turismo', 'viagem', 'lazer', 'diversão', 'brincadeira', 'cinema', 'teatro']
        }
        
        text_lower = text.lower()
        found_topics = []
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                found_topics.append(topic)
        
        return list(set(found_topics))
    
    def _identify_patterns(self, results: List[SearchResult]) -> Dict[str, Any]:
        """Identifica padrões nos resultados"""
        patterns = {
            'common_domains': set(),
            'url_patterns': [],
            'title_similarity': [],
            'content_clusters': {}
        }
        
        # Analisar domínios comuns
        for result in results:
            try:
                from urllib.parse import urlparse
                domain = urlparse(result.url).netloc.lower()
                if domain:
                    patterns['common_domains'].add(domain)
            except:
                pass
        
        # Identificar padrões de similaridade
        titles = [r.title.lower() for r in results]
        for i, title in enumerate(titles):
            for j, other_title in enumerate(titles[i+1:], i+1):
                similarity = len(set(title.split()) & set(other_title.split())) / max(len(title.split()), len(other_title.split()))
                if similarity > 0.5:
                    patterns['title_similarity'].append({
                        'title1': results[i].title,
                        'title2': results[j].title,
                        'similarity': similarity
                    })
        
        return {
            'domain_analysis': {
                'most_common': list(patterns['common_domains'])[:5],
                'diversity': len(patterns['common_domains'])
            },
            'content_similarity': patterns['title_similarity']
        }
    
    def _identify_trends(self, results: List[SearchResult]) -> Dict[str, Any]:
        """Identifica tendências nos resultados"""
        if not results:
            return {'trending_topics': [], 'emerging_sources': []}
        
        # Analisar palavras mais frequentes
        all_text = ' '.join([r.title + ' ' + r.description for r in results])
        words = all_text.lower().split()
        
        # Remover stopwords
        stopwords = {'o', 'a', 'os', 'as', 'da', 'de', 'do', 'em', 'um', 'para', 'com', 'na', 'no', 'por', 'se', 'mais', 'mas', 'ao', 'pelo', 'que', 'como', 'dos', 'das', 'à', 'às'}
        filtered_words = [w for w in words if len(w) > 3 and w not in stopwords]
        
        # Contar frequência
        from collections import Counter
        word_freq = Counter(filtered_words)
        
        trending_words = [word for word, count in word_freq.most_common(20)]
        
        # Analisar fontes emergentes
        sources = [r.source for r in results]
        source_count = Counter(sources)
        emerging_sources = [source for source, count in source_count.items() if count == 1]
        
        return {
            'trending_words': trending_words,
            'trending_topics': self._extract_topics(' '.join(trending_words)),
            'emerging_sources': emerging_sources,
            'source_diversity': len(set(sources))
        }
    
    def _calculate_quality_score(self, results: List[SearchResult]) -> float:
        """Calcula score de qualidade dos resultados"""
        if not results:
            return 0.0
        
        quality_scores = []
        
        for result in results:
            score = 0.0
            
            # Título e descrição (40%)
            if result.title and len(result.title) > 10:
                score += 0.4
            if result.description and len(result.description) > 50:
                score += 0.4
            
            # Dados extraídos (30%)
            if result.extracted_data:
                data_types = len([k for k, v in result.extracted_data.items() if v])
                score += min(data_types * 0.1, 0.3)
            
            # Score de relevância (20%)
            score += min(result.relevance_score * 0.2, 0.2)
            
            # Fonte confiável (10%)
            source_scores = {
                'wikipedia': 0.1,
                'github': 0.09,
                'reddit': 0.07,
                'news': 0.08,
                'web': 0.05,
                'bing': 0.06
            }
            score += source_scores.get(result.source.lower(), 0.05)
            
            quality_scores.append(score)
        
        return sum(quality_scores) / len(quality_scores)
    
    def _calculate_trust_score(self, result: SearchResult) -> float:
        """Calcula score de confiança do resultado"""
        score = 0.5  # Base
        
        # Fontes confiáveis
        trusted_sources = ['wikipedia', 'github', 'stackoverflow', 'w3', 'mozilla']
        if any(source in result.url.lower() for source in trusted_sources):
            score += 0.3
        
        # HTTPS vs HTTP
        if result.url.startswith('https://'):
            score += 0.1
        
        # Domínios educacionais/governamentais
        edu_domains = ['.edu', '.gov', '.org']
        if any(domain in result.url for domain in edu_domains):
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_freshness(self, result: SearchResult) -> float:
        """Calcula frescor do resultado"""
        if not result.timestamp:
            return 0.0
        
        import time
        age_hours = (time.time() - result.timestamp) / 3600
        
        # Mais recente = maior score
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
    
    def _assess_content_quality(self, result: SearchResult) -> Dict[str, Any]:
        """Avalia qualidade do conteúdo"""
        quality = {
            'has_title': bool(result.title),
            'title_length': len(result.title) if result.title else 0,
            'has_description': bool(result.description),
            'description_length': len(result.description) if result.description else 0,
            'has_extracted_data': bool(result.extracted_data),
            'extracted_data_types': len(result.extracted_data.keys()) if result.extracted_data else 0,
            'relevance_score': result.relevance_score,
            'url_valid': result.url.startswith(('http://', 'https://')),
            'overall_score': 0.0
        }
        
        # Calcular score geral
        score = 0.0
        if quality['has_title'] and quality['title_length'] > 5:
            score += 0.3
        if quality['has_description'] and quality['description_length'] > 20:
            score += 0.3
        if quality['has_extracted_data']:
            score += 0.2
        if quality['url_valid']:
            score += 0.1
        if quality['relevance_score'] > 0.5:
            score += 0.1
        
        quality['overall_score'] = min(score, 1.0)
        return quality
    
    def _get_most_common_entities(self, entities: set) -> Dict[str, List[str]]:
        """Retorna entidades mais comuns"""
        entity_list = list(entities)
        
        # Agrupar por tipo
        emails = [e for e in entity_list if '@' in e]
        phones = [p for p in entity_list if any(c.isdigit() for c in p)]
        companies = [c for c in entity_list if any(word in c.lower() for word in ['ltda', 'sa', 'inc', 'company'])]
        people = [p for p in entity_list if len(p.split()) >= 2 and p[0].isupper()]
        
        return {
            'emails': emails[:5],
            'phones': phones[:5],
            'companies': companies[:5],
            'people': people[:5]
        }
    
    def _generate_insights(self, query: str, results: List[SearchResult], 
                           extracted_data: Dict[str, Any], sentiment: Dict[str, Any], 
                           topics: List[str]) -> List[str]:
        """Gera insights automáticos"""
        insights = []
        
        # Insights sobre a query
        if len(query.split()) > 3:
            insights.append(f"Consulta complexa com múltiplos termos: '{query}'")
        
        # Insights sobre os resultados
        if len(results) > 0:
            avg_relevance = sum(r.relevance_score for r in results) / len(results)
            if avg_relevance > 0.7:
                insights.append("Resultados com alta relevância encontrados")
            elif avg_relevance < 0.3:
                insights.append("Resultados com baixa relevância, considere refinar a busca")
        
        # Insights sobre fontes
        sources = [r.source for r in results]
        if len(set(sources)) > 5:
            insights.append("Grande diversidade de fontes encontrada")
        
        # Insights sobre entidades
        if extracted_data:
            total_entities = sum(len(v) if isinstance(v, list) else 1 for v in extracted_data.values())
            if total_entities > 10:
                insights.append(f"Quantidade significativa de entidades extraídas: {total_entities}")
        
        # Insights sobre sentimento
        if sentiment['sentiment'] == 'positive':
            insights.append("Conteúdo geralmente positivo e favorável")
        elif sentiment['sentiment'] == 'negative':
            insights.append("Conteúdo com tendências negativas identificadas")
        
        # Insights sobre tópicos
        if topics:
            insights.append(f"Tópicos principais identificados: {', '.join(topics[:3])}")
        
        return insights
    
    async def _build_summary_prompt(self, query: str, context: Dict[str, Any]) -> str:
        """Constrói prompt para geração de resumo"""
        prompt = f"""
        {self.config.system_prompt}
        
        QUERY ORIGINAL: {context['query']}
        
        CONTEXTO DA ANÁLISE:
        - Total de resultados encontrados: {context['total_results']}
        - Resultados analisados: {context['analyzed_results']}
        - Fontes utilizadas: {', '.join(context['sources'])}
        - Data da análise: {context['timestamp']}
        
        INSIGHTS PRINCIPAIS:
        {chr(10).join(f"- {insight}" for insight in context['key_insights'])}
        
        TOP 10 RESULTADOS:
        """
        
        for result in context['top_results']:
            prompt += f"""
        {result['rank']}. {result['title']}
           Fonte: {result['source']} (Relevância: {result['relevance_score']:.2f})
           URL: {result['url']}
           Descrição: {result['description']}
        """
        
        prompt += f"""
        DADOS EXTRAÍDOS:
        - Emails: {len(context['extracted_entities'].get('emails', []))}
        - Telefones: {len(context['extracted_entities'].get('phones', []))}
        - Empresas: {len(context['extracted_entities'].get('companies', []))}
        - Links: {len(context['extracted_entities'].get('links', []))}
        - Palavras-chave: {', '.join(context['extracted_entities'].get('keywords', [])[:10])}
        
        INSTRUÇÕES:
        1. Analise cuidadosamente todos os resultados acima
        2. Identifique os temas e padrões principais
        3. Destaque informações mais relevantes e acionáveis
        4. Forneça uma visão geral clara e objetiva
        5. Inclua recomendações ou próximos passos se aplicável
        6. Seja conciso mas completo
        
        GERE UM RESUMO ESTRUTURADO E INTELIGENTE:
        """
        
        return prompt
    
    async def _generate_response(self, prompt: str) -> str:
        """Gera resposta usando o LLM configurado"""
        try:
            if self.config.provider == 'openai':
                return await self._generate_openai_response(prompt)
            elif self.config.provider == 'anthropic':
                return await self._generate_anthropic_response(prompt)
            elif self.config.provider == 'huggingface':
                return await self._generate_huggingface_response(prompt)
            elif self.config.provider == 'local':
                return await self._generate_local_response(prompt)
            else:
                raise ValueError(f"Provider não suportado: {self.config.provider}")
        
        except Exception as e:
            logger.error(f"❌ Erro gerando resposta: {str(e)}")
            raise
    
    async def _generate_openai_response(self, prompt: str) -> str:
        """Gera resposta usando OpenAI"""
        try:
            payload = {
                'model': self.config.model,
                'messages': [
                    {'role': 'system', 'content': self.config.system_prompt},
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': self.config.max_tokens,
                'temperature': self.config.temperature
            }
            
            async with self.session.post(
                self.api_endpoints['openai'],
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"OpenAI API error {response.status}: {error_text}")
                
                data = await response.json()
                
                if 'choices' in data and len(data['choices']) > 0:
                    return data['choices'][0]['message']['content'].strip()
                else:
                    raise Exception("Resposta inválida da OpenAI API")
        
        except Exception as e:
            logger.error(f"❌ Erro OpenAI: {str(e)}")
            raise
    
    async def _generate_anthropic_response(self, prompt: str) -> str:
        """Gera resposta usando Anthropic Claude"""
        try:
            payload = {
                'model': self.config.model,
                'max_tokens': self.config.max_tokens,
                'temperature': self.config.temperature,
                'messages': [
                    {'role': 'user', 'content': prompt}
                ],
                'system': self.config.system_prompt
            }
            
            async with self.session.post(
                self.api_endpoints['anthropic'],
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Anthropic API error {response.status}: {error_text}")
                
                data = await response.json()
                
                if 'content' in data and len(data['content']) > 0:
                    return data['content'][0]['text'].strip()
                else:
                    raise Exception("Resposta inválida da Anthropic API")
        
        except Exception as e:
            logger.error(f"❌ Erro Anthropic: {str(e)}")
            raise
    
    async def _generate_huggingface_response(self, prompt: str) -> str:
        """Gera resposta usando HuggingFace"""
        try:
            payload = {
                'inputs': prompt,
                'parameters': {
                    'max_new_tokens': self.config.max_tokens,
                    'temperature': self.config.temperature,
                    'return_full_text': False
                }
            }
            
            model_url = f"{self.api_endpoints['huggingface']}/{self.config.model}"
            
            async with self.session.post(
                model_url,
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"HuggingFace API error {response.status}: {error_text}")
                
                data = await response.json()
                
                if isinstance(data, list) and len(data) > 0:
                    return data[0]['generated_text'].strip()
                else:
                    raise Exception("Resposta inválida da HuggingFace API")
        
        except Exception as e:
            logger.error(f"❌ Erro HuggingFace: {str(e)}")
            raise
    
    async def _generate_local_response(self, prompt: str) -> str:
        """Gera resposta usando modelo local"""
        try:
            payload = {
                'model': self.config.model,
                'messages': [
                    {'role': 'system', 'content': self.config.system_prompt},
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': self.config.max_tokens,
                'temperature': self.config.temperature
            }
            
            async with self.session.post(
                self.api_endpoints['local'],
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Local API error {response.status}: {error_text}")
                
                data = await response.json()
                
                if 'choices' in data and len(data['choices']) > 0:
                    return data['choices'][0]['message']['content'].strip()
                else:
                    raise Exception("Resposta inválida da API local")
        
        except Exception as e:
            logger.error(f"❌ Erro API local: {str(e)}")
            raise
    
    async def _generate_fallback_summary(self, query: str, results: List[SearchResult],
                                       extracted_data: Dict[str, Any]) -> str:
        """Gera resumo de fallback (sem IA)"""
        logger.info("🔄 Usando resumo de fallback")
        
        # Análise básica dos resultados
        sources = list(set(r.source for r in results))
        high_relevance = [r for r in results if r.relevance_score > 0.7]
        
        summary = f"""
        # Análise de Resultados para: "{query}"
        
        ## Estatísticas Gerais
        - Total de resultados analisados: {len(results)}
        - Fontes utilizadas: {', '.join(sources)}
        - Resultados com alta relevância: {len(high_relevance)}
        
        ## Principais Descobertas
        """
        
        # Adicionar insights dos dados extraídos
        if extracted_data.get('emails'):
            summary += f"- {len(extracted_data['emails'])} endereços de email encontrados\n"
        
        if extracted_data.get('phones'):
            summary += f"- {len(extracted_data['phones'])} números de telefone encontrados\n"
        
        if extracted_data.get('companies'):
            summary += f"- {len(extracted_data['companies'])} empresas identificadas\n"
        
        if extracted_data.get('keywords'):
            top_keywords = extracted_data['keywords'][:5]
            summary += f"- Palavras-chave principais: {', '.join(top_keywords)}\n"
        
        # Adicionar top resultados
        summary += "\n## Resultados Mais Relevantes\n"
        for i, result in enumerate(results[:5]):
            summary += f"{i+1}. **{result.title}** ({result.source})\n"
            summary += f"   {result.description[:200]}...\n\n"
        
        summary += """
        ## Recomendações
        - Analisar os resultados com alta relevância para obter informações detalhadas
        - Verificar os dados extraídos para contatos e entidades relevantes
        - Considerar buscas adicionais baseadas nos padrões encontrados
        """
        
        return summary.strip()
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analisa sentimento do texto
        
        Args:
            text: Texto para analisar
            
        Returns:
            Análise de sentimento
        """
        try:
            prompt = f"""
            Analise o sentimento do seguinte texto e classifique como:
            - Positivo, Negativo ou Neutro
            - Score de confiança (0-1)
            - Emoções principais
            - Tópicos abordados
            
            Texto: "{text}"
            
            Responda em formato JSON:
            {{
                "sentiment": "positivo/negativo/neutro",
                "confidence": 0.0,
                "emotions": ["emoção1", "emoção2"],
                "topics": ["tópico1", "tópico2"],
                "explanation": "breve explicação"
            }}
            """
            
            response = await self._generate_response(prompt)
            
            # Tentar parsear JSON
            try:
                import json
                return json.loads(response)
            except:
                return {
                    'sentiment': 'neutro',
                    'confidence': 0.5,
                    'emotions': [],
                    'topics': [],
                    'explanation': response[:200]
                }
        
        except Exception as e:
            logger.error(f"❌ Erro análise sentimento: {str(e)}")
            return {
                'sentiment': 'neutro',
                'confidence': 0.0,
                'emotions': [],
                'topics': [],
                'explanation': 'Erro na análise'
            }
    
    async def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extrai entidades nomeadas do texto
        
        Args:
            text: Texto para analisar
            
        Returns:
            Entidades extraídas
        """
        try:
            prompt = f"""
            Extraia entidades nomeadas do seguinte texto e classifique em:
            - Pessoas
            - Organizações
            - Locais
            - Datas
            - Números
            - Outros
            
            Texto: "{text}"
            
            Responda em formato JSON:
            {{
                "people": ["pessoa1", "pessoa2"],
                "organizations": ["org1", "org2"],
                "locations": ["local1", "local2"],
                "dates": ["data1", "data2"],
                "numbers": ["número1", "número2"],
                "others": ["outro1", "outro2"]
            }}
            """
            
            response = await self._generate_response(prompt)
            
            # Tentar parsear JSON
            try:
                import json
                return json.loads(response)
            except:
                return {
                    'people': [],
                    'organizations': [],
                    'locations': [],
                    'dates': [],
                    'numbers': [],
                    'others': []
                }
        
        except Exception as e:
            logger.error(f"❌ Erro extração entidades: {str(e)}")
            return {
                'people': [],
                'organizations': [],
                'locations': [],
                'dates': [],
                'numbers': [],
                'others': []
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificação de saúde do serviço"""
        return {
            'status': 'healthy',
            'component': 'llm_service',
            'timestamp': time.time(),
            'session_active': self.session is not None,
            'provider': self.config.provider,
            'model': self.config.model,
            'api_key_configured': bool(self.config.api_key)
        }
    
    async def cleanup(self):
        """Limpa recursos"""
        if self.session:
            await self.session.close()
        
        logger.info("🧹 LLM Service limpo")
