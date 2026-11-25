"""Assignment-backed final-program additions and independent audit provenance."""
import json
from pathlib import Path
from services.database import connect, query

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'A4 third-party documentary audit, IA_A4_23i2116-23i2127-23i2079.docx'
SCHEMA = '''
CREATE TABLE IF NOT EXISTS final_imports (version INTEGER PRIMARY KEY);
CREATE TABLE IF NOT EXISTS external_findings (
 id TEXT PRIMARY KEY, severity TEXT NOT NULL, title TEXT NOT NULL, observation TEXT NOT NULL,
 evidence_refs TEXT, recommendation TEXT NOT NULL, owner TEXT, period_days TEXT,
 response TEXT, status TEXT NOT NULL DEFAULT 'Open', closure_evidence TEXT, reviewer TEXT, reviewed_on TEXT,
 source TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS audit_heads (id INTEGER PRIMARY KEY, head TEXT, weight REAL, points REAL);
CREATE TABLE IF NOT EXISTS audit_tests (id TEXT PRIMARY KEY, objective TEXT, outcome TEXT, basis TEXT, source TEXT);
CREATE TABLE IF NOT EXISTS program_sections (id TEXT PRIMARY KEY, title TEXT, content TEXT, source TEXT, status TEXT);
CREATE TABLE IF NOT EXISTS audit_test_plan (control_id TEXT PRIMARY KEY REFERENCES controls(id), risk_ids TEXT,
 test_procedure TEXT, pass_criterion TEXT, evidence_needed TEXT, owner TEXT, frequency TEXT);
CREATE TABLE IF NOT EXISTS recovery_design (asset_id TEXT PRIMARY KEY REFERENCES assets(id), dependencies TEXT,
 proposed_rto TEXT, proposed_rpo TEXT, fallback TEXT, acceptance_test TEXT, status TEXT, proposed_mtd TEXT, business_impact TEXT, data_classification TEXT);
CREATE TABLE IF NOT EXISTS project_coverage (component TEXT PRIMARY KEY, route TEXT, source TEXT, status TEXT, remaining_evidence TEXT);
CREATE TABLE IF NOT EXISTS supplier_reviews (id TEXT PRIMARY KEY, service TEXT, owner TEXT, data_access TEXT,
 requirements TEXT, evidence_request TEXT, residual_concern TEXT, status TEXT);
CREATE TABLE IF NOT EXISTS project_benchmark (id TEXT PRIMARY KEY, expected TEXT, observed TEXT,
 passed INTEGER, elapsed_seconds REAL, scope TEXT);
CREATE TABLE IF NOT EXISTS risk_decisions (risk_id TEXT PRIMARY KEY REFERENCES risks(id), proposed_owner TEXT,
 decision TEXT, rationale TEXT, approved_by TEXT, decision_date TEXT, review_date TEXT, evidence_id TEXT REFERENCES evidence(id));
CREATE TABLE IF NOT EXISTS external_finding_evidence (finding_id TEXT REFERENCES external_findings(id),
 evidence_id TEXT REFERENCES evidence(id), PRIMARY KEY(finding_id,evidence_id));
'''


