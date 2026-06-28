import { useState } from 'react'
import { Play, Download } from 'lucide-react'
import type { PredictResponse } from '../types'
import { intentApi } from '../hooks/useApi'

export default function BatchPanel() {
  const [input, setInput] = useState('')
  const [results, setResults] = useState<PredictResponse[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [latency, setLatency] = useState<number | null>(null)

  const runBatch = async () => {
    const texts = input.split('\n').map((t) => t.trim()).filter(Boolean)
    if (!texts.length) return
    setLoading(true)
    setError(null)
    try {
      const res = await intentApi.predictBatch(texts, 3)
      setResults(res.results)
      setLatency(res.latency_ms)
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? 'Batch prediction failed')
    } finally {
      setLoading(false)
    }
  }

  const downloadCSV = () => {
    const headers = 'Text,Intent,Confidence,Cached,Latency(ms)\n'
    const rows = results
      .map((r) =>
        `"${r.text}","${r.top_intent.intent_label}",${(r.top_intent.confidence * 100).toFixed(1)},${r.cached},${r.latency_ms}`
      )
      .join('\n')
    const blob = new Blob([headers + rows], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'intent_predictions.csv'
    a.click()
  }

  const CONFIDENCE_BADGE = (c: number) =>
    c >= 0.8
      ? 'bg-emerald-100 text-emerald-700'
      : c >= 0.5
      ? 'bg-amber-100 text-amber-700'
      : 'bg-red-100 text-red-700'

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
        <label className="block text-sm font-semibold text-slate-600 mb-2">
          Messages (one per line, max 50)
        </label>
        <textarea
          rows={8}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={"I forgot my password\nI was charged twice\nThe app keeps crashing\n..."}
          className="w-full resize-none rounded-xl border border-slate-200 px-4 py-3 text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm font-mono"
        />
        <div className="flex justify-between items-center mt-3">
          <span className="text-xs text-slate-400">
            {input.split('\n').filter((t) => t.trim()).length} messages
          </span>
          <button
            onClick={runBatch}
            disabled={loading || !input.trim()}
            className="px-6 py-2.5 bg-indigo-600 text-white rounded-xl font-semibold hover:bg-indigo-700 disabled:opacity-50 transition-all flex items-center gap-2 text-sm"
          >
            {loading ? (
              <span className="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
            ) : (
              <Play size={14} />
            )}
            {loading ? 'Running...' : 'Run Batch'}
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl p-4 text-sm">
          {error}
        </div>
      )}

      {results.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="flex justify-between items-center p-4 border-b border-slate-100">
            <div>
              <span className="font-semibold text-slate-700">{results.length} results</span>
              {latency && (
                <span className="ml-3 text-xs text-slate-400">{latency}ms total</span>
              )}
            </div>
            <button
              onClick={downloadCSV}
              className="flex items-center gap-2 text-sm text-indigo-600 hover:text-indigo-800 font-medium"
            >
              <Download size={14} /> Export CSV
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 border-b border-slate-100">
                <tr>
                  <th className="text-left px-4 py-3 font-semibold text-slate-600">#</th>
                  <th className="text-left px-4 py-3 font-semibold text-slate-600">Message</th>
                  <th className="text-left px-4 py-3 font-semibold text-slate-600">Intent</th>
                  <th className="text-left px-4 py-3 font-semibold text-slate-600">Confidence</th>
                  <th className="text-left px-4 py-3 font-semibold text-slate-600">Latency</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {results.map((r, i) => (
                  <tr key={i} className="hover:bg-slate-50 transition-colors">
                    <td className="px-4 py-3 text-slate-400 font-mono">{i + 1}</td>
                    <td className="px-4 py-3 text-slate-700 max-w-xs truncate">{r.text}</td>
                    <td className="px-4 py-3">
                      <span className="px-2.5 py-1 bg-indigo-50 text-indigo-700 rounded-full text-xs font-medium">
                        {r.top_intent.intent_label}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${CONFIDENCE_BADGE(r.top_intent.confidence)}`}>
                        {(r.top_intent.confidence * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-400 text-xs font-mono">
                      {r.cached ? '⚡ cached' : `${r.latency_ms}ms`}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
