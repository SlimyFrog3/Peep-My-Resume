from pathlib import Path
import unittest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from pdfminer.pdfdocument import PDFPasswordIncorrect
from pdfminer.pdfparser import PDFSyntaxError
from backend.main import app
from backend.parser import read_pdf_page, parse_resume
from backend.layout import PageReading

ROOT = Path(__file__).resolve().parent.parent

class ErrorTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.data = (ROOT / 'examples/simple.pdf').read_bytes()

    def upload(self):
        return self.client.post('/parse', files={'file': ('resume.pdf', self.data)})

    def test_nonzero_page_bounds(self):
        # Reproduce a page whose origin is not (0, 0), without personal data.
        page = Mock()
        page.bbox = (12, -7.92, 624, 784.08)
        page.width, page.height = 612, 792
        page.extract_words.return_value = []
        page.extract_text_lines.return_value = [{'text': 'Readable document', 'x0': 24, 'top': 40, 'x1': 130, 'bottom': 50}]
        reading = read_pdf_page(page)
        self.assertEqual([line.text for line in reading.main], ['Readable document'])
        self.assertFalse(reading.sidebar)

    def test_layout_failure_uses_standard_text_and_warning(self):
        with patch('backend.parser.read_pdf_page', side_effect=ValueError('crop bounds')):
            result = parse_resume(self.data, 'resume.pdf')
        self.assertIn('Jordan Lee', result['extractedText'])
        self.assertTrue(any('standard text reading' in note for note in result['warnings']))

    def test_confirmed_password_error(self):
        with patch('backend.parser.pdfplumber.open', side_effect=PDFPasswordIncorrect()):
            response = self.upload()
        self.assertEqual(response.status_code, 422)
        self.assertIn('requires a password', response.json()['detail'])

    def test_pdf_structure_error_does_not_claim_password(self):
        with patch('backend.parser.pdfplumber.open', side_effect=PDFSyntaxError('bad structure')):
            response = self.upload()
        self.assertEqual(response.status_code, 422)
        self.assertIn('structure', response.json()['detail'])
        self.assertNotIn('password', response.json()['detail'])

    def test_unexpected_failure_is_neutral_and_private(self):
        with patch('backend.main.parse_resume', side_effect=RuntimeError('private diagnostic')):
            response = self.upload()
        self.assertEqual(response.status_code, 500)
        message = response.json()['detail']
        for word in ['private diagnostic', 'password', 'corrupted']:
            self.assertNotIn(word, message)

    def test_no_text_is_not_assumed_to_be_scan(self):
        with patch('backend.parser.read_pdf_page', return_value=PageReading([], [])):
            response = self.upload()
        self.assertEqual(response.status_code, 422)
        self.assertIn('No readable text was extracted', response.json()['detail'])
        self.assertIn('If this is a scan', response.json()['detail'])

    def test_bad_docx_structure(self):
        response = self.client.post('/parse', files={'file': ('resume.docx', b'bad zip')})
        self.assertEqual(response.status_code, 422)
        self.assertIn('DOCX contents', response.json()['detail'])
