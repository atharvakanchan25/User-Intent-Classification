import { useState } from 'react'
import { MessageSquare, Layers, BarChart2, Tag, Brain } from 'lucide-react'
import type { AppTab } from './types'
import ClassifyPanel from './components/ClassifyPanel'
import BatchPanel from './components/BatchPanel'
import AnalyticsPanel from './components/AnalyticsPanel'
import IntentsPanel from './components/IntentsPanel'
import clsx from 'clsx'

const NAV: { id: AppTab; label: string; icon: any; desc: string }[] = [
  { id: 'classify', label: 'Classify', icon: MessageSquare, desc: 'Single message classification' },
  { id: 'batch', label: 'Batch', icon: Layers, desc: 'Multi-message prediction' },
  { id: 'analytics', label: 'Analytics', icon: BarChart2, desc: 'Live metrics & charts' },
  { id: 'intents', label: 'Intents', icon: Tag, desc: 'View registered intents' },
]

export default function App() {
  const [tab, setTab] = useState<AppTab>('classify')

  const Panel = tab === 'classify' ? ClassifyPanel
    : tab === 'batch' ? BatchPanel
    : tab === 'analytics' ? AnalyticsPanel
    : IntentsPanel

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-slate-200 flex flex-col fixed h-full z-10">
        {/* Logo */}
        <div className="px-6 py-5 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-indigo-600 rounded-xl flex items-center justify-center">
              <Brain size={18} className="text-white" />
            </div>
            <div>
              <div className="font-bold text-slate-800 text-sm leading-tight">IntentIQ</div>
              <div className="text-xs text-slate-400">NLP Classification</div>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV.map(({ id, label, icon: Icon, desc }) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={clsx(
                'w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-all',
                tab === id
                  ? 'bg-indigo-50 text-indigo-700'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-800'
              )}
            >
              <Icon size={17} className={tab === id ? 'text-indigo-600' : 'text-slate-400'} />
              <div>
                <div className="text-sm font-semibold leading-tight">{label}</div>
                <div className="text-xs text-slate-400 leading-tight">{desc}</div>
              </div>
            </button>
          ))}
        </nav>

        {/* Footer */}
        <div className="px-5 py-4 border-t border-slate-100">
          <p className="text-xs text-slate-400">Powered by DistilBERT</p>
          <p className="text-xs text-slate-300 mt-0.5">v1.0.0 · MIT License</p>
        </div>
      </aside>

      {/* Main content */}
      <main className="ml-64 flex-1 flex flex-col min-h-screen">
        {/* Top bar */}
        <header className="bg-white border-b border-slate-200 px-8 py-4 flex items-center justify-between sticky top-0 z-10">
          <div>
            <h1 className="text-lg font-bold text-slate-800">
              {NAV.find((n) => n.id === tab)?.label}
            </h1>
            <p className="text-xs text-slate-400">{NAV.find((n) => n.id === tab)?.desc}</p>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs text-slate-500 font-medium">API Connected</span>
          </div>
        </header>

        {/* Page content */}
        <div className="flex-1 px-8 py-6 max-w-5xl w-full mx-auto">
          <Panel />
        </div>
      </main>
    </div>
  )
}
