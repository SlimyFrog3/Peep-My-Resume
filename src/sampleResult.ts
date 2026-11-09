// Only used when VITE_USE_MOCK=true; live uploads never use sample results.
import type { ParseResult } from './types/ParseResult'
export const sampleResult: ParseResult = {
  parseCheck: { status: 'looks_good', reasons: [] },
  workExperience: [{ organization: 'Example Co.', title: 'Software Developer Intern', location: null,
    parentOrganization: null, dates: { raw: '2025–2026', start: { value: '2025', precision: 'year' }, end: { value: '2026', precision: 'year' } },
    description: ['Built an internal dashboard and maintained web services.'], source: [] }],
  unassignedExperience: [],
  educationRecords: [{ institution: 'Example University', qualification: 'B.S. Computer Science', date: { value: '2027', precision: 'year' }, notes: [], source: [] }],
  certificationRecords: [], linkRecords: [],
  summary: [], certifications: [], projects: [], leadership: [], volunteer: [],
  links: [], awards: [], languages: [], other: [], warnings: ['These are sample results.'],
  contact: ['Jordan Lee', 'jordan.lee@example.com', 'Phoenix, AZ'],
  experience: ['Software Developer Intern · Example Co. · 2025–2026', 'Built an internal dashboard and maintained web services.'],
  education: ['B.S. Computer Science · Example University · 2027'],
  skills: ['TypeScript', 'React', 'Python', 'SQL'],
  extractedText: 'Jordan Lee\nPhoenix, AZ · jordan.lee@example.com\n\nEXPERIENCE\nSoftware Developer Intern · Example Co. · 2025–2026\nBuilt an internal dashboard and maintained web services.\n\nEDUCATION\nB.S. Computer Science · Example University · 2027\n\nSKILLS\nTypeScript · React · Python · SQL',
}
