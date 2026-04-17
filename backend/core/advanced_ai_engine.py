"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Advanced AI Engine
Motor de inteligência artificial avançado com múltiplos modelos e capacidades
"""

import asyncio
import time
import json
import hashlib
import re
from typing import List, Dict, Any, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import logging
import math

from ..services.ai.llm import LLMService
from ..services.ai.summarizer import SummarizerService
from ..services.ai.fallback import FallbackAIService
from ..collectors.massive_collector_factory import UnifiedSearchResult
from ..utils.logger import setup_logger
from ..utils.metrics import MetricsCollector
from ..utils.ttl_cache import TTLCache

logger = setup_logger(__name__)
metrics = MetricsCollector()

@dataclass
class AIRequest:
    """Requisição para processamento de IA"""
    request_id: str
    task_type: str  # summarize, analyze, classify, extract, generate, translate
    input_data: Any
    context: Dict[str, Any] = field(default_factory=dict)
    model_preferences: List[str] = field(default_factory=list)
    temperature: float = 0.7
    max_tokens: int = 1000
    priority: int = 1  # 1-5, onde 5 é maior prioridade
    timeout: int = 30

@dataclass
class AIResponse:
    """Resposta da IA com metadados avançados"""
    request_id: str
    task_type: str
    result: Any
    confidence: float = 0.0
    processing_time: float = 0.0
    model_used: str = ""
    tokens_used: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    alternatives: List[Any] = field(default_factory=list)
    reasoning: str = ""
    quality_score: float = 0.0

@dataclass
class AIModel:
    """Modelo de IA com configurações"""
    name: str
    model_type: str  # llm, summarizer, classifier, extractor
    capabilities: List[str] = field(default_factory=list)
    max_tokens: int = 4000
    temperature_range: Tuple[float, float] = (0.0, 2.0)
    cost_per_token: float = 0.0
    speed: float = 1.0  # Tokens por segundo
    quality_score: float = 1.0
    available: bool = True

class AdvancedAIEngine:
    """Motor de IA avançado com múltiplos modelos e orquestração inteligente"""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.summarizer = SummarizerService()
        self.fallback_ai = FallbackAIService()
        self.cache = TTLCache(ttl=3600)  # 1 hora
        self.request_queue: List[AIRequest] = []
        self.active_requests: Dict[str, AIRequest] = {}
        self.processing_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_processing_time': 0.0,
            'cache_hit_rate': 0.0,
            'model_usage': defaultdict(int)
        }
        
        # Configurar modelos disponíveis
        self.models = self._setup_available_models()
        
        # Configurações de otimização
        self.config = {
            'max_concurrent_requests': 10,
            'auto_model_selection': True,
            'fallback_enabled': True,
            'caching_enabled': True,
            'quality_threshold': 0.7,
            'cost_optimization': True,
            'speed_optimization': False,
            'reasoning_enabled': True,
            'alternatives_enabled': True,
            'confidence_threshold': 0.5
        }
        
        logger.info(" Advanced AI Engine inicializado")
    
    def _setup_available_models(self) -> Dict[str, AIModel]:
        """Configura modelos de IA disponíveis"""
        models = {
            'gpt-4': AIModel(
                name='gpt-4',
                model_type='llm',
                capabilities=['summarize', 'analyze', 'classify', 'extract', 'generate', 'translate'],
                max_tokens=8000,
                temperature_range=(0.0, 2.0),
                cost_per_token=0.00003,
                speed=50,
                quality_score=0.95
            ),
            'gpt-3.5-turbo': AIModel(
                name='gpt-3.5-turbo',
                model_type='llm',
                capabilities=['summarize', 'analyze', 'classify', 'extract', 'generate', 'translate'],
                max_tokens=4000,
                temperature_range=(0.0, 2.0),
                cost_per_token=0.000001,
                speed=100,
                quality_score=0.85
            ),
            'claude-3': AIModel(
                name='claude-3',
                model_type='llm',
                capabilities=['summarize', 'analyze', 'classify', 'extract', 'generate'],
                max_tokens=100000,
                temperature_range=(0.0, 1.0),
                cost_per_token=0.000015,
                speed=40,
                quality_score=0.92
            ),
            'specialized-summarizer': AIModel(
                name='specialized-summarizer',
                model_type='summarizer',
                capabilities=['summarize'],
                max_tokens=2000,
                temperature_range=(0.1, 0.8),
                cost_per_token=0.000002,
                speed=80,
                quality_score=0.88
            ),
            'text-classifier': AIModel(
                name='text-classifier',
                model_type='classifier',
                capabilities=['classify'],
                max_tokens=1000,
                temperature_range=(0.0, 0.5),
                cost_per_token=0.000001,
                speed=120,
                quality_score=0.82
            ),
            'entity-extractor': AIModel(
                name='entity-extractor',
                model_type='extractor',
                capabilities=['extract'],
                max_tokens=1500,
                temperature_range=(0.0, 0.3),
                cost_per_token=0.000001,
                speed=100,
                quality_score=0.86
            ),
            'fallback-model': AIModel(
                name='fallback-model',
                model_type='llm',
                capabilities=['summarize', 'analyze', 'classify', 'extract', 'generate'],
                max_tokens=2000,
                temperature_range=(0.5, 1.0),
                cost_per_token=0.0,
                speed=200,
                quality_score=0.6
            )
        }
        
        return models
    
    async def initialize(self):
        """Inicializa o motor de IA"""
        logger.info(" Advanced AI Engine pronto")
    
    async def process_request(self, request: AIRequest) -> AIResponse:
        """
        Processa uma requisição de IA com orquestração inteligente
        
        Args:
            request: Requisição de processamento
            
        Returns:
            Resposta processada com metadados
        """
        start_time = time.time()
        
        logger.info(f" Processando requisição {request.request_id}: {request.task_type}")
        
        try:
            # Verificar cache
            if self.config['caching_enabled']:
                cache_key = f"ai_request:{hashlib.md5(str(request).encode()).hexdigest()}"
                cached_response = await self.cache.get(cache_key)
                if cached_response:
                    logger.debug(f" Cache hit para requisição {request.request_id}")
                    metrics.increment_cache_hit()
                    return cached_response
            
            # Selecionar modelo ótimo
            selected_model = await self._select_optimal_model(request)
            
            # Processar requisição
            response = await self._execute_with_model(request, selected_model)
            
            # Adicionar reasoning se habilitado
            if self.config['reasoning_enabled']:
                response.reasoning = await self._generate_reasoning(request, response)
            
            # Gerar alternativas se habilitado
            if self.config['alternatives_enabled']:
                response.alternatives = await self._generate_alternatives(request, response)
            
            # Calcular score de qualidade
            response.quality_score = self._calculate_response_quality(request, response)
            
            # Atualizar estatísticas
            self.processing_stats['total_requests'] += 1
            self.processing_stats['successful_requests'] += 1
            self.processing_stats['model_usage'][selected_model.name] += 1
            
            # Atualizar tempo médio
            processing_time = time.time() - start_time
            self._update_avg_processing_time(processing_time)
            response.processing_time = processing_time
            
            # Salvar em cache
            if self.config['caching_enabled']:
                await self.cache.set(cache_key, response)
            
            logger.info(f" Requisição {request.request_id} concluída em {processing_time:.2f}s")
            return response
            
        except Exception as e:
            logger.error(f" Erro na requisição {request.request_id}: {str(e)}")
            
            # Tentar fallback
            if self.config['fallback_enabled']:
                try:
                    fallback_response = await self._execute_fallback(request)
                    fallback_response.processing_time = time.time() - start_time
                    return fallback_response
                except Exception as fallback_error:
                    logger.error(f" Erro no fallback: {str(fallback_error)}")
            
            # Retornar resposta de erro
            self.processing_stats['total_requests'] += 1
            self.processing_stats['failed_requests'] += 1
            
            return AIResponse(
                request_id=request.request_id,
                task_type=request.task_type,
                result=None,
                confidence=0.0,
                processing_time=time.time() - start_time,
                model_used="error",
                metadata={'error': str(e)},
                quality_score=0.0
            )
    
    async def _select_optimal_model(self, request: AIRequest) -> AIModel:
        """Seleciona o modelo ótimo para a requisição"""
        if not self.config['auto_model_selection']:
            # Usar preferências do usuário
            if request.model_preferences:
                for model_name in request.model_preferences:
                    if model_name in self.models and self.models[model_name].available:
                        return self.models[model_name]
        
        # Filtrar modelos por capacidade
        capable_models = [
            model for model in self.models.values()
            if request.task_type in model.capabilities and model.available
        ]
        
        if not capable_models:
            # Usar fallback
            return self.models['fallback-model']
        
        # Ordenar por critérios de otimização
        if self.config['cost_optimization']:
            # Otimizar por custo
            capable_models.sort(key=lambda m: m.cost_per_token)
        elif self.config['speed_optimization']:
            # Otimizar por velocidade
            capable_models.sort(key=lambda m: -m.speed)
        else:
            # Otimizar por qualidade (padrão)
            capable_models.sort(key=lambda m: -m.quality_score)
        
        # Verificar limites de tokens
        for model in capable_models:
            if model.max_tokens >= request.max_tokens:
                return model
        
        # Se nenhum modelo atender aos requisitos, usar o primeiro capaz
        return capable_models[0]
    
    async def _execute_with_model(self, request: AIRequest, model: AIModel) -> AIResponse:
        """Executa requisição com modelo específico"""
        try:
            if request.task_type == 'summarize':
                return await self._execute_summarization(request, model)
            elif request.task_type == 'analyze':
                return await self._execute_analysis(request, model)
            elif request.task_type == 'classify':
                return await self._execute_classification(request, model)
            elif request.task_type == 'extract':
                return await self._execute_extraction(request, model)
            elif request.task_type == 'generate':
                return await self._execute_generation(request, model)
            elif request.task_type == 'translate':
                return await self._execute_translation(request, model)
            else:
                raise ValueError(f"Tipo de tarefa não suportado: {request.task_type}")
                
        except Exception as e:
            logger.error(f" Erro executando com modelo {model.name}: {str(e)}")
            raise
    
    async def _execute_summarization(self, request: AIRequest, model: AIModel) -> AIResponse:
        """Executa tarefa de sumarização"""
        if isinstance(request.input_data, str):
            text = request.input_data
        elif isinstance(request.input_data, list):
            # Combinar múltiplos textos
            text = '\n\n'.join(str(item) for item in request.input_data)
        else:
            text = str(request.input_data)
        
        # Usar serviço especializado se disponível
        if model.name == 'specialized-summarizer':
            summary = await self.summarizer.summarize_text(text, request.max_tokens)
        else:
            # Usar LLM genérico
            prompt = f"Resuma o seguinte texto de forma concisa e clara:\n\n{text}\n\nResumo:"
            summary = await self.llm_service.generate_text(prompt, request.max_tokens, request.temperature)
        
        confidence = self._calculate_confidence(text, summary, 'summarize')
        
        return AIResponse(
            request_id=request.request_id,
            task_type='summarize',
            result=summary,
            confidence=confidence,
            model_used=model.name,
            tokens_used=len(summary.split()) + len(text.split()),
            metadata={'input_length': len(text), 'summary_length': len(summary)}
        )
    
    async def _execute_analysis(self, request: AIRequest, model: AIModel) -> AIResponse:
        """Executa tarefa de análise"""
        if isinstance(request.input_data, str):
            text = request.input_data
        else:
            text = str(request.input_data)
        
        # Análise abrangente
        prompt = f"""
        Analise o seguinte texto de forma completa:
        
        {text}
        
        Forneça:
        1. Sentimento geral (positivo, negativo, neutro)
        2. Tópicos principais
        3. Entidades mencionadas
        4. Tom e estilo
        5. Qualidade e credibilidade
        6. Insights relevantes
        
        Análise:
        """
        
        analysis = await self.llm_service.generate_text(prompt, request.max_tokens, request.temperature)
        
        confidence = self._calculate_confidence(text, analysis, 'analyze')
        
        return AIResponse(
            request_id=request.request_id,
            task_type='analyze',
            result=analysis,
            confidence=confidence,
            model_used=model.name,
            tokens_used=len(analysis.split()) + len(text.split()),
            metadata={'input_length': len(text), 'analysis_length': len(analysis)}
        )
    
    async def _execute_classification(self, request: AIRequest, model: AIModel) -> AIResponse:
        """Executa tarefa de classificação"""
        text = str(request.input_data)
        
        # Determinar categorias com base no contexto
        categories = request.context.get('categories', ['positivo', 'negativo', 'neutro'])
        
        prompt = f"""
        Classifique o seguinte texto em uma das categorias: {', '.join(categories)}
        
        Texto: {text}
        
        Responda apenas com o nome da categoria:
        """
        
        classification = await self.llm_service.generate_text(prompt, 50, 0.1)
        
        # Limpar resposta
        classification = classification.strip().lower()
        if classification not in categories:
            # Tentar encontrar categoria mais próxima
            for category in categories:
                if category in classification or classification in category:
                    classification = category
                    break
        
        confidence = self._calculate_confidence(text, classification, 'classify')
        
        return AIResponse(
            request_id=request.request_id,
            task_type='classify',
            result=classification,
            confidence=confidence,
            model_used=model.name,
            tokens_used=len(text.split()),
            metadata={'categories': categories, 'input_length': len(text)}
        )
    
    async def _execute_extraction(self, request: AIRequest, model: AIModel) -> AIResponse:
        """Executa tarefa de extração"""
        text = str(request.input_data)
        
        # Determinar o que extrair
        extract_types = request.context.get('extract_types', ['entities', 'keywords', 'sentences'])
        
        prompt = f"""
        Extraia as seguintes informações do texto: {', '.join(extract_types)}
        
        Texto: {text}
        
        Extraia e formate como JSON:
        """
        
        extracted = await self.llm_service.generate_text(prompt, request.max_tokens, 0.1)
        
        # Tentar parsear JSON
        try:
            extracted_data = json.loads(extracted)
        except:
            # Fallback para extração manual
            extracted_data = self._manual_extraction(text, extract_types)
        
        confidence = self._calculate_confidence(text, extracted_data, 'extract')
        
        return AIResponse(
            request_id=request.request_id,
            task_type='extract',
            result=extracted_data,
            confidence=confidence,
            model_used=model.name,
            tokens_used=len(extracted.split()) + len(text.split()),
            metadata={'extract_types': extract_types, 'input_length': len(text)}
        )
    
    async def _execute_generation(self, request: AIRequest, model: AIModel) -> AIResponse:
        """Executa tarefa de geração"""
        prompt = str(request.input_data)
        
        generated = await self.llm_service.generate_text(prompt, request.max_tokens, request.temperature)
        
        confidence = self._calculate_confidence(prompt, generated, 'generate')
        
        return AIResponse(
            request_id=request.request_id,
            task_type='generate',
            result=generated,
            confidence=confidence,
            model_used=model.name,
            tokens_used=len(generated.split()) + len(prompt.split()),
            metadata={'prompt_length': len(prompt), 'generated_length': len(generated)}
        )
    
    async def _execute_translation(self, request: AIRequest, model: AIModel) -> AIResponse:
        """Executa tarefa de tradução"""
        text = str(request.input_data)
        target_language = request.context.get('target_language', 'inglês')
        
        prompt = f"""
        Traduza o seguinte texto para {target_language}:
        
        {text}
        
        Tradução:
        """
        
        translation = await self.llm_service.generate_text(prompt, request.max_tokens, 0.3)
        
        confidence = self._calculate_confidence(text, translation, 'translate')
        
        return AIResponse(
            request_id=request.request_id,
            task_type='translate',
            result=translation,
            confidence=confidence,
            model_used=model.name,
            tokens_used=len(translation.split()) + len(text.split()),
            metadata={'source_language': 'auto', 'target_language': target_language}
        )
    
    async def _execute_fallback(self, request: AIRequest) -> AIResponse:
        """Executa processamento com fallback"""
        try:
            if request.task_type == 'summarize':
                result = await self.fallback_ai.generate_summary(str(request.input_data))
            elif request.task_type == 'analyze':
                result = f"Análise básica de: {str(request.input_data)[:200]}..."
            elif request.task_type == 'classify':
                result = "neutro"  # Classificação padrão
            elif request.task_type == 'extract':
                result = {"entities": [], "keywords": [], "sentences": []}
            elif request.task_type == 'generate':
                result = f"Resposta gerada para: {str(request.input_data)[:100]}..."
            elif request.task_type == 'translate':
                result = str(request.input_data)  # Sem tradução
            else:
                result = "Processamento não disponível"
            
            return AIResponse(
                request_id=request.request_id,
                task_type=request.task_type,
                result=result,
                confidence=0.3,
                model_used='fallback-model',
                metadata={'fallback_used': True}
            )
            
        except Exception as e:
            raise Exception(f"Fallback failed: {str(e)}")
    
    def _manual_extraction(self, text: str, extract_types: List[str]) -> Dict[str, Any]:
        """Extração manual como fallback"""
        result = {}
        
        if 'entities' in extract_types:
            # Extrair entidades básicas
            entities = []
            
            # Emails
            emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
            entities.extend([{'type': 'email', 'value': email} for email in emails])
            
            # URLs
            urls = re.findall(r'https?://[^\s]+', text)
            entities.extend([{'type': 'url', 'value': url} for url in urls])
            
            # Telefone
            phones = re.findall(r'\b\d{2,4}[-.\s]?\d{4,5}[-.\s]?\d{4}\b', text)
            entities.extend([{'type': 'phone', 'value': phone} for phone in phones])
            
            result['entities'] = entities
        
        if 'keywords' in extract_types:
            # Extrair palavras-chave
            words = re.findall(r'\b\w+\b', text.lower())
            stop_words = {'o', 'a', 'os', 'as', 'de', 'do', 'da', 'em', 'para', 'com', 'que', 'e', 'é', 'um', 'uma'}
            keywords = [w for w in words if w not in stop_words and len(w) > 3]
            result['keywords'] = list(set(keywords))[:20]  # Top 20
        
        if 'sentences' in extract_types:
            # Extrair sentenças
            sentences = re.split(r'[.!?]+', text)
            result['sentences'] = [s.strip() for s in sentences if s.strip()][:10]  # Top 10
        
        return result
    
    def _calculate_confidence(self, input_data: Any, result: Any, task_type: str) -> float:
        """Calcula confiança da resposta"""
        confidence = 0.5  # Base
        
        # Ajustar por tipo de tarefa
        if task_type == 'summarize':
            # Sumarização: baseado no comprimento relativo
            if isinstance(input_data, str) and isinstance(result, str):
                ratio = len(result) / len(input_data)
                if 0.1 <= ratio <= 0.3:  # Resumo ideal
                    confidence += 0.3
                elif 0.05 <= ratio <= 0.5:
                    confidence += 0.1
        
        elif task_type == 'classify':
            # Classificação: baseado na clareza
            if isinstance(result, str) and len(result.split()) == 1:
                confidence += 0.3
        
        elif task_type == 'extract':
            # Extração: baseado na quantidade de dados extraídos
            if isinstance(result, dict):
                total_items = sum(len(v) if isinstance(v, list) else 1 for v in result.values())
                if total_items > 0:
                    confidence += min(total_items / 10, 0.3)
        
        elif task_type == 'generate':
            # Geração: baseado no comprimento e relevância
            if isinstance(result, str):
                if len(result) > 50:
                    confidence += 0.2
                if len(result.split()) > 10:
                    confidence += 0.1
        
        return min(confidence, 1.0)
    
    async def _generate_reasoning(self, request: AIRequest, response: AIResponse) -> str:
        """Gera explicação do raciocínio"""
        try:
            prompt = f"""
            Explique brevemente como chegou a esta resposta:
            
            Tarefa: {request.task_type}
            Entrada: {str(request.input_data)[:200]}...
            Saída: {str(response.result)[:200]}...
            
            Raciocínio:
            """
            
            reasoning = await self.llm_service.generate_text(prompt, 200, 0.3)
            return reasoning.strip()
            
        except Exception as e:
            logger.warning(f" Erro gerando reasoning: {str(e)}")
            return "Raciocínio baseado em análise padrão do conteúdo."
    
    async def _generate_alternatives(self, request: AIRequest, response: AIResponse) -> List[Any]:
        """Gera respostas alternativas"""
        try:
            if request.task_type in ['classify', 'extract']:
                # Para classificação e extração, não faz sentido gerar alternativas
                return []
            
            alternatives = []
            
            # Gerar 2 alternativas com temperaturas diferentes
            for temp in [request.temperature - 0.2, request.temperature + 0.2]:
                if 0.0 <= temp <= 2.0:
                    alt_request = AIRequest(
                        request_id=f"{request.request_id}_alt_{temp}",
                        task_type=request.task_type,
                        input_data=request.input_data,
                        temperature=temp,
                        max_tokens=request.max_tokens // 2  # Alternativas menores
                    )
                    
                    alt_response = await self._execute_with_model(alt_request, self.models[response.model_used])
                    alternatives.append(alt_response.result)
            
            return alternatives
            
        except Exception as e:
            logger.warning(f" Erro gerando alternativas: {str(e)}")
            return []
    
    def _calculate_response_quality(self, request: AIRequest, response: AIResponse) -> float:
        """Calcula score de qualidade da resposta"""
        quality = 0.0
        
        # Confiança (40%)
        quality += response.confidence * 0.4
        
        # Comprimento apropriado (20%)
        if isinstance(response.result, str):
            length = len(response.result)
            if 50 <= length <= 1000:
                quality += 0.2
            elif 20 <= length <= 2000:
                quality += 0.1
        
        # Relevância (20%)
        if isinstance(request.input_data, str) and isinstance(response.result, str):
            input_words = set(request.input_data.lower().split())
            result_words = set(response.result.lower().split())
            overlap = len(input_words & result_words)
            quality += min(overlap / max(len(input_words), 1), 0.2)
        
        # Formato (10%)
        if request.task_type == 'extract' and isinstance(response.result, dict):
            quality += 0.1
        elif request.task_type in ['summarize', 'generate'] and isinstance(response.result, str):
            quality += 0.1
        
        # Alternativas (10%)
        if response.alternatives:
            quality += 0.1
        
        return min(quality, 1.0)
    
    def _update_avg_processing_time(self, processing_time: float):
        """Atualiza tempo médio de processamento"""
        total = self.processing_stats['total_requests']
        current_avg = self.processing_stats['avg_processing_time']
        new_avg = (current_avg * (total - 1) + processing_time) / total
        self.processing_stats['avg_processing_time'] = new_avg
    
    async def batch_process(self, requests: List[AIRequest]) -> List[AIResponse]:
        """Processa múltiplas requisições em lote"""
        logger.info(f" Processando lote de {len(requests)} requisições")
        
        # Ordenar por prioridade
        sorted_requests = sorted(requests, key=lambda r: r.priority, reverse=True)
        
        # Processar em lotes concorrentes
        batch_size = self.config['max_concurrent_requests']
        results = []
        
        for i in range(0, len(sorted_requests), batch_size):
            batch = sorted_requests[i:i + batch_size]
            
            # Executar lote concorrentemente
            batch_tasks = [self.process_request(req) for req in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Processar resultados do lote
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f" Erro no lote: {str(result)}")
                    # Criar resposta de erro
                    error_response = AIResponse(
                        request_id="error",
                        task_type="error",
                        result=None,
                        confidence=0.0,
                        model_used="error",
                        metadata={'error': str(result)},
                        quality_score=0.0
                    )
                    results.append(error_response)
                else:
                    results.append(result)
        
        logger.info(f" Lote processado: {len(results)} respostas")
        return results
    
    async def intelligent_summarize(self, results: List[UnifiedSearchResult], query: str) -> str:
        """Sumarização inteligente de múltiplos resultados"""
        # Agrupar resultados por fonte
        grouped_results = defaultdict(list)
        for result in results:
            grouped_results[result.source].append(result)
        
        # Gerar resumo por fonte
        source_summaries = []
        for source, source_results in grouped_results.items():
            combined_content = '\n\n'.join([
                f"Título: {r.title}\nConteúdo: {r.content[:300]}..."
                for r in source_results[:5]  # Limitar por fonte
            ])
            
            request = AIRequest(
                request_id=f"summary_{source}_{int(time.time())}",
                task_type='summarize',
                input_data=combined_content,
                max_tokens=200,
                temperature=0.5
            )
            
            response = await self.process_request(request)
            if response.result:
                source_summaries.append(f"Fonte {source}: {response.result}")
        
        # Gerar resumo final
        if source_summaries:
            final_summary_request = AIRequest(
                request_id=f"final_summary_{int(time.time())}",
                task_type='summarize',
                input_data='\n\n'.join(source_summaries),
                max_tokens=300,
                temperature=0.3
            )
            
            final_response = await self.process_request(final_summary_request)
            return final_response.result or "Não foi possível gerar resumo."
        
        return "Nenhum conteúdo disponível para resumir."
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificação de saúde do motor de IA"""
        try:
            # Testar modelo básico
            test_request = AIRequest(
                request_id="health_check",
                task_type='generate',
                input_data="Teste de saúde",
                max_tokens=10
            )
            
            test_response = await self.process_request(test_request)
            
            return {
                'status': 'healthy',
                'component': 'advanced_ai_engine',
                'timestamp': datetime.now().isoformat(),
                'models_available': len([m for m in self.models.values() if m.available]),
                'processing_stats': self.processing_stats,
                'cache_status': {
                    'cache_size': len(self.cache.cache),
                    'hit_rate': self.processing_stats['cache_hit_rate']
                },
                'config': self.config,
                'test_result': {
                    'success': test_response.confidence > 0,
                    'response_time': test_response.processing_time,
                    'model_used': test_response.model_used
                }
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'component': 'advanced_ai_engine',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    async def cleanup(self):
        """Limpa recursos do motor de IA"""
        self.cache.clear()
        self.request_queue.clear()
        self.active_requests.clear()
        logger.info(" Advanced AI Engine limpo")
