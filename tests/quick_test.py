"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Quick Test
Teste rápido para validar os coletores implementados
"""

import asyncio
import sys
import os
from pathlib import Path
import time
import logging

# Adiciona o backend ao path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def quick_test_collectors():
    """Teste rápido de alguns coletores representativos"""
    
    print("Iniciando teste rápido dos coletores...")
    
    # Testa alguns coletores de diferentes categorias
    test_collectors = []
    
    # Testa Web Scraping (1-30)
    try:
        from backend.collectors.massive.web_scraping.web_scraping_collectors import (
            BeautifulSoupCollector, ScrapyCollector, SeleniumCollector
        )
        test_collectors.extend([BeautifulSoupCollector, ScrapyCollector, SeleniumCollector])
        print("OK: Web Scraping collectors carregados")
    except Exception as e:
        print(f"ERRO: Web Scraping - {e}")
    
    # Testa APIs (31-60)
    try:
        from backend.collectors.massive.apis_platforms.apis_platforms_collectors import (
            TwitterAPICollector, FacebookAPICollector, InstagramAPICollector
        )
        test_collectors.extend([TwitterAPICollector, FacebookAPICollector, InstagramAPICollector])
        print("OK: APIs collectors carregados")
    except Exception as e:
        print(f"ERRO: APIs - {e}")
    
    # Testa IA Avançada (1661-1740)
    try:
        from backend.collectors.massive.ai_advanced.ai_advanced_collectors import (
            LangChainCollector, LlamaIndexCollector, HaystackCollector
        )
        test_collectors.extend([LangChainCollector, LlamaIndexCollector, HaystackCollector])
        print("OK: AI Advanced collectors carregados")
    except Exception as e:
        print(f"ERRO: AI Advanced - {e}")
    
    # Testa Infraestrutura Cloud (1741-1940)
    try:
        from backend.collectors.massive.infrastructure_cloud.infrastructure_cloud_collectors import (
            AWSCollector, AzureCloudCollector, GoogleCloudCollector
        )
        test_collectors.extend([AWSCollector, AzureCloudCollector, GoogleCloudCollector])
        print("OK: Infrastructure Cloud collectors carregados")
    except Exception as e:
        print(f"ERRO: Infrastructure Cloud - {e}")
    
    # Testa Engenharia Reversa (1941-1970)
    try:
        from backend.collectors.massive.reverse_engineering.reverse_engineering_collectors import (
            GhidraCollector, IDAFreeCollector, BinaryNinjaCollector
        )
        test_collectors.extend([GhidraCollector, IDAFreeCollector, BinaryNinjaCollector])
        print("OK: Reverse Engineering collectors carregados")
    except Exception as e:
        print(f"ERRO: Reverse Engineering - {e}")
    
    # Testa Agentes Autônomos (2041-2070)
    try:
        from backend.collectors.massive.autonomous_agents.autonomous_agents_collectors import (
            AutoGPTCollector, BabyAGICollector, AgentGPTCollector
        )
        test_collectors.extend([AutoGPTCollector, BabyAGICollector, AgentGPTCollector])
        print("OK: Autonomous Agents collectors carregados")
    except Exception as e:
        print(f"ERRO: Autonomous Agents - {e}")
    
    # Testa IA Autônoma Avançada (2101-2140)
    try:
        from backend.collectors.massive.advanced_ai.advanced_ai_collectors import (
            OpenAIPICollector, ClaudeAPICollector, GeminiAPICollector
        )
        test_collectors.extend([OpenAIPICollector, ClaudeAPICollector, GeminiAPICollector])
        print("OK: Advanced AI collectors carregados")
    except Exception as e:
        print(f"ERRO: Advanced AI - {e}")
    
    print(f"\nTotal de coletores para teste: {len(test_collectors)}")
    
    # Testa cada coletor
    passed = 0
    failed = 0
    
    for i, collector_class in enumerate(test_collectors, 1):
        collector_name = collector_class.__name__
        print(f"\n[{i}/{len(test_collectors)}] Testando: {collector_name}")
        
        try:
            # Testa instanciação
            collector = collector_class()
            print(f"  OK: Instanciação bem-sucedida")
            
            # Testa setup
            await collector._setup_collector()
            print(f"  OK: Setup bem-sucedido")
            
            # Testa coleta básica
            from backend.collectors.base_collector import CollectorRequest
            request = CollectorRequest(
                query="test query",
                url="https://example.com",
                parameters={},
                timeout=5
            )
            
            result = await collector._async_collect(request)
            
            if isinstance(result, dict) and 'success' in result:
                print(f"  OK: Coleta bem-sucedida")
                passed += 1
            else:
                print(f"  ERRO: Coleta retornou formato inválido")
                failed += 1
                
        except Exception as e:
            print(f"  ERRO: {e}")
            failed += 1
    
    # Resumo
    print(f"\n{'='*60}")
    print("RESUMO DO TESTE RÁPIDO")
    print(f"{'='*60}")
    print(f"Coletores testados: {len(test_collectors)}")
    print(f"Passaram: {passed}")
    print(f"Falharam: {failed}")
    print(f"Taxa de sucesso: {(passed/len(test_collectors)*100):.1f}%")
    
    if failed == 0:
        print("\nSTATUS: EXCELENTE! Todos os coletores testados passaram!")
    elif failed <= len(test_collectors) * 0.1:  # Até 10% de falha
        print("\nSTATUS: BOM! Poucos coletores falharam.")
    else:
        print("\nSTATUS: PRECISA ATENÇÃO! Muitos coletores falharam.")
    
    return passed, failed

if __name__ == "__main__":
    passed, failed = asyncio.run(quick_test_collectors())
    sys.exit(0 if failed == 0 else 1)
