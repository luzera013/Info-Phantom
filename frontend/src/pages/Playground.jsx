import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Play, 
  Code, 
  Database, 
  Settings, 
  Copy, 
  Check,
  Terminal,
  Activity,
  Globe,
  Brain,
  Cloud,
  Zap,
  Cpu
} from 'lucide-react'
import { useCollectorStore } from '../stores/collectorStore'

const Playground = () => {
  const { executeSearch, activeJobs, categories } = useCollectorStore()
  const [selectedCollector, setSelectedCollector] = useState(null)
  const [testQuery, setTestQuery] = useState('test query')
  const [testResults, setTestResults] = useState(null)
  const [copiedCode, setCopiedCode] = useState(false)
  const [isRunning, setIsRunning] = useState(false)

  const exampleQueries = [
    { query: 'machine learning algorithms', description: 'Busca por algoritmos de machine learning' },
    { query: 'cloud computing trends 2024', description: 'Tendências de cloud computing' },
    { query: 'cybersecurity best practices', description: 'Melhores práticas de segurança' },
    { query: 'AI automation tools', description: 'Ferramentas de automação com IA' }
  ]

  const codeExamples = {
    python: `# Exemplo de uso do Info-Phantom
from info_phantom import InfoPhantomClient

# Inicializa o cliente
client = InfoPhantomClient(api_key="your-api-key")

# Executa busca multi-fonte
results = await client.search(
    query="machine learning",
    sources=["web", "ai", "cloud"],
    max_results=100,
    use_cache=True,
    use_ai=True
)

# Processa resultados
for result in results.data:
    print(f"Fonte: {result.source}")
    print(f"Título: {result.title}")
    print(f"Conteúdo: {result.content[:200]}...")
    print("-" * 50)`,

    javascript: `// Exemplo de uso do Info-Phantom
import { InfoPhantomClient } from '@info-phantom/client';

// Inicializa o cliente
const client = new InfoPhantomClient({
  apiKey: 'your-api-key',
  endpoint: 'https://api.info-phantom.com'
});

// Executa busca multi-fonte
const results = await client.search({
  query: 'machine learning',
  sources: ['web', 'ai', 'cloud'],
  maxResults: 100,
  useCache: true,
  useAI: true
});

// Processa resultados
results.data.forEach(result => {
  console.log(\`Fonte: \${result.source}\`);
  console.log(\`Título: \${result.title}\`);
  console.log(\`Conteúdo: \${result.content.substring(0, 200)}...\`);
  console.log('-'.repeat(50));
});`,

    curl: `# Exemplo de uso do Info-Phantom com cURL
curl -X POST "https://api.info-phantom.com/v1/search" \\
  -H "Authorization: Bearer your-api-key" \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "machine learning",
    "sources": ["web", "ai", "cloud"],
    "max_results": 100,
    "use_cache": true,
    "use_ai": true
  }'`
  }

  const handleTestCollector = async () => {
    if (!selectedCollector || !testQuery.trim()) return
    
    setIsRunning(true)
    setTestResults(null)
    
    try {
      // Simula teste do coletor
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      setTestResults({
        collector: selectedCollector,
        query: testQuery,
        results: Math.floor(Math.random() * 50) + 10,
        duration: Math.floor(Math.random() * 2000) + 500,
        status: 'success',
        data: {
          source: selectedCollector.name,
          query: testQuery,
          timestamp: new Date().toISOString(),
          results: [
            { title: `Resultado 1 para "${testQuery}"`, content: "Conteúdo simulado do resultado..." },
            { title: `Resultado 2 para "${testQuery}"`, content: "Mais conteúdo simulado..." },
            { title: `Resultado 3 para "${testQuery}"`, content: "Conteúdo adicional simulado..." }
          ]
        }
      })
    } finally {
      setIsRunning(false)
    }
  }

  const copyCode = (code) => {
    navigator.clipboard.writeText(code)
    setCopiedCode(true)
    setTimeout(() => setCopiedCode(false), 2000)
  }

  const categoryIcons = {
    web_scraping: Globe,
    ai_advanced: Brain,
    infrastructure_cloud: Cloud,
    reverse_engineering: Terminal,
    autonomous_agents: Zap,
    advanced_ai: Cpu
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <h1 className="text-4xl font-bold text-slate-900 dark:text-white mb-4">
          Playground Interativo
        </h1>
        <p className="text-xl text-slate-600 dark:text-slate-300">
          Teste e explore os 2240 coletores de dados em tempo real
        </p>
      </motion.div>

      {/* Quick Test */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6"
      >
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6">
          Teste Rápido de Coletores
        </h2>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Collector Selection */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Selecione um Coletor
            </label>
            <div className="grid grid-cols-2 gap-2 max-h-64 overflow-y-auto">
              {categories.slice(0, 3).map((category) => {
                const Icon = categoryIcons[category.id] || Database
                return category.collectors.slice(0, 4).map((collector) => (
                  <button
                    key={collector.id}
                    onClick={() => setSelectedCollector(collector)}
                    className={`p-2 border rounded-lg text-left transition-colors ${
                      selectedCollector?.id === collector.id
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                        : 'border-slate-200 dark:border-slate-700 hover:border-slate-300'
                    }`}
                  >
                    <div className="flex items-center space-x-2">
                      <Icon className="w-4 h-4 text-blue-500" />
                      <span className="text-sm font-medium text-slate-900 dark:text-white">
                        {collector.name}
                      </span>
                    </div>
                    <span className="text-xs text-slate-500">
                      Performance: {collector.performance}%
                    </span>
                  </button>
                ))
              })}
            </div>
          </div>

          {/* Test Configuration */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Query de Teste
            </label>
            <input
              type="text"
              value={testQuery}
              onChange={(e) => setTestQuery(e.target.value)}
              placeholder="Digite sua query de teste..."
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white mb-4"
            />

            <div className="space-y-2">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                Queries de Exemplo:
              </label>
              {exampleQueries.map((example, index) => (
                <button
                  key={index}
                  onClick={() => setTestQuery(example.query)}
                  className="block w-full text-left p-2 border border-slate-200 dark:border-slate-700 rounded hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
                >
                  <div className="font-medium text-slate-900 dark:text-white">
                    {example.query}
                  </div>
                  <div className="text-xs text-slate-500">
                    {example.description}
                  </div>
                </button>
              ))}
            </div>

            <button
              onClick={handleTestCollector}
              disabled={!selectedCollector || !testQuery.trim() || isRunning}
              className="w-full mt-4 px-4 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-slate-300 text-white rounded-lg font-medium transition-colors flex items-center justify-center space-x-2"
            >
              {isRunning ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Testando...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  <span>Executar Teste</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Test Results */}
        {testResults && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-6 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg"
          >
            <div className="flex items-center space-x-2 mb-4">
              <Check className="w-5 h-5 text-green-600" />
              <span className="font-medium text-green-800 dark:text-green-200">
                Teste Concluído com Sucesso
              </span>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
              <div>
                <span className="text-sm text-slate-600 dark:text-slate-400">Coletor:</span>
                <p className="font-medium text-slate-900 dark:text-white">
                  {testResults.collector.name}
                </p>
              </div>
              <div>
                <span className="text-sm text-slate-600 dark:text-slate-400">Query:</span>
                <p className="font-medium text-slate-900 dark:text-white">
                  {testResults.query}
                </p>
              </div>
              <div>
                <span className="text-sm text-slate-600 dark:text-slate-400">Resultados:</span>
                <p className="font-medium text-slate-900 dark:text-white">
                  {testResults.results}
                </p>
              </div>
              <div>
                <span className="text-sm text-slate-600 dark:text-slate-400">Duração:</span>
                <p className="font-medium text-slate-900 dark:text-white">
                  {testResults.duration}ms
                </p>
              </div>
            </div>

            <div className="space-y-2">
              <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                Amostra de Resultados:
              </span>
              {testResults.data.results.map((result, index) => (
                <div key={index} className="p-2 bg-white dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
                  <div className="font-medium text-slate-900 dark:text-white">
                    {result.title}
                  </div>
                  <div className="text-sm text-slate-600 dark:text-slate-400">
                    {result.content}
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </motion.div>

      {/* Code Examples */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6"
      >
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6">
          Exemplos de Código
        </h2>
        
        <div className="space-y-6">
          {Object.entries(codeExamples).map(([language, code]) => (
            <div key={language} className="border border-slate-200 dark:border-slate-700 rounded-lg">
              <div className="flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-700">
                <div className="flex items-center space-x-2">
                  <Code className="w-4 h-4 text-slate-600 dark:text-slate-400" />
                  <span className="font-medium text-slate-900 dark:text-white capitalize">
                    {language}
                  </span>
                </div>
                <button
                  onClick={() => copyCode(code)}
                  className="flex items-center space-x-2 px-3 py-1 text-sm bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 rounded transition-colors"
                >
                  {copiedCode ? (
                    <>
                      <Check className="w-4 h-4 text-green-600" />
                      <span>Copiado!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-4 h-4" />
                      <span>Copiar</span>
                    </>
                  )}
                </button>
              </div>
              <div className="p-4">
                <pre className="text-sm text-slate-700 dark:text-slate-300 overflow-x-auto">
                  <code>{code}</code>
                </pre>
              </div>
            </div>
          ))}
        </div>
      </motion.div>

      {/* API Documentation */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6"
      >
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6">
          Documentação da API
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
              Endpoints Principais
            </h3>
            <div className="space-y-3">
              <div className="p-3 border border-slate-200 dark:border-slate-700 rounded-lg">
                <div className="font-medium text-slate-900 dark:text-white">POST /v1/search</div>
                <div className="text-sm text-slate-600 dark:text-slate-400">
                  Executa busca multi-fonte
                </div>
              </div>
              <div className="p-3 border border-slate-200 dark:border-slate-700 rounded-lg">
                <div className="font-medium text-slate-900 dark:text-white">GET /v1/collectors</div>
                <div className="text-sm text-slate-600 dark:text-slate-400">
                  Lista todos os coletores disponíveis
                </div>
              </div>
              <div className="p-3 border border-slate-200 dark:border-slate-700 rounded-lg">
                <div className="font-medium text-slate-900 dark:text-white">GET /v1/stats</div>
                <div className="text-sm text-slate-600 dark:text-slate-400">
                  Estatísticas do sistema
                </div>
              </div>
            </div>
          </div>
          
          <div>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
              Parâmetros da Busca
            </h3>
            <div className="space-y-2">
              <div className="flex justify-between p-2 border-b border-slate-100 dark:border-slate-700">
                <span className="text-slate-700 dark:text-slate-300">query</span>
                <span className="text-slate-500">string</span>
              </div>
              <div className="flex justify-between p-2 border-b border-slate-100 dark:border-slate-700">
                <span className="text-slate-700 dark:text-slate-300">sources</span>
                <span className="text-slate-500">array</span>
              </div>
              <div className="flex justify-between p-2 border-b border-slate-100 dark:border-slate-700">
                <span className="text-slate-700 dark:text-slate-300">max_results</span>
                <span className="text-slate-500">number</span>
              </div>
              <div className="flex justify-between p-2 border-b border-slate-100 dark:border-slate-700">
                <span className="text-slate-700 dark:text-slate-300">use_cache</span>
                <span className="text-slate-500">boolean</span>
              </div>
              <div className="flex justify-between p-2">
                <span className="text-slate-700 dark:text-slate-300">use_ai</span>
                <span className="text-slate-500">boolean</span>
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  )
}

export default Playground
