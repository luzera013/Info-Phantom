#!/usr/bin/env python3
"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - System Validation Script
Script final para validação completa do sistema
"""

import asyncio
import sys
import json
import time
from pathlib import Path

# Adicionar diretório do projeto ao path
sys.path.append(str(Path(__file__).parent))

from core.system_validator import SystemValidator
from utils.logger import setup_logger

logger = setup_logger(__name__)

async def main():
    """Função principal de validação"""
    print("🎯 OMNISCIENT_ULTIMATE_SYSTEM_FINAL - VALIDAÇÃO COMPLETA")
    print("=" * 60)
    
    # Inicializar validador
    validator = SystemValidator()
    
    try:
        # Inicializar componentes
        print("\n🔧 Inicializando componentes...")
        await validator.initialize()
        
        # Executar validação completa
        print("\n🔍 Executando validação completa do sistema...")
        result = await validator.validate_complete_system()
        
        # Exibir resultados
        print("\n" + "=" * 60)
        print("📊 RESULTADOS DA VALIDAÇÃO")
        print("=" * 60)
        
        print(f"\n🎯 STATUS GERAL: {result.overall_status.upper()}")
        print(f"📈 Componentes validados: {result.components_validated}")
        print(f"✅ Componentes passaram: {result.components_passed}")
        print(f"❌ Componentes falharam: {result.components_failed}")
        print(f"⏱️ Tempo de validação: {result.validation_timestamp:.2f}s")
        
        # Detalhes por categoria
        print("\n📋 DETALHES POR CATEGORIA:")
        print("-" * 40)
        
        for category, tests in result.test_results.items():
            print(f"\n🔸 {category.upper()}:")
            
            if isinstance(tests, dict):
                if 'results' in tests:
                    # Validação de componentes
                    for component, test_result in tests['results'].items():
                        status_icon = "✅" if test_result.get('status') == 'passed' else "❌"
                        print(f"  {status_icon} {component}: {test_result.get('message', 'Sem mensagem')}")
                else:
                    # Outros tipos de teste
                    for test_name, test_result in tests.items():
                        status_icon = "✅" if test_result.get('status') == 'passed' else "❌"
                        print(f"  {status_icon} {test_name}: {test_result.get('message', 'Sem mensagem')}")
            else:
                print(f"  📄 {tests}")
        
        # Recomendações
        if result.recommendations:
            print("\n💡 RECOMENDAÇÕES:")
            print("-" * 30)
            for i, rec in enumerate(result.recommendations, 1):
                print(f"  {i}. {rec}")
        
        # Métricas do sistema
        if result.system_metrics:
            print("\n📊 MÉTRICAS DO SISTEMA:")
            print("-" * 35)
            
            if 'cpu' in result.system_metrics:
                cpu = result.system_metrics['cpu']
                print(f"  🖥️  CPU: {cpu.get('usage_percent', 0):.1f}% ({cpu.get('core_count', 0)} cores)")
            
            if 'memory' in result.system_metrics:
                memory = result.system_metrics['memory']
                print(f"  🧠  Memória: {memory.get('percent', 0):.1f}% ({memory.get('used_gb', 0):.1f}GB/{memory.get('total_gb', 0):.1f}GB)")
            
            if 'disk' in result.system_metrics:
                disk = result.system_metrics['disk']
                print(f"  💾  Disco: {disk.get('percent', 0):.1f}% ({disk.get('used_gb', 0):.1f}GB/{disk.get('total_gb', 0):.1f}GB)")
        
        # Status final
        print("\n" + "=" * 60)
        if result.overall_status == 'healthy':
            print("🎉 SISTEMA 100% OPERACIONAL!")
            print("✅ Todos os componentes estão funcionando perfeitamente")
            print("🚀 Sistema pronto para produção")
        elif result.overall_status == 'degraded':
            print("⚠️ SISTEMA OPERACIONAL COM LIMITAÇÕES")
            print("🔧 Alguns componentes precisam de atenção")
            print("📊 Sistema funcional mas com restrições")
        else:
            print("❌ SISTEMA COM PROBLEMAS CRÍTICOS")
            print("🚨 Múltiplos componentes com falhas")
            print("🔧 Requer intervenção imediata")
        
        print("=" * 60)
        
        # Salvar relatório completo
        report_file = Path("./logs/validation_report.json")
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            # Converter resultado para JSON serializável
            result_dict = {
                'overall_status': result.overall_status,
                'components_validated': result.components_validated,
                'components_passed': result.components_passed,
                'components_failed': result.components_failed,
                'validation_timestamp': result.validation_timestamp,
                'test_results': result.test_results,
                'recommendations': result.recommendations,
                'system_metrics': result.system_metrics
            }
            
            json.dump(result_dict, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📄 Relatório completo salvo em: {report_file}")
        
        # Código de saída baseado no status
        if result.overall_status == 'healthy':
            sys.exit(0)
        elif result.overall_status == 'degraded':
            sys.exit(1)
        else:
            sys.exit(2)
        
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO NA VALIDAÇÃO: {str(e)}")
        print("🔧 Verificar logs para detalhes")
        sys.exit(3)
    
    finally:
        # Limpar recursos
        try:
            await validator.cleanup()
        except:
            pass

if __name__ == "__main__":
    # Configurar logging
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Executar validação
    asyncio.run(main())
