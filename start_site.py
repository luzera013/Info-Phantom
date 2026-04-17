#!/usr/bin/env python3
"""
Script para iniciar o site Info-Phantom na porta 8080
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path

# Define o diretório correto
DIRECTORY = Path(__file__).parent / "frontend"

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        # Adiciona headers CORS para permitir requisições de qualquer origem
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

def main():
    # Verifica se o diretório existe
    if not DIRECTORY.exists():
        print(f"Erro: Diretório {DIRECTORY} não encontrado!")
        sys.exit(1)
    
    # Verifica se o index.html existe
    index_file = DIRECTORY / "index.html"
    if not index_file.exists():
        print(f"Erro: Arquivo {index_file} não encontrado!")
        sys.exit(1)
    
    # Muda para o diretório correto
    os.chdir(DIRECTORY)
    
    # Configura o servidor
    port = 8080
    handler = CustomHTTPRequestHandler
    
    # Cria o servidor
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"")
        print(f"=" * 60)
        print(f"INFO-PHANTOM SITE INICIADO")
        print(f"=" * 60)
        print(f"Servidor rodando em: http://localhost:{port}")
        print(f"Diretório: {DIRECTORY}")
        print(f"Arquivo principal: {index_file}")
        print(f"")
        print(f"Pressione Ctrl+C para parar o servidor")
        print(f"=" * 60)
        print(f"")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print(f"\nServidor parado pelo usuário")
            sys.exit(0)

if __name__ == "__main__":
    main()
