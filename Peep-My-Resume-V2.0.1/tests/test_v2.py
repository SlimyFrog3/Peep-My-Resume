from io import BytesIO
from pathlib import Path
import unittest
from docx import Document
from backend.parser import group_sections, parse_resume

class V2Tests(unittest.TestCase):
    def test_expanded_sections(self):
        result = group_sections('Jamie Lee\njamie@example.com\nPROFESSIONAL SUMMARY\nDeveloper\nCERTIFICATIONS\nCPR\nPROJECTS\nApp\nLEADERSHIP EXPERIENCE\nClub officer\nVOLUNTEER WORK\nFood bank\nWEBSITES\nhttps://github.com/jamie\nAWARDS & ACTIVITIES\nHonor society\nLANGUAGES\nEnglish')
        for key, value in {'summary':'Developer', 'certifications':'CPR', 'projects':'App', 'leadership':'Club officer', 'volunteer':'Food bank', 'awards':'Honor society', 'languages':'English'}.items():
            self.assertEqual(result[key], [value])
        self.assertEqual(result['skills'], [])
        self.assertEqual(result['links'], ['https://github.com/jamie'])

    def test_inline_labels_do_not_swallow_parent_section(self):
        result = group_sections('SKILLS & ACTIVITIES\nComputer Languages: SQL\nLanguages: English\nTechnical Skills: Excel\nVolunteer: Food bank\nActivities: Student government')
        self.assertEqual(result['skills'], ['SQL', 'Excel'])
        self.assertEqual(result['languages'], ['English'])
        self.assertEqual(result['volunteer'], ['Food bank'])
        self.assertEqual(result['awards'], ['Student government'])

    def test_contact_and_links_anywhere(self):
        result = group_sections('SUMMARY\nDeveloper\nCONTACT\njamie@example.com 480-555-0123\nhttps://linkedin.com/in/jamie')
        self.assertIn('https://linkedin.com/in/jamie', result['links'])
        self.assertTrue(any('480-555-0123' in line for line in result['contact']))

    def test_docx_preserves_accented_original(self):
        doc = Document()
        for line in ['José Lee', 'SUMMARY', 'Résumé writing', 'CERTIFICATIONS', 'CPR']:
            doc.add_paragraph(line)
        buffer = BytesIO(); doc.save(buffer)
        result = parse_resume(buffer.getvalue(), 'test.docx')
        self.assertIn('José Lee', result['contact'])
        self.assertEqual(result['summary'], ['Résumé writing'])

    def test_two_column_pdf_and_page_continuation(self):
        result = parse_resume(Path('examples/two-column.pdf').read_bytes(), 'columns.pdf')
        self.assertEqual(result['summary'], ['Builds software'])
        self.assertEqual(result['experience'], ['Example Co.', 'Built a dashboard'])
        self.assertEqual(result['skills'], ['Python, SQL'])
        self.assertEqual(result['certifications'], ['CPR'])
        self.assertIn('Continued education details', result['education'])
        self.assertTrue(any('two-column' in warning for warning in result['warnings']))

    def test_right_aligned_dates_are_not_columns(self):
        result = parse_resume(Path('examples/right-aligned-dates.pdf').read_bytes(), 'dates.pdf')
        self.assertTrue(any('2020 - 2026' in line for line in result['experience']))
        self.assertFalse(any('two-column' in warning for warning in result['warnings']))

    def test_unclassified_text_preserved(self):
        result = group_sections('Jamie\nREFERENCES\nAvailable on request')
        self.assertEqual(result['other'], ['Available on request'])

if __name__ == '__main__': unittest.main()
