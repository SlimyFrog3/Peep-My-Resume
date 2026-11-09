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
  workExperience: JobRecord[]
  unassignedExperience: string[]
  educationRecords: EducationRecord[]
  certificationRecords: CertificationRecord[]
  linkRecords: LinkRecord[]
}

export type ParseCheckStatus = 'looks_good' | 'needs_review' | 'could_not_assess'
export type ParseCheckResult = { status: ParseCheckStatus; reasons: string[] }
export type SourceLine = { text: string; page: number | null; region: string; line: number; bbox: number[] | null }
export type DateValue = { value: string; precision: 'year' | 'month' | 'present' }
export type JobRecord = {
  organization: string | null
  title: string | null
  location: string | null
  parentOrganization: string | null
  dates: { raw: string; start: DateValue; end: DateValue } | null
  description: string[]
  source: SourceLine[]
}
export type EducationRecord = { institution: string | null; qualification: string | null; date: DateValue | null; notes: string[]; source: SourceLine[] }
export type CertificationRecord = { name: string; status: string | null; description: string[]; source: SourceLine[] }
export type LinkRecord = { url: string; method: string; source: SourceLine[] }
