import { isParseResult } from './parserApi'
import type { ExportPreview, ReviewBlock, SectionKey, TemplateId, ResumeTemplate } from '../types/ParseResult'

const base = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')
const clean = (blocks: ReviewBlock[]) => blocks.map(({ id, section, text, resolution }) => ({ id, section, text, resolution: resolution ?? 'include' }))

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

export async function getTemplates(): Promise<ResumeTemplate[]> {
  const data = await (await request('/templates')).json()
  if (!Array.isArray(data.templates) || data.templates.length !== 3) throw new Error('The style list could not be loaded.')
  return data.templates
}
export async function previewResume(original: ReviewBlock[], blocks: ReviewBlock[], templateId: TemplateId, sectionOrder: SectionKey[]): Promise<ExportPreview> {
  const data = await (await request('/review/preview', { original: clean(original), blocks: clean(blocks), templateId, sectionOrder })).json()
  if (!isParseResult(data.result) || typeof data.coverage?.retainedPercent !== 'number'
    || typeof data.exportPreservesApprovedWords !== 'boolean' || !Array.isArray(data.unresolvedBlocks)
    || !Array.isArray(data.document?.sections) || typeof data.docxBase64 !== 'string') throw new Error('Unexpected preview response. Check the deployed frontend and backend versions.')
  return data
}
export function downloadPreview(preview: ExportPreview) {
  const bytes = Uint8Array.from(atob(preview.docxBase64), c => c.charCodeAt(0))
  const blob = new Blob([bytes], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a'); a.href = url; a.download = `Peep-My-Resume-${preview.template.id}.docx`; a.click()
  window.setTimeout(() => URL.revokeObjectURL(url), 1000)
}
