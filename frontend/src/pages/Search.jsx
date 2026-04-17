import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Search, 
  Play, 
  Settings, 
  Download, 
  Activity,
  Globe,
  Brain,
  Cloud,
  Zap,
  Cpu,
  Database
} from 'lucide-react'
import { useCollectorStore } from '../stores/collectorStore'

const Search = () => {
  const { executeSearch, activeJobs, recentSearches, categories } = useCollectorStore()
  const [query, setQuery] = useState('')
  const [selectedSources, setSelectedSources] = useState(['web', 'ai', 'cloud'])
  const [maxResults, setMaxResults] = useState(100)
  const [isSearching, setIsSearching] = useState(false)

  const sourceOptions = [
    { id: 'web', name: 'Web Scraping', icon: Globe, count: 30 },
    { id: 'ai', name: 'IA & Automação', icon: Brain, count: 80 },
    { id: 'cloud', name: 'Cloud & Infraestrutura', icon: Cloud, count: 200 },
    { id: 'reverse', name: 'Engenharia Reversa', icon: Search, count: 30 },
    { id: 'autonomous', name: 'Agentes Autônomos', icon: Zap, count: 30 },
    { id: 'advanced', name: 'IA Avançada', icon: Cpu, count: 40 }
  ]

  const handleSearch = async () => {
    if (!query.trim()) return
    
    setIsSearching(true)
    try {
      await executeSearch(query, {
        sources: selectedSources,
        maxResults,
        useCache: true,
        useAI: true
      })
    } finally {
      setIsSearching(false)
    }
  }

  const toggleSource = (sourceId) => {
    setSelectedSources(prev => 
      prev.includes(sourceId) 
        ? prev.filter(id => id !== sourceId)
        : [...prev, sourceId]
    )
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
          Busca Multi-Fonte
        </h1>
        <p className="text-xl text-slate-600 dark:text-slate-300">
          Execute buscas simultâneas em 2240 coletores especializados
        </p>
      </motion.div>

      {/* Search Interface */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6"
      >
        {/* Search Input */}
        <div className="mb-6">
          <div className="flex space-x-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Digite sua busca aqui..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                className="w-full pl-10 pr-4 py-3 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white text-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <button
              onClick={handleSearch}
              disabled={!query.trim() || isSearching}
              className="px-6 py-3 bg-blue-500 hover:bg-blue-600 disabled:bg-slate-300 text-white rounded-lg font-medium transition-colors flex items-center space-x-2"
            >
              {isSearching ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Buscando...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  <span>Executar Busca</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Source Selection */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
            Fontes de Dados
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            {sourceOptions.map((source) => {
              const Icon = source.icon
              const isSelected = selectedSources.includes(source.id)
              
              return (
                <button
                  key={source.id}
                  onClick={() => toggleSource(source.id)}
                  className={`p-3 rounded-lg border-2 transition-all ${
                    isSelected
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-slate-200 dark:border-slate-700 hover:border-slate-300'
                  }`}
                >
                  <div className="flex flex-col items-center space-y-2">
                    <Icon className={`w-6 h-6 ${isSelected ? 'text-blue-500' : 'text-slate-400'}`} />
                    <span className={`text-xs font-medium ${isSelected ? 'text-blue-600 dark:text-blue-400' : 'text-slate-600 dark:text-slate-400'}`}>
                      {source.name}
                    </span>
                    <span className="text-xs text-slate-500">
                      {source.count}
                    </span>
                  </div>
                </button>
              )
            })}
          </div>
        </div>

        {/* Advanced Options */}
        <div className="border-t border-slate-200 dark:border-slate-700 pt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Máximo de Resultados
              </label>
              <input
                type="number"
                min="10"
                max="1000"
                value={maxResults}
                onChange={(e) => setMaxResults(parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
              />
            </div>
            
            <div className="flex items-center space-x-4">
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  defaultChecked
                  className="w-4 h-4 text-blue-500 border-slate-300 rounded focus:ring-blue-500"
                />
                <span className="text-sm text-slate-700 dark:text-slate-300">
                  Usar Cache
                </span>
              </label>
              
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  defaultChecked
                  className="w-4 h-4 text-blue-500 border-slate-300 rounded focus:ring-blue-500"
                />
                <span className="text-sm text-slate-700 dark:text-slate-300">
                  Análise IA
                </span>
              </label>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Active Jobs */}
      {activeJobs.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6"
        >
          <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-4">
            Buscas em Andamento
          </h2>
          <div className="space-y-4">
            {activeJobs.map((job) => (
              <div key={job.id} className="border border-slate-200 dark:border-slate-700 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-slate-900 dark:text-white">
                    {job.query}
                  </span>
                  <span className="text-sm text-slate-500">
                    {Math.floor((Date.now() - job.startTime) / 1000)}s
                  </span>
                </div>
                <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2">
                  <div 
                    className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${job.progress}%` }}
                  />
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  {job.progress}% concluído
                </p>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Recent Searches */}
      {recentSearches.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">
              Buscas Recentes
            </h2>
            <button className="text-sm text-blue-500 hover:text-blue-600">
              Limpar Histórico
            </button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {recentSearches.slice(0, 6).map((search) => (
              <div key={search.id} className="border border-slate-200 dark:border-slate-700 rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <span className="font-medium text-slate-900 dark:text-white">
                    {search.query}
                  </span>
                  <Download className="w-4 h-4 text-slate-400 cursor-pointer hover:text-blue-500" />
                </div>
                <div className="space-y-1 text-xs text-slate-500">
                  <div className="flex justify-between">
                    <span>Resultados:</span>
                    <span>{search.results}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Fontes:</span>
                    <span>{search.sources}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Duração:</span>
                    <span>{(search.duration / 1000).toFixed(1)}s</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  )
}

export default Search
