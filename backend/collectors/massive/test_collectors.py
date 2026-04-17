"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Massive Collectors Test Suite
Teste e validação dos 100 coletores de dados da internet
"""

import asyncio
import time
import json
from typing import List, Dict, Any, Optional
import logging

from .unified_interface import UnifiedInterface, UnifiedSearchRequest, SearchType, CollectorCategory
from .massive_collector_factory import massive_collector_factory
from .massive_cache_system import massive_cache_system
from .collector_registry import collector_registry
from .web_scraping.web_scraping_collectors import get_web_scraping_collectors
from .api_platforms.api_platforms_collectors import get_api_platforms_collectors
from .crawlers_bots.crawlers_bots_collectors import get_crawlers_bots_collectors
from .massive_platforms.massive_platforms_collectors import get_massive_platforms_collectors

logger = logging.getLogger(__name__)

class MassiveCollectorsTestSuite:
    """Suite de testes para os 100 coletores"""
    
    def __init__(self):
        self.unified_interface = UnifiedInterface()
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'skipped_tests': 0,
            'test_details': []
        }
        
    async def run_all_tests(self) -> Dict[str, Any]:
        """Executa todos os testes dos 100 coletores"""
        logger.info(" Iniciando suite de testes dos 100 coletores...")
        start_time = time.time()
        
        try:
            # Inicializar sistemas
            await self.unified_interface.initialize()
            
            # Teste 1: Validação de estrutura
            await self.test_structure_validation()
            
            # Teste 2: Teste de coletores individuais
            await self.test_individual_collectors()
            
            # Teste 3: Teste de busca unificada
            await self.test_unified_search()
            
            # Teste 4: Teste de busca por categoria
            await self.test_category_search()
            
            # Teste 5: Teste de busca inteligente
            await self.test_intelligent_search()
            
            # Teste 6: Teste de performance
            await self.test_performance()
            
            # Teste 7: Teste de cache
            await self.test_cache_system()
            
            # Teste 8: Teste de orquestração
            await self.test_orchestration()
            
            # Teste 9: Teste de limites e escalabilidade
            await self.test_limits_and_scalability()
            
            # Teste 10: Teste de resiliência
            await self.test_resilience()
            
        except Exception as e:
            logger.error(f" Erro na execução dos testes: {str(e)}")
            self._add_test_result("suite_execution", False, str(e))
        
        # Calcular tempo total
        total_time = time.time() - start_time
        
        # Gerar relatório final
        final_report = {
            'test_summary': {
                'total_tests': self.test_results['total_tests'],
                'passed_tests': self.test_results['passed_tests'],
                'failed_tests': self.test_results['failed_tests'],
                'skipped_tests': self.test_results['skipped_tests'],
                'success_rate': (
                    self.test_results['passed_tests'] / max(1, self.test_results['total_tests']) * 100
                ),
                'total_time': total_time
            },
            'test_details': self.test_results['test_details'],
            'collector_validation': await self._validate_all_collectors(),
            'performance_metrics': await self._get_performance_metrics(),
            'recommendations': self._generate_recommendations()
        }
        
        logger.info(f" Suite de testes concluída em {total_time:.2f}s")
        logger.info(f" Resultado: {self.test_results['passed_tests']}/{self.test_results['total_tests']} testes passaram")
        
        return final_report
    
    async def test_structure_validation(self):
        """Teste 1: Validação da estrutura dos 100 coletores"""
        logger.info(" Teste 1: Validação de estrutura...")
        
        try:
            # Verificar se temos exatamente 100 coletores
            web_scraping_collectors = get_web_scraping_collectors()
            api_collectors = get_api_platforms_collectors()
            crawler_collectors = get_crawlers_bots_collectors()
            massive_collectors = get_massive_platforms_collectors()
            
            total_collectors = (
                len(web_scraping_collectors) +
                len(api_collectors) +
                len(crawler_collectors) +
                len(massive_collectors)
            )
            
            assert total_collectors == 100, f"Esperado 100 coletores, encontrado {total_collectors}"
            assert len(web_scraping_collectors) == 30, f"Esperado 30 web scraping, encontrado {len(web_scraping_collectors)}"
            assert len(api_collectors) == 30, f"Esperado 30 APIs, encontrado {len(api_collectors)}"
            assert len(crawler_collectors) == 20, f"Esperado 20 crawlers, encontrado {len(crawler_collectors)}"
            assert len(massive_collectors) == 20, f"Esperado 20 massive, encontrado {len(massive_collectors)}"
            
            # Verificar se todos os coletores têm metadados
            for collector_class in web_scraping_collectors + api_collectors + crawler_collectors + massive_collectors:
                instance = collector_class()
                assert hasattr(instance, 'metadata'), f"Coletor {collector_class.__name__} não tem metadados"
                assert instance.metadata, f"Metadados vazios para {collector_class.__name__}"
            
            self._add_test_result("structure_validation", True, "Estrutura validada com sucesso")
            
        except Exception as e:
            self._add_test_result("structure_validation", False, str(e))
    
    async def test_individual_collectors(self):
        """Teste 2: Teste de coletores individuais"""
        logger.info(" Teste 2: Teste de coletores individuais...")
        
        try:
            # Testar uma amostra de coletores de cada categoria
            test_queries = [
                "python programming",  # Web scraping
                "weather forecast",   # APIs
                "data mining",        # Crawlers
                "machine learning"    # Massive platforms
            ]
            
            categories = [
                (get_web_scraping_collectors(), test_queries[0]),
                (get_api_platforms_collectors(), test_queries[1]),
                (get_crawlers_bots_collectors(), test_queries[2]),
                (get_massive_platforms_collectors(), test_queries[3])
            ]
            
            for collectors, query in categories:
                # Testar primeiro coletor de cada categoria
                if collectors:
                    collector_class = collectors[0]
                    try:
                        instance = collector_class()
                        await instance.initialize()
                        
                        # Criar requisição de teste
                        from .base_collector import CollectorRequest
                        request = CollectorRequest(
                            request_id=f"test_{collector_class.__name__}",
                            query=query,
                            limit=5
                        )
                        
                        # Executar coletor
                        result = await instance.execute_request(request)
                        
                        assert result is not None, f"Coletor {collector_class.__name__} retornou None"
                        assert hasattr(result, 'success'), f"Coletor {collector_class.__name__} não tem atributo success"
                        
                        self._add_test_result(
                            f"individual_{collector_class.__name__}",
                            result.success,
                            f"Coletor {collector_class.__name__}: {'success' if result.success else 'failed'}"
                        )
                        
                    except Exception as e:
                        self._add_test_result(
                            f"individual_{collector_class.__name__}",
                            False,
                            f"Erro no coletor {collector_class.__name__}: {str(e)}"
                        )
            
        except Exception as e:
            self._add_test_result("individual_collectors", False, str(e))
    
    async def test_unified_search(self):
        """Teste 3: Teste de busca unificada"""
        logger.info(" Teste 3: Teste de busca unificada...")
        
        try:
            # Busca unificada simples
            request = UnifiedSearchRequest(
                query="artificial intelligence",
                search_type=SearchType.UNIFIED,
                max_collectors=10,
                max_results_per_collector=5
            )
            
            result = await self.unified_interface.search(request)
            
            assert result is not None, "Busca unificada retornou None"
            assert hasattr(result, 'results'), "Resultado não tem atributo results"
            assert result.total_collectors_used > 0, "Nenhum coletor foi usado"
            
            self._add_test_result(
                "unified_search",
                True,
                f"Busca unificada: {result.total_collectors_used} coletores, {len(result.results)} resultados"
            )
            
        except Exception as e:
            self._add_test_result("unified_search", False, str(e))
    
    async def test_category_search(self):
        """Teste 4: Teste de busca por categoria"""
        logger.info(" Teste 4: Teste de busca por categoria...")
        
        try:
            # Busca por categoria específica
            request = UnifiedSearchRequest(
                query="machine learning",
                search_type=SearchType.CATEGORY_SPECIFIC,
                categories=[CollectorCategory.WEB_SCRAPING],
                max_collectors=5
            )
            
            result = await self.unified_interface.search(request)
            
            assert result is not None, "Busca por categoria retornou None"
            assert result.total_collectors_used > 0, "Nenhum coletor da categoria foi usado"
            
            self._add_test_result(
                "category_search",
                True,
                f"Busca por categoria: {result.total_collectors_used} coletores, {len(result.results)} resultados"
            )
            
        except Exception as e:
            self._add_test_result("category_search", False, str(e))
    
    async def test_intelligent_search(self):
        """Teste 5: Teste de busca inteligente"""
        logger.info(" Teste 5: Teste de busca inteligente...")
        
        try:
            # Busca inteligente
            request = UnifiedSearchRequest(
                query="buy cheap flights to europe",
                search_type=SearchType.INTELLIGENT,
                max_collectors=15
            )
            
            result = await self.unified_interface.search(request)
            
            assert result is not None, "Busca inteligente retornou None"
            assert result.total_collectors_used > 0, "Nenhum coletor inteligente foi selecionado"
            
            self._add_test_result(
                "intelligent_search",
                True,
                f"Busca inteligente: {result.total_collectors_used} coletores, {len(result.results)} resultados"
            )
            
        except Exception as e:
            self._add_test_result("intelligent_search", False, str(e))
    
    async def test_performance(self):
        """Teste 6: Teste de performance"""
        logger.info(" Teste 6: Teste de performance...")
        
        try:
            # Teste de performance com múltiplas requisições
            queries = [
                "python programming",
                "data science",
                "web development",
                "machine learning",
                "artificial intelligence"
            ]
            
            start_time = time.time()
            results = []
            
            for query in queries:
                request = UnifiedSearchRequest(
                    query=query,
                    search_type=SearchType.UNIFIED,
                    max_collectors=5,
                    max_results_per_collector=3
                )
                
                result = await self.unified_interface.search(request)
                results.append(result)
            
            total_time = time.time() - start_time
            avg_time = total_time / len(queries)
            
            # Verificar performance
            assert avg_time < 30.0, f"Tempo médio muito alto: {avg_time:.2f}s"
            assert all(r is not None for r in results), "Algumas buscas retornaram None"
            
            self._add_test_result(
                "performance",
                True,
                f"Performance: {len(queries)} buscas em {total_time:.2f}s (avg: {avg_time:.2f}s)"
            )
            
        except Exception as e:
            self._add_test_result("performance", False, str(e))
    
    async def test_cache_system(self):
        """Teste 7: Teste do sistema de cache"""
        logger.info(" Teste 7: Teste do sistema de cache...")
        
        try:
            # Teste de cache hit
            query = "test cache functionality"
            
            # Primeira requisição (cache miss)
            request1 = UnifiedSearchRequest(
                query=query,
                search_type=SearchType.UNIFIED,
                max_collectors=3,
                enable_caching=True
            )
            
            start_time = time.time()
            result1 = await self.unified_interface.search(request1)
            first_time = time.time() - start_time
            
            # Segunda requisição (cache hit)
            start_time = time.time()
            result2 = await self.unified_interface.search(request1)
            second_time = time.time() - start_time
            
            assert result1 is not None, "Primeira requisição falhou"
            assert result2 is not None, "Segunda requisição falhou"
            assert second_time < first_time, "Cache não melhorou performance"
            
            cache_improvement = ((first_time - second_time) / first_time) * 100
            
            self._add_test_result(
                "cache_system",
                True,
                f"Cache: {cache_improvement:.1f}% de melhoria ({first_time:.3f}s -> {second_time:.3f}s)"
            )
            
        except Exception as e:
            self._add_test_result("cache_system", False, str(e))
    
    async def test_orchestration(self):
        """Teste 8: Teste de orquestração"""
        logger.info(" Teste 8: Teste de orquestração...")
        
        try:
            # Teste de orquestração com múltiplos coletores
            request = UnifiedSearchRequest(
                query="distributed systems architecture",
                search_type=SearchType.COMPREHENSIVE,
                max_collectors=20,
                orchestration_mode="adaptive"
            )
            
            result = await self.unified_interface.search(request)
            
            assert result is not None, "Busca orquestrada retornou None"
            assert result.total_collectors_used > 0, "Nenhum coletor foi orquestrado"
            assert result.successful_collectors > 0, "Nenhum coletor teve sucesso"
            
            success_rate = result.successful_collectors / result.total_collectors_used * 100
            
            self._add_test_result(
                "orchestration",
                True,
                f"Orquestração: {result.total_collectors_used} coletores, {success_rate:.1f}% sucesso"
            )
            
        except Exception as e:
            self._add_test_result("orchestration", False, str(e))
    
    async def test_limits_and_scalability(self):
        """Teste 9: Teste de limites e escalabilidade"""
        logger.info(" Teste 9: Teste de limites e escalabilidade...")
        
        try:
            # Teste com limite máximo de coletores
            request = UnifiedSearchRequest(
                query="scalability test",
                search_type=SearchType.UNIFIED,
                max_collectors=50,
                max_results_per_collector=10,
                max_total_results=500
            )
            
            result = await self.unified_interface.search(request)
            
            assert result is not None, "Busca de escalabilidade retornou None"
            assert len(result.results) <= 500, "Excedeu limite máximo de resultados"
            
            self._add_test_result(
                "limits_scalability",
                True,
                f"Escalabilidade: {len(result.results)} resultados (limite: 500)"
            )
            
        except Exception as e:
            self._add_test_result("limits_scalability", False, str(e))
    
    async def test_resilience(self):
        """Teste 10: Teste de resiliência"""
        logger.info(" Teste 10: Teste de resiliência...")
        
        try:
            # Teste com query que pode causar erros
            request = UnifiedSearchRequest(
                query="invalid_url_that_should_fail",
                search_type=SearchType.UNIFIED,
                max_collectors=10,
                timeout=10  # Timeout curto
            )
            
            result = await self.unified_interface.search(request)
            
            assert result is not None, "Busca de resiliência retornou None"
            # Mesmo com erros, deve retornar resultado com falhas registradas
            assert hasattr(result, 'errors'), "Resultado não tem atributo errors"
            
            self._add_test_result(
                "resilience",
                True,
                f"Resiliência: {len(result.errors)} erros, {len(result.results)} resultados"
            )
            
        except Exception as e:
            self._add_test_result("resilience", False, str(e))
    
    def _add_test_result(self, test_name: str, passed: bool, message: str):
        """Adiciona resultado de teste"""
        self.test_results['total_tests'] += 1
        
        if passed:
            self.test_results['passed_tests'] += 1
        else:
            self.test_results['failed_tests'] += 1
        
        self.test_results['test_details'].append({
            'test_name': test_name,
            'passed': passed,
            'message': message,
            'timestamp': time.time()
        })
    
    async def _validate_all_collectors(self) -> Dict[str, Any]:
        """Valida todos os 100 coletores"""
        validation_result = {
            'total_collectors': 0,
            'valid_collectors': 0,
            'invalid_collectors': 0,
            'categories': {},
            'issues': []
        }
        
        try:
            all_collectors = get_all_collectors()
            
            for category_name, collectors in all_collectors.items():
                category_validation = {
                    'total': len(collectors),
                    'valid': 0,
                    'invalid': 0,
                    'issues': []
                }
                
                for collector_class in collectors:
                    validation_result['total_collectors'] += 1
                    
                    try:
                        # Validação básica
                        instance = collector_class()
                        
                        # Verificar atributos obrigatórios
                        required_attrs = ['metadata', 'initialize', 'execute_request']
                        for attr in required_attrs:
                            if not hasattr(instance, attr):
                                raise AttributeError(f"Atributo obrigatório '{attr}' ausente")
                        
                        # Verificar metadados
                        if not instance.metadata:
                            raise ValueError("Metadados ausentes")
                        
                        category_validation['valid'] += 1
                        validation_result['valid_collectors'] += 1
                        
                    except Exception as e:
                        category_validation['invalid'] += 1
                        validation_result['invalid_collectors'] += 1
                        category_validation['issues'].append(f"{collector_class.__name__}: {str(e)}")
                        validation_result['issues'].append(f"{category_name}.{collector_class.__name__}: {str(e)}")
                
                validation_result['categories'][category_name] = category_validation
            
        except Exception as e:
            validation_result['error'] = str(e)
        
        return validation_result
    
    async def _get_performance_metrics(self) -> Dict[str, Any]:
        """Obtém métricas de performance"""
        try:
            # Status da interface
            interface_status = await self.unified_interface.get_interface_status()
            
            # Status do factory
            factory_status = await massive_collector_factory.get_factory_status()
            
            # Status do cache
            cache_stats = massive_cache_system.get_global_stats()
            
            return {
                'interface': interface_status,
                'factory': factory_status,
                'cache': cache_stats,
                'timestamp': time.time()
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _generate_recommendations(self) -> List[str]:
        """Gera recomendações baseadas nos testes"""
        recommendations = []
        
        success_rate = (
            self.test_results['passed_tests'] / max(1, self.test_results['total_tests']) * 100
        )
        
        if success_rate < 80:
            recommendations.append("Baixa taxa de sucesso nos testes. Verificar configurações e dependências.")
        
        if self.test_results['failed_tests'] > 0:
            failed_tests = [t for t in self.test_results['test_details'] if not t['passed']]
            recommendations.append(f"Corrigir {len(failed_tests)} testes falhos antes de usar em produção.")
        
        # Recomendações específicas baseadas nos resultados
        for test in self.test_results['test_details']:
            if not test['passed'] and 'cache' in test['test_name'].lower():
                recommendations.append("Verificar configuração do sistema de cache.")
            elif not test['passed'] and 'performance' in test['test_name'].lower():
                recommendations.append("Otimizar configurações de performance e limites.")
            elif not test['passed'] and 'orchestration' in test['test_name'].lower():
                recommendations.append("Verificar configuração do orquestrador distribuído.")
        
        if not recommendations:
            recommendations.append("Todos os testes passaram! Sistema pronto para uso em produção.")
        
        return recommendations

# Função principal para executar todos os testes
async def run_massive_collectors_tests():
    """Executa suite completa de testes dos 100 coletores"""
    test_suite = MassiveCollectorsTestSuite()
    return await test_suite.run_all_tests()

# Função para validação rápida
async def quick_validation():
    """Validação rápida dos 100 coletores"""
    logger.info(" Executando validação rápida...")
    
    try:
        # Inicializar interface
        interface = UnifiedInterface()
        await interface.initialize()
        
        # Teste básico
        request = UnifiedSearchRequest(
            query="test validation",
            search_type=SearchType.UNIFIED,
            max_collectors=5,
            max_results_per_collector=2
        )
        
        result = await interface.search(request)
        
        if result and result.total_collectors_used > 0:
            logger.info(f" Validação rápida bem-sucedida: {result.total_collectors_used} coletores")
            return True
        else:
            logger.error(" Validação rápida falhou")
            return False
            
    except Exception as e:
        logger.error(f" Erro na validação rápida: {str(e)}")
        return False

if __name__ == "__main__":
    # Executar testes se chamado diretamente
    import asyncio
    
    async def main():
        print("=== Test Suite dos 100 Coletores ===")
        
        # Validação rápida primeiro
        print("\n1. Validação rápida...")
        quick_result = await quick_validation()
        print(f"   Resultado: {'PASS' if quick_result else 'FAIL'}")
        
        if quick_result:
            # Suite completa
            print("\n2. Suite completa de testes...")
            results = await run_massive_collectors_tests()
            
            print(f"\n=== Resumo dos Testes ===")
            print(f"Total de testes: {results['test_summary']['total_tests']}")
            print(f"Passaram: {results['test_summary']['passed_tests']}")
            print(f"Falharam: {results['test_summary']['failed_tests']}")
            print(f"Taxa de sucesso: {results['test_summary']['success_rate']:.1f}%")
            print(f"Tempo total: {results['test_summary']['total_time']:.2f}s")
            
            print(f"\n=== Recomendações ===")
            for rec in results['recommendations']:
                print(f"- {rec}")
            
            print(f"\n=== Validação de Coletores ===")
            validation = results['collector_validation']
            print(f"Total de coletores: {validation['total_collectors']}")
            print(f"Válidos: {validation['valid_collectors']}")
            print(f"Inválidos: {validation['invalid_collectors']}")
            
            if validation['issues']:
                print(f"\nProblemas encontrados:")
                for issue in validation['issues'][:5]:  # Mostrar apenas 5 primeiros
                    print(f"- {issue}")
                if len(validation['issues']) > 5:
                    print(f"... e mais {len(validation['issues']) - 5} problemas")
        
        print("\n=== Testes Concluídos ===")
    
    asyncio.run(main())