def initialize_final():
    with connect() as con:
        con.executescript(SCHEMA)
        if con.execute('SELECT 1 FROM final_imports WHERE version=1').fetchone():
            initialize_external_links()
            return
        data = json.loads((ROOT / 'data/seed/final_program.json').read_text(encoding='utf-8'))
        for table, rows in data.items():
            for row in rows:
                columns = ','.join(row)
                placeholders = ','.join('?' for _ in row)
                con.execute(f'INSERT OR IGNORE INTO {table} ({columns}) VALUES ({placeholders})', tuple(row.values()))
        for row in con.execute('SELECT id, evidence_requirement, owner FROM controls').fetchall():
            control_id, evidence, owner = row
            risks = [r[0] for r in con.execute('SELECT risk_id FROM risk_controls WHERE control_id=?', (control_id,))]
            tests = CONTROL_TESTS.get(control_id, ('Inspect configuration and reperform the control on synthetic data.', 'Expected authorization, integrity and availability conditions hold.'))
            con.execute('INSERT OR IGNORE INTO audit_test_plan VALUES (?,?,?,?,?,?,?)',
                        (control_id, ', '.join(risks), tests[0], tests[1], evidence, owner or 'CISO with system owner', 'Quarterly and after material change'))
        scores = {'Governance':2, 'Risk Management':3, 'IAM':3, 'Data Protection':2,
                  'Incident Response':3, 'BC/DR':2, 'AI Governance':2, 'OT Security':2,
                  'Supply Chain':2, 'Audit':1}
        for dimension, score in scores.items():
            con.execute('UPDATE maturity_scores SET score=?, rationale=?, assessor=?, assessed_on=?, source=? WHERE dimension=? AND score IS NULL',
                (score, 'Documentary self-assessment using A1-A3 and independent A4. Scale: 1 Initial, 2 Repeatable/partial, 3 Defined, 4 Measured, 5 Optimized. No operating validation claimed.',
                 'Final-project documentary assessment; reviewer sign-off pending', '2026-11-22', 'A1-A4; final-project rubric', dimension))
        for risk in con.execute('SELECT r.id,a.owner FROM risks r LEFT JOIN assets a ON a.id=r.asset_id').fetchall():
            con.execute('INSERT OR IGNORE INTO risk_decisions (risk_id,proposed_owner,decision) VALUES (?,?,?)',
                        (risk[0], risk[1] or 'CISO / Risk and Compliance', 'Pending review'))
        owners = {'Public':'Stadium Operations', 'Internal':'Business information owner',
                  'Confidential':'CIO / Business owner', 'Restricted':'Privacy / Data owner', 'Critical':'CIO / Facilities / CISO'}
        for classification, owner in owners.items():
            con.execute('UPDATE data_items SET owner=? WHERE classification=? AND owner IS NULL',
                        ('Proposed: '+owner, classification))
        con.execute('INSERT INTO final_imports VALUES (1)')
    initialize_external_links()


def initialize_external_links():
    """Add documentary audit evidence links without assigning operating verdicts."""
    with connect() as con:
        if con.execute('SELECT 1 FROM final_imports WHERE version=2').fetchone():
            con.execute("UPDATE project_coverage SET route='Submission & Coverage' WHERE route='Program Completion'")
            return
        titles=['Organization profile','Governance roles','Asset inventory','Risk register and rationale',
                'Treatment estimates','Control matrix','Compliance heat map','Initial audit plan',
                'Assurance priorities','Auditor recalculations','IAM design','Data classifications',
                'Recovery design','Ransomware response','Operational checklist']
        for index,title in enumerate(titles,1):
            con.execute('INSERT OR IGNORE INTO evidence (id,type,description,owner,status,source) VALUES (?,?,?,?,?,?)',
                        (f'EXT-E-{index:02d}','Documentary source',title,'Independent auditors / Group 10','Collected',f'A4 evidence E-{index:02d}; docs/sources/A4.txt'))
        links={'F-01':[6,15],'F-02':[5,8,15],'F-03':[5,6,10],'F-04':[3,13,14],
               'F-05':[11,12,13,14,15],'F-06':[6,7,12],'F-07':[1,4,5],
               'F-08':[3,4,11],'F-09':[6,11,12,13,14],'F-10':[3,12],
               'F-11':[5,7,15],'F-12':[1,2,3,11,12,13,14,15],'F-13':[13,14,15]}
        for finding,indices in links.items():
            con.executemany('INSERT OR IGNORE INTO external_finding_evidence VALUES (?,?)',
                            [(finding,f'EXT-E-{index:02d}') for index in indices])
        con.execute('INSERT INTO final_imports VALUES (2)')
        con.execute("UPDATE project_coverage SET route='Submission & Coverage' WHERE route='Program Completion'")


