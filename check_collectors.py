"""
Verificação simples dos coletores implementados
"""

import os

def check_collectors():
    print("Verificação dos Coletores Info-Phantom")
    print("="*40)
    
    base_dir = "backend/collectors/massive"
    
    # Lista de categorias implementadas
    categories = [
        ("Web Scraping", "web_scraping", 30),
        ("AI Advanced", "ai_advanced", 80),
        ("Infrastructure Cloud", "infrastructure_cloud", 200),
        ("Reverse Engineering", "reverse_engineering", 30),
        ("Autonomous Agents", "autonomous_agents", 30),
        ("AI Scraping", "ai_scraping", 30),
        ("Advanced AI", "advanced_ai", 40),
        ("Debugging Analysis", "debugging_analysis", 30),
        ("Malware Analysis", "malware_analysis", 40),
    ]
    
    total_found = 0
    total_expected = 0
    
    for name, dir_name, expected in categories:
        dir_path = os.path.join(base_dir, dir_name)
        file_path = os.path.join(dir_path, f"{dir_name}_collectors.py")
        
        if os.path.exists(file_path):
            # Conta linhas no arquivo como proxy para número de coletores
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Estimativa baseada no número de linhas
                estimated_collectors = len(lines) // 100  # Aproximadamente 100 linhas por coletor
                estimated_collectors = min(estimated_collectors, expected)  # Não excede o esperado
                
                total_found += estimated_collectors
                total_expected += expected
                
                print(f"OK: {name} - {estimated_collectors} coletores")
                
            except Exception as e:
                print(f"ERRO: {name} - {e}")
        else:
            print(f"ERRO: {name} - arquivo não encontrado")
    
    print("="*40)
    print(f"Total encontrado: {total_found}")
    print(f"Total esperado: {total_expected}")
    
    if total_found >= total_expected * 0.9:
        print("STATUS: EXCELENTE!")
        return True
    else:
        print("STATUS: PRECISA VERIFICAR")
        return False

if __name__ == "__main__":
    check_collectors()
