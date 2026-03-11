#!/usr/bin/env python3
"""
Script para executar os testes do SixPet Catalog Engine.
"""

import sys
import subprocess
from pathlib import Path

def run_tests():
    """Executa os testes usando pytest."""
    try:
        # Garantir que estamos no diretório correto
        project_root = Path(__file__).parent
        
        # Executar pytest
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/", 
            "-v", 
            "--tb=short",
            "--color=yes"
        ], cwd=project_root, capture_output=False)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"Erro ao executar testes: {e}")
        return False

if __name__ == "__main__":
    success = run_tests()
    if not success:
        print("\n❌ Alguns testes falharam!")
        sys.exit(1)
    else:
        print("\n✅ Todos os testes passaram!")
        sys.exit(0)