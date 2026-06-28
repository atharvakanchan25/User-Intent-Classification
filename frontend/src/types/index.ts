export interface IntentPrediction {
  intent_id: string
  intent_label: string
  confidence: number
}

export interface PredictResponse {
  text: string
  top_intent: IntentPrediction
  all_predictions: IntentPrediction[]
  model_version: string
  cached: boolean
  latency_ms: number
}

export interface BatchPredictResponse {
  results: PredictResponse[]
  total: number
  latency_ms: number
}

export interface HealthResponse {
  status: string
  model_loaded: boolean
  device: string
  num_intents: number
  uptime_seconds: number
}

export interface MetricsResponse {
  total_requests: number
  cache_hits: number
  cache_hit_rate: number
  avg_latency_ms: number
  intent_distribution: Record<string, number>
}

export interface IntentInfo {
  id: string
  label: string
}

export type AppTab = 'classify' | 'batch' | 'analytics' | 'intents'
