import { sections, type ParseResult } from '../types/ParseResult'
import { requestErrorMessage } from './requestErrors'
import { sampleResult } from '../sampleResult'

export const demoMode = import.meta.env.VITE_USE_MOCK === 'true'

function isParseResult(value: unknown): value is ParseResult {
  if (!value || typeof value !== 'object') return false
  const data = value as Record<string, unknown>
  return sections.every(([key]) =>
    Array.isArray(data[key]) && data[key].every(item => typeof item === 'string')
  ) && typeof data.extractedText === 'string' && Array.isArray(data.warnings) && data.warnings.every(item => typeof item === 'string')
}

// The caller can cancel when a new file replaces an in-flight upload.
export async function parseResume(file: File, signal?: AbortSignal): Promise<ParseResult> {
  if (demoMode) {
    await new Promise(resolve => setTimeout(resolve, 450))
    return sampleResult
  }
  const body = new FormData()
  body.append('file', file)
  const controller = new AbortController()
  const cancel = () => controller.abort()
  signal?.addEventListener('abort', cancel, { once: true })
  if (signal?.aborted) controller.abort()
  let timedOut = false
  const timeout = window.setTimeout(() => { timedOut = true; controller.abort() }, 90000)
  try {
    const baseUrl = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')
    const response = await fetch(`${baseUrl}/parse`, { method: 'POST', body, signal: controller.signal })
    if (!response.ok) {
      const problem: unknown = await response.json().catch(() => null)
      throw new Error(requestErrorMessage(response.status, problem))
    }

    const result: unknown = await response.json().catch(() => null)
    if (!isParseResult(result)) throw new Error('The service returned an unreadable response. Refresh the page and retry. If it continues, report the issue.')
    return result
  } catch (error) {
    if (controller.signal.aborted) throw new Error(timedOut ? 'The request timed out. Please retry; the service may still be starting.' : 'Analysis was canceled.', { cause: error })
    if (error instanceof TypeError) throw new Error('A network connection to the service could not be completed. Check your connection and try again.', { cause: error })
    throw error
  } finally {
    signal?.removeEventListener('abort', cancel)
    window.clearTimeout(timeout)
  }
}