CONTROL_TESTS = {
 'C01': ('In a lab, compare authorized-load and rate-limit logs for ticketing.', 'Approved traffic passes; excessive requests are limited and alerted.'),
 'C02': ('Submit one synthetic ticket twice and test a revoked ticket.', 'First valid use passes; replay and revoked ticket are rejected and logged.'),
 'C03': ('Inspect POS patch/EDR records and attempt an unapproved network path in a lab.', 'POS is current and only approved payment paths work.'),
 'C04': ('Test guest-to-staff and guest-to-OT paths using approved synthetic probes.', 'Unapproved cross-zone traffic is denied and logged.'),
 'C05': ('Inspect CCTV administrative MFA, firmware and recording permissions.', 'Only named authorized roles can administer or export recordings.'),
 'C06': ('Reperform sponsored vendor access and safe isolation in an OT test environment.', 'MFA, approval, expiry and logging work; isolation retains approved safe operation.'),
 'C07': ('Submit sensor data using an unregistered identity and a modified payload in a simulator.', 'Untrusted identity/payload is rejected or flagged.'),
 'C09': ('Review cloud storage visibility, privileged grants, secret storage and change history.', 'No unintended public access; least privilege and traceable changes.'),
 'C10': ('Test privileged MFA, joiner/mover/leaver changes and reviewer sign-off.', 'MFA enforced; stale access removed; reviews identify owners and exceptions.'),
 'C11': ('Walk a ransomware tabletop from detection through restoration with operations present.', 'Owners act against the approved timeline; evidence is retained and safety gates applied.'),
 'C12': ('Use synthetic spectators to test database access, export monitoring and encryption.', 'Unauthorized reads/exports fail; authorized exports are attributable and encrypted.'),
 'C13': ('Review supplier questionnaire, contract clauses and a vendor access lifecycle.', 'Sponsor, scope, MFA, expiry, logs and incident obligations are evidenced.'),
 'C14': ('Restore a protected backup in an isolated environment and measure time/data loss.', 'Integrity check succeeds; measured RTO/RPO meet the approved targets.'),
 'C15': ('Inject labeled test events from IAM, endpoint, cloud and selected OT sources.', 'Required sources arrive with correct clocks; expected alerts reach the SOC.'),
 'C16': ('Run fixed, negative, ambiguous and malicious-input recommendation cases.', 'Outputs use catalog IDs; uncertain cases go to human review; no automatic high-impact action.'),
}


def update_external_finding(finding_id, response, status, evidence, reviewer, reviewed_on):
    if status == 'Closed' and not all((evidence.strip(), reviewer.strip(), reviewed_on)):
        raise ValueError('Closing a finding requires closure evidence, a reviewer and review date.')
    with connect() as con:
        if status == 'Closed':
            row = con.execute('SELECT status FROM evidence WHERE id=?', (evidence.strip(),)).fetchone()
            if row is None or row[0] != 'Verified':
                raise ValueError('Select a Verified Evidence Register ID before closing the finding.')
            linked = con.execute('SELECT finding_id FROM evidence WHERE id=?', (evidence.strip(),)).fetchone()
            if linked[0] != 'EXT-'+finding_id:
                raise ValueError('Closure evidence must be linked to EXT-'+finding_id+' in the Evidence Register.')
        con.execute('UPDATE external_findings SET response=?,status=?,closure_evidence=?,reviewer=?,reviewed_on=? WHERE id=?',
                    (response, status, evidence, reviewer, reviewed_on, finding_id))


