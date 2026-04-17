"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Run All Tests
Script principal para executar todos os testes dos 2240 coletores
"""

import asyncio
import sys
import os
import time
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

# Adiciona o backend ao path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from test_framework import CollectorTestFramework, TestResult

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tests.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AllCollectorTests:
    """Classe para executar todos os testes dos coletores"""
    
    def __init__(self):
        self.framework = CollectorTestFramework()
        self.collectors = []
        self.results = None
        
    async def load_all_collectors(self):
        """Carrega todos os 2240 coletores"""
        logger.info("Carregando todos os coletores...")
        
        # Lista de todas as funções get_*_collectors
        collector_modules = [
            # Web Scraping (1-30)
            ("web_scraping.web_scraping_collectors", "get_web_scraping_collectors"),
            
            # APIs e Plataformas (31-60)
            ("apis_platforms.apis_platforms_collectors", "get_apis_platforms_collectors"),
            
            # Crawlers e Bots (61-80)
            ("crawlers_bots.crawlers_bots_collectors", "get_crawlers_bots_collectors"),
            
            # Plataformas Massivas (81-100)
            ("massive_platforms.massive_platforms_collectors", "get_massive_platforms_collectors"),
            
            # Ferramentas Avançadas (101-130)
            ("advanced_tools.advanced_tools_collectors", "get_advanced_tools_collectors"),
            
            # APIs Especializadas (131-160)
            ("specialized_apis.specialized_apis_collectors", "get_specialized_apis_collectors"),
            
            # Técnicas de Coleta (161-190)
            ("collection_techniques.collection_techniques_collectors", "get_collection_techniques_collectors"),
            
            # Bancos de Dados (191-220)
            ("databases.databases_collectors", "get_databases_collectors"),
            
            # Plataformas de IA (221-240)
            ("ai_platforms.ai_platforms_collectors", "get_ai_platforms_collectors"),
            
            # Ferramentas de Nicho (241-270)
            ("niche_tools.niche_tools_collectors", "get_niche_tools_collectors"),
            
            # Motores de Busca Alternativos (271-300)
            ("alternative_search.alternative_search_collectors", "get_alternative_search_collectors"),
            
            # Coleta Técnica (301-320)
            ("technical_collection.technical_collection_collectors", "get_technical_collection_collectors"),
            
            # Analytics Comportamental (321-340)
            ("behavioral_analytics.behavioral_analytics_collectors", "get_behavioral_analytics_collectors"),
            
            # Infraestrutura (341-370)
            ("infrastructure.infrastructure_collectors", "get_infrastructure_collectors"),
            
            # OSINT (371-400)
            ("osint.osint_collectors", "get_osint_collectors"),
            
            # Automação IA (401-420)
            ("ai_automation.ai_automation_collectors", "get_ai_automation_collectors"),
            
            # Apps e Sistemas (421-440)
            ("apps_networks_systems.apps_networks_systems_collectors", "get_apps_networks_systems_collectors"),
            
            # Geoespaciais e Sensores (441-470)
            ("geospatial_sensors.geospatial_sensors_collectors", "get_geospatial_sensors_collectors"),
            
            # Financeiros e Mercado (471-500)
            ("financial_market.financial_market_collectors", "get_financial_market_collectors"),
            
            # Educacionais e Conhecimento (501-520)
            ("educational_knowledge.educational_knowledge_collectors", "get_educational_knowledge_collectors"),
            
            # Industriais e Sistemas (521-540)
            ("industrial_systems.industrial_systems_collectors", "get_industrial_systems_collectors"),
            
            # Biológicos e Saúde (541-570)
            ("biological_health.biological_health_collectors", "get_biological_health_collectors"),
            
            # Jogos e Plataformas (571-600)
            ("gaming_platforms.gaming_platforms_collectors", "get_gaming_platforms_collectors"),
            
            # E-commerce e Consumo (601-620)
            ("ecommerce_consumption.ecommerce_consumption_collectors", "get_ecommerce_consumption_collectors"),
            
            # Mobile e Comportamento (621-640)
            ("mobile_behavior.mobile_behavior_collectors", "get_mobile_behavior_collectors"),
            
            # Busca Dark Web (641-670)
            ("dark_web_search.dark_web_search_collectors", "get_dark_web_search_collectors"),
            
            # OSINT Deep Web (671-700)
            ("dark_web_osint.dark_web_osint_collectors", "get_dark_web_osint_collectors"),
            
            # Fóruns e Vazamentos (701-720)
            ("forums_leaks.forums_leaks_collectors", "get_forums_leaks_collectors"),
            
            # Inteligência Anônima (721-740)
            ("anonymous_network_intelligence.anonymous_network_intelligence_collectors", "get_anonymous_network_intelligence_collectors"),
            
            # Diretórios Onion (741-770)
            ("onion_directories.onion_directories_collectors", "get_onion_directories_collectors"),
            
            # Inteligência de Ameaças (771-800)
            ("threat_intelligence.threat_intelligence_collectors", "get_threat_intelligence_collectors"),
            
            # Automação Anônima (801-820)
            ("anonymous_automation.anonymous_automation_collectors", "get_anonymous_automation_collectors"),
            
            # Fontes Ocultas (821-840)
            ("hidden_public_sources.hidden_public_sources_collectors", "get_hidden_public_sources_collectors"),
            
            # Plataformas Sociais (841-870)
            ("social_platforms.social_platforms_collectors", "get_social_platforms_collectors"),
            
            # Notícias e Mídia (871-900)
            ("news_media.news_media_collectors", "get_news_media_collectors"),
            
            # Integração e Automação (901-920)
            ("integration_automation.integration_automation_collectors", "get_integration_automation_collectors"),
            
            # Infraestrutura Web (921-940)
            ("web_infrastructure.web_infrastructure_collectors", "get_web_infrastructure_collectors"),
            
            # Conectores e ETL (941-1000)
            ("connectors_etl.connectors_etl_collectors", "get_connectors_etl_collectors"),
            
            # IA Inteligente (1001-1080)
            ("ai_intelligent.ai_intelligent_collectors", "get_ai_intelligent_collectors"),
            
            # Fontes Massivas (1081-1200)
            ("massive_sources.massive_sources_collectors", "get_massive_sources_collectors"),
            
            # Tracking Avançado (1201-1220)
            ("advanced_tracking.advanced_tracking_collectors", "get_advanced_tracking_collectors"),
            
            # Network Telemetry (1221-1240)
            ("network_telemetry.network_telemetry_collectors", "get_network_telemetry_collectors"),
            
            # Segurança (1241-1260)
            ("security.security_collectors", "get_security_collectors"),
            
            # Cloud Logs (1261-1280)
            ("cloud_logs.cloud_logs_collectors", "get_cloud_logs_collectors"),
            
            # App Logs (1281-1300)
            ("app_logs.app_logs_collectors", "get_app_logs_collectors"),
            
            # Observabilidade (1301-1320)
            ("observability.observability_collectors", "get_observability_collectors"),
            
            # User Behavior (1321-1340)
            ("user_behavior.user_behavior_collectors", "get_user_behavior_collectors"),
            
            # Marketing Data (1341-1360)
            ("marketing_data.marketing_data_collectors", "get_marketing_data_collectors"),
            
            # FinTech Data (1361-1380)
            ("fintech_data.fintech_data_collectors", "get_fintech_data_collectors"),
            
            # IoT Extremo (1381-1400)
            ("iot_extreme.iot_extreme_collectors", "get_iot_extreme_collectors"),
            
            # Edge Computing (1401-1420)
            ("edge_computing.edge_computing_collectors", "get_edge_computing_collectors"),
            
            # Data Fusion (1421-1440)
            ("data_fusion.data_fusion_collectors", "get_data_fusion_collectors"),
            
            # Segurança Defensiva & Análise (1441-1500)
            ("defensive_security.defensive_security_collectors", "get_defensive_security_collectors"),
            
            # Reconhecimento & Mapeamento (1501-1580)
            ("reconnaissance_mapping.reconnaissance_mapping_collectors", "get_reconnaissance_mapping_collectors"),
            
            # Engenharia de Dados & Scraping Profissional (1581-1660)
            ("data_engineering.data_engineering_collectors", "get_data_engineering_collectors"),
            
            # IA + Automação Avançada (1661-1740)
            ("ai_advanced.ai_advanced_collectors", "get_ai_advanced_collectors"),
            
            # Infraestrutura, Cloud e Coleta em Escala Extrema (1741-1940)
            ("infrastructure_cloud.infrastructure_cloud_collectors", "get_infrastructure_cloud_collectors"),
            
            # Engenharia Reversa (1941-1970)
            ("reverse_engineering.reverse_engineering_collectors", "get_reverse_engineering_collectors"),
            
            # Debugging e Análise Dinâmica (1971-2000)
            ("debugging_analysis.debugging_analysis_collectors", "get_debugging_analysis_collectors"),
            
            # Malware Analysis, Sandbox e Proteção (2001-2040)
            ("malware_analysis.malware_analysis_collectors", "get_malware_analysis_collectors"),
            
            # Agentes Autônomos de Coleta (2041-2070)
            ("autonomous_agents.autonomous_agents_collectors", "get_autonomous_agents_collectors"),
            
            # IA para Scraping Inteligente (2071-2100)
            ("ai_scraping.ai_scraping_collectors", "get_ai_scraping_collectors"),
            
            # IA Autônoma Avançada (2101-2140)
            ("advanced_ai.advanced_ai_collectors", "get_advanced_ai_collectors"),
        ]
        
        loaded_collectors = 0
        failed_modules = []
        
        for module_name, function_name in collector_modules:
            try:
                # Importa o módulo
                module_path = f"backend.collectors.massive.{module_name}"
                module = __import__(module_path, fromlist=[function_name])
                
                # Obtém a função
                get_collectors_func = getattr(module, function_name)
                
                # Executa a função
                collectors = get_collectors_func()
                
                # Adiciona à lista
                self.collectors.extend(collectors)
                loaded_collectors += len(collectors)
                
                logger.info(f"Carregados {len(collectors)} coletores de {module_name}")
                
            except Exception as e:
                logger.error(f"Erro ao carregar {module_name}: {e}")
                failed_modules.append(module_name)
        
        logger.info(f"Total de coletores carregados: {loaded_collectors}")
        logger.info(f"Módulos com erro: {len(failed_modules)}")
        
        if failed_modules:
            logger.warning(f"Módulos que falharam: {failed_modules}")
        
        return loaded_collectors
    
    async def run_all_tests(self):
        """Executa todos os testes"""
        logger.info("Iniciando execução de todos os testes...")
        
        # Carrega coletores
        await self.load_all_collectors()
        
        if not self.collectors:
            logger.error("Nenhum coletor foi carregado!")
            return None
        
        # Executa testes
        self.results = await self.framework.run_all_tests(self.collectors)
        
        # Salva resultados
        await self.save_results()
        
        # Gera relatório
        self.print_report()
        
        return self.results
    
    async def save_results(self):
        """Salva os resultados em arquivo"""
        if not self.results:
            return
        
        # Salva resultados completos
        with open('test_results.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
        
        # Salva resumo
        summary = {
            "timestamp": time.time(),
            "summary": self.results["summary"],
            "failed_collectors_count": len(self.results["failed_collectors"]),
            "recommendations": self.results["recommendations"]
        }
        
        with open('test_summary.json', 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info("Resultados salvos em test_results.json e test_summary.json")
    
    def print_report(self):
        """Imprime relatório completo"""
        if not self.results:
            return
        
        print("\n" + "="*100)
        print("RELATÓRIO COMPLETO DE TESTES - 2240 COLETORES")
        print("="*100)
        
        summary = self.results["summary"]
        
        print(f"\nRESUMO GERAL:")
        print(f"  Coletores testados: {summary['total_collectors']}")
        print(f"  Total de testes: {summary['total_tests']}")
        print(f"  Tempo total: {summary['total_duration']:.2f} segundos")
        print(f"  Taxa de sucesso: {summary['success_rate']:.1f}%")
        print(f"  Passaram: {summary['passed']}")
        print(f"  Falharam: {summary['failed']}")
        print(f"  Ignorados: {summary['skipped']}")
        print(f"  Erros: {summary['errors']}")
        
        # Tipos de teste
        print(f"\nRESULTADOS POR TIPO DE TESTE:")
        for test_type, results in self.results["test_types"].items():
            total = sum(results.values())
            passed = results["passed"]
            percentage = (passed / total * 100) if total > 0 else 0
            print(f"  {test_type}: {passed}/{total} ({percentage:.1f}%)")
        
        # Coletores com problemas
        failed_collectors = self.results["failed_collectors"]
        if failed_collectors:
            print(f"\nCOLETORES COM PROBLEMAS ({len(failed_collectors)}):")
            for i, collector in enumerate(failed_collectors[:20]):  # Limita a 20 para não poluir
                print(f"  {i+1}. {collector['name']}: {collector['failed']} falhas, {collector['errors']} erros")
            
            if len(failed_collectors) > 20:
                print(f"  ... e mais {len(failed_collectors) - 20} coletores")
        
        # Performance
        performance = self.results["performance"]
        print(f"\nPERFORMANCE:")
        print(f"  Tempo médio de coleta: {performance['avg_performance_time']:.3f}s")
        print(f"  Testes de performance: {performance['performance_tests_count']}")
        
        # Coletores mais lentos
        slow_collectors = self.results["top_slow_collectors"]
        if slow_collectors:
            print(f"\nCOLETORES MAIS LENTOS (Top 10):")
            for i, collector in enumerate(slow_collectors):
                print(f"  {i+1}. {collector['collector']}: {collector['avg_time']:.3f}s média")
        
        # Recomendações
        print(f"\nRECOMENDAÇÕES:")
        for i, rec in enumerate(self.results["recommendations"], 1):
            print(f"  {i}. {rec}")
        
        # Status final
        success_rate = summary["success_rate"]
        if success_rate >= 95:
            print(f"\nSTATUS: EXCELENTE ({success_rate:.1f}% de sucesso)")
        elif success_rate >= 90:
            print(f"\nSTATUS: BOM ({success_rate:.1f}% de sucesso)")
        elif success_rate >= 80:
            print(f"\nSTATUS: ACEITÁVEL ({success_rate:.1f}% de sucesso)")
        else:
            print(f"\nSTATUS: PRECISA MELHORAR ({success_rate:.1f}% de sucesso)")
        
        print("\n" + "="*100)

async def main():
    """Função principal"""
    print("Iniciando testes do Info-Phantom - 2240 Coletores")
    print("Este processo pode levar vários minutos...")
    
    tester = AllCollectorTests()
    results = await tester.run_all_tests()
    
    if results:
        print("\nTestes concluídos! Verifique os arquivos:")
        print("  - test_results.json (resultados completos)")
        print("  - test_summary.json (resumo)")
        print("  - tests.log (log detalhado)")
    else:
        print("\nFalha ao executar testes!")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
