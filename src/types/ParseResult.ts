// Shared card definitions keep rendering and API validation in sync.
export const sections = [
  ['contact', 'Contact'], ['summary', 'Professional Summary'],
  ['experience', 'Experience'], ['education', 'Education'], ['skills', 'Skills'],
  ['certifications', 'Certifications'], ['projects', 'Projects'],
  ['leadership', 'Leadership'], ['volunteer', 'Volunteer Work'],
  ['links', 'Links'], ['awards', 'Awards & Activities'], ['languages', 'Languages'],
  ['other', 'Other / Unclassified'],
] as const
export type SectionKey = typeof sections[number][0]
export type ParseResult = Record<SectionKey, string[]> & {
  extractedText: string
  warnings: string[]
  parseCheck: ParseCheckResult
  readability: Readability
  reviewBlocks: ReviewBlock[]
  excludedFurniture: string[]
  workExperience: JobRecord[]
  unassignedExperience: string[]
  educationRecords: EducationRecord[]
  certificationRecords: CertificationRecord[]
  linkRecords: LinkRecord[]
}

export type ParseCheckStatus = 'looks_good' | 'needs_review' | 'could_not_assess'
export const reviewSections = {
  experience: 'Experience', education: 'Education', other: 'Other / Unclassified',
  contact: 'Contact', extractedText: 'extracted text',
} as const
export type ParseFinding = { message: string; nextStep: string; section: keyof typeof reviewSections }
export type ParseCheckResult = { status: ParseCheckStatus; reasons: string[]; findings?: ParseFinding[] }
export type SourceLine = { text: string; page: number | null; region: string; line: number; bbox: number[] | null }
export type DateValue = { value: string; precision: 'year' | 'month' | 'present' }
export type JobRecord = {
  organization: string | null
  title: string | null
  location: string | null
  parentOrganization: string | null
  isEmployerOverview?: boolean
  dates: { raw: string; start: DateValue; end: DateValue } | null
  description: string[]
  source: SourceLine[]
}
export type EducationRecord = { institution: string | null; qualification: string | null; program?: string | null; date: DateValue | null; notes: string[]; source: SourceLine[] }
export type CertificationRecord = { name: string; status: string | null; description: string[]; source: SourceLine[] }
export type LinkRecord = { url: string; method: string; source: SourceLine[] }

export type ReviewBlock = { id: string; section: SectionKey; text: string; source?: SourceLine[]; resolution?: 'pending' | 'include' | 'exclude' }
export type Readability = {
  score: number | null; status: ParseCheckStatus | 'needs_attention'; rubricVersion: string; note: string
  greenChecklist?: { label: string; met: boolean; action: string }[]
  categories: { assessed?: boolean; strength?: string | null; status?: 'strong' | 'review' | 'attention' | 'not_assessed'; key: string; label: string; earned: number; possible: number; detail: string }[]
}
export type ExportPreview = {
  result: ParseResult
  coverage: { retainedPercent: number; removedTokenCount: number; addedTokenCount: number; removedExamples: string[]; addedExamples: string[]; note: string }
  exportPreservesApprovedWords: boolean
  formattingCheck: { passed: boolean; headingCount: number; checks: { heading: string; beforePt: number; afterPt: number; keptWithNext: boolean }[]; note: string }
  unresolvedBlocks: string[]
  document: ResumeDocument
  template: ResumeTemplate
  docxBase64: string
}
export type TemplateId = 'classic' | 'modern' | 'compact'
export type ResumeTemplate = { id: TemplateId; name: string; caption: string; font: string; bodyPt: number; namePt: number; headingPt: number; accent: string; margin: number; paragraphAfter: number; headingBefore: number; lineSpacing: number }
export type ResumeParagraph = { kind: 'name' | 'contact' | 'heading' | 'entry' | 'date' | 'body' | 'bullet' | 'space' | 'link' | 'tenure' | 'subheading'; text: string }
export type ResumeDocument = { sections: { key: SectionKey; title: string; blocks: { id: string; paragraphs: ResumeParagraph[] }[] }[] }
