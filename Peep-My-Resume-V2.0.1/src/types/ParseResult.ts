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
}
