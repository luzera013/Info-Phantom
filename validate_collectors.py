"""
Validação direta dos coletores implementados
"""

import os
import sys
from pathlib import Path

def validate_collector_files():
    """Valida se os arquivos dos coletores existem"""
    
    print("Validando arquivos dos coletores...")
    
    # Lista de arquivos que devem existir
    collector_files = [
        "backend/collectors/massive/web_scraping/web_scraping_collectors.py",
        "backend/collectors/massive/ai_advanced/ai_advanced_collectors.py",
        "backend/collectors/massive/infrastructure_cloud/infrastructure_cloud_collectors.py",
        "backend/collectors/massive/reverse_engineering/reverse_engineering_collectors.py",
        "backend/collectors/massive/autonomous_agents/autonomous_agents_collectors.py",
        "backend/collectors/massive/ai_scraping/ai_scraping_collectors.py",
        "backend/collectors/massive/advanced_ai/advanced_ai_collectors.py",
        "backend/collectors/massive/debugging_analysis/debugging_analysis_collectors.py",
        "backend/collectors/massive/malware_analysis/malware_analysis_collectors.py",
    ]
    
    existing_files = 0
    missing_files = 0
    
    for file_path in collector_files:
        if os.path.exists(file_path):
            existing_files += 1
            print(f"OK: {file_path}")
        else:
            missing_files += 1
            print(f"ERRO: {file_path} não encontrado")
    
    print(f"\nArquivos existentes: {existing_files}/{len(collector_files)}")
    print(f"Arquivos faltantes: {missing_files}")
    
    return missing_files == 0

def count_collectors_in_files():
    """Conta o número de coletores implementados"""
    
    print("\nContando coletores implementados...")
    
    # Padrões para encontrar classes de coletores
    import re
    
    total_collectors = 0
    file_details = []
    
    collector_files = [
        ("Web Scraping", "backend/collectors/massive/web_scraping/web_scraping_collectors.py"),
        ("AI Advanced", "backend/collectors/massive/ai_advanced/ai_advanced_collectors.py"),
        ("Infrastructure Cloud", "backend/collectors/massive/infrastructure_cloud/infrastructure_cloud_collectors.py"),
        ("Reverse Engineering", "backend/collectors/massive/reverse_engineering/reverse_engineering_collectors.py"),
        ("Autonomous Agents", "backend/collectors/massive/autonomous_agents/autonomous_agents_collectors.py"),
        ("AI Scraping", "backend/collectors/massive/ai_scraping/ai_scraping_collectors.py"),
        ("Advanced AI", "backend/collectors/massive/advanced_ai/advanced_ai_collectors.py"),
        ("Debugging Analysis", "backend/collectors/massive/debugging_analysis/debugging_analysis_collectors.py"),
        ("Malware Analysis", "backend/collectors/massive/malware_analysis/malware_analysis_collectors.py"),
    ]
    
    for category, file_path in collector_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Conta classes que seguem o padrão
                class_pattern = r'class\s+(\w+Collector)\s*\('
                classes = re.findall(class_pattern, content)
                
                # Remove duplicatas e classes de base
                unique_classes = list(set(classes))
                unique_classes = [c for c in unique_classes if not c.startswith(('Asynchronous', 'Synchronous', 'Base'))]
                
                count = len(unique_classes)
                total_collectors += count
                
                file_details.append((category, count, unique_classes[:5]))  # Mostra primeiros 5
                
                print(f"{category:20} | {count:3} coletores")
                
            except Exception as e:
                print(f"ERRO ao ler {file_path}: {e}")
        else:
            print(f"{category:20} | {'ERRO':3} arquivo não encontrado")
    
    print(f"\nTotal de coletores implementados: {total_collectors}")
    return total_collectors, file_details

def validate_collector_structure():
    """Valida a estrutura básica dos arquivos de coletores"""
    
    print("\nValidando estrutura dos coletores...")
    
    # Verifica um arquivo de exemplo
    example_file = "backend/collectors/massive/ai_advanced/ai_advanced_collectors.py"
    
    if not os.path.exists(example_file):
        print(f"ERRO: Arquivo de exemplo {example_file} não encontrado")
        return False
    
    try:
        with open(example_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verifica elementos essenciais
        required_elements = [
            "import asyncio",
            "from typing import",
            "class AsynchronousCollector",
            "class CollectorMetadata",
            "def __init__",
            "async def _setup_collector",
            "async def _async_collect",
            "def get_",
        ]
        
        missing_elements = []
        for element in required_elements:
            if element not in content:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"ERRO: Elementos faltando: {missing_elements}")
            return False
        else:
            print("OK: Estrutura básica está correta")
            return True
            
    except Exception as e:
        print(f"ERRO ao validar estrutura: {e}")
        return False

def main():
    """Função principal"""
    print("Validação dos Coletores Info-Phantom")
    print("="*60)
    
    # Valida arquivos
    files_ok = validate_collector_files()
    
    # Conta coletores
    total_collectors, file_details = count_collectors_in_files()
    
    # Valida estrutura
    structure_ok = validate_collector_structure()
    
    # Resumo final
    print("\n" + "="*60)
    print("RESUMO DA VALIDAÇÃO")
    print("="*60)
    
    print(f"Arquivos de coletores: {'OK' if files_ok else 'ERRO'}")
    print(f"Estrutura do código: {'OK' if structure_ok else 'ERRO'}")
    print(f"Total de coletores: {total_collectors}")
    
    # Verifica se atingimos a meta
    expected_collectors = 2240
    if total_collectors >= expected_collectors:
        print(f"STATUS: EXCELENTE! {total_collectors} coletores implementados (meta: {expected_collectors})")
        print("Todos os coletores estão prontos para uso!")
    elif total_collectors >= expected_collectors * 0.9:
        print(f"STATUS: BOM! {total_collectors} coletores implementados (meta: {expected_collectors})")
        print("Quase todos os coletores estão prontos!")
    else:
        print(f"STATUS: EM ANDAMENTO! {total_collectors} coletores implementados (meta: {expected_collectors})")
        print("Ainda há coletores para implementar.")
    
    # Mostra detalhes dos arquivos
    print(f"\nDetalhes por categoria:")
    for category, count, examples in file_details:
        print(f"  {category}: {count} coletores")
        if examples:
            print(f"    Exemplos: {', '.join(examples[:3])}...")
    
    return total_collectors >= expected_collectors

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
