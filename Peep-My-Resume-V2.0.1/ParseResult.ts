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
export type EducationRecord = { institution: string | null; qualification: string | null; date: DateValue | null; notes: string[]; source: SourceLine[] }
export type CertificationRecord = { name: string; status: string | null; description: string[]; source: SourceLine[] }
export type LinkRecord = { url: string; method: string; source: SourceLine[] }

export type ReviewBlock = { id: string; section: SectionKey; text: string; source?: SourceLine[] }
export type Readability = {
  score: number | null; status: ParseCheckStatus; rubricVersion: string; note: string
  categories: { key: string; label: string; earned: number; possible: number; detail: string }[]
}
export type ExportPreview = {
  result: ParseResult
  coverage: { retainedPercent: number; removedTokenCount: number; addedTokenCount: number; removedExamples: string[]; addedExamples: string[]; note: string }
  exportPreservesApprovedWords: boolean
}
export type AISuggestion = { id: string; section: SectionKey; reason: string }
