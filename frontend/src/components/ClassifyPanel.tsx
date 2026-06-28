import { useState, KeyboardEvent } from 'react'
import { Send, Zap, Clock, Database } from 'lucide-react'
import type { PredictResponse } from '../types'
import { intentApi } from '../hooks/useApi'

const CONFIDENCE_COLOR = (c: number) =>
  c >= 0.8 ? 'bg-emerald-500' : c >= 0.5 ? 'bg-amber-400' : 'bg-red-400'

const SAMPLE_QUERIES = [
  'I forgot my password',
  'I was charged twice this month',
  'The app keeps crashing',
  'I want to delete my account',
  'Connect me to a real agent',
  'Can you add dark mode?',
]

export default function ClassifyPanel() {
  const [text, setText] = useState('')
  const [result, setResult] = useState<PredictResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const classify = async (input?: string) => {
    const query = (input ?? text).trim()
    if (!query) return
    setLoading(true)
    setError(null)
    try {
      const res = await intentApi.predict(query, 5)
      setResult(res)
      if (input) setText(input)
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? 'Prediction failed. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  const onKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); classify() }
  }

  return (
    <div className="space-y-6">
      {/* Input */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
        <label className="block text-sm font-semibold text-slate-600 mb-2">User Message</label>
        <div className="flex gap-3">
          <textarea
            rows={3}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={onKey}
            placeholder="Type a user message... (Enter to classify)"
            className="flex-1 resize-none rounded-xl border border-slate-200 px-4 py-3 text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
          />
          <button
            onClick={() => classify()}
            disabled={loading || !text.trim()}
            className="self-end px-6 py-3 bg-indigo-600 text-white rounded-xl font-semibold hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
          >
            {loading ? (
              <span className="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
            ) : (
              <Send size={16} />
            )}
            {loading ? 'Classifying...' : 'Classify'}
          </button>
        </div>

        {/* Sample queries */}
        <div className="mt-4">
          <p className="text-xs text-slate-400 mb-2 font-medium">Try a sample:</p>
          <div className="flex flex-wrap gap-2">
            {SAMPLE_QUERIES.map((q) => (
              <button
                key={q}
                onClick={() => classify(q)}
                className="text-xs px-3 py-1.5 bg-slate-100 hover:bg-indigo-50 hover:text-indigo-700 text-slate-600 rounded-full transition-colors border border-slate-200"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl p-4 text-sm">
          {error}
        </div>
      )}

      {/* Result */}
      {result && !error && (
        <div className="space-y-4 animate-fade-in">
          {/* Top intent card */}
          <div className="bg-gradient-to-br from-indigo-600 to-indigo-800 rounded-2xl p-6 text-white">
            <div className="flex items-center justify-between mb-3">
              <span className="text-indigo-200 text-sm font-medium uppercase tracking-wide">Top Intent</span>
              <div className="flex items-center gap-3 text-xs text-indigo-200">
                {result.cached && (
                  <span className="flex items-center gap-1"><Database size={12} /> Cached</span>
                )}
                <span className="flex items-center gap-1"><Clock size={12} /> {result.latency_ms}ms</span>
                <span className="flex items-center gap-1"><Zap size={12} /> {result.model_version}</span>
              </div>
            </div>
            <h2 className="text-3xl font-bold mb-1">{result.top_intent.intent_label}</h2>
            <p className="text-indigo-200 text-sm">"{result.text}"</p>
            <div className="mt-4">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-indigo-200">Confidence</span>
                <span className="font-bold">{(result.top_intent.confidence * 100).toFixed(1)}%</span>
              </div>
              <div className="h-2 bg-indigo-900 rounded-full overflow-hidden">
                <div
                  className="h-full bg-white rounded-full transition-all duration-700"
                  style={{ width: `${result.top_intent.confidence * 100}%` }}
                />
              </div>
            </div>
          </div>

          {/* All predictions */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
            <h3 className="text-sm font-semibold text-slate-600 mb-4">All Predictions</h3>
            <div className="space-y-3">
              {result.all_predictions.map((pred, i) => (
                <div key={pred.intent_id}>
                  <div className="flex justify-between text-sm mb-1">
                    <div className="flex items-center gap-2">
                      <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold text-white ${i === 0 ? 'bg-indigo-600' : 'bg-slate-300'}`}>
                        {i + 1}
                      </span>
                      <span className="font-medium text-slate-700">{pred.intent_label}</span>
                    </div>
                    <span className="font-semibold text-slate-600">{(pred.confidence * 100).toFixed(1)}%</span>
                  </div>
                  <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden ml-7">
                    <div
                      className={`h-full rounded-full transition-all duration-500 delay-${i * 100} ${CONFIDENCE_COLOR(pred.confidence)}`}
                      style={{ width: `${pred.confidence * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
