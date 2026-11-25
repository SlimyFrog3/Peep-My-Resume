from pathlib import Path
import unittest
from urllib.parse import urlsplit
from fastapi.testclient import TestClient
from backend.main import app
from backend.layout import Line
from backend.links import recover_links
from backend.parser import group_sections, parse_resume

ROOT = Path(__file__).resolve().parent.parent


class BetaTests(unittest.TestCase):
    def test_two_page_sidebar_records_and_links(self):
        p = ROOT / 'examples/beta-sidebar.pdf'
        response = TestClient(app).post('/parse', files={'file': (p.name, p.read_bytes())})
        self.assertEqual(response.status_code, 200)
        result = response.json()
        jobs = result['workExperience']
        self.assertEqual([j['organization'] for j in jobs], ['BRIGHT SAMPLE LABS', 'NEXT SAMPLE SYSTEMS', 'EXAMPLE COLLEGE'])
        self.assertEqual(jobs[0]['title'], 'QA MANAGER')
        self.assertEqual(jobs[0]['dates']['start'], {'value':'2022-11','precision':'month'})
        self.assertEqual(jobs[1]['dates']['start'], {'value':'2024','precision':'year'})
        self.assertEqual(jobs[1]['dates']['end']['precision'], 'present')
        self.assertTrue(any('page two' in text for text in jobs[1]['description']))
        self.assertEqual({line['page'] for line in jobs[1]['source']}, {1,2})
        self.assertEqual(result['languages'], ['Spanish'])
        self.assertIn('Java', result['skills'])
        self.assertIn('Selenium', result['skills'])
        self.assertEqual(result['educationRecords'][0]['institution'], 'Sample State University')
        self.assertEqual(result['educationRecords'][0]['date']['value'], '2022-05')
        self.assertTrue(any(cert['status']=='In progress' for cert in result['certificationRecords']))
        self.assertEqual({(urlsplit(link['url']).path,link['method']) for link in result['linkRecords']},
                         {('/in/morgan-demo','embedded'),('/morgan-demo','wrapped text')})
        self.assertEqual(result['parseCheck']['status'], 'looks_good')

    def test_headerless_work_history_and_bullet_not_employer(self):
        result = group_sections('Morgan Avery\nmorgan@example.com\nSAMPLE COMPANY 2022 - 2024\nQA MANAGER\n'
                                'Tested the dashboard & deployed\nLEAD SOFTWARE ENGINEER\nSample Client, Dallas June 2024 - Present')
        self.assertEqual([j['organization'] for j in result['workExperience']], ['SAMPLE COMPANY','Sample Client'])
        self.assertIn('Tested the dashboard & deployed',result['workExperience'][0]['description'])
        self.assertEqual(result['workExperience'][1]['location'],'Dallas')

    def test_link_wrap_refuses_unrelated_region_or_page(self):
        for following in [Line('projects',1,'right',2,(25,40,80,50)),
                          Line('projects',2,'left',1,(25,40,80,50)),
                          Line('projects',1,'left',2,(25,180,80,190))]:
            records, _, partial = recover_links(([Line('https://github.com/',1,'left',1,(25,21,100,32)),following],),[])
            self.assertEqual(records, [])
            self.assertEqual(partial, {'github.com'})

    def test_parse_check_levels_and_raw_fallback(self):
        good = parse_resume((ROOT/'examples/simple.docx').read_bytes(),'simple.docx')
        self.assertEqual(good['parseCheck']['status'],'looks_good')
        review = group_sections('Morgan Avery\nmorgan@example.com\nEXPERIENCE\nWorked as a contractor\nLINKS\nhttps://github.com/')
        self.assertEqual(review['parseCheck']['status'],'needs_review')
        self.assertEqual(review['unassignedExperience'],['Worked as a contractor'])
        self.assertFalse(review['links'])
        red = group_sections('No recognizable sections here.')
        self.assertEqual(red['parseCheck']['status'],'could_not_assess')
        self.assertIn('No recognizable sections here.',red['extractedText'])

    def test_employer_overview_is_explained_without_claiming_lost_text(self):
        result = group_sections(
            'Sam Example\nsam@example.com\nWORK EXPERIENCE\nFICTIONAL LABS 2015 - 2021\n'
            'Company-wide work\nQA MANAGER\nSample Client, Dallas June 2017 - July 2021'
        )
        self.assertEqual(result['unassignedExperience'], [])
        self.assertTrue(result['workExperience'][0]['isEmployerOverview'])
        self.assertEqual(result['workExperience'][1]['title'], 'QA MANAGER')
        self.assertEqual(result['parseCheck']['status'], 'looks_good')
        finding, = result['parseCheck']['observations']
        self.assertIn('FICTIONAL LABS as an employer overview', finding['message'])
        self.assertIn('leave it as is', finding['nextStep'])

    def test_distinct_review_findings_point_to_the_relevant_evidence(self):
        result = group_sections(
            'Sam Example\nsam@example.com\nEXPERIENCE\nWorked as a contractor\n'
            'EDUCATION\nSample State University\nLANGUAGES\nCustom list'
        )
        findings = {finding['section']: finding for finding in result['parseCheck']['findings']}
        self.assertEqual(set(findings), {'experience', 'education', 'other'})
        self.assertIn('Unassigned experience text', findings['experience']['nextStep'])
        self.assertIn('View source', findings['education']['nextStep'])
        self.assertIn('clearer heading', findings['other']['nextStep'])
        self.assertEqual(result['educationRecords'][0]['institution'], 'Sample State University')
        self.assertIsNone(result['educationRecords'][0]['qualification'])
        self.assertEqual(result['other'], ['Custom list'])

    def test_health_reports_beta(self):
        self.assertEqual(TestClient(app).get('/health').json()['version'],'4.0.3-beta')
