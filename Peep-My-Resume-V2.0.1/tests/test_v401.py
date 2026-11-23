from base64 import b64decode
from io import BytesIO
from unittest.mock import patch
import unittest
from docx import Document
from fastapi.testclient import TestClient
from backend.main import app
from backend.parser import group_sections
from backend.scoring import score_result
from backend.templates import TEMPLATES
from backend.workflow import Block, ReviewRequest, SECTION_TITLES, export_docx, preview_export

class Release401Tests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.blocks = [
            {'id':'name', 'section':'contact', 'text':'Taylor Example\ntaylor@example.com'},
            {'id':'jobA', 'section':'experience', 'text':'QA Engineer | Sample Labs | 2022 - Present\n- Built tests.'},
            {'id':'jobB', 'section':'experience', 'text':'QA Analyst | Sample Systems | 2020 - 2022\n- Reviewed releases.'},
            {'id':'skill', 'section':'skills', 'text':'Python, SQL'},
        ]

    def test_no_external_ai_routes_or_configuration(self):
        paths=self.client.get('/openapi.json').json()['paths']
        self.assertNotIn('/ai/review',paths)
        self.assertNotIn('aiEnabled', self.client.get('/capabilities').json())
        self.assertEqual(self.client.get('/health').json()['version'],'4.0.1-beta')

    def test_three_template_choices_and_muted_green(self):
        choices=self.client.get('/templates').json()['templates']
        self.assertEqual([t['name'] for t in choices], ['Classic Professional','Modern Accent','Compact Professional'])
        self.assertEqual(TEMPLATES['modern']['accent'],'#527766')
        self.assertEqual(len({t['font'] for t in choices}),3)

    def test_all_templates_preserve_exact_approved_words(self):
        for template in TEMPLATES:
            with self.subTest(template=template):
                request=ReviewRequest(original=self.blocks,blocks=self.blocks,templateId=template)
                preview=preview_export(request)
                self.assertTrue(preview['exportPreservesApprovedWords'])
                self.assertEqual(preview['coverage']['retainedPercent'],100)
                data=b64decode(preview['docxBase64'])
                doc=Document(BytesIO(data))
                self.assertFalse(doc.tables)
                self.assertFalse(doc.styles.element.xpath('.//w:pBdr'))
                self.assertEqual([s['key'] for s in preview['document']['sections']],['contact','experience','skills'])
                self.assertIn('QA Engineer | Sample Labs | 2022 - Present',[p.text for p in doc.paragraphs])

    def test_user_section_and_entry_order_is_respected(self):
        order=['skills','experience','contact']+[k for k in SECTION_TITLES if k not in {'skills','experience','contact'}]
        blocks=[self.blocks[0],self.blocks[2],self.blocks[1],self.blocks[3]]
        preview=preview_export(ReviewRequest(original=self.blocks,blocks=blocks,sectionOrder=order))
        model=preview['document']
        self.assertEqual([s['key'] for s in model['sections']],['skills','experience','contact'])
        self.assertEqual([b['id'] for b in model['sections'][1]['blocks']],['jobB','jobA'])
        paragraphs=[p.text for p in Document(BytesIO(b64decode(preview['docxBase64']))).paragraphs]
        self.assertLess(paragraphs.index('Python, SQL'),paragraphs.index('QA Analyst | Sample Systems | 2020 - 2022'))
        self.assertLess(paragraphs.index('QA Analyst | Sample Systems | 2020 - 2022'),paragraphs.index('QA Engineer | Sample Labs | 2022 - Present'))

    def test_unplaced_content_requires_explicit_decision(self):
        unknown={'id':'unknown','section':'other','text':'An important source sentence.','resolution':'pending'}
        body={'original':self.blocks+[unknown],'blocks':self.blocks+[unknown]}
        preview=self.client.post('/review/preview',json=body).json()
        self.assertEqual(preview['unresolvedBlocks'],['unknown'])
        self.assertEqual(self.client.post('/review/export',json=body).status_code,422)
        unknown['resolution']='include'
        response=self.client.post('/review/export',json=body)
        self.assertEqual(response.status_code,200)
        self.assertIn('An important source sentence.',[p.text for p in Document(BytesIO(response.content)).paragraphs])

    def test_exclusion_is_reversible_and_reported_as_omission(self):
        approved=[dict(b) for b in self.blocks]
        approved[1]['resolution']='exclude'
        preview=preview_export(ReviewRequest(original=self.blocks,blocks=approved))
        self.assertGreater(preview['coverage']['removedTokenCount'],0)
        self.assertTrue(preview['exportPreservesApprovedWords'])
        self.assertNotIn('jobA',[b['id'] for s in preview['document']['sections'] for b in s['blocks']])

    def test_invalid_template_or_section_order_is_rejected(self):
        for extra in [{'templateId':'unknown'},{'sectionOrder':['contact','contact']},{'sectionOrder':[]}]:
            response=self.client.post('/review/preview',json={'original':self.blocks,'blocks':self.blocks,**extra})
            self.assertEqual(response.status_code,422)

    def test_high_score_with_finding_stays_yellow_with_reason(self):
        r=group_sections('Taylor Example\ntaylor@example.com\nSKILLS\nPython')
        r['parseCheck']={'status':'needs_review','reasons':['Please confirm the source.'],'findings':[
            {'message':'Please confirm the source.','nextStep':'Compare the entry with the original.'}]}
        score=score_result(r)
        self.assertEqual(score['score'],100)
        self.assertEqual(score['status'],'needs_review')
        self.assertFalse(score['greenChecklist'][1]['met'])
        self.assertEqual(score['greenChecklist'][1]['action'],'Compare the entry with the original.')

    def test_green_and_unassessable_states(self):
        r=group_sections('Taylor Example\ntaylor@example.com\nSKILLS\nPython')
        self.assertEqual(r['readability']['status'],'looks_good')
        self.assertTrue(all(item['met'] for item in r['readability']['greenChecklist']))
        self.assertIsNone(group_sections('Unrecognizable text')['readability']['score'])

    def test_score_thresholds_54_55_89_90(self):
        # Patch only category rounding to isolate exact presentation boundaries.
        r=group_sections('Taylor Example\ntaylor@example.com\nSKILLS\nPython')
        for total,status in [(54,'needs_attention'),(55,'needs_review'),(89,'needs_review'),(90,'looks_good')]:
            with self.subTest(total=total), patch('builtins.round',side_effect=[total-20,0,0]):
                score=score_result(r)
                self.assertEqual(score['score'],total)
                self.assertEqual(score['status'],status)

    def test_no_praise_for_absent_records(self):
        r=group_sections('Taylor Example\ntaylor@example.com\nSKILLS\nPython')
        records=next(c for c in r['readability']['categories'] if c['key']=='records')
        self.assertFalse(records['assessed'])
        self.assertIsNone(records['strength'])
        self.assertEqual(records['status'],'not_assessed')

    def test_parser_flags_unknown_blocks_for_placement(self):
        r=group_sections('Taylor Example\ntaylor@example.com\nSKILLS\nPython\nREFERENCES\nAvailable on request')
        other=next(b for b in r['reviewBlocks'] if b['section']=='other')
        self.assertEqual(other['resolution'],'pending')

    def test_long_template_exports_remain_complete(self):
        blocks=[Block(**self.blocks[0])]+[
            Block(id=f'job{i}',section='experience',text=f'QA Engineer | Example Team {i} | 2020 - 2022\n'+'\n'.join(f'- Tested release {j} and documented every finding.' for j in range(12)))
            for i in range(10)]
        for template in TEMPLATES:
            preview=preview_export(ReviewRequest(original=blocks,blocks=blocks,templateId=template))
            self.assertTrue(preview['exportPreservesApprovedWords'])
            self.assertEqual(preview['coverage']['retainedPercent'],100)
