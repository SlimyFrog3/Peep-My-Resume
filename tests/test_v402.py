import unittest
from io import BytesIO
from unittest.mock import patch
from docx import Document
from backend.layout import Line
from backend.parser import group_sections
from backend.records import _period, _name
from backend.workflow import Block, ReviewRequest, paragraphs_for, preview_export, export_docx, inspect_section_spacing
from backend.templates import TEMPLATES

class LinkedInRegressionTests(unittest.TestCase):
    def test_duration_annotations_are_not_mistaken_for_employer_text(self):
        result=group_sections('Taylor Example\ntaylor@example.com\nExperience\n'
          'Example Labs\n3 years 3 months\nSenior QA Manager\nAugust 2021 - Present (2 years 9 months)\n'
          'Montreal, Quebec, Canada\nManaged release testing.\nQA Manager\nFebruary 2021 - August 2021 (7 months)\n'
          'Another Systems\n9 years\nQA Manager\nMarch 2018 - February 2021 (3 years)\n'
          'A final sentence about leadership.\nLead Quality Analyst\nSeptember 2016 - May 2018 (1 year 9 months)')
        jobs=result['workExperience']
        self.assertEqual([j['organization'] for j in jobs],['Example Labs','Example Labs','Another Systems','Another Systems'])
        self.assertEqual([j['title'] for j in jobs],['Senior QA Manager','QA Manager','QA Manager','Lead Quality Analyst'])
        self.assertEqual(result['unassignedExperience'],[])
        self.assertEqual(jobs[0]['dates']['end']['precision'],'present')
        self.assertIn('3 years 3 months', [s['text'] for s in jobs[0]['source']])

    def test_only_recognized_duration_suffix_is_accepted(self):
        self.assertIsNotNone(_period('March 2020 - May 2022 (2 years 3 months)'))
        self.assertIsNone(_period('March 2020 - May 2022 (performed testing and analysis)'))
        self.assertIsNone(_period('March 2020 - May 2022 Led a testing team'))

    def test_narrative_sentence_is_not_an_employer(self):
        self.assertFalse(_name('data analysis and trend interpretation.'))
        self.assertFalse(_name('leadership.'))
        self.assertTrue(_name('Sample Co.'))

    def test_missing_employer_is_not_invented(self):
        result=group_sections('Taylor\ntaylor@example.com\nExperience\nQA Manager\n2020 - 2022 (2 years)')
        self.assertIsNone(result['workExperience'][0]['organization'])
        self.assertTrue(any('employer' in s for s in result['parseCheck']['reasons']))

    def test_ordinary_previous_job_does_not_supply_missing_employer(self):
        result=group_sections('Taylor\ntaylor@example.com\nExperience\n'
          'QA Engineer | Sample Labs | 2020 - 2022\nBuilt checks.\n'
          'QA Manager\n2022 - Present (2 years)')
        self.assertEqual(result['workExperience'][0]['organization'],'Sample Labs')
        self.assertIsNone(result['workExperience'][1]['organization'])
        self.assertTrue(result['parseCheck']['reasons'])

    def test_education_credential_stays_with_its_institution(self):
        result=group_sections('Taylor\ntaylor@example.com\nEducation\nSample College\n'
                             'CISCO Certified Network Associate, Networking · (2010 - 2011)')
        record,=result['educationRecords']
        self.assertEqual(record['institution'],'Sample College')
        self.assertIn('CISCO Certified Network Associate', record['qualification'])
        self.assertFalse(result['certifications'])
        self.assertEqual(result['readability']['score'],100)

    def test_program_does_not_invent_awarded_degree(self):
        result=group_sections('Taylor\ntaylor@example.com\nEducation\nSample University\n'
                             'Mathematics and Statistics · (March 2007 - December 2009)')
        record,=result['educationRecords']
        self.assertIsNone(record['qualification'])
        self.assertEqual(record['program'],'Mathematics and Statistics · (March 2007 - December 2009)')
        self.assertFalse(result['parseCheck']['reasons'])
        self.assertEqual(result['readability']['rubricVersion'],'1.1')

    def test_school_only_still_requires_review(self):
        result=group_sections('Taylor\ntaylor@example.com\nEducation\nSample University')
        self.assertTrue(any('qualification/program' in s for s in result['parseCheck']['reasons']))

    def test_export_preserves_link_boundaries(self):
        block=Block(id='links',section='links',text='https://www.linkedin.com/in/taylor?tracking=example\nhttps://www.linkedin.com/in/taylor')
        items=paragraphs_for(block)
        self.assertEqual(len(items),2)
        self.assertTrue(all(item['kind']=='link' for item in items))
        result=group_sections('Taylor\ntaylor@example.com\nLinks\n'+block.text)
        self.assertEqual(len(result['links']),2)
        self.assertFalse(result['other'])

    def test_previous_joined_pure_urls_are_not_unclassified(self):
        result=group_sections('Taylor\ntaylor@example.com\nSkills\nPython\nLinks\n'
                             'https://github.com/taylor https://linkedin.com/in/taylor')
        self.assertEqual(len(result['links']),2)
        self.assertFalse(result['other'])

    def test_url_with_explanatory_prose_is_preserved(self):
        result=group_sections('Taylor\ntaylor@example.com\nAdditional Information\n'
                             'See the demo at https://github.com/taylor for details.')
        self.assertTrue(any('See the demo' in text for text in result['other']))

    def test_all_styles_have_real_section_spacing_and_preserve_words(self):
        blocks=[Block(id='contact',section='contact',text='Taylor Example\ntaylor@example.com'),
                Block(id='jobs',section='experience',text='Example Labs\n3 years 3 months\nSenior QA Manager\nAugust 2021 - Present (2 years 9 months)\nManaged release testing.'),
                Block(id='education',section='education',text='Sample University\nMathematics and Statistics')]
        for template in TEMPLATES:
            with self.subTest(template=template):
                result=preview_export(ReviewRequest(original=blocks,blocks=blocks,templateId=template))
                self.assertTrue(result['formattingCheck']['passed'])
                self.assertEqual(result['formattingCheck']['headingCount'],2)
                self.assertTrue(result['exportPreservesApprovedWords'])
                self.assertEqual(result['result']['workExperience'][0]['organization'],'Example Labs')
                self.assertEqual(result['result']['readability']['score'],100)

    def test_bad_section_spacing_is_detected_not_awarded_automatic_pass(self):
        blocks=[Block(id='skills',section='skills',text='Python')]
        config={**TEMPLATES['compact'],'headingBefore':0}
        with patch.dict(TEMPLATES,{'compact':config}):
            doc=Document(BytesIO(export_docx(blocks,'compact')))
        self.assertFalse(inspect_section_spacing(doc)['passed'])

    def test_nested_role_and_short_subheadings_are_styled(self):
        block=Block(id='job',section='experience',text='Example Labs\n3 years 3 months\nQA Manager\n2021 - Present (2 years)\nKey Achievements:\nBuilt automated checks.')
        paragraphs=paragraphs_for(block)
        self.assertEqual([p['kind'] for p in paragraphs[:5]],['entry','tenure','entry','date','subheading'])
