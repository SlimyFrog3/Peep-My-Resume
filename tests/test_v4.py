"""Regression tests use fictional resumes only."""
from io import BytesIO
import json
import unittest
from unittest.mock import patch
from docx import Document
from docx.oxml import OxmlElement
from fastapi.testclient import TestClient
from reportlab.pdfgen.canvas import Canvas
from backend.main import app
from backend.parser import group_sections, parse_resume
from backend.workflow import Block, ReviewRequest, export_docx, preview_export, coverage
from backend.ai_review import prepare_blocks, validate_suggestions

class V4Tests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.blocks = [
            {'id':'contact','section':'contact','text':'Jordan Example\njordan@example.com'},
            {'id':'job','section':'experience','text':'QA Engineer | Sample Labs | Jan 2022 - Present\n- Built automation that reduced manual work by 20%.'},
            {'id':'school','section':'education','text':'Bachelor of Science | Sample University | 2021'},
        ]

    def test_heading_aliases_and_prose_not_contact(self):
        r = group_sections('Jordan Example\njordan@example.com\n'
                           'I am an experienced quality engineer who builds and maintains reliable automated tests for complex web applications across multiple teams and releases.\n'
                           'TOP SKILLS\nPython\nACADEMIC QUALIFICATIONS\nBachelor of Computing\nSample University\n'
                           'WORK EXPERIENCE & JOB DUTIES\nQA Engineer | Sample Labs | 2020 - Present')
        self.assertEqual(r['contact'], ['Jordan Example','jordan@example.com'])
        self.assertTrue(r['summary'])
        self.assertEqual(r['skills'], ['Python'])
        self.assertEqual(r['workExperience'][0]['organization'], 'Sample Labs')
        self.assertEqual(r['educationRecords'][0]['institution'], 'Sample University')

    def test_missing_literal_spaces_pdf_uses_character_geometry(self):
        stream = BytesIO()
        canvas = Canvas(stream)
        canvas.drawString(40, 790, 'Jordan Example')
        canvas.drawString(40, 770, 'jordan@example.com')
        canvas.drawString(40, 740, 'SKILL SUMMARY')
        # Explicit positioned glyphs with visual gaps but no actual space characters.
        x = 40
        for word in 'I am an experienced quality engineer building automated tests'.split():
            for char in word:
                canvas.drawString(x, 720, char)
                x += canvas.stringWidth(char)
            x += 2
        canvas.save()
        r = parse_resume(stream.getvalue(), 'spacing.pdf')
        self.assertIn('I am an experienced quality engineer', r['extractedText'])
        self.assertFalse(any('experienced' in x for x in r['contact']))

    def test_wrapped_employer_and_ongoing_dates(self):
        r=group_sections('Jordan\njordan@example.com\nEXPERIENCE\nQA MANAGER\n'
                         'Sample Labs with a distributed engineering team\nRemote from Arizona\n2022 - ON GOING\n- Built tests.')
        self.assertEqual(r['workExperience'][0]['title'], 'QA MANAGER')
        self.assertEqual(r['workExperience'][0]['dates']['end']['value'], 'present')
        self.assertFalse(r['unassignedExperience'])

    def test_certification_boundary_and_repeated_page_headers(self):
        stream=BytesIO(); c=Canvas(stream, pagesize=(612,792))
        for i in (1,2):
            c.drawString(40,760,'Jordan Example Resume')
            if i==1:
                c.drawString(40,735,'jordan@example.com')
                c.drawString(40,700,'CERTIFICATIONS')
                c.drawString(40,680,'Quality Certificate October 2019')
            else:
                c.drawString(40,700,'NOTABLE PROJECT')
                c.drawString(40,680,'Release Dashboard')
            c.drawString(40,35,f'Page {i} of 2');c.showPage()
        c.save()
        r=parse_resume(stream.getvalue(),'headers.pdf')
        self.assertEqual(len(r['certificationRecords']),1)
        self.assertIn('Release Dashboard',r['projects'])
        self.assertNotIn('Jordan Example Resume',r['certifications'])
        self.assertIn('Page 2 of 2', r['excludedFurniture'])

    def test_one_line_education_from_institution(self):
        r=group_sections('Jordan\njordan@example.com\nEDUCATION\nMaster of Science from Sample University, Arizona 2020 - 2022')
        self.assertEqual(r['educationRecords'][0]['qualification'],'Master of Science')
        self.assertEqual(r['educationRecords'][0]['institution'],'Sample University, Arizona')

    def test_word_header_and_textbox_preserved(self):
        d=Document()
        d.sections[0].header.paragraphs[0].text='jordan@example.com'
        d.add_paragraph('Jordan Example')
        d.add_heading('Skills',1); d.add_paragraph('Python')
        box=OxmlElement('w:txbxContent'); paragraph=OxmlElement('w:p')
        run=OxmlElement('w:r'); text=OxmlElement('w:t'); text.text='Extra source text'
        run.append(text); paragraph.append(run); box.append(paragraph); d.element.body.append(box)
        stream=BytesIO();d.save(stream)
        r=parse_resume(stream.getvalue(),'header.docx')
        self.assertIn('jordan@example.com',r['extractedText'])
        self.assertIn('Extra source text',r['extractedText'])

    def test_rubric_is_deterministic_bounded_and_optional_sections_neutral(self):
        r=group_sections('Jordan\njordan@example.com\nSKILLS\nPython')
        self.assertEqual(r['readability']['score'],100)
        self.assertEqual(sum(x['possible'] for x in r['readability']['categories']),100)
        self.assertEqual(r['readability'],group_sections('Jordan\njordan@example.com\nSKILLS\nPython')['readability'])
        red=group_sections('Just a name')
        self.assertIsNone(red['readability']['score'])
        bad=group_sections('Jordan\nSKILLS\n'+'badword'*25+'\nLINKS\nhttps://github.com/')
        self.assertLess(bad['readability']['score'],100)

    def test_export_roundtrip_actual_docx_and_word_preservation(self):
        response=self.client.post('/review/preview', json={'original':self.blocks,'blocks':self.blocks})
        self.assertEqual(response.status_code,200,response.text)
        preview=response.json()
        self.assertTrue(preview['exportPreservesApprovedWords'])
        self.assertEqual(preview['coverage']['retainedPercent'],100)
        response=self.client.post('/review/export',json={'original':self.blocks,'blocks':self.blocks})
        self.assertEqual(response.status_code,200)
        self.assertIn('wordprocessingml',response.headers['content-type'])
        doc=Document(BytesIO(response.content))
        self.assertFalse(doc.tables)
        self.assertIn('QA Engineer | Sample Labs | Jan 2022 - Present',[p.text for p in doc.paragraphs])
        parsed=parse_resume(response.content,'export.docx')
        self.assertEqual(preview['result']['readability'],parsed['readability'])

    def test_removing_content_is_flagged_even_when_score_improves(self):
        before=[Block(**b) for b in self.blocks]
        after=before[:1]+[Block(id='skills',section='skills',text='Python')]
        check=coverage(before,after)
        self.assertGreater(check['removedTokenCount'],0)
        self.assertLess(check['retainedPercent'],100)

    def test_invalid_empty_and_duplicate_blocks_rejected(self):
        for blocks in ([self.blocks[0],self.blocks[0]],[{'id':'x','section':'other','text':''}],
                       [{'id':'x','section':'unknown','text':'test'}]):
            response=self.client.post('/review/preview',json={'original':self.blocks,'blocks':blocks})
            self.assertEqual(response.status_code,422)

    def test_blank_pdf_reports_zero_without_scoring_network_errors(self):
        stream=BytesIO(); canvas=Canvas(stream); canvas.showPage(); canvas.save()
        response=self.client.post('/parse',files={'file':('blank.pdf',stream.getvalue())})
        self.assertEqual(response.status_code,422)
        self.assertEqual(response.headers.get('X-Readability-Score'),'0')
        self.assertNotIn('X-Readability-Score',self.client.post('/parse').headers)

    def test_review_size_and_invalid_document_characters(self):
        response=self.client.post('/review/preview',content=b'x'*(2*1024*1024+1),
                                  headers={'Content-Type':'application/json'})
        self.assertEqual(response.status_code,413)
        bad=[{'id':'x','section':'other','text':'invalid\x00text'}]
        response=self.client.post('/review/preview',json={'original':self.blocks,'blocks':bad})
        self.assertEqual(response.status_code,422)

    def test_ai_opt_in_disabled_and_source_validation(self):
        with patch.dict('os.environ',{'AI_ENABLED':'false'}):
            self.assertFalse(self.client.get('/capabilities').json()['aiEnabled'])
            self.assertEqual(self.client.post('/ai/review',json={'consent':False,'blocks':self.blocks}).status_code,400)
            self.assertEqual(self.client.post('/ai/review',json={'consent':True,'blocks':self.blocks}).status_code,503)
        blocks=[Block(**b) for b in self.blocks]
        sent=prepare_blocks(blocks)
        self.assertNotIn('contact',[b['id'] for b in sent])
        moves=validate_suggestions({'suggestions':[
            {'id':'job','section':'projects','reason':'A potential project'},
            {'id':'missing','section':'education','reason':'Invented ID'},
            {'id':'contact','section':'other','reason':'Do not send contact'},
            {'id':'job','section':'skills','reason':'Duplicate'},
        ]},blocks)
        self.assertEqual(len(moves),1)
        self.assertEqual(moves[0]['id'],'job')
        self.assertNotIn('text',moves[0])

    def test_ai_mocked_provider_roundtrip(self):
        import httpx
        class MockClient:
            async def __aenter__(self): return self
            async def __aexit__(self,*args): pass
            async def post(self,url,json,headers):
                self.body=json
                assert json['store'] is False
                assert 'jordan@example.com' not in json['input']
                payload={'suggestions':[{'id':'job','section':'projects','reason':'Example section move.'}]}
                return httpx.Response(200,json={'status':'completed','output':[
                    {'content':[{'type':'output_text','text':__import__('json').dumps(payload)}]}]},
                    request=httpx.Request('POST',url))
        with patch.dict('os.environ',{'AI_ENABLED':'true','OPENAI_API_KEY':'test-key','OPENAI_MODEL':'test-model'}), patch('backend.ai_review.httpx.AsyncClient',return_value=MockClient()):
            response=self.client.post('/ai/review',json={'consent':True,'blocks':self.blocks})
            self.assertEqual(response.status_code,200,response.text)
            self.assertEqual(response.json()['suggestions'][0]['section'],'projects')
