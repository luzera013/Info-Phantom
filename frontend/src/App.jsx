import React, { useState, useEffect } from 'react'
import { Routes, Route } from 'react-router-dom'
import { motion } from 'framer-motion'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import Search from './pages/Search'
import Collectors from './pages/Collectors'
import Playground from './pages/Playground'
import Documentation from './pages/Documentation'
import { useCollectorStore } from './stores/collectorStore'

function App() {
  const [darkMode, setDarkMode] = useState(true)
  const { initializeCollectors } = useCollectorStore()

  useEffect(() => {
    // Inicializa os coletores quando o app carrega
    initializeCollectors()
  }, [initializeCollectors])

  return (
    <div className={`min-h-screen ${darkMode ? 'dark' : 'light'}`}>
      <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 min-h-screen">
        <Navbar darkMode={darkMode} setDarkMode={setDarkMode} />
        
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="container mx-auto px-4 py-8"
        >
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/search" element={<Search />} />
            <Route path="/collectors" element={<Collectors />} />
            <Route path="/playground" element={<Playground />} />
            <Route path="/docs" element={<Documentation />} />
          </Routes>
        </motion.div>

        {/* Footer */}
        <footer className="bg-slate-800 dark:bg-slate-900 text-white py-8 mt-16">
          <div className="container mx-auto px-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
              <div>
                <h3 className="text-xl font-bold mb-4">Info-Phantom</h3>
                <p className="text-slate-300">
                  O maior sistema de coleta de dados da internet com 2240 coletores especializados
                </p>
              </div>
              <div>
                <h4 className="font-semibold mb-4">Recursos</h4>
                <ul className="space-y-2 text-slate-300">
                  <li><a href="/collectors" className="hover:text-white">Coletores</a></li>
                  <li><a href="/playground" className="hover:text-white">Playground</a></li>
                  <li><a href="/docs" className="hover:text-white">Documentação</a></li>
                </ul>
              </div>
              <div>
                <h4 className="font-semibold mb-4">Categorias</h4>
                <ul className="space-y-2 text-slate-300">
                  <li>Web Scraping</li>
                  <li>IA & Automação</li>
                  <li>Cloud & Infraestrutura</li>
                  <li>Segurança & Análise</li>
                </ul>
              </div>
              <div>
                <h4 className="font-semibold mb-4">Estatísticas</h4>
                <ul className="space-y-2 text-slate-300">
                  <li>2240 Coletores</li>
                  <li>44 Categorias</li>
                  <li>1100 Requisições/s</li>
                  <li>Cache Multi-nível</li>
                </ul>
              </div>
            </div>
            <div className="border-t border-slate-700 mt-8 pt-8 text-center text-slate-400">
              <p>&copy; 2024 Info-Phantom. Todos os direitos reservados.</p>
            </div>
          </div>
        </footer>
      </div>
    </div>
  )
}

export default App
