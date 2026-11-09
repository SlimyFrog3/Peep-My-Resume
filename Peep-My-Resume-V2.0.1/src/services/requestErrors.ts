// Explain what we know from HTTP status; never guess that a file is corrupted.
export function requestErrorMessage(status: number, problem: unknown): string {
  // Only display document-specific details from our validation responses.
  if ((status === 413 || status === 422) && problem && typeof problem === 'object' &&
      'detail' in problem && typeof problem.detail === 'string') return problem.detail
  if (status === 413) return 'The upload exceeds the service size limit. Choose a smaller file.'
  if (status === 422) return 'The upload could not be validated. Select a PDF or DOCX file and try again.'
  if (status === 429) return 'The service is receiving too many requests. Wait a moment and retry.'
  if ([502, 503, 504].includes(status)) return 'The service is temporarily unavailable or did not respond in time. Wait a moment and retry.'
  if (status >= 500) return 'The service could not process this request. Retry, and report the issue if it continues.'
  if (status === 404) return 'The analysis endpoint could not be found. Refresh the page; if it continues, report the issue.'
  return `The request could not be completed (HTTP ${status}). Please retry.`
}
