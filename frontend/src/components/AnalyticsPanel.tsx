import { useEffect, useState, useCallback } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts'
import { RefreshCw, Activity, Cpu, Clock, Database } from 'lucide-react'
import type { MetricsResponse, HealthResponse } from '../types'
import { intentApi } from '../hooks/useApi'

const COLORS = ['#6366f1','#8b5cf6','#06b6d4','#10b981','#f59e0b','#ef4444','#ec4899','#14b8a6','#f97316','#84cc16']

function StatCard({ icon: Icon, label, value, sub }: { icon: any; label: string; value: string; sub?: string }) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
      <div className="flex items-center gap-3 mb-2">
        <div className="w-9 h-9 bg-indigo-50 rounded-xl flex items-center justify-center">
          <Icon size={18} className="text-indigo-600" />
        </div>
        <span className="text-sm text-slate-500 font-medium">{label}</span>
      </div>
      <div className="text-2xl font-bold text-slate-800">{value}</div>
      {sub && <div className="text-xs text-slate-400 mt-1">{sub}</div>}
    </div>
  )
}

export default function AnalyticsPanel() {
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null)
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [loading, setLoading] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [m, h] = await Promise.all([intentApi.metrics(), intentApi.health()])
      setMetrics(m)
      setHealth(h)
    } catch { /* backend may not be available */ }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  const barData = metrics
    ? Object.entries(metrics.intent_distribution)
        .sort(([, a], [, b]) => b - a)
        .map(([id, count]) => ({
          name: id.replace(/_/g, ' '),
          count,
        }))
    : []

  const pieData = barData.map((d, i) => ({ ...d, fill: COLORS[i % COLORS.length] }))

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-semibold text-slate-700">Live Analytics</h2>
        <button
          onClick={load}
          disabled={loading}
          className="flex items-center gap-2 text-sm text-indigo-600 hover:text-indigo-800 font-medium"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Health */}
      {health && (
        <div className={`flex items-center gap-3 px-4 py-3 rounded-xl border text-sm font-medium ${
          health.status === 'healthy'
            ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
            : 'bg-red-50 border-red-200 text-red-700'
        }`}>
          <span className={`w-2 h-2 rounded-full ${health.status === 'healthy' ? 'bg-emerald-500' : 'bg-red-500'} animate-pulse`} />
          Service {health.status} · {health.num_intents} intents · Device: {health.device} · Uptime: {health.uptime_seconds}s
        </div>
      )}

      {/* Stat cards */}
      {metrics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard icon={Activity} label="Total Requests" value={metrics.total_requests.toString()} />
          <StatCard icon={Database} label="Cache Hits" value={metrics.cache_hits.toString()} sub={`${(metrics.cache_hit_rate * 100).toFixed(1)}% hit rate`} />
          <StatCard icon={Clock} label="Avg Latency" value={`${metrics.avg_latency_ms}ms`} />
          <StatCard icon={Cpu} label="Intents Served" value={Object.keys(metrics.intent_distribution).length.toString()} />
        </div>
      )}

      {/* Charts */}
      {barData.length > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
            <h3 className="text-sm font-semibold text-slate-600 mb-4">Intent Distribution (Bar)</h3>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={barData} margin={{ left: -10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-20} textAnchor="end" height={50} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ borderRadius: 12, border: '1px solid #e2e8f0', fontSize: 12 }}
                />
                <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
            <h3 className="text-sm font-semibold text-slate-600 mb-4">Intent Distribution (Pie)</h3>
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie data={pieData} dataKey="count" nameKey="name" cx="50%" cy="50%" outerRadius={90} label={({ name, percent }) => `${(percent * 100).toFixed(0)}%`} labelLine={false}>
                  {pieData.map((entry, i) => (
                    <Cell key={i} fill={entry.fill} />
                  ))}
                </Pie>
                <Legend iconSize={10} wrapperStyle={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ borderRadius: 12, border: '1px solid #e2e8f0', fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center text-slate-400 shadow-sm">
          <Activity size={40} className="mx-auto mb-3 opacity-30" />
          <p className="text-sm">No prediction data yet. Run some classifications to see analytics.</p>
        </div>
      )}
    </div>
  )
}
