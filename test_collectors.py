"""
Teste simples para validar os coletores implementados
"""

import sys
import os
from pathlib import Path

# Adiciona o backend ao path
sys.path.append(str(Path(__file__).parent / "backend"))

def test_collector_imports():
    """Testa se os coletores podem ser importados"""
    
    print("Testando importação dos coletores...")
    
    test_results = []
    
    # Testa Web Scraping
    try:
        from backend.collectors.massive.web_scraping.web_scraping_collectors import get_web_scraping_collectors
        collectors = get_web_scraping_collectors()
        test_results.append(("Web Scraping", len(collectors), True))
        print(f"OK: Web Scraping - {len(collectors)} coletores")
    except Exception as e:
        test_results.append(("Web Scraping", 0, False))
        print(f"ERRO: Web Scraping - {e}")
    
    # Testa AI Advanced
    try:
        from backend.collectors.massive.ai_advanced.ai_advanced_collectors import get_ai_advanced_collectors
        collectors = get_ai_advanced_collectors()
        test_results.append(("AI Advanced", len(collectors), True))
        print(f"OK: AI Advanced - {len(collectors)} coletores")
    except Exception as e:
        test_results.append(("AI Advanced", 0, False))
        print(f"ERRO: AI Advanced - {e}")
    
    # Testa Infrastructure Cloud
    try:
        from backend.collectors.massive.infrastructure_cloud.infrastructure_cloud_collectors import get_infrastructure_cloud_collectors
        collectors = get_infrastructure_cloud_collectors()
        test_results.append(("Infrastructure Cloud", len(collectors), True))
        print(f"OK: Infrastructure Cloud - {len(collectores)} coletores")
    except Exception as e:
        test_results.append(("Infrastructure Cloud", 0, False))
        print(f"ERRO: Infrastructure Cloud - {e}")
    
    # Testa Reverse Engineering
    try:
        from backend.collectors.massive.reverse_engineering.reverse_engineering_collectors import get_reverse_engineering_collectors
        collectors = get_reverse_engineering_collectors()
        test_results.append(("Reverse Engineering", len(collectors), True))
        print(f"OK: Reverse Engineering - {len(collectores)} coletores")
    except Exception as e:
        test_results.append(("Reverse Engineering", 0, False))
        print(f"ERRO: Reverse Engineering - {e}")
    
    # Testa Autonomous Agents
    try:
        from backend.collectors.massive.autonomous_agents.autonomous_agents_collectors import get_autonomous_agents_collectors
        collectors = get_autonomous_agents_collectors()
        test_results.append(("Autonomous Agents", len(collectors), True))
        print(f"OK: Autonomous Agents - {len(collectors)} coletores")
    except Exception as e:
        test_results.append(("Autonomous Agents", 0, False))
        print(f"ERRO: Autonomous Agents - {e}")
    
    # Testa AI Scraping
    try:
        from backend.collectors.massive.ai_scraping.ai_scraping_collectors import get_ai_scraping_collectors
        collectors = get_ai_scraping_collectors()
        test_results.append(("AI Scraping", len(collectors), True))
        print(f"OK: AI Scraping - {len(collectors)} coletores")
    except Exception as e:
        test_results.append(("AI Scraping", 0, False))
        print(f"ERRO: AI Scraping - {e}")
    
    # Testa Advanced AI
    try:
        from backend.collectors.massive.advanced_ai.advanced_ai_collectors import get_advanced_ai_collectors
        collectors = get_advanced_ai_collectors()
        test_results.append(("Advanced AI", len(collectors), True))
        print(f"OK: Advanced AI - {len(collectors)} coletores")
    except Exception as e:
        test_results.append(("Advanced AI", 0, False))
        print(f"ERRO: Advanced AI - {e}")
    
    # Resumo
    print("\n" + "="*60)
    print("RESUMO DOS TESTES DE IMPORTAÇÃO")
    print("="*60)
    
    total_modules = len(test_results)
    successful_modules = sum(1 for _, _, success in test_results if success)
    total_collectors = sum(count for _, count, _ in test_results)
    
    for module, count, success in test_results:
        status = "OK" if success else "ERRO"
        print(f"{module:20} | {count:4} coletores | {status}")
    
    print("-"*60)
    print(f"{'Total':20} | {total_collectors:4} coletores | {successful_modules}/{total_modules} módulos")
    print(f"Taxa de sucesso: {(successful_modules/total_modules*100):.1f}%")
    
    return successful_modules == total_modules

def test_collector_instantiation():
    """Testa instanciação de alguns coletores"""
    
    print("\nTestando instanciação de coletores...")
    
    # Testa alguns coletores específicos
    test_cases = [
        ("Web Scraping", "backend.collectors.massive.web_scraping.web_scraping_collectors", "BeautifulSoupCollector"),
        ("AI Advanced", "backend.collectors.massive.ai_advanced.ai_advanced_collectors", "LangChainCollector"),
        ("Infrastructure", "backend.collectors.massive.infrastructure_cloud.infrastructure_cloud_collectors", "AWSCollector"),
        ("Reverse Eng", "backend.collectors.massive.reverse_engineering.reverse_engineering_collectors", "GhidraCollector"),
        ("Autonomous", "backend.collectors.massive.autonomous_agents.autonomous_agents_collectors", "AutoGPTCollector"),
        ("Advanced AI", "backend.collectors.massive.advanced_ai.advanced_ai_collectors", "OpenAIPICollector"),
    ]
    
    passed = 0
    failed = 0
    
    for category, module_path, class_name in test_cases:
        try:
            module = __import__(module_path, fromlist=[class_name])
            collector_class = getattr(module, class_name)
            
            # Tenta instanciar
            collector = collector_class()
            
            # Verifica atributos básicos
            assert hasattr(collector, 'name')
            assert hasattr(collector, 'metadata')
            assert hasattr(collector, '_setup_collector')
            assert hasattr(collector, '_async_collect')
            
            print(f"OK: {category} - {class_name}")
            passed += 1
            
        except Exception as e:
            print(f"ERRO: {category} - {class_name}: {e}")
            failed += 1
    
    print(f"\nInstanciação: {passed} passaram, {failed} falharam")
    return failed == 0

if __name__ == "__main__":
    print("Teste dos Coletores Info-Phantom")
    print("="*60)
    
    # Testa importações
    import_success = test_collector_imports()
    
    # Testa instanciação
    instantiation_success = test_collector_instantiation()
    
    # Resultado final
    print("\n" + "="*60)
    print("RESULTADO FINAL")
    print("="*60)
    
    if import_success and instantiation_success:
        print("STATUS: EXCELENTE! Todos os testes passaram!")
        print("Os coletores estão implementados corretamente.")
    else:
        print("STATUS: ATENÇÃO! Alguns testes falharam.")
        print("Verifique os erros acima para corrigir os problemas.")
    
    print("="*60)
