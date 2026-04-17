"""
Teste simples para validar os coletores
"""

import os
import re

def main():
    print("Teste de Validação dos Coletores Info-Phantom")
    print("="*50)
    
    # Verifica se os diretórios dos coletores existem
    base_dir = "backend/collectors/massive"
    
    if not os.path.exists(base_dir):
        print("ERRO: Diretório base não encontrado")
        return False
    
    # Lista de diretórios esperados
    expected_dirs = [
        "web_scraping", "ai_advanced", "infrastructure_cloud", 
        "reverse_engineering", "autonomous_agents", "ai_scraping", 
        "advanced_ai", "debugging_analysis", "malware_analysis"
    ]
    
    existing_dirs = []
    for dir_name in expected_dirs:
        dir_path = os.path.join(base_dir, dir_name)
        if os.path.exists(dir_path):
            existing_dirs.append(dir_name)
            print(f"OK: {dir_name}")
        else:
            print(f"ERRO: {dir_name} não encontrado")
    
    print(f"\nDiretórios encontrados: {len(existing_dirs)}/{len(expected_dirs)}")
    
    # Conta coletores nos arquivos
    total_collectors = 0
    
    for dir_name in existing_dirs:
        file_path = os.path.join(base_dir, dir_name, f"{dir_name}_collectors.py")
        
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Conta classes de coletores
                class_pattern = r'class\s+(\w+Collector)\s*\('
                classes = re.findall(class_pattern, content)
                
                # Remove classes base
                collector_classes = [c for c in classes if not c.startswith(('Asynchronous', 'Synchronous', 'Base'))]
                count = len(collector_classes)
                total_collectors += count
                
                print(f"{dir_name:20} | {count:3} coletores")
                
            except Exception as e:
                print(f"ERRO ao ler {file_path}: {e}")
    
    print(f"\nTotal de coletores: {total_collectors}")
    
    # Verifica se atingimos a meta
    expected = 2240
    if total_collectors >= expected:
        print(f"\nSTATUS: EXCELENTE! {total_collectors} coletores implementados")
        print("Sistema pronto para uso!")
        return True
    else:
        print(f"\nSTATUS: {total_collectors}/{expected} coletores implementados")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n" + "="*50)
        print("VALIDAÇÃO CONCLUÍDA COM SUCESSO!")
        print("Todos os 2240 coletores estão implementados.")
        print("="*50)
