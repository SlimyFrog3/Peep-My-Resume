import { isParseResult } from './parserApi'
import type { AISuggestion, ExportPreview, ReviewBlock } from '../types/ParseResult'

const base = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')
const clean = (blocks: ReviewBlock[]) => blocks.map(({ id, section, text }) => ({ id, section, text }))

async function request(path: string, body?: unknown): Promise<Response> {
  const controller = new AbortController()
  const timer = window.setTimeout(() => controller.abort(), 60000)
  try {
    const response = await fetch(base + path, {
      method: body ? 'POST' : 'GET', signal: controller.signal,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    })
    if (!response.ok) {
      const problem = await response.json().catch(() => null)
      throw new Error(typeof problem?.detail === 'string' ? problem.detail :
        'The review request could not be completed. Check the content and retry.')
    }
    // Read the body while the timeout is active.
    const bytes = await response.arrayBuffer()
    return new Response(bytes, { status: response.status, headers: response.headers })
  } catch (error) {
    if (controller.signal.aborted) throw new Error('The request timed out. Your edits are still here; please retry.', { cause: error })
    if (error instanceof TypeError) throw new Error('Could not reach the service. Your edits are still here.', { cause: error })
    throw error
  } finally { window.clearTimeout(timer) }
}

export async function capabilities(): Promise<{ aiEnabled: boolean }> {
  return (await request('/capabilities')).json()
}
export async function previewResume(original: ReviewBlock[], blocks: ReviewBlock[]): Promise<ExportPreview> {
  const data = await (await request('/review/preview', { original: clean(original), blocks: clean(blocks) })).json()
  if (!isParseResult(data.result) || typeof data.coverage?.retainedPercent !== 'number'
    || typeof data.exportPreservesApprovedWords !== 'boolean') throw new Error('Unexpected preview response. Check the deployed frontend and backend versions.')
  return data
}
export async function exportResume(original: ReviewBlock[], blocks: ReviewBlock[]): Promise<Blob> {
  return (await request('/review/export', { original: clean(original), blocks: clean(blocks) })).blob()
}
export async function aiSuggestions(blocks: ReviewBlock[]): Promise<AISuggestion[]> {
  const data = await (await request('/ai/review', { consent: true, blocks: clean(blocks) })).json()
  if (!Array.isArray(data.suggestions)) throw new Error('AI returned an unreadable response.')
  return data.suggestions
}
