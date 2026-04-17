import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Search, 
  Filter, 
  Database, 
  CheckCircle, 
  AlertCircle,
  Clock,
  TrendingUp,
  Globe,
  Brain,
  Cloud,
  Cpu,
  Zap,
  Activity
} from 'lucide-react'
import { useCollectorStore } from '../stores/collectorStore'

const Collectors = () => {
  const { 
    initializeCollectors, 
    categories, 
    selectedCategory, 
    setSelectedCategory,
    searchQuery,
    setSearchQuery,
    getFilteredCollectors,
    isLoading 
  } = useCollectorStore()

  const [showFilters, setShowFilters] = useState(false)
  const [sortBy, setSortBy] = useState('name')
  const [filterStatus, setFilterStatus] = useState('all')

  useEffect(() => {
    initializeCollectors()
  }, [initializeCollectors])

  const filteredCollectors = getFilteredCollectors()
  
  // Aplica filtros adicionais
  const processedCollectors = filteredCollectors
    .filter(collector => {
      if (filterStatus === 'all') return true
      return collector.status === filterStatus
    })
    .sort((a, b) => {
      if (sortBy === 'name') return a.name.localeCompare(b.name)
      if (sortBy === 'performance') return (b.performance || 0) - (a.performance || 0)
      if (sortBy === 'id') return a.id - b.id
      return 0
    })

  const categoryIcons = {
    web_scraping: Globe,
    ai_advanced: Brain,
    infrastructure_cloud: Cloud,
    reverse_engineering: Search,
    autonomous_agents: Zap,
    advanced_ai: Cpu
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-500" />
      default:
        return <Clock className="w-4 h-4 text-yellow-500" />
    }
  }

  const getPerformanceColor = (performance) => {
    if (performance >= 95) return 'text-green-600'
    if (performance >= 85) return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <h1 className="text-4xl font-bold text-slate-900 dark:text-white mb-4">
          2240 Coletores de Dados
        </h1>
        <p className="text-xl text-slate-600 dark:text-slate-300">
          Explore a maior coleção de coletores de dados da internet
        </p>
      </motion.div>

      {/* Search and Filters */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6"
      >
        <div className="flex flex-col lg:flex-row gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Buscar coletores..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Filter Toggle */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center space-x-2 px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
          >
            <Filter className="w-4 h-4" />
            <span>Filtros</span>
          </button>
        </div>

        {/* Advanced Filters */}
        {showFilters && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-700"
          >
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Sort */}
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  Ordenar por
                </label>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
                >
                  <option value="name">Nome</option>
                  <option value="performance">Performance</option>
                  <option value="id">ID</option>
                </select>
              </div>

              {/* Status Filter */}
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  Status
                </label>
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
                >
                  <option value="all">Todos</option>
                  <option value="active">Ativos</option>
                  <option value="failed">Falharam</option>
                </select>
              </div>

              {/* Category Filter */}
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  Categoria
                </label>
                <select
                  value={selectedCategory || ''}
                  onChange={(e) => setSelectedCategory(e.target.value || null)}
                  className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
                >
                  <option value="">Todas</option>
                  {categories.map(cat => (
                    <option key={cat.id} value={cat.id}>{cat.name}</option>
                  ))}
                </select>
              </div>
            </div>
          </motion.div>
        )}
      </motion.div>

      {/* Categories Overview */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {categories.map((category, index) => {
            const Icon = categoryIcons[category.id] || Database
            const categoryCollectors = getFilteredCollectors().filter(c => c.category === category.id)
            const isActive = selectedCategory === category.id
            
            return (
              <motion.div
                key={category.id}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.2 + index * 0.05 }}
                onClick={() => setSelectedCategory(isActive ? null : category.id)}
                className={`bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6 cursor-pointer transition-all ${
                  isActive ? 'ring-2 ring-blue-500' : 'hover:shadow-xl'
                }`}
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                    <Icon className="w-6 h-6 text-white" />
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-slate-900 dark:text-white">
                      {categoryCollectors.length}
                    </p>
                    <p className="text-sm text-slate-500">coletores</p>
                  </div>
                </div>
                <h3 className="font-semibold text-slate-900 dark:text-white mb-2">
                  {category.name}
                </h3>
                <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">
                  {category.description}
                </p>
                <div className="flex items-center justify-between text-xs text-slate-500">
                  <span>IDs: {category.range}</span>
                  {isActive && (
                    <span className="text-blue-500">Selecionado</span>
                  )}
                </div>
              </motion.div>
            )
          })}
        </div>
      </motion.div>

      {/* Collectors List */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6"
      >
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
            Coletores ({processedCollectors.length})
          </h2>
          <div className="flex items-center space-x-2 text-sm text-slate-500">
            <Database className="w-4 h-4" />
            <span>{processedCollectors.length} de {getFilteredCollectors().length}</span>
          </div>
        </div>

        {isLoading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            <p className="mt-4 text-slate-500">Carregando coletores...</p>
          </div>
        ) : processedCollectors.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {processedCollectors.map((collector, index) => (
              <motion.div
                key={collector.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 + index * 0.02 }}
                className="border border-slate-200 dark:border-slate-700 rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(collector.status)}
                    <span className="font-medium text-slate-900 dark:text-white text-sm">
                      {collector.name}
                    </span>
                  </div>
                  <span className="text-xs text-slate-500">#{collector.id}</span>
                </div>
                
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-500">Performance</span>
                    <div className="flex items-center space-x-1">
                      <TrendingUp className="w-3 h-3" />
                      <span className={`text-xs font-medium ${getPerformanceColor(collector.performance)}`}>
                        {collector.performance}%
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-500">Categoria</span>
                    <span className="text-xs text-slate-600 dark:text-slate-400">
                      {collector.categoryName}
                    </span>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <Database className="w-16 h-16 text-slate-300 mx-auto mb-4" />
            <p className="text-slate-500">Nenhum coletor encontrado</p>
            <p className="text-sm text-slate-400 mt-2">
              Tente ajustar os filtros ou a busca
            </p>
          </div>
        )}
      </motion.div>
    </div>
  )
}

export default Collectors
