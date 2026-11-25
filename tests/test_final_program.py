import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from services.database import initialize, query, connect
from services.final_program import initialize_final, assurance_snapshot, update_external_finding, record_risk_decision
from views.program import run_benchmark
from services.project_exports import dashboard_pdf, automation_pdf, final_report_pdf, register_zip


class FinalProgramTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.enterContext(patch.dict(os.environ,{'PASS_DB_PATH':str(Path(temporary.name)/'test.sqlite3')}))
        initialize();initialize_final()

    def test_baseline_and_independent_audit_are_reproducible(self):
        snapshot=assurance_snapshot()
        self.assertEqual(len(snapshot['risks']),16)
        self.assertEqual(sum(r['score'] for r in snapshot['risks']),229)
        self.assertEqual(snapshot['high_critical'],15)
        self.assertAlmostEqual(snapshot['audit_score'],44.46)
        counts={level:sum(r['severity']==level for r in snapshot['findings']) for level in ('High','Medium','Low','Critical')}
        self.assertEqual(counts,{'High':5,'Medium':7,'Low':1,'Critical':0})
        self.assertEqual(len(query('SELECT * FROM project_coverage')),27)
        self.assertEqual(len(query('SELECT * FROM recovery_design')),16)
        self.assertEqual(len(query('SELECT * FROM audit_test_plan')),15)

    def test_import_preserves_saved_reviews_and_assessments(self):
        with connect() as con:
            con.execute("UPDATE external_findings SET response='Saved management response' WHERE id='F-01'")
            con.execute("UPDATE maturity_scores SET score=4 WHERE dimension='IAM'")
        initialize_final()
        self.assertEqual(query("SELECT response FROM external_findings WHERE id='F-01'")[0]['response'],'Saved management response')
        self.assertEqual(query("SELECT score FROM maturity_scores WHERE dimension='IAM'")[0]['score'],4)

    def test_finding_closure_requires_verified_linked_evidence(self):
        with self.assertRaises(ValueError):update_external_finding('F-01','Done','Closed','','','')
        with self.assertRaises(ValueError):update_external_finding('F-01','Done','Closed','DOC-A1','Reviewer','2026-11-22')
        with connect() as con:
            con.execute("INSERT INTO evidence (id,description,status,finding_id) VALUES ('TEST-E','Control test record','Verified','EXT-F-01')")
        update_external_finding('F-01','Re-tested','Closed','TEST-E','Independent reviewer','2026-11-22')
        self.assertEqual(query("SELECT status FROM external_findings WHERE id='F-01'")[0]['status'],'Closed')
        with self.assertRaises(ValueError):update_external_finding('F-02','Done','Closed','TEST-E','Reviewer','2026-11-22')

    def test_risk_acceptance_requires_evidence_and_review(self):
        with self.assertRaises(ValueError):record_risk_decision('R10','Accept','','',None,None,None)
        with self.assertRaises(ValueError):record_risk_decision('R10','Accept','Basis','Board','2026-11-22','2026-12-22','DOC-A1')
        record_risk_decision('R10','Escalate','Needs treatment','CISO','2026-11-22','2026-12-22',None)
        self.assertEqual(query("SELECT decision FROM risk_decisions WHERE risk_id='R10'")[0]['decision'],'Escalate')

    def test_machine_benchmark_does_not_invent_human_evaluation(self):
        cases=run_benchmark()
        self.assertEqual(len(cases),18)
        self.assertEqual(sum(c[3] for c in cases),18)
        self.assertEqual(query('SELECT COUNT(*) AS n FROM ai_evaluations')[0]['n'],0)
        snapshot=assurance_snapshot()
        self.assertIsNone(snapshot['gain'])
        self.assertIsNone(snapshot['ai_accuracy'])
        self.assertEqual(snapshot['controls_assessed'],0)

    def test_submission_exports_are_generated(self):
        run_benchmark()
        for export in (dashboard_pdf,automation_pdf,final_report_pdf):
            self.assertTrue(export().startswith(b'%PDF-'))
        import zipfile
        from io import BytesIO
        with zipfile.ZipFile(BytesIO(register_zip())) as archive:
            for name in ('assets.csv','risks.csv','controls.csv','compliance_requirements.csv','evidence.csv','risk_decisions.csv'):
                self.assertIn(name,archive.namelist())

    def test_dashboard_counts_external_actions_and_updates_on_closure(self):
        self.assertEqual(assurance_snapshot()['open_corrective_actions'],13)
        with connect() as con:
            con.execute("UPDATE corrective_actions SET status='Closed'")
        self.assertEqual(assurance_snapshot()['open_corrective_actions'],13)
        with connect() as con:
            con.execute("INSERT INTO evidence (id,description,status,finding_id) VALUES ('CLOSE-E','Reviewed test','Verified','EXT-F-04')")
        update_external_finding('F-04','Re-tested','Closed','CLOSE-E','Independent reviewer','2026-11-23')
        snapshot=assurance_snapshot()
        self.assertEqual(snapshot['open_corrective_actions'],12)
        self.assertEqual(snapshot['closed_findings'],1)
        from services.final_program import executive_recommendations
        self.assertNotIn('F-04',[r['id'] for r in executive_recommendations(snapshot['findings'])])

    def test_unassessed_effectiveness_differs_from_measured_zero(self):
        self.assertIsNone(assurance_snapshot()['control_effectiveness'])
        with connect() as con:
            con.execute("UPDATE controls SET effectiveness='Ineffective' WHERE id='C10'")
        self.assertEqual(assurance_snapshot()['control_effectiveness'],0)
        with connect() as con:
            con.execute("UPDATE controls SET effectiveness='Effective' WHERE id='C10'")
        self.assertAlmostEqual(assurance_snapshot()['control_effectiveness'],100/15)
