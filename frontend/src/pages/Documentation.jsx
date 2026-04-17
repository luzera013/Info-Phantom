import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  BookOpen, 
  Search, 
  Database, 
  Code, 
  Globe, 
  Brain,
  Cloud,
  Zap,
  Cpu,
  Terminal,
  CheckCircle,
  ArrowRight,
  ExternalLink,
  Github,
  FileText
} from 'lucide-react'

const Documentation = () => {
  const [searchQuery, setSearchQuery] = useState('')
  const [activeSection, setActiveSection] = useState('overview')

  const sections = [
    { id: 'overview', name: 'Visão Geral', icon: Globe },
    { id: 'collectors', name: 'Coletores', icon: Database },
    { id: 'api', name: 'API', icon: Code },
    { id: 'examples', name: 'Exemplos', icon: BookOpen },
    { id: 'deployment', name: 'Deploy', icon: Cloud }
  ]

  const documentationContent = {
    overview: {
      title: 'Visão Geral do Info-Phantom',
      content: `
        O Info-Phantom é o maior sistema de coleta de dados da internet, com **2240 coletores especializados** 
        distribuídos em **44 categorias** diferentes. Nosso sistema é capaz de processar **1100 requisições simultâneas** 
        com cache multi-nível e orquestração distribuída.
        
        ## Características Principais
        
        - **2240 Coletores Especializados**: Cobertura completa de todas as principais fontes de dados
        - **1100 Requisições Simultâneas**: Performance extrema para processamento em massa
        - **Cache Multi-nível**: Otimização inteligente para reduzir latência
        - **Orquestração Distribuída**: Balanceamento automático de carga
        - **Resiliência Enterprise**: Recuperação automática e fallback handlers
        - **Interface Unificada**: API simples e consistente para todos os coletores
        
        ## Arquitetura
        
        O sistema é construído com uma arquitetura modular que permite:
        
        - Escalabilidade horizontal
        - Alta disponibilidade
        - Monitoramento em tempo real
        - Atualizações sem downtime
      `
    },
    collectors: {
      title: 'Coletores de Dados',
      content: `
        O Info-Phantom possui 2240 coletores organizados em 44 categorias especializadas:
        
        ## Categorias Principais
        
        ### Web Scraping (30 coletores)
        - BeautifulSoup, Scrapy, Selenium, Puppeteer, Playwright
        - Extração de dados de páginas web com suporte a JavaScript
        
        ### IA e Automação Avançada (80 coletores)
        - LangChain, LlamaIndex, Haystack, OpenAI, Claude, Gemini
        - Processamento de linguagem natural e geração de conteúdo
        
        ### Infraestrutura Cloud (200 coletores)
        - AWS, Azure, Google Cloud, DigitalOcean, Vultr
        - Monitoramento e coleta de dados de serviços cloud
        
        ### Engenharia Reversa (30 coletores)
        - Ghidra, IDA Pro, Radare2, Binary Ninja, x64dbg
        - Análise de binários e código reverso
        
        ### Agentes Autônomos (30 coletores)
        - AutoGPT, BabyAGI, AgentGPT, CrewAI, LangGraph
        - Agentes AI que operam de forma autônoma
        
        ### IA Autônoma Avançada (40 coletores)
        - OpenAI API, Claude API, Gemini API, Perplexity AI
        - Sistemas de IA avançados para análise e decisão
        
        ## Implementação
        
        Cada coletor segue o mesmo padrão arquitetural:
        
        \`\`\`python
        class ExampleCollector(AsynchronousCollector):
            def __init__(self, config=None):
                metadata = CollectorMetadata(
                    name="Example",
                    category=CollectorCategory.WEB_SCRAPING,
                    description="Example collector",
                    version="1.0",
                    author="Info-Phantom",
                    tags=["example", "scraping"],
                    capabilities=["web_scraping", "data_extraction"],
                    real_time=False,
                    bulk_support=True
                )
                super().__init__("example", metadata, config)
            
            async def _setup_collector(self):
                # Configuração do coletor
                pass
            
            async def _async_collect(self, request: CollectorRequest):
                # Lógica de coleta de dados
                return {"data": "collected_data", "success": True}
        \`\`\`
      `
    },
    api: {
      title: 'API Reference',
      content: `
        A API do Info-Phantom permite integração fácil com qualquer aplicação.
        
        ## Autenticação
        
        Use sua API key no header Authorization:
        
        \`\`\`http
        Authorization: Bearer your-api-key
        \`\`\`
        
        ## Endpoints Principais
        
        ### Busca Multi-Fonte
        
        \`\`\`http
        POST /api/v1/search
        Content-Type: application/json
        
        {
          "query": "machine learning",
          "sources": ["web", "ai", "cloud"],
          "max_results": 100,
          "use_cache": true,
          "use_ai": true
        }
        \`\`\`
        
        ### Listar Coletores
        
        \`\`\`http
        GET /api/v1/collectors
        \`\`\`
        
        ### Estatísticas do Sistema
        
        \`\`\`http
        GET /api/v1/stats
        \`\`\`
        
        ## Respostas
        
        Todas as respostas seguem o formato padrão:
        
        \`\`\`json
        {
          "success": true,
          "data": {
            "results": [...],
            "total": 100,
            "sources_used": 15,
            "processing_time": 2.5
          },
          "metadata": {
            "timestamp": "2024-01-01T00:00:00Z",
            "request_id": "req_123"
          }
        }
        \`\`\`
      `
    },
    examples: {
      title: 'Exemplos de Uso',
      content: `
        ## Python SDK
        
        \`\`\`python
        from info_phantom import InfoPhantomClient
        
        # Inicialização
        client = InfoPhantomClient(api_key="your-api-key")
        
        # Busca simples
        results = await client.search("machine learning")
        
        # Busca avançada
        results = await client.search(
            query="cybersecurity trends",
            sources=["web", "ai", "cloud"],
            max_results=200,
            use_cache=True,
            use_ai=True
        )
        
        # Processar resultados
        for result in results.data.results:
            print(f"Fonte: {result.source}")
            print(f"Título: {result.title}")
            print(f"Conteúdo: {result.content[:200]}...")
        \`\`\`
        
        ## JavaScript SDK
        
        \`\`\`javascript
        import { InfoPhantomClient } from '@info-phantom/client';
        
        // Inicialização
        const client = new InfoPhantomClient({
          apiKey: 'your-api-key'
        });
        
        // Busca
        const results = await client.search({
          query: 'cloud computing',
          sources: ['web', 'cloud'],
          maxResults: 100
        });
        
        // Processar resultados
        results.data.results.forEach(result => {
          console.log(result.title, result.content);
        });
        \`\`\`
        
        ## cURL
        
        \`\`\`bash
        curl -X POST "https://api.info-phantom.com/v1/search" \\
          -H "Authorization: Bearer your-api-key" \\
          -H "Content-Type: application/json" \\
          -d '{
            "query": "artificial intelligence",
            "sources": ["web", "ai"],
            "max_results": 50
          }'
        \`\`\`
      `
    },
    deployment: {
      title: 'Deploy e Configuração',
      content: `
        ## Docker Deployment
        
        Use nosso Docker Compose para deploy rápido:
        
        \`\`\`yaml
        version: '3.8'
        services:
          info-phantom:
            image: info-phantom:latest
            ports:
              - "8000:8000"
            environment:
              - API_KEY=your-api-key
              - REDIS_URL=redis://redis:6379
            depends_on:
              - redis
          
          redis:
            image: redis:alpine
            ports:
              - "6379:6379"
        \`\`\`
        
        ## Configuração
        
        Variáveis de ambiente obrigatórias:
        
        \`\`\`bash
        API_KEY=your-api-key
        REDIS_URL=redis://localhost:6379
        LOG_LEVEL=INFO
        MAX_CONCURRENT_REQUESTS=1100
        CACHE_TTL=3600
        \`\`\`
        
        ## Performance
        
        Para produção, recomendamos:
        
        - 4+ CPUs
        - 8GB+ RAM
        - Redis cluster para cache
        - Load balancer para alta disponibilidade
        - Monitoramento com Prometheus + Grafana
        
        ## Monitoramento
        
        O sistema expõe métricas em `/metrics`:
        
        - Número de requisições ativas
        - Tempo médio de resposta
        - Taxa de cache hits
        - Saúde dos coletores
      `
    }
  }

  const currentContent = documentationContent[activeSection]

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <h1 className="text-4xl font-bold text-slate-900 dark:text-white mb-4">
          Documentação
        </h1>
        <p className="text-xl text-slate-600 dark:text-slate-300">
          Guia completo do sistema Info-Phantom
        </p>
      </motion.div>

      {/* Navigation */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6"
      >
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Section Navigation */}
          <div className="lg:w-64">
            <h3 className="font-semibold text-slate-900 dark:text-white mb-4">
              Seções
            </h3>
            <nav className="space-y-2">
              {sections.map((section) => {
                const Icon = section.icon
                const isActive = activeSection === section.id
                
                return (
                  <button
                    key={section.id}
                    onClick={() => setActiveSection(section.id)}
                    className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors ${
                      isActive
                        ? 'bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300'
                        : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{section.name}</span>
                  </button>
                )
              })}
            </nav>
          </div>

          {/* Content */}
          <div className="flex-1">
            <div className="prose prose-slate dark:prose-invert max-w-none">
              <h2 className="text-3xl font-bold text-slate-900 dark:text-white mb-6">
                {currentContent.title}
              </h2>
              
              <div 
                className="text-slate-700 dark:text-slate-300 leading-relaxed"
                dangerouslySetInnerHTML={{ 
                  __html: currentContent.content.replace(/\n/g, '<br>').replace(/`/g, '') 
                }}
              />
            </div>

            {/* Quick Links */}
            <div className="mt-8 pt-6 border-t border-slate-200 dark:border-slate-700">
              <h3 className="font-semibold text-slate-900 dark:text-white mb-4">
                Links Rápidos
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <a
                  href="https://github.com/info-phantom"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center space-x-2 p-3 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
                >
                  <Github className="w-4 h-4" />
                  <span>GitHub Repository</span>
                  <ExternalLink className="w-4 h-4 ml-auto" />
                </a>
                <a
                  href="/playground"
                  className="flex items-center space-x-2 p-3 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
                >
                  <PlayCircle className="w-4 h-4" />
                  <span>Playground Interativo</span>
                  <ArrowRight className="w-4 h-4 ml-auto" />
                </a>
                <a
                  href="/collectors"
                  className="flex items-center space-x-2 p-3 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
                >
                  <Database className="w-4 h-4" />
                  <span>Lista de Coletores</span>
                  <ArrowRight className="w-4 h-4 ml-auto" />
                </a>
                <a
                  href="mailto:support@info-phantom.com"
                  className="flex items-center space-x-2 p-3 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
                >
                  <FileText className="w-4 h-4" />
                  <span>Documentação PDF</span>
                  <ArrowRight className="w-4 h-4 ml-auto" />
                </a>
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Stats */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl shadow-lg p-8 text-white"
      >
        <div className="text-center">
          <h2 className="text-3xl font-bold mb-6">
            Info-Phantom em Números
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div>
              <div className="text-4xl font-bold">2240</div>
              <div className="text-blue-100">Coletores</div>
            </div>
            <div>
              <div className="text-4xl font-bold">44</div>
              <div className="text-blue-100">Categorias</div>
            </div>
            <div>
              <div className="text-4xl font-bold">1100</div>
              <div className="text-blue-100">Req/s</div>
            </div>
            <div>
              <div className="text-4xl font-bold">99.9%</div>
              <div className="text-blue-100">Uptime</div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  )
}

export default Documentation
