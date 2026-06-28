import axios from 'axios'
import type {
  PredictResponse,
  BatchPredictResponse,
  HealthResponse,
  MetricsResponse,
  IntentInfo,
} from '../types'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

export const intentApi = {
  predict: (text: string, top_k = 3): Promise<PredictResponse> =>
    api.post<PredictResponse>('/predict', { text, top_k }).then((r) => r.data),

  predictBatch: (texts: string[], top_k = 3): Promise<BatchPredictResponse> =>
    api.post<BatchPredictResponse>('/predict/batch', { texts, top_k }).then((r) => r.data),

  health: (): Promise<HealthResponse> =>
    api.get<HealthResponse>('/health').then((r) => r.data),

  metrics: (): Promise<MetricsResponse> =>
    api.get<MetricsResponse>('/metrics').then((r) => r.data),

  intents: (): Promise<IntentInfo[]> =>
    api.get<IntentInfo[]>('/intents').then((r) => r.data),
}
