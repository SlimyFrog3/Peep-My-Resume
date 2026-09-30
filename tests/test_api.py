"""Run from the project root: python -m unittest discover -s tests -v"""
from pathlib import Path
import unittest
from fastapi.testclient import TestClient
from backend.main import app
from backend.parser import group_sections

ROOT = Path(__file__).resolve().parent.parent

class ParserTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_real_pdf_and_docx(self):
        for filename in ['simple.pdf', 'simple.docx']:
            with self.subTest(filename=filename):
                data = (ROOT / 'examples' / filename).read_bytes()
                response = self.client.post('/parse', files={'file': (filename, data)})
                self.assertEqual(response.status_code, 200)
                result = response.json()
                self.assertEqual(result['contact'][0], 'Jordan Lee')
                self.assertIn('Example Software Inc.', result['experience'])
                self.assertIn('May 2027', result['education'])
                self.assertEqual(result['skills'], ['Python, Java, TypeScript, React, SQL, Git'])
                self.assertIn('Built a React dashboard', result['extractedText'])

    def test_missing_sections_stay_empty(self):
        result = group_sections('Jordan Lee\njordan@example.com\nSkills: Python, SQL')
        self.assertEqual(result['education'], [])
        self.assertEqual(result['experience'], [])
        self.assertEqual(result['skills'], ['Python, SQL'])

    def test_other_sections_do_not_leak_into_education(self):
        result = group_sections('EDUCATION:\nExample University\nPROJECTS\nResume App\nTECHNICAL SKILLS\nReact')
        self.assertEqual(result['education'], ['Example University'])
        self.assertEqual(result['skills'], ['React'])
        self.assertIn('Resume App', result['extractedText'])

    def test_bad_inputs(self):
        for filename, data in [('broken.pdf', b'not pdf'), ('broken.docx', b'bad zip'), ('resume.txt', b'Hello'), ('empty.pdf', b'')]:
            with self.subTest(filename=filename):
                response = self.client.post('/parse', files={'file': (filename, data)})
                self.assertEqual(response.status_code, 422)
                self.assertIsInstance(response.json()['detail'], str)

    def test_size_limit(self):
        response = self.client.post('/parse', files={'file': ('large.pdf', b'x' * (10 * 1024 * 1024 + 1))})
        self.assertEqual(response.status_code, 413)

    def test_missing_upload(self):
        self.assertEqual(self.client.post('/parse').status_code, 422)

    def test_health(self):
        self.assertEqual(self.client.get('/health').json()['status'], 'ok')

if __name__ == '__main__':
    unittest.main()
