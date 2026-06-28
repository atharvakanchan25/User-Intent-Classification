import { useEffect, useState } from 'react'
import { Tag, Search } from 'lucide-react'
import type { IntentInfo } from '../types'
import { intentApi } from '../hooks/useApi'

const PALETTE = [
  'bg-indigo-50 text-indigo-700 border-indigo-100',
  'bg-purple-50 text-purple-700 border-purple-100',
  'bg-cyan-50 text-cyan-700 border-cyan-100',
  'bg-emerald-50 text-emerald-700 border-emerald-100',
  'bg-amber-50 text-amber-700 border-amber-100',
  'bg-rose-50 text-rose-700 border-rose-100',
  'bg-pink-50 text-pink-700 border-pink-100',
  'bg-teal-50 text-teal-700 border-teal-100',
  'bg-orange-50 text-orange-700 border-orange-100',
  'bg-lime-50 text-lime-700 border-lime-100',
]

export default function IntentsPanel() {
  const [intents, setIntents] = useState<IntentInfo[]>([])
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    intentApi.intents()
      .then(setIntents)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const filtered = intents.filter(
    (i) =>
      i.label.toLowerCase().includes(query.toLowerCase()) ||
      i.id.toLowerCase().includes(query.toLowerCase())
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 bg-white border border-slate-200 rounded-xl px-4 py-2.5 shadow-sm">
        <Search size={16} className="text-slate-400" />
        <input
          type="text"
          placeholder="Search intents..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="flex-1 text-sm text-slate-700 placeholder-slate-400 focus:outline-none"
        />
      </div>

      {loading ? (
        <div className="text-center py-12 text-slate-400 text-sm">Loading intents...</div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((intent, i) => (
            <div
              key={intent.id}
              className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="flex items-start gap-3">
                <div className={`w-9 h-9 rounded-xl border flex items-center justify-center flex-shrink-0 ${PALETTE[i % PALETTE.length]}`}>
                  <Tag size={16} />
                </div>
                <div>
                  <div className="font-semibold text-slate-800 text-sm">{intent.label}</div>
                  <div className="text-xs text-slate-400 mt-0.5 font-mono">{intent.id}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {!loading && filtered.length === 0 && (
        <div className="text-center py-12 text-slate-400 text-sm">No intents found.</div>
      )}
    </div>
  )
}
