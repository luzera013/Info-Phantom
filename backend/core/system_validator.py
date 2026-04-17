"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - System Validator
Validação completa e final de todo o sistema
"""

import asyncio
import time
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

from .pipeline import SearchPipeline
from .data_aggregator import DataAggregator
from .robustness_manager import RobustnessManager
from ..utils.logger import setup_logger
from ..utils.metrics import MetricsCollector

logger = setup_logger(__name__)
metrics = MetricsCollector()

@dataclass
class ValidationResult:
    """Resultado da validação do sistema"""
    overall_status: str  # healthy, degraded, critical
    components_validated: int
    components_passed: int
    components_failed: int
    validation_timestamp: float
    test_results: Dict[str, Any]
    recommendations: List[str]
    system_metrics: Dict[str, Any]

class SystemValidator:
    """Validador completo do sistema OMNISCIENT"""
    
    def __init__(self):
        self.pipeline = None
        self.aggregator = None
        self.robustness_manager = None
        self.validation_results = {}
        
        logger.info("🎯 System Validator inicializado")
    
    async def initialize(self):
        """Inicializa componentes para validação"""
        logger.info("🔧 Inicializando componentes para validação...")
        
        # Inicializar pipeline
        self.pipeline = SearchPipeline()
        await self.pipeline.initialize()
        
        # Inicializar agregador
        self.aggregator = DataAggregator()
        
        # Inicializar gerenciador de robustez
        self.robustness_manager = RobustnessManager()
        await self.robustness_manager.initialize()
        
        logger.info("✅ Componentes inicializados para validação")
    
    async def validate_complete_system(self) -> ValidationResult:
        """
        Executa validação completa do sistema
        
        Returns:
            ValidationResult com status detalhado
        """
        logger.info("🎯 Iniciando validação completa do sistema...")
        start_time = time.time()
        
        # Inicializar se necessário
        if not self.pipeline:
            await self.initialize()
        
        try:
            # 1. Validação de componentes básicos
            component_validation = await self._validate_components()
            
            # 2. Validação de integração
            integration_validation = await self._validate_integration()
            
            # 3. Validação de performance
            performance_validation = await self._validate_performance()
            
            # 4. Validação de robustez
            robustness_validation = await self._validate_robustness()
            
            # 5. Validação funcional completa
            functional_validation = await self._validate_functionality()
            
            # 6. Validação de agregação unificada
            aggregation_validation = await self._validate_unified_aggregation()
            
            # 7. Validação de recuperação de falhas
            recovery_validation = await self._validate_recovery_mechanisms()
            
            # 8. Validação de métricas
            metrics_validation = await self._validate_metrics()
            
            # Combinar todos os resultados
            all_validations = {
                'components': component_validation,
                'integration': integration_validation,
                'performance': performance_validation,
                'robustness': robustness_validation,
                'functionality': functional_validation,
                'aggregation': aggregation_validation,
                'recovery': recovery_validation,
                'metrics': metrics_validation
            }
            
            # Calcular status geral
            overall_status = self._calculate_overall_status(all_validations)
            
            # Gerar recomendações
            recommendations = self._generate_recommendations(all_validations)
            
            # Obter métricas do sistema
            system_metrics = await self._get_system_metrics()
            
            # Contar componentes
            total_components = len(component_validation.get('results', {}))
            passed_components = sum(
                1 for result in component_validation.get('results', {}).values()
                if result.get('status') == 'passed'
            )
            failed_components = total_components - passed_components
            
            validation_time = time.time() - start_time
            
            validation_result = ValidationResult(
                overall_status=overall_status,
                components_validated=total_components,
                components_passed=passed_components,
                components_failed=failed_components,
                validation_timestamp=validation_time,
                test_results=all_validations,
                recommendations=recommendations,
                system_metrics=system_metrics
            )
            
            logger.info(f"✅ Validação concluída em {validation_time:.2f}s - Status: {overall_status}")
            
            # Salvar resultado da validação
            await self._save_validation_result(validation_result)
            
            return validation_result
            
        except Exception as e:
            logger.error(f"❌ Erro na validação do sistema: {str(e)}")
            
            return ValidationResult(
                overall_status='critical',
                components_validated=0,
                components_passed=0,
                components_failed=1,
                validation_timestamp=time.time(),
                test_results={'error': str(e)},
                recommendations=['Corrigir erro crítico na validação'],
                system_metrics={}
            )
    
    async def _validate_components(self) -> Dict[str, Any]:
        """Valida componentes individuais"""
        logger.info("🔍 Validando componentes individuais...")
        
        results = {}
        
        # Validar pipeline
        try:
            pipeline_health = await self.pipeline.health_check()
            results['pipeline'] = {
                'status': 'passed' if pipeline_health.get('status') == 'healthy' else 'failed',
                'details': pipeline_health,
                'message': 'Pipeline operacional' if pipeline_health.get('status') == 'healthy' else 'Pipeline com problemas'
            }
        except Exception as e:
            results['pipeline'] = {
                'status': 'failed',
                'error': str(e),
                'message': 'Pipeline com erro crítico'
            }
        
        # Validar coletores web
        web_collectors = ['web_search', 'bing_search', 'crawler', 'parser']
        for collector in web_collectors:
            try:
                component = getattr(self.pipeline, collector, None)
                if component and hasattr(component, 'health_check'):
                    health = await component.health_check()
                    results[collector] = {
                        'status': 'passed' if health.get('status') == 'healthy' else 'failed',
                        'details': health,
                        'message': f'{collector} operacional'
                    }
                else:
                    results[collector] = {
                        'status': 'failed',
                        'error': 'Método health_check não encontrado',
                        'message': f'{collector} com problemas de estrutura'
                    }
            except Exception as e:
                results[collector] = {
                    'status': 'failed',
                    'error': str(e),
                    'message': f'{collector} com erro crítico'
                }
        
        # Validar coletores sociais
        social_collectors = ['reddit_collector', 'github_collector']
        for collector in social_collectors:
            try:
                component = getattr(self.pipeline, collector, None)
                if component and hasattr(component, 'health_check'):
                    health = await component.health_check()
                    results[collector] = {
                        'status': 'passed' if health.get('status') == 'healthy' else 'failed',
                        'details': health,
                        'message': f'{collector} operacional'
                    }
                else:
                    results[collector] = {
                        'status': 'failed',
                        'error': 'Método health_check não encontrado',
                        'message': f'{collector} com problemas de estrutura'
                    }
            except Exception as e:
                results[collector] = {
                    'status': 'failed',
                    'error': str(e),
                    'message': f'{collector} com erro crítico'
                }
        
        # Validar coletores de conhecimento
        knowledge_collectors = ['wikipedia_collector', 'wikidata_collector']
        for collector in knowledge_collectors:
            try:
                component = getattr(self.pipeline, collector, None)
                if component and hasattr(component, 'health_check'):
                    health = await component.health_check()
                    results[collector] = {
                        'status': 'passed' if health.get('status') == 'healthy' else 'failed',
                        'details': health,
                        'message': f'{collector} operacional'
                    }
                else:
                    results[collector] = {
                        'status': 'failed',
                        'error': 'Método health_check não encontrado',
                        'message': f'{collector} com problemas de estrutura'
                    }
            except Exception as e:
                results[collector] = {
                    'status': 'failed',
                    'error': str(e),
                    'message': f'{collector} com erro crítico'
                }
        
        # Validar coletores de notícias
        news_collectors = ['rss_collector', 'news_collector']
        for collector in news_collectors:
            try:
                component = getattr(self.pipeline, collector, None)
                if component and hasattr(component, 'health_check'):
                    health = await component.health_check()
                    results[collector] = {
                        'status': 'passed' if health.get('status') == 'healthy' else 'failed',
                        'details': health,
                        'message': f'{collector} operacional'
                    }
                else:
                    results[collector] = {
                        'status': 'failed',
                        'error': 'Método health_check não encontrado',
                        'message': f'{collector} com problemas de estrutura'
                    }
            except Exception as e:
                results[collector] = {
                    'status': 'failed',
                    'error': str(e),
                    'message': f'{collector} com erro crítico'
                }
        
        # Validar coletores Tor
        tor_collectors = ['tor_client', 'onion_scraper']
        for collector in tor_collectors:
            try:
                component = getattr(self.pipeline, collector, None)
                if component and hasattr(component, 'health_check'):
                    health = await component.health_check()
                    results[collector] = {
                        'status': 'passed' if health.get('status') == 'healthy' else 'failed',
                        'details': health,
                        'message': f'{collector} operacional'
                    }
                else:
                    results[collector] = {
                        'status': 'failed',
                        'error': 'Método health_check não encontrado',
                        'message': f'{collector} com problemas de estrutura'
                    }
            except Exception as e:
                results[collector] = {
                    'status': 'failed',
                    'error': str(e),
                    'message': f'{collector} com erro crítico'
                }
        
        # Validar serviços de IA
        ai_services = ['llm_service', 'summarizer', 'fallback_ai']
        for service in ai_services:
            try:
                component = getattr(self.pipeline, service, None)
                if component and hasattr(component, 'health_check'):
                    health = await component.health_check()
                    results[service] = {
                        'status': 'passed' if health.get('status') == 'healthy' else 'failed',
                        'details': health,
                        'message': f'{service} operacional'
                    }
                else:
                    results[service] = {
                        'status': 'failed',
                        'error': 'Método health_check não encontrado',
                        'message': f'{service} com problemas de estrutura'
                    }
            except Exception as e:
                results[service] = {
                    'status': 'failed',
                    'error': str(e),
                    'message': f'{service} com erro crítico'
                }
        
        # Validar sistemas de cache
        cache_systems = ['cache', 'memory_cache']
        for cache in cache_systems:
            try:
                component = getattr(self.pipeline, cache, None)
                if component and hasattr(component, 'health_check'):
                    health = await component.health_check()
                    results[cache] = {
                        'status': 'passed' if health.get('status') == 'healthy' else 'failed',
                        'details': health,
                        'message': f'{cache} operacional'
                    }
                else:
                    results[cache] = {
                        'status': 'failed',
                        'error': 'Método health_check não encontrado',
                        'message': f'{cache} com problemas de estrutura'
                    }
            except Exception as e:
                results[cache] = {
                    'status': 'failed',
                    'error': str(e),
                    'message': f'{cache} com erro crítico'
                }
        
        passed_count = sum(1 for result in results.values() if result.get('status') == 'passed')
        total_count = len(results)
        
        logger.info(f"📊 Validação de componentes: {passed_count}/{total_count} passaram")
        
        return {
            'results': results,
            'passed_count': passed_count,
            'total_count': total_count,
            'message': f'Validação de componentes concluída: {passed_count}/{total_count} passaram'
        }
    
    async def _validate_integration(self) -> Dict[str, Any]:
        """Valida integração entre componentes"""
        logger.info("🔗 Validando integração entre componentes...")
        
        results = {}
        
        # Testar integração pipeline -> agregador
        try:
            if self.pipeline and self.aggregator:
                # Criar dados de teste
                test_results = await self.pipeline.execute_search("test query", max_results=10)
                
                # Validar estrutura da resposta
                required_fields = ['query', 'total', 'data', 'summary']
                missing_fields = [field for field in required_fields if field not in test_results]
                
                if not missing_fields:
                    results['pipeline_aggregator'] = {
                        'status': 'passed',
                        'message': 'Integração pipeline-agregador funcional',
                        'test_data': test_results
                    }
                else:
                    results['pipeline_aggregator'] = {
                        'status': 'failed',
                        'message': f'Campos obrigatórios faltando: {missing_fields}',
                        'missing_fields': missing_fields
                    }
            else:
                results['pipeline_aggregator'] = {
                    'status': 'failed',
                    'message': 'Componentes não inicializados'
                }
        except Exception as e:
            results['pipeline_aggregator'] = {
                'status': 'failed',
                'error': str(e),
                'message': 'Erro na integração pipeline-agregador'
            }
        
        # Testar integração com robustez
        try:
            if self.robustness_manager:
                # Testar circuit breaker
                test_result = await self.robustness_manager.execute_with_robustness(
                    lambda: "test_operation",
                    "test_operation",
                    "robustness_test"
                )
                
                results['robustness_integration'] = {
                    'status': 'passed' if test_result else 'failed',
                    'message': 'Integração com robustez funcional' if test_result else 'Problema na integração com robustez'
                }
            else:
                results['robustness_integration'] = {
                    'status': 'failed',
                    'message': 'Gerenciador de robustez não inicializado'
                }
        except Exception as e:
            results['robustness_integration'] = {
                'status': 'failed',
                'error': str(e),
                'message': 'Erro na integração com robustez'
            }
        
        logger.info("🔗 Validação de integração concluída")
        return results
    
    async def _validate_performance(self) -> Dict[str, Any]:
        """Valida performance do sistema"""
        logger.info("⚡ Validando performance do sistema...")
        
        results = {}
        
        # Testar performance com carga
        try:
            start_time = time.time()
            
            # Executar múltiplas buscas em paralelo
            tasks = []
            for i in range(5):
                task = self.pipeline.execute_search(f"test query {i}", max_results=20)
                tasks.append(task)
            
            # Medir tempo de resposta
            response_times = await asyncio.gather(*tasks, return_exceptions=True)
            
            total_time = time.time() - start_time
            successful_requests = [r for r in response_times if not isinstance(r, Exception)]
            
            # Calcular métricas
            avg_response_time = sum(
                r.get('processing_stats', {}).get('total_search_time', 0)
                for r in successful_requests
            ) / len(successful_requests) if successful_requests else 0
            
            results['performance_stress'] = {
                'status': 'passed' if len(successful_requests) >= 4 else 'failed',
                'message': f'Performance sob carga: {len(successful_requests)}/5 requisições bem-sucedidas',
                'avg_response_time': avg_response_time,
                'total_time': total_time,
                'concurrent_requests': 5
            }
            
        except Exception as e:
            results['performance_stress'] = {
                'status': 'failed',
                'error': str(e),
                'message': 'Erro no teste de performance sob carga'
            }
        
        # Validar uso de memória
        try:
            import psutil
            memory = psutil.virtual_memory()
            
            results['memory_usage'] = {
                'status': 'passed' if memory.percent < 80 else 'warning',
                'message': f'Uso de memória: {memory.percent:.1f}%',
                'details': {
                    'used_gb': memory.used / (1024**3),
                    'available_gb': memory.available / (1024**3),
                    'percent': memory.percent
                }
            }
        except Exception as e:
            results['memory_usage'] = {
                'status': 'failed',
                'error': str(e),
                'message': 'Erro verificando uso de memória'
            }
        
        logger.info("⚡ Validação de performance concluída")
        return results
    
    async def _validate_robustness(self) -> Dict[str, Any]:
        """Valida mecanismos de robustez"""
        logger.info("🛡️ Validando mecanismos de robustez...")
        
        results = {}
        
        # Testar circuit breakers
        try:
            if self.robustness_manager:
                stats = self.robustness_manager.get_robustness_stats()
                
                results['circuit_breakers'] = {
                    'status': 'passed' if stats.get('circuit_breaker_stats', {}).get('open_breakers', 0) == 0 else 'warning',
                    'message': f'Circuit breakers: {stats.get("circuit_breaker_stats", {}).get("open_breakers", 0)} abertos',
                    'details': stats
                }
            else:
                results['circuit_breakers'] = {
                    'status': 'failed',
                    'message': 'Gerenciador de robustez não inicializado'
                }
        except Exception as e:
            results['circuit_breakers'] = {
                'status': 'failed',
                'error': str(e),
                'message': 'Erro validando circuit breakers'
            }
        
        # Testar recuperação automática
        try:
            if self.robustness_manager:
                recovery_stats = stats.get('recovery_stats', {})
                
                results['auto_recovery'] = {
                    'status': 'passed' if recovery_stats.get('success_rate', 0) > 0.5 else 'warning',
                    'message': f'Taxa de recuperação: {recovery_stats.get("success_rate", 0):.1%}',
                    'details': recovery_stats
                }
            else:
                results['auto_recovery'] = {
                    'status': 'failed',
                    'message': 'Gerenciador de robustez não inicializado'
                }
        except Exception as e:
            results['auto_recovery'] = {
                'status': 'failed',
                'error': str(e),
                'message': 'Erro validando recuperação automática'
            }
        
        logger.info("🛡️ Validação de robustez concluída")
        return results
    
    async def _validate_functionality(self) -> Dict[str, Any]:
        """Valida funcionalidade completa do sistema"""
        logger.info("🧪 Validando funcionalidade completa...")
        
        results = {}
        
        # Testar busca unificada com query real
        try:
            test_queries = [
                "python programming",
                "artificial intelligence",
                "web scraping",
                "data analysis"
            ]
            
            all_results = []
            for query in test_queries:
                result = await self.pipeline.execute_search(query, max_results=10)
                all_results.append(result)
            
            # Validar estrutura das respostas
            valid_responses = 0
            for result in all_results:
                if isinstance(result, dict) and 'data' in result and 'summary' in result:
                    valid_responses += 1
                    
                    # Validar qualidade dos dados
                    data_items = result.get('data', [])
                    if len(data_items) > 0:
                        valid_data = any(
                            item.get('title') and item.get('link') and item.get('content')
                            for item in data_items[:5]  # Verificar primeiros 5 itens
                        )
                        
                        if not valid_data:
                            logger.warning(f"Dados inválidos encontrados para query: {query}")
            
            results['end_to_end_functionality'] = {
                'status': 'passed' if valid_responses == len(test_queries) else 'failed',
                'message': f'Funcionalidade E2E: {valid_responses}/{len(test_queries)} queries bem-sucedidas',
                'test_queries': test_queries,
                'success_rate': valid_responses / len(test_queries)
            }
            
        except Exception as e:
            results['end_to_end_functionality'] = {
                'status': 'failed',
                'error': str(e),
                'message': 'Erro no teste de funcionalidade E2E'
            }
        
        logger.info("🧪 Validação de funcionalidade concluída")
        return results
    
    async def _validate_unified_aggregation(self) -> Dict[str, Any]:
        """Valida sistema de agregação unificada"""
        logger.info("🔗 Validando agregação unificada...")
        
        results = {}
        
        try:
            if self.aggregator:
                # Criar dados de teste para agregação
                test_data = {
                    'web_results': [
                        {'title': 'Test Web 1', 'url': 'http://example1.com', 'description': 'Test description 1'},
                        {'title': 'Test Web 2', 'url': 'http://example2.com', 'description': 'Test description 2'}
                    ],
                    'news_results': [
                        {'title': 'Test News 1', 'url': 'http://news1.com', 'description': 'Test news 1'},
                        {'title': 'Test News 2', 'url': 'http://news2.com', 'description': 'Test news 2'}
                    ]
                }
                
                # Testar agregação
                aggregated = await self.aggregator.aggregate_all_sources(
                    query="test aggregation",
                    **test_data
                )
                
                # Validar estrutura da agregação
                required_fields = ['query', 'total', 'data', 'summary', 'sources_analyzed']
                missing_fields = [field for field in required_fields if field not in aggregated]
                
                if not missing_fields:
                    # Validar qualidade dos dados agregados
                    data_items = aggregated.get('data', [])
                    valid_data = any(
                        item.get('source') and item.get('title') and item.get('analysis')
                        for item in data_items[:5]
                    )
                    
                    results['unified_aggregation'] = {
                        'status': 'passed' if valid_data else 'failed',
                        'message': f'Agregação unificada {"funciona" if valid_data else "com problemas"}',
                        'aggregated_items': len(data_items),
                        'sources_count': len(aggregated.get('sources_analyzed', [])),
                        'details': aggregated
                    }
                else:
                    results['unified_aggregation'] = {
                        'status': 'failed',
                        'message': f'Campos obrigatórios faltando: {missing_fields}',
                        'missing_fields': missing_fields
                    }
            else:
                results['unified_aggregation'] = {
                    'status': 'failed',
                    'message': 'Agregador não inicializado'
                }
                
        except Exception as e:
            results['unified_aggregation'] = {
                'status': 'failed',
                'error': str(e),
                'message': 'Erro na validação da agregação unificada'
            }
        
        logger.info("🔗 Validação de agregação unificada concluída")
        return results
    
    async def _validate_recovery_mechanisms(self) -> Dict[str, Any]:
        """Valida mecanismos de recuperação de falhas"""
        logger.info("🔄 Validando mecanismos de recuperação...")
        
        results = {}
        
        # Testar fallbacks
        try:
            # Simular falha e testar fallback
            test_operations = [
                ('search', 'web_search'),
                ('ai', 'llm_service'),
                ('storage', 'cache')
            ]
            
            fallback_tests = []
            for operation, component in test_operations:
                try:
                    # Simular operação com falha
                    result = await self.robustness_manager.execute_with_robustness(
                        lambda: None,  # Simular falha
                        f"test_{operation}",
                        component
                    )
                    
                    # Verificar se fallback foi usado
                    fallback_used = (
                        isinstance(result, dict) and 
                        'fallback' in str(result).lower()
                    )
                    
                    fallback_tests.append({
                        'operation': operation,
                        'component': component,
                        'fallback_triggered': fallback_used,
                        'status': 'passed' if fallback_used else 'failed'
                    })
                    
                except Exception as e:
                    fallback_tests.append({
                        'operation': operation,
                        'component': component,
                        'fallback_triggered': False,
                        'status': 'failed',
                        'error': str(e)
                    })
            
            successful_fallbacks = sum(1 for test in fallback_tests if test.get('fallback_triggered'))
            
            results['fallback_mechanisms'] = {
                'status': 'passed' if successful_fallbacks >= 2 else 'warning',
                'message': f'Fallbacks funcionando: {successful_fallbacks}/{len(test_operations)}',
                'test_results': fallback_tests
            }
            
        except Exception as e:
            results['fallback_mechanisms'] = {
                'status': 'failed',
                'error': str(e),
                'message': 'Erro testando mecanismos de fallback'
            }
        
        logger.info("🔄 Validação de recuperação concluída")
        return results
    
    async def _validate_metrics(self) -> Dict[str, Any]:
        """Valida sistema de métricas"""
        logger.info("📊 Validando sistema de métricas...")
        
        results = {}
        
        try:
            # Verificar se métricas estão sendo coletadas
            if hasattr(metrics, 'get_all_metrics'):
                all_metrics = metrics.get_all_metrics()
                
                results['metrics_collection'] = {
                    'status': 'passed' if all_metrics else 'failed',
                    'message': f'Métricas coletadas: {len(all_metrics)} tipos',
                    'metrics_count': len(all_metrics),
                    'details': all_metrics
                }
            else:
                results['metrics_collection'] = {
                    'status': 'failed',
                    'message': 'Sistema de métricas não disponível'
                }
                
        except Exception as e:
            results['metrics_collection'] = {
                'status': 'failed',
                'error': str(e),
                'message': 'Erro validando sistema de métricas'
            }
        
        logger.info("📊 Validação de métricas concluída")
        return results
    
    def _calculate_overall_status(self, all_validations: Dict[str, Any]) -> str:
        """Calcula status geral do sistema"""
        status_scores = []
        
        # Pontuar cada validação
        for validation_name, validation in all_validations.items():
            if validation.get('status') == 'passed':
                status_scores.append(1.0)
            elif validation.get('status') == 'warning':
                status_scores.append(0.5)
            elif validation.get('status') == 'failed':
                status_scores.append(0.0)
        
        if not status_scores:
            return 'critical'
        
        avg_score = sum(status_scores) / len(status_scores)
        
        if avg_score >= 0.8:
            return 'healthy'
        elif avg_score >= 0.6:
            return 'degraded'
        else:
            return 'critical'
    
    def _generate_recommendations(self, all_validations: Dict[str, Any]) -> List[str]:
        """Gera recomendações baseadas nos resultados da validação"""
        recommendations = []
        
        # Analisar problemas comuns
        issues_found = []
        
        for validation_name, validation in all_validations.items():
            if validation.get('status') == 'failed':
                issues_found.append(validation_name)
        
        # Recomendações específicas
        if 'components' in issues_found:
            recommendations.append("Verificar configurações dos coletores e dependências")
        
        if 'performance' in issues_found:
            recommendations.append("Otimizar uso de recursos e configurar limits adequados")
        
        if 'robustness' in issues_found:
            recommendations.append("Revisar estratégias de recuperação e circuit breakers")
        
        if 'functionality' in issues_found:
            recommendations.append("Testar integração entre componentes em ambiente controlado")
        
        if 'integration' in issues_found:
            recommendations.append("Verificar contratos e interfaces entre componentes")
        
        # Recomendações gerais
        if len(issues_found) > 3:
            recommendations.append("Considerar rollback para versão estável se disponível")
        
        if not recommendations:
            recommendations.append("Sistema operando normalmente - monitorar continuamente")
        
        return recommendations
    
    async def _get_system_metrics(self) -> Dict[str, Any]:
        """Obtém métricas detalhadas do sistema"""
        try:
            import psutil
            
            # Métricas de CPU
            cpu_metrics = {
                'usage_percent': psutil.cpu_percent(interval=1),
                'core_count': psutil.cpu_count(),
                'frequency': psutil.cpu_freq()
            }
            
            # Métricas de memória
            memory = psutil.virtual_memory()
            memory_metrics = {
                'total_gb': memory.total / (1024**3),
                'available_gb': memory.available / (1024**3),
                'used_gb': memory.used / (1024**3),
                'percent': memory.percent
            }
            
            # Métricas de disco
            disk = psutil.disk_usage('/')
            disk_metrics = {
                'total_gb': disk.total / (1024**3),
                'used_gb': disk.used / (1024**3),
                'free_gb': disk.free / (1024**3),
                'percent': disk.percent
            }
            
            # Métricas de rede
            network = psutil.net_io_counters()
            network_metrics = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }
            
            return {
                'cpu': cpu_metrics,
                'memory': memory_metrics,
                'disk': disk_metrics,
                'network': network_metrics,
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"❌ Erro obtendo métricas do sistema: {str(e)}")
            return {}
    
    async def _save_validation_result(self, result: ValidationResult):
        """Salva resultado da validação"""
        try:
            # Criar diretório de logs se não existir
            log_dir = Path("./logs")
            log_dir.mkdir(exist_ok=True)
            
            # Salvar resultado em JSON
            validation_file = log_dir / f"validation_{int(result.validation_timestamp)}.json"
            
            with open(validation_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(result), f, indent=2, ensure_ascii=False)
            
            logger.info(f"📄 Resultado da validação salvo em: {validation_file}")
            
        except Exception as e:
            logger.error(f"❌ Erro salvando validação: {str(e)}")
    
    async def cleanup(self):
        """Limpa recursos do validador"""
        logger.info("🧹 Limpando recursos do System Validator...")
        
        if self.pipeline:
            await self.pipeline.cleanup()
        
        if self.robustness_manager:
            await self.robustness_manager.cleanup()
        
        logger.info("✅ System Validator limpo")
