import React, { useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  Database, 
  Activity, 
  TrendingUp, 
  Clock, 
  CheckCircle, 
  AlertCircle,
  Zap,
  Globe,
  Brain,
  Cloud,
  Search
} from 'lucide-react'
import { useCollectorStore } from '../stores/collectorStore'

const Dashboard = () => {
  const { 
    initializeCollectors, 
    stats, 
    categories, 
    recentSearches, 
    activeJobs,
    getStats 
  } = useCollectorStore()

  useEffect(() => {
    initializeCollectors()
  }, [initializeCollectors])

  const currentStats = getStats()

  const statCards = [
    {
      title: 'Total de Coletores',
      value: currentStats.total,
      icon: Database,
      color: 'blue',
      change: '+0',
      changeType: 'neutral'
    },
    {
      title: 'Coletores Ativos',
      value: currentStats.active,
      icon: CheckCircle,
      color: 'green',
      change: '+0',
      changeType: 'positive'
    },
    {
      title: 'Performance Média',
      value: `${currentStats.avgPerformance}%`,
      icon: TrendingUp,
      color: 'purple',
      change: '+2.1%',
      changeType: 'positive'
    },
    {
      title: 'Buscas Ativas',
      value: activeJobs.length,
      icon: Activity,
      color: 'orange',
      change: activeJobs.length > 0 ? '+1' : '0',
      changeType: activeJobs.length > 0 ? 'positive' : 'neutral'
    }
  ]

  const categoryIcons = {
    web_scraping: Globe,
    ai_advanced: Brain,
    infrastructure_cloud: Cloud,
    reverse_engineering: Search,
    autonomous_agents: Zap,
    advanced_ai: Brain
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
          Info-Phantom Dashboard
        </h1>
        <p className="text-xl text-slate-600 dark:text-slate-300">
          Monitoramento em tempo real dos 2240 coletores de dados
        </p>
      </motion.div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat, index) => {
          const Icon = stat.icon
          const colorClasses = {
            blue: 'bg-blue-500',
            green: 'bg-green-500',
            purple: 'bg-purple-500',
            orange: 'bg-orange-500'
          }

          return (
            <motion.div
              key={stat.title}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.1 }}
              className="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-600 dark:text-slate-400">{stat.title}</p>
                  <p className="text-3xl font-bold text-slate-900 dark:text-white mt-2">
                    {stat.value}
                  </p>
                  <p className={`text-sm mt-2 ${
                    stat.changeType === 'positive' 
                      ? 'text-green-600' 
                      : 'text-slate-500'
                  }`}>
                    {stat.change}
                  </p>
                </div>
                <div className={`w-12 h-12 ${colorClasses[stat.color]} rounded-lg flex items-center justify-center`}>
                  <Icon className="w-6 h-6 text-white" />
                </div>
              </div>
            </motion.div>
          )
        })}
      </div>

      {/* Categories Overview */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6"
      >
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6">
          Categorias de Coletores
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {categories.map((category, index) => {
            const Icon = categoryIcons[category.id] || Database
            
            return (
              <motion.div
                key={category.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.5 + index * 0.1 }}
                className="border border-slate-200 dark:border-slate-700 rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                    <Icon className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-900 dark:text-white">
                      {category.name}
                    </h3>
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                      {category.count} coletores
                    </p>
                  </div>
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">
                  IDs: {category.range}
                </p>
              </motion.div>
            )
          })}
        </div>
      </motion.div>

      {/* Active Jobs */}
      {activeJobs.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6"
        >
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6">
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
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.7 }}
        className="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6"
      >
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6">
          Buscas Recentes
        </h2>
        {recentSearches.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-700">
                  <th className="text-left py-2 text-slate-600 dark:text-slate-400">Query</th>
                  <th className="text-left py-2 text-slate-600 dark:text-slate-400">Resultados</th>
                  <th className="text-left py-2 text-slate-600 dark:text-slate-400">Fontes</th>
                  <th className="text-left py-2 text-slate-600 dark:text-slate-400">Duração</th>
                  <th className="text-left py-2 text-slate-600 dark:text-slate-400">Quando</th>
                </tr>
              </thead>
              <tbody>
                {recentSearches.map((search) => (
                  <tr key={search.id} className="border-b border-slate-100 dark:border-slate-800">
                    <td className="py-2 text-slate-900 dark:text-white">{search.query}</td>
                    <td className="py-2 text-slate-600 dark:text-slate-400">{search.results}</td>
                    <td className="py-2 text-slate-600 dark:text-slate-400">{search.sources}</td>
                    <td className="py-2 text-slate-600 dark:text-slate-400">
                      {(search.duration / 1000).toFixed(1)}s
                    </td>
                    <td className="py-2 text-slate-600 dark:text-slate-400">
                      {new Date(search.timestamp).toLocaleTimeString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-slate-500 dark:text-slate-400 text-center py-8">
            Nenhuma busca realizada ainda
          </p>
        )}
      </motion.div>
    </div>
  )
}

export default Dashboard
