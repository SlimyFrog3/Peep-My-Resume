import unittest
from io import BytesIO
from base64 import b64decode
from unittest.mock import patch
from docx import Document
from fastapi.testclient import TestClient
from backend.main import app
from backend.parser import group_sections, parse_resume
from backend.workflow import Block, ReviewRequest, preview_export, check_records, prepare_blocks, export_docx
from backend.structured import record_spec, repair_suggestions

class RecordPreservationTests(unittest.TestCase):
    def setUp(self):
        self.blocks = [Block(id='name', section='contact', text='Taylor\nMorgan\ntaylor@example.com'),
          Block(id='education', section='education', text='Master of Science in Computer\nScience (SMU, Dallas)'),
          Block(id='job', section='experience', text='QA Engineer | Sample Labs | 2020 - 2022\n- Built high-\nquality checks.'),
          Block(id='cert1', section='certifications', text='Data Analytics\nCertificate\nBuilding Reports\nAccess controls and sharing'),
          Block(id='cert2', section='certifications', text='ISTQB (in progress)')]
        self.seeded = [Block(**{k:v for k,v in b.items() if k != 'suggestions'}) for b in prepare_blocks(self.blocks)]

    def test_all_templates_round_trip_records_name_and_words(self):
        for style in ('classic','modern','compact'):
            with self.subTest(style=style):
                p = preview_export(ReviewRequest(original=self.seeded,blocks=self.seeded,templateId=style))
                self.assertTrue(p['exportQuality']['passed'],p['recordCheck'])
                self.assertTrue(p['exportPreservesApprovedWords'])
                self.assertEqual(p['result']['readability']['score'],100)
                self.assertEqual(len(p['result']['certificationRecords']),2)
                self.assertEqual(p['result']['educationRecords'][0]['institution'],'SMU, Dallas')
                doc = Document(BytesIO(b64decode(p['docxBase64'])))
                self.assertEqual([p.text for p in doc.paragraphs if p.style.name=='Title'],['Taylor Morgan'])
                self.assertEqual([p.text for p in doc.paragraphs if p.style.name=='Heading 2'],['Data Analytics','ISTQB (in progress)'])

    def test_adjacent_education_pairs_do_not_borrow_each_others_school(self):
        blocks = [self.seeded[0], Block(id='a',section='education',text='Sample College\nCISCO Certified Network Associate, Networking · (2010 - 2011)'),
                  Block(id='b',section='education',text='Another College\nPre-Engineering, Mathematics and Computer Science'),
                  Block(id='c',section='education',text='Example University\nMathematics and Statistics · (March 2007 - December 2009)')]
        p=preview_export(ReviewRequest(original=blocks,blocks=blocks))
        self.assertTrue(p['exportQuality']['passed'],p['recordCheck'])
        records=p['result']['educationRecords']
        self.assertEqual([r['institution'] for r in records],['Sample College','Another College','Example University'])
        self.assertEqual(records[-1]['date']['value'],'2009-12')

    def test_wrapped_role_description_has_a_safe_repair_suggestion(self):
        text='QA Engineer | Sample Labs | 2020 - 2022\nBuilt reliable\ntools.'
        spec=record_spec('experience',text,{'organization':'Sample Labs','title':'QA Engineer','dates':{'raw':'2020 - 2022'},'description':['Built reliable tools.']})
        suggestions=repair_suggestions({'section':'experience','text':text,'record':spec})
        self.assertIn('Built reliable tools.',suggestions[0]['after'])
        self.assertIn('role descriptions',suggestions[0]['title'])

    def test_word_credential_title_soft_breaks_remain_one_record(self):
        doc=Document();doc.add_paragraph('Taylor Example');doc.add_paragraph('taylor@example.com')
        doc.add_heading('Certifications',level=1)
        doc.add_heading('Data Science & Big Data\nAnalytics: Making Data-\nDriven Decisions (Example Academy)',level=2)
        doc.add_paragraph('Built reports and explored clustering.')
        data=BytesIO();doc.save(data)
        result=parse_resume(data.getvalue(),'credential.docx')
        self.assertEqual(len(result['certificationRecords']),1)
        self.assertIn('Data-Driven Decisions',result['certificationRecords'][0]['name'])
        blocks=[Block(**{k:b[k] for k in ('id','section','text','record')}) for b in result['reviewBlocks']]
        preview=preview_export(ReviewRequest(original=blocks,blocks=blocks))
        self.assertTrue(preview['exportQuality']['passed'],preview['recordCheck'])

    def test_approved_name_capitalization_uses_one_title(self):
        block=Block(id='name',section='contact',text='Taylor Morgan\ntaylor@example.com',record={
            'kind':'contact','sourceText':'Taylor Morgan\ntaylor@example.com','fields':{'fullName':'TAYLOR MORGAN'}})
        p=preview_export(ReviewRequest(original=[block,self.seeded[1]],blocks=[block,self.seeded[1]]))
        self.assertTrue(p['exportQuality']['passed'])
        self.assertEqual(p['document']['sections'][0]['blocks'][0]['paragraphs'][0],{'kind':'name','text':'TAYLOR MORGAN'})

    def test_source_parser_seeds_fields_and_specific_repairs(self):
        r=group_sections('Taylor\nMorgan\ntaylor@example.com\nEducation\nMaster of Science in Computer\nScience (SMU, Dallas)')
        contact=next(b for b in r['reviewBlocks'] if b['section']=='contact')
        education=next(b for b in r['reviewBlocks'] if b['section']=='education')
        self.assertEqual(contact['record']['fields']['fullName'],'Taylor Morgan')
        self.assertIn('Taylor Morgan',contact['suggestions'][0]['after'])
        self.assertEqual(education['record']['fields']['institution'],'SMU, Dallas')
        self.assertIn('Computer Science',education['suggestions'][0]['after'])

    def test_structured_fields_need_literal_evidence(self):
        with self.assertRaises(ValueError):
            Block(id='x',section='education',text='Sample University',record={'kind':'education','sourceText':'Sample University','fields':{'qualification':'PhD'}})
        with self.assertRaises(ValueError):
            Block(id='x',section='contact',text='Taylor',record={'kind':'contact','sourceText':'Taylor','fields':{'credential':'Taylor'}})

    def test_stale_fields_are_rejected(self):
        payload=self.seeded[1].model_dump();payload['text']='Completely changed education'
        with self.assertRaises(ValueError): Block(**payload)

    def test_reprepare_does_not_restore_an_edited_away_field(self):
        edited=Block(id='education',section='education',text='Sample University')
        refreshed=prepare_blocks([edited],self.seeded)[0]
        self.assertNotIn('qualification',(refreshed['record'] or {}).get('fields',{}))

    def test_manual_assignment_of_existing_school_abbreviation(self):
        body={'id':'edu','section':'education','text':'BS Computer Science\nABC','record':{
            'kind':'education','sourceText':'BS Computer Science\nABC','fields':{'qualification':'BS Computer Science','institution':'ABC'}}}
        record=Block(**body)
        self.assertEqual(record.record.fields['institution'],'ABC')
        # The explicit approved pairing is rendered with a visible parenthetical institution.
        p=preview_export(ReviewRequest(original=[self.seeded[0],record],blocks=[self.seeded[0],record]))
        self.assertTrue(p['recordCheck']['passed'])
        self.assertEqual(p['result']['educationRecords'][0]['institution'],'ABC')

    def test_same_record_count_with_swapped_supporting_text_fails(self):
        blocks=[Block(id='a',section='experience',text='QA Engineer | Alpha Labs | 2020 - 2022\nBuilt release tools.'),
                Block(id='b',section='experience',text='QA Manager | Beta Labs | 2022 - Present\nManaged regional teams.')]
        data=export_docx(blocks)
        doc=Document(BytesIO(data))
        for p in doc.paragraphs:
            if p.text=='Built release tools.':p.text='Managed regional teams.'
            elif p.text=='Managed regional teams.':p.text='Built release tools.'
        out=BytesIO();doc.save(out)
        parsed=parse_resume(out.getvalue(),'changed.docx')
        self.assertEqual(len(parsed['workExperience']),2)
        self.assertFalse(check_records(blocks,parsed,doc)['passed'])

    def test_broken_certification_styles_detect_fragmentation(self):
        doc=Document(BytesIO(export_docx(self.seeded)))
        for p in doc.paragraphs:
            if p.style.name=='Heading 2':p.style='Normal'
        out=BytesIO();doc.save(out)
        parsed=parse_resume(out.getvalue(),'changed.docx')
        check=check_records(self.seeded,parsed,doc)
        self.assertFalse(check['passed'])
        self.assertIn('certifications',check['extraRecords'])

    def test_lost_name_style_fails_even_if_words_survive(self):
        doc=Document(BytesIO(export_docx(self.seeded)))
        for p in doc.paragraphs:
            if p.style.name=='Title':p.style='Normal'
        out=BytesIO();doc.save(out)
        self.assertFalse(check_records(self.seeded,parse_resume(out.getvalue(),'changed.docx'),doc)['passed'])

    def test_record_exclusion_is_compared_with_approved_content(self):
        chosen=[b.model_copy(deep=True) for b in self.seeded];chosen[-1].resolution='exclude'
        p=preview_export(ReviewRequest(original=self.seeded,blocks=chosen))
        self.assertTrue(p['exportQuality']['passed'])
        self.assertEqual(len(p['result']['certificationRecords']),1)
        self.assertGreater(p['coverage']['removedTokenCount'],0)

    def test_job_group_reordering_that_loses_parent_is_detected(self):
        r=group_sections('Taylor\ntaylor@example.com\nExperience\nEXAMPLE LABS 2015 - 2021\nCompany-wide work\nQA MANAGER\nSample Client, Dallas June 2017 - July 2021')
        blocks=[Block(**{k:b[k] for k in ('id','section','text','record')}) for b in r['reviewBlocks']]
        jobs=[b for b in blocks if b.section=='experience']
        self.assertEqual(jobs[1].record.fields['parentOrganization'],'EXAMPLE LABS')
        reordered=[b for b in blocks if b.section!='experience']+list(reversed(jobs))
        p=preview_export(ReviewRequest(original=blocks,blocks=reordered))
        self.assertFalse(p['recordCheck']['passed'])

    def test_complete_employer_group_is_information_not_missing_title(self):
        r=group_sections('Taylor\ntaylor@example.com\nExperience\nEXAMPLE LABS 2015 - 2021\nCompany-wide work\nQA MANAGER\nSample Client, Dallas June 2017 - July 2021')
        self.assertEqual(r['readability']['status'],'looks_good')
        self.assertTrue(r['parseCheck']['observations'])
        self.assertFalse(r['parseCheck']['reasons'])

    def test_quality_failure_blocks_direct_export_api(self):
        client=TestClient(app)
        body={'original':[b.model_dump() for b in self.seeded],'blocks':[b.model_dump() for b in self.seeded]}
        with patch('backend.main.preview_export',return_value={'exportQuality':{'passed':False}}):
            response=client.post('/review/export',json=body)
        self.assertEqual(response.status_code,422)
        self.assertIn('generated copy',response.json()['detail'])

    def test_prepare_route_returns_repairs_and_retains_source_fields(self):
        client=TestClient(app)
        body={'original':[b.model_dump() for b in self.seeded],'blocks':[b.model_dump() for b in self.blocks]}
        response=client.post('/review/prepare',json=body)
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['blocks'][1]['record']['fields']['institution'],'SMU, Dallas')
        self.assertTrue(response.json()['blocks'][0]['suggestions'])

    def test_score_regression_blocks_quality_even_with_same_records(self):
        import backend.parser as parser
        original=parser.parse_resume
        def lower(*args):
            r=original(*args);r['readability']['score']=50;return r
        with patch('backend.parser.parse_resume',side_effect=lower):
            p=preview_export(ReviewRequest(original=self.seeded,blocks=self.seeded))
        self.assertFalse(p['exportQuality']['passed'])
        self.assertFalse(p['exportQuality']['scoreDidNotDecrease'])