def record_risk_decision(risk_id, decision, rationale, approver, decision_date, review_date, evidence):
    if decision == 'Accept' and not all((rationale.strip(), approver.strip(), decision_date, review_date, evidence)):
        raise ValueError('Risk acceptance requires a rationale, approver, decision/review dates and verified supporting evidence.')
    if decision_date and review_date and review_date <= decision_date:
        raise ValueError('The review date must be later than the decision date.')
    with connect() as con:
        if decision == 'Accept':
            status = con.execute('SELECT status,control_id FROM evidence WHERE id=?', (evidence,)).fetchone()
            if status is None or status[0] != 'Verified':
                raise ValueError('Acceptance evidence must be Verified in the Evidence Register.')
            linked = con.execute('SELECT 1 FROM risk_controls WHERE risk_id=? AND control_id=?', (risk_id,status[1])).fetchone()
            if linked is None:
                raise ValueError('Acceptance evidence must support a control linked to this risk.')
        con.execute('UPDATE risk_decisions SET decision=?,rationale=?,approved_by=?,decision_date=?,review_date=?,evidence_id=? WHERE risk_id=?',
                    (decision,rationale,approver,decision_date,review_date,evidence or None,risk_id))


def assurance_snapshot():
    from services.calculations import ai_accuracy, evaluation_gain, maturity, percentage, recovery_outcome, recovery_readiness, control_effectiveness, compliance, pisf_clauses
    from services.database import recovery_services
    risks = query('SELECT *, likelihood*impact AS score FROM risks ORDER BY score DESC, impact DESC, id')
    controls = query('SELECT * FROM controls WHERE applicable=1')
    requirements = query("SELECT * FROM compliance_requirements WHERE applicable=1 AND (clause_ref IS NULL OR clause_ref='')")
    dimensions = query('SELECT * FROM maturity_scores')
    scores = {r['dimension']: r['score'] for r in dimensions}
    evals = query('SELECT * FROM ai_evaluations')
    verified = [r for r in evals if r['human_verified'] and r['correct'] is not None]
    paired = [r for r in evals if r['human_verified'] and r['manual_seconds'] is not None and r['ai_seconds'] is not None]
    findings = query('SELECT * FROM external_findings ORDER BY id')
    return {
      'risk_mean': sum(r['score'] for r in risks)/len(risks) if risks else None, 'risks':risks,
      'high_critical':sum(r['score']>=10 for r in risks),
      'maturity':maturity(scores.values()), 'scores':scores,
      'control_effectiveness':control_effectiveness(controls),
      'controls_assessed':sum(r['effectiveness'] in ('Effective','Ineffective') for r in controls), 'controls_total':len(controls),
      'compliance':compliance(requirements), 'requirements_total':len(requirements),
      'pisf_compliance':compliance(pisf_clauses(query('SELECT * FROM compliance_requirements'))),
      'critical_gaps':query("SELECT COUNT(DISTINCT c.id) AS n FROM controls c JOIN risk_controls m ON m.control_id=c.id JOIN risks r ON r.id=m.risk_id WHERE c.applicable=1 AND c.status='Gap' AND r.likelihood*r.impact>=17")[0]['n'],
      'findings':findings, 'audit_score':sum(r['points'] for r in query('SELECT points FROM audit_heads')),
      'open_corrective_actions':sum(row['status'] != 'Closed' for row in findings),
      'closed_findings':sum(row['status'] == 'Closed' for row in findings),
      'bcdr':recovery_readiness([recovery_outcome(r) for r in recovery_services()]),
      'ai_accuracy':ai_accuracy(evals), 'gain':evaluation_gain(evals),
      'correct':sum(r['correct']==1 for r in verified), 'incorrect':sum(r['correct']==0 for r in verified), 'reviewed':len(verified),
      'verification_rate':percentage(sum(bool(r['human_verified']) for r in evals),len(evals)),
      'manual_seconds':sum(r['manual_seconds'] for r in paired) if paired else None,
      'assisted_seconds':sum(r['ai_seconds'] for r in paired) if paired else None,
      'paired_cases':len(paired),
    }


def executive_recommendations(findings):
    """Prioritize open independent findings, including the explicit safety escalation."""
    severity_order = {'Critical':0, 'High':1, 'Medium':2, 'Low':3}
    open_findings = [row for row in findings if row['status'] != 'Closed']
    return sorted(open_findings, key=lambda row: (
        0 if row['id'] == 'F-04' else 1,
        severity_order.get(row['severity'],4), row['id'],
    ))[:5]
