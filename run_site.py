#!/usr/bin/env python3
"""
Script para iniciar o site Info-Phantom com todos os arquivos necessários
"""

import http.server
import socketserver
import webbrowser
import os
import sys
import threading
import time
from pathlib import Path

# Define o diretório raiz do projeto
ROOT_DIR = Path(__file__).parent

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT_DIR, **kwargs)
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()
    
    def do_GET(self):
        # Se for a requisição para a página específica, serve o arquivo correto
        if self.path == '/':
            self.path = '/site_standalone.html'
        
        # Se for o favicon, retorna um favicon simples
        elif self.path == '/favicon.ico':
            self.send_response(200)
            self.send_header('Content-Type', 'image/svg+xml')
            self.end_headers()
            favicon = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">data</text></svg>'
            self.wfile.write(favicon.encode())
            return
        
        return super().do_GET()

def open_browser():
    """Abre o navegador após 2 segundos"""
    time.sleep(2)
    webbrowser.open('http://localhost:8080')

def main():
    port = 8080
    
    print("=" * 60)
    print("INFO-PHANTOM SITE INICIADO")
    print("=" * 60)
    print(f"Servidor rodando em: http://localhost:{port}")
    print(f"Diretório raiz: {ROOT_DIR}")
    print()
    print("Arquivos disponíveis:")
    print(f"  - site_standalone.html (página principal)")
    print(f"  - frontend/ (aplicação React)")
    print(f"  - backend/ (API backend)")
    print()
    print("Pressione Ctrl+C para parar o servidor")
    print("=" * 60)
    print()
    
    # Inicia o navegador em uma thread separada
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Configura e inicia o servidor
    handler = CustomHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            print(f"Servidor iniciado na porta {port}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor parado pelo usuário")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"Erro: Porta {port} já está em uso!")
            print(f"Tente: python -m http.server {port + 1}")
        else:
            print(f"Erro ao iniciar servidor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
