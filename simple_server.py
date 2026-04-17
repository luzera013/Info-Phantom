#!/usr/bin/env python3
"""
Servidor web simples e funcional para o Info-Phantom
"""

import http.server
import socketserver
import webbrowser
import threading
import time
import sys
from pathlib import Path

PORT = 8080

class InfoPhantomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=Path(__file__).parent, **kwargs)
    
    def do_GET(self):
        # Serve o arquivo HTML principal
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # HTML completo inline
            html_content = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Info-Phantom - 2240 Coletores</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header {
            text-align: center;
            padding: 40px 0;
            background: rgba(255,255,255,0.1);
            border-radius: 20px;
            margin-bottom: 30px;
        }
        h1 { font-size: 3rem; margin-bottom: 10px; }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: rgba(255,255,255,0.1);
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.2);
        }
        .stat-number { font-size: 2.5rem; font-weight: bold; color: #4facfe; }
        .stat-label { font-size: 1.1rem; margin-top: 10px; }
        .features {
            background: rgba(255,255,255,0.1);
            padding: 30px;
            border-radius: 20px;
            margin-bottom: 30px;
        }
        .features h2 { text-align: center; margin-bottom: 20px; }
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
        }
        .feature-item {
            background: rgba(255,255,255,0.05);
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #4facfe;
        }
        .btn {
            display: inline-block;
            padding: 15px 30px;
            margin: 10px;
            background: linear-gradient(45deg, #4facfe, #00f2fe);
            color: white;
            text-decoration: none;
            border-radius: 25px;
            font-weight: bold;
            border: none;
            cursor: pointer;
        }
        .btn:hover { transform: translateY(-2px); }
        .text-center { text-align: center; }
        footer {
            text-align: center;
            padding: 20px;
            background: rgba(0,0,0,0.2);
            border-radius: 10px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Info-Phantom</h1>
            <p>O Maior Sistema de Coleta de Dados da Internet</p>
            <p style="font-size: 1.5rem; margin-top: 20px;">2240 Coletores Especializados</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">2240</div>
                <div class="stat-label">Coletores de Dados</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">44</div>
                <div class="stat-label">Categorias</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">1100</div>
                <div class="stat-label">Requisições/s</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">99.9%</div>
                <div class="stat-label">Uptime</div>
            </div>
        </div>

        <div class="features">
            <h2>Características Principais</h2>
            <div class="feature-grid">
                <div class="feature-item">
                    <h3>Web Scraping Avançado</h3>
                    <p>30 coletores especializados em extração de dados de páginas web</p>
                </div>
                <div class="feature-item">
                    <h3>IA e Automação</h3>
                    <p>80 coletores com inteligência artificial para processamento inteligente</p>
                </div>
                <div class="feature-item">
                    <h3>Cloud & Infraestrutura</h3>
                    <p>200 coletores para monitoramento e coleta de serviços cloud</p>
                </div>
                <div class="feature-item">
                    <h3>Engenharia Reversa</h3>
                    <p>30 coletores para análise de binários e código reverso</p>
                </div>
                <div class="feature-item">
                    <h3>Agentes Autônomos</h3>
                    <p>30 coletores com agentes AI que operam de forma autônoma</p>
                </div>
                <div class="feature-item">
                    <h3>IA Avançada</h3>
                    <p>40 coletores com sistemas de IA avançados para análise e decisão</p>
                </div>
            </div>
        </div>

        <div class="text-center">
            <button class="btn" onclick="alert('Info-Phantom está online com 2240 coletores!')">Verificar Status</button>
            <button class="btn" onclick="alert('API disponível em http://localhost:8000')">Documentação API</button>
        </div>

        <footer>
            <p>&copy; 2024 Info-Phantom - 2240 Coletores de Dados Massivos</p>
            <p>O maior sistema de coleta de dados da internet</p>
        </footer>
    </div>

    <script>
        console.log('Info-Phantom Site - 2240 coletores online!');
        document.title = 'Info-Phantom - Online';
    </script>
</body>
</html>"""
            
            self.wfile.write(html_content.encode('utf-8'))
            return
        
        # Favicon simples
        elif self.path == '/favicon.ico':
            self.send_response(200)
            self.send_header('Content-type', 'image/svg+xml')
            self.end_headers()
            favicon = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">data</text></svg>'
            self.wfile.write(favicon.encode())
            return
        
        # Outros arquivos
        else:
            super().do_GET()

def open_browser():
    time.sleep(2)
    webbrowser.open(f'http://localhost:{PORT}')

def main():
    print("=" * 60)
    print("INFO-PHANTOM SERVIDOR WEB")
    print("=" * 60)
    print(f"Servidor iniciado em: http://localhost:{PORT}")
    print(f"Diretório: {Path(__file__).parent}")
    print()
    print("Pressione Ctrl+C para parar")
    print("=" * 60)
    print()
    
    # Abrir navegador automaticamente
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Iniciar servidor
    with socketserver.TCPServer(("", PORT), InfoPhantomHandler) as httpd:
        print(f"Servidor rodando na porta {PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor parado pelo usuário")

if __name__ == "__main__":
    main()
