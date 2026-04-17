import { create } from 'zustand'

// Dados simulados dos 2240 coletores
const COLLECTORS_DATA = {
  categories: [
    {
      id: 'web_scraping',
      name: 'Web Scraping',
      description: 'Coleta de dados de páginas web',
      icon: 'globe',
      count: 30,
      range: '1-30',
      collectors: [
        { id: 1, name: 'BeautifulSoupCollector', status: 'active', performance: 95 },
        { id: 2, name: 'ScrapyCollector', status: 'active', performance: 92 },
        { id: 3, name: 'SeleniumCollector', status: 'active', performance: 88 },
        // ... mais 27 coletores
      ]
    },
    {
      id: 'ai_advanced',
      name: 'IA + Automação Avançada',
      description: 'Coletores com inteligência artificial',
      icon: 'brain',
      count: 80,
      range: '1661-1740',
      collectors: [
        { id: 1661, name: 'LangChainCollector', status: 'active', performance: 94 },
        { id: 1662, name: 'LlamaIndexCollector', status: 'active', performance: 91 },
        { id: 1663, name: 'HaystackCollector', status: 'active', performance: 89 },
        // ... mais 77 coletores
      ]
    },
    {
      id: 'infrastructure_cloud',
      name: 'Infraestrutura, Cloud e Coleta em Escala Extrema',
      description: 'Coletores de cloud e infraestrutura',
      icon: 'cloud',
      count: 200,
      range: '1741-1940',
      collectors: [
        { id: 1741, name: 'AWSCollector', status: 'active', performance: 96 },
        { id: 1742, name: 'AzureCloudCollector', status: 'active', performance: 93 },
        { id: 1743, name: 'GoogleCloudCollector', status: 'active', performance: 94 },
        // ... mais 197 coletores
      ]
    },
    {
      id: 'reverse_engineering',
      name: 'Engenharia Reversa',
      description: 'Ferramentas de engenharia reversa',
      icon: 'search',
      count: 30,
      range: '1941-1970',
      collectors: [
        { id: 1941, name: 'GhidraCollector', status: 'active', performance: 90 },
        { id: 1942, name: 'IDAFreeCollector', status: 'active', performance: 87 },
        { id: 1943, name: 'BinaryNinjaCollector', status: 'active', performance: 85 },
        // ... mais 27 coletores
      ]
    },
    {
      id: 'autonomous_agents',
      name: 'Agentes Autônomos de Coleta',
      description: 'Agentes AI autônomos',
      icon: 'robot',
      count: 30,
      range: '2041-2070',
      collectors: [
        { id: 2041, name: 'AutoGPTCollector', status: 'active', performance: 92 },
        { id: 2042, name: 'BabyAGICollector', status: 'active', performance: 89 },
        { id: 2043, name: 'AgentGPTCollector', status: 'active', performance: 91 },
        // ... mais 27 coletores
      ]
    },
    {
      id: 'advanced_ai',
      name: 'IA Autônoma Avançada',
      description: 'Sistemas de IA avançados',
      icon: 'cpu',
      count: 40,
      range: '2101-2140',
      collectors: [
        { id: 2101, name: 'OpenAIPICollector', status: 'active', performance: 98 },
        { id: 2102, name: 'ClaudeAPICollector', status: 'active', performance: 96 },
        { id: 2103, name: 'GeminiAPICollector', status: 'active', performance: 95 },
        // ... mais 37 coletores
      ]
    }
  ]
}

const useCollectorStore = create((set, get) => ({
  // Estado
  collectors: [],
  categories: COLLECTORS_DATA.categories,
  selectedCategory: null,
  searchQuery: '',
  isLoading: false,
  stats: {
    total: 2240,
    active: 2240,
    failed: 0,
    avgPerformance: 92.5
  },
  recentSearches: [],
  activeJobs: [],

  // Ações
  initializeCollectors: () => {
    set({ isLoading: true })
    
    // Simula carregamento dos coletores
    setTimeout(() => {
      const allCollectors = COLLECTORS_DATA.categories.flatMap(cat => 
        cat.collectors.map(collector => ({
          ...collector,
          category: cat.id,
          categoryName: cat.name
        }))
      )
      
      set({ 
        collectors: allCollectors,
        isLoading: false 
      })
    }, 1000)
  },

  setSelectedCategory: (categoryId) => {
    set({ selectedCategory: categoryId })
  },

  setSearchQuery: (query) => {
    set({ searchQuery: query })
  },

  getFilteredCollectors: () => {
    const { collectors, selectedCategory, searchQuery } = get()
    
    let filtered = collectors
    
    if (selectedCategory) {
      filtered = filtered.filter(c => c.category === selectedCategory)
    }
    
    if (searchQuery) {
      filtered = filtered.filter(c => 
        c.name.toLowerCase().includes(searchQuery.toLowerCase())
      )
    }
    
    return filtered
  },

  executeSearch: async (query, options = {}) => {
    const jobId = Date.now()
    
    // Adiciona job ativo
    set(state => ({
      activeJobs: [...state.activeJobs, {
        id: jobId,
        query,
        status: 'running',
        progress: 0,
        startTime: Date.now()
      }]
    }))

    // Simula progresso da busca
    const progressInterval = setInterval(() => {
      set(state => ({
        activeJobs: state.activeJobs.map(job =>
          job.id === jobId
            ? { ...job, progress: Math.min(job.progress + 10, 90) }
            : job
        )
      }))
    }, 500)

    // Simula conclusão da busca
    setTimeout(() => {
      clearInterval(progressInterval)
      
      set(state => ({
        activeJobs: state.activeJobs.map(job =>
          job.id === jobId
            ? { ...job, status: 'completed', progress: 100 }
            : job
        ),
        recentSearches: [
          {
            id: jobId,
            query,
            timestamp: Date.now(),
            results: Math.floor(Math.random() * 1000) + 100,
            duration: Math.floor(Math.random() * 5000) + 1000,
            sources: Math.floor(Math.random() * 50) + 10
          },
          ...state.recentSearches.slice(0, 9)
        ]
      }))
    }, 5000)

    return jobId
  },

  getStats: () => {
    const { collectors } = get()
    
    const activeCount = collectors.filter(c => c.status === 'active').length
    const failedCount = collectors.filter(c => c.status === 'failed').length
    const avgPerformance = collectors.reduce((sum, c) => sum + (c.performance || 0), 0) / collectors.length
    
    return {
      total: collectors.length,
      active: activeCount,
      failed: failedCount,
      avgPerformance: avgPerformance.toFixed(1)
    }
  }
}))

export { useCollectorStore, COLLECTORS_DATA }
