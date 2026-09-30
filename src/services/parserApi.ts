import type { ParseResult } from '../types/ParseResult'
import { sampleResult } from '../sampleResult'

export const demoMode = import.meta.env.VITE_USE_MOCK === 'true'

function isParseResult(value: unknown): value is ParseResult {
  if (!value || typeof value !== 'object') return false
  const data = value as Record<string, unknown>
  return ['contact', 'experience', 'education', 'skills'].every(key =>
    Array.isArray(data[key]) && data[key].every(item => typeof item === 'string')
  ) && typeof data.extractedText === 'string'
}

// Only this function knows whether results come from a mock or our future service.
export async function parseResume(file: File): Promise<ParseResult> {
  if (demoMode) {
    await new Promise(resolve => setTimeout(resolve, 450))
    return sampleResult
  }
  const body = new FormData()
  body.append('file', file)
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), 90000)
  try {
    const baseUrl = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')
    const response = await fetch(`${baseUrl}/parse`, { method: 'POST', body, signal: controller.signal })
    if (!response.ok) {
      let message = `Parser request failed (${response.status}). Check that the backend is running.`
      const problem: unknown = await response.json().catch(() => null)
      if (problem && typeof problem === 'object' && 'detail' in problem && typeof problem.detail === 'string') message = problem.detail
      throw new Error(message)
    }
    const result: unknown = await response.json()
    if (!isParseResult(result)) throw new Error('The parser returned an unexpected results format.')
    return result
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw new Error('The parser took too long. Please try again.', { cause: error })
    if (error instanceof TypeError) throw new Error('Could not reach the parser service. Check that it is running.', { cause: error })
    throw error
  } finally {
    window.clearTimeout(timeout)
  }
}
