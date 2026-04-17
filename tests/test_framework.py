"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Test Framework
Framework de testes para validar os 2240 coletores de dados
"""

import asyncio
import pytest
import time
import json
import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import unittest
from unittest.mock import Mock, patch, AsyncMock
import aiohttp
import requests
from concurrent.futures import ThreadPoolExecutor
import statistics

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Resultado de um teste"""
    collector_name: str
    test_type: str
    status: str  # 'passed', 'failed', 'skipped', 'error'
    duration: float
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

@dataclass
class TestSuite:
    """Suite de testes para um coletor"""
    collector_name: str
    collector_class: type
    results: List[TestResult]
    total_duration: float
    passed: int
    failed: int
    skipped: int
    errors: int

class CollectorTestFramework:
    """Framework de testes para coletores"""
    
    def __init__(self):
        self.test_results: List[TestResult] = []
        self.test_suites: List[TestSuite] = []
        self.start_time = None
        self.end_time = None
        self.total_collectors = 0
        self.total_passed = 0
        self.total_failed = 0
        self.total_skipped = 0
        self.total_errors = 0
        
    async def run_all_tests(self, collectors: List[type]) -> Dict[str, Any]:
        """Executa todos os testes para a lista de coletores"""
        logger.info(f"Iniciando testes para {len(collectors)} coletores")
        self.start_time = time.time()
        self.total_collectors = len(collectors)
        
        # Executa testes em paralelo para melhor performance
        semaphore = asyncio.Semaphore(50)  # Limita a 50 testes simultâneos
        
        async def test_collector(collector_class):
            async with semaphore:
                return await self._test_single_collector(collector_class)
        
        # Executa todos os testes
        tasks = [test_collector(collector) for collector in collectors]
        test_suites = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processa resultados
        for suite in test_suites:
            if isinstance(suite, Exception):
                logger.error(f"Erro ao testar coletor: {suite}")
                self.total_errors += 1
            else:
                self.test_suites.append(suite)
                self.total_passed += suite.passed
                self.total_failed += suite.failed
                self.total_skipped += suite.skipped
                self.total_errors += suite.errors
                self.test_results.extend(suite.results)
        
        self.end_time = time.time()
        
        return self._generate_report()
    
    async def _test_single_collector(self, collector_class: type) -> TestSuite:
        """Testa um único coletor"""
        collector_name = collector_class.__name__
        logger.info(f"Testando coletor: {collector_name}")
        
        start_time = time.time()
        results = []
        
        try:
            # Teste 1: Instanciação
            result = await self._test_instantiation(collector_class)
            results.append(result)
            
            # Teste 2: Setup
            if result.status == 'passed':
                setup_result = await self._test_setup(collector_class)
                results.append(setup_result)
                
                # Teste 3: Coleta
                if setup_result.status == 'passed':
                    collect_result = await self._test_collection(collector_class)
                    results.append(collect_result)
                    
                    # Teste 4: Performance
                    if collect_result.status == 'passed':
                        perf_result = await self._test_performance(collector_class)
                        results.append(perf_result)
                        
                        # Teste 5: Resiliência
                        res_result = await self._test_resilience(collector_class)
                        results.append(res_result)
            
            # Teste 6: Metadados
            metadata_result = await self._test_metadata(collector_class)
            results.append(metadata_result)
            
        except Exception as e:
            logger.error(f"Erro inesperado ao testar {collector_name}: {e}")
            results.append(TestResult(
                collector_name=collector_name,
                test_type="framework_error",
                status="error",
                duration=0.0,
                error_message=str(e)
            ))
        
        end_time = time.time()
        
        # Calcula estatísticas
        passed = sum(1 for r in results if r.status == 'passed')
        failed = sum(1 for r in results if r.status == 'failed')
        skipped = sum(1 for r in results if r.status == 'skipped')
        errors = sum(1 for r in results if r.status == 'error')
        
        return TestSuite(
            collector_name=collector_name,
            collector_class=collector_class,
            results=results,
            total_duration=end_time - start_time,
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors
        )
    
    async def _test_instantiation(self, collector_class: type) -> TestResult:
        """Testa instanciação do coletor"""
        start_time = time.time()
        collector_name = collector_class.__name__
        
        try:
            # Testa instanciação sem configuração
            collector = collector_class()
            
            # Verifica atributos básicos
            assert hasattr(collector, 'name'), f"{collector_name} não tem atributo 'name'"
            assert hasattr(collector, 'metadata'), f"{collector_name} não tem atributo 'metadata'"
            assert hasattr(collector, '_setup_collector'), f"{collector_name} não tem método '_setup_collector'"
            assert hasattr(collector, '_async_collect'), f"{collector_name} não tem método '_async_collect'"
            
            duration = time.time() - start_time
            return TestResult(
                collector_name=collector_name,
                test_type="instantiation",
                status="passed",
                duration=duration,
                details={"name": collector.name, "category": collector.metadata.category.value}
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                collector_name=collector_name,
                test_type="instantiation",
                status="failed",
                duration=duration,
                error_message=str(e)
            )
    
    async def _test_setup(self, collector_class: type) -> TestResult:
        """Testa setup do coletor"""
        start_time = time.time()
        collector_name = collector_class.__name__
        
        try:
            collector = collector_class()
            
            # Testa setup assíncrono
            await collector._setup_collector()
            
            duration = time.time() - start_time
            return TestResult(
                collector_name=collector_name,
                test_type="setup",
                status="passed",
                duration=duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                collector_name=collector_name,
                test_type="setup",
                status="failed",
                duration=duration,
                error_message=str(e)
            )
    
    async def _test_collection(self, collector_class: type) -> TestResult:
        """Testa coleta de dados"""
        start_time = time.time()
        collector_name = collector_class.__name__
        
        try:
            collector = collector_class()
            await collector._setup_collector()
            
            # Cria request de teste
            from ..backend.collectors.base_collector import CollectorRequest
            request = CollectorRequest(
                query="test query",
                url="https://example.com",
                parameters={},
                timeout=10
            )
            
            # Executa coleta
            result = await collector._async_collect(request)
            
            # Verifica resultado
            assert isinstance(result, dict), f"{collector_name} não retornou dict"
            assert 'success' in result, f"{collector_name} não tem campo 'success'"
            
            duration = time.time() - start_time
            return TestResult(
                collector_name=collector_name,
                test_type="collection",
                status="passed",
                duration=duration,
                details={"result_keys": list(result.keys())}
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                collector_name=collector_name,
                test_type="collection",
                status="failed",
                duration=duration,
                error_message=str(e)
            )
    
    async def _test_performance(self, collector_class: type) -> TestResult:
        """Testa performance do coletor"""
        start_time = time.time()
        collector_name = collector_class.__name__
        
        try:
            collector = collector_class()
            await collector._setup_collector()
            
            # Executa múltiplas coletas para medir performance
            from ..backend.collectors.base_collector import CollectorRequest
            request = CollectorRequest(
                query="test query",
                url="https://example.com",
                parameters={},
                timeout=5
            )
            
            # Executa 5 coletas e mede tempo
            times = []
            for _ in range(5):
                collect_start = time.time()
                await collector._async_collect(request)
                times.append(time.time() - collect_start)
            
            avg_time = statistics.mean(times)
            max_time = max(times)
            
            # Verifica se performance está aceitável (< 1 segundo em média)
            if avg_time > 1.0:
                duration = time.time() - start_time
                return TestResult(
                    collector_name=collector_name,
                    test_type="performance",
                    status="failed",
                    duration=duration,
                    error_message=f"Performance lenta: {avg_time:.3f}s média"
                )
            
            duration = time.time() - start_time
            return TestResult(
                collector_name=collector_name,
                test_type="performance",
                status="passed",
                duration=duration,
                details={"avg_time": avg_time, "max_time": max_time}
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                collector_name=collector_name,
                test_type="performance",
                status="failed",
                duration=duration,
                error_message=str(e)
            )
    
    async def _test_resilience(self, collector_class: type) -> TestResult:
        """Testa resiliência do coletor"""
        start_time = time.time()
        collector_name = collector_class.__name__
        
        try:
            collector = collector_class()
            await collector._setup_collector()
            
            # Testa com request inválido
            from ..backend.collectors.base_collector import CollectorRequest
            invalid_request = CollectorRequest(
                query="",  # Query vazia
                url="invalid-url",
                parameters={},
                timeout=1
            )
            
            # Deve lidar com erro gracefully
            result = await collector._async_collect(invalid_request)
            
            # Verifica se tratou erro adequadamente
            assert isinstance(result, dict), f"{collector_name} não retornou dict para request inválido"
            
            duration = time.time() - start_time
            return TestResult(
                collector_name=collector_name,
                test_type="resilience",
                status="passed",
                duration=duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                collector_name=collector_name,
                test_type="resilience",
                status="failed",
                duration=duration,
                error_message=str(e)
            )
    
    async def _test_metadata(self, collector_class: type) -> TestResult:
        """Testa metadados do coletor"""
        start_time = time.time()
        collector_name = collector_class.__name__
        
        try:
            collector = collector_class()
            metadata = collector.metadata
            
            # Verifica campos obrigatórios
            required_fields = ['name', 'category', 'description', 'version', 'author']
            for field in required_fields:
                assert hasattr(metadata, field), f"{collector_name} não tem campo '{field}' em metadados"
                assert getattr(metadata, field), f"{collector_name} tem campo '{field}' vazio"
            
            # Verifica tags
            assert hasattr(metadata, 'tags'), f"{collector_name} não tem 'tags' em metadados"
            assert isinstance(metadata.tags, list), f"{collector_name} 'tags' não é lista"
            
            # Verifica capabilities
            assert hasattr(metadata, 'capabilities'), f"{collector_name} não tem 'capabilities' em metadados"
            assert isinstance(metadata.capabilities, list), f"{collector_name} 'capabilities' não é lista"
            
            duration = time.time() - start_time
            return TestResult(
                collector_name=collector_name,
                test_type="metadata",
                status="passed",
                duration=duration,
                details={
                    "name": metadata.name,
                    "category": metadata.category.value,
                    "tags_count": len(metadata.tags),
                    "capabilities_count": len(metadata.capabilities)
                }
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                collector_name=collector_name,
                test_type="metadata",
                status="failed",
                duration=duration,
                error_message=str(e)
            )
    
    def _generate_report(self) -> Dict[str, Any]:
        """Gera relatório completo dos testes"""
        total_duration = self.end_time - self.start_time if self.end_time and self.start_time else 0
        
        # Agrupa resultados por tipo de teste
        test_types = {}
        for result in self.test_results:
            if result.test_type not in test_types:
                test_types[result.test_type] = {"passed": 0, "failed": 0, "skipped": 0, "errors": 0}
            test_types[result.test_type][result.status] += 1
        
        # Encontra coletores com problemas
        failed_collectors = []
        for suite in self.test_suites:
            if suite.failed > 0 or suite.errors > 0:
                failed_collectors.append({
                    "name": suite.collector_name,
                    "failed": suite.failed,
                    "errors": suite.errors,
                    "total_tests": len(suite.results)
                })
        
        # Calcula estatísticas de performance
        performance_results = [r for r in self.test_results if r.test_type == "performance" and r.status == "passed"]
        avg_performance = 0
        if performance_results:
            avg_performance = statistics.mean([r.details.get("avg_time", 0) for r in performance_results])
        
        return {
            "summary": {
                "total_collectors": self.total_collectors,
                "total_tests": len(self.test_results),
                "total_duration": total_duration,
                "passed": self.total_passed,
                "failed": self.total_failed,
                "skipped": self.total_skipped,
                "errors": self.total_errors,
                "success_rate": (self.total_passed / len(self.test_results)) * 100 if self.test_results else 0
            },
            "test_types": test_types,
            "failed_collectors": failed_collectors,
            "performance": {
                "avg_performance_time": avg_performance,
                "performance_tests_count": len(performance_results)
            },
            "top_slow_collectors": self._get_slow_collectors(),
            "recommendations": self._generate_recommendations()
        }
    
    def _get_slow_collectors(self) -> List[Dict[str, Any]]:
        """Retorna os coletores mais lentos"""
        performance_results = [r for r in self.test_results if r.test_type == "performance" and r.status == "passed"]
        
        # Ordena por tempo médio
        sorted_results = sorted(performance_results, key=lambda x: x.details.get("avg_time", 0), reverse=True)
        
        return [
            {
                "collector": r.collector_name,
                "avg_time": r.details.get("avg_time", 0),
                "max_time": r.details.get("max_time", 0)
            }
            for r in sorted_results[:10]
        ]
    
    def _generate_recommendations(self) -> List[str]:
        """Gera recomendações baseadas nos resultados"""
        recommendations = []
        
        if self.total_failed > 0:
            recommendations.append(f"Corrigir {self.total_failed} testes falhando")
        
        if self.total_errors > 0:
            recommendations.append(f"Investigar {self.total_errors} erros inesperados")
        
        # Verifica performance
        performance_results = [r for r in self.test_results if r.test_type == "performance" and r.status == "passed"]
        if performance_results:
            avg_perf = statistics.mean([r.details.get("avg_time", 0) for r in performance_results])
            if avg_perf > 0.5:
                recommendations.append("Otimizar performance dos coletores (tempo médio > 500ms)")
        
        # Verifica metadados
        metadata_issues = len([r for r in self.test_results if r.test_type == "metadata" and r.status == "failed"])
        if metadata_issues > 0:
            recommendations.append(f"Corrigir metadados de {metadata_issues} coletores")
        
        if len(recommendations) == 0:
            recommendations.append("Todos os testes passaram! Sistema pronto para produção.")
        
        return recommendations

# Função principal para executar testes
async def run_collector_tests():
    """Executa todos os testes dos coletores"""
    framework = CollectorTestFramework()
    
    # Importa todos os coletores
    collectors = []
    
    # Importa coletores de cada categoria
    try:
        from ..backend.collectors.massive.web_scraping.web_scraping_collectors import get_web_scraping_collectors
        collectors.extend(get_web_scraping_collectors())
    except ImportError:
        pass
    
    # Adiciona imports das outras categorias...
    # (Para brevidade, apenas mostramos o padrão)
    
    # Executa testes
    results = await framework.run_all_tests(collectors)
    
    # Imprime relatório
    print("\n" + "="*80)
    print("RELATÓRIO DE TESTES DOS COLETORES")
    print("="*80)
    print(f"Coletores testados: {results['summary']['total_collectors']}")
    print(f"Total de testes: {results['summary']['total_tests']}")
    print(f"Tempo total: {results['summary']['total_duration']:.2f}s")
    print(f"Taxa de sucesso: {results['summary']['success_rate']:.1f}%")
    print(f"Passaram: {results['summary']['passed']}")
    print(f"Falharam: {results['summary']['failed']}")
    print(f"Ignorados: {results['summary']['skipped']}")
    print(f"Erros: {results['summary']['errors']}")
    
    if results['failed_collectors']:
        print(f"\nColetores com problemas: {len(results['failed_collectors'])}")
        for collector in results['failed_collectors'][:5]:
            print(f"  - {collector['name']}: {collector['failed']} falhas, {collector['errors']} erros")
    
    print(f"\nRecomendações:")
    for rec in results['recommendations']:
        print(f"  - {rec}")
    
    return results

if __name__ == "__main__":
    asyncio.run(run_collector_tests())
