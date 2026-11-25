"""Single executive overview with all required CISO indicators."""
import streamlit as st
from services.calculations import risk_level
from services.database import query
from services.final_program import assurance_snapshot, executive_recommendations
from services.project_exports import value
from views.common import number
from views.theme import kpis, section, summary_table, quick_link


def dashboard():
    snapshot = assurance_snapshot()
    risks = snapshot['risks']
    scores = snapshot['scores']
    high = sum(risk_level(row['score']) == 'High' for row in risks)
    critical = sum(risk_level(row['score']) == 'Critical' for row in risks)
    assets = query('SELECT COUNT(*) AS n FROM assets')[0]['n']
    st.caption(f'{assets} assets | {len(risks)} risks | {high} High / {critical} Critical')
    section('Executive assurance overview')
    kpis(
        ('Governance maturity', number(snapshot['maturity'], ' / 5'), 'Documentary self-assessment; reviewer sign-off pending'),
        ('Overall risk exposure', f"{snapshot['risk_mean']:.2f} / 25" if snapshot['risk_mean'] is not None else 'Not Yet Assessed', 'Mean inherent risk across the Risk Register'),
        ('High / Critical risks', snapshot['high_critical'], f'{high} High and {critical} Critical'),
        ('Independent audit score', f"{snapshot['audit_score']:.2f} / 100", 'Documentary audit baseline; Insufficient assurance'),
    )
    kpis(
        ('Control effectiveness', number(snapshot['control_effectiveness'], '%'),
         f"{snapshot['controls_assessed']} of {snapshot['controls_total']} applicable controls assessed"),
        ('Compliance', number(snapshot['compliance'], '%'), 'Satisfied / applicable A2 framework areas'),
        ('External audit findings', len(snapshot['findings']),
         f"{snapshot['open_corrective_actions']} open / {snapshot['closed_findings']} closed"),
        ('Critical control gaps', snapshot['critical_gaps'], 'Gap-status controls linked to Critical risks'),
    )
    kpis(
        ('IAM readiness', number(scores.get('IAM'), ' / 5'), 'Documentary self-assessment'),
        ('BC/DR readiness', number(snapshot['bcdr'], '%'), 'Latest measured restore results against RTO/RPO'),
        ('Incident response readiness', number(scores.get('Incident Response'), ' / 5'), 'Documentary self-assessment'),
        ('AI governance readiness', number(None if scores.get('AI Governance') is None else scores['AI Governance']*2, ' / 10'),
         'Documentary self-assessment, scaled from five points'),
    )
    section('AI automation impact')
    kpis(
        ('AI accuracy', number(snapshot['ai_accuracy'], '%'), 'AI Trust Score from human-reviewed verdicts'),
        ('AI automation gain', number(snapshot['gain'], '%'), 'Paired end-to-end manual and assisted workflows'),
    )
    st.caption(
        f"{snapshot['correct']} correct / {snapshot['incorrect']} incorrect / {snapshot['reviewed']} reviewed cases. "
        f"Manual time {value(snapshot['manual_seconds'], ' sec')} | "
        f"Assisted time {value(snapshot['assisted_seconds'], ' sec')} | Human approval required."
    )
    left, right = st.columns([1.15, 1], gap='medium')
    with left:
        section('Top 5 Risks')
        summary_table(('Risk', 'Scenario', 'Score', 'Severity'), [
            (row['id'], row['event'], row['score'], risk_level(row['score'])) for row in risks[:5]
        ], badge_columns=(3,))
    with right:
        section('Priority control gaps')
        gaps = query('''
            SELECT c.id,c.name,c.owner,group_concat(r.id, ', ') AS risks,
                   MAX(r.likelihood*r.impact) AS score
            FROM controls c LEFT JOIN risk_controls m ON m.control_id=c.id
            LEFT JOIN risks r ON r.id=m.risk_id
            WHERE c.applicable=1 AND c.status='Gap'
            GROUP BY c.id ORDER BY score DESC,c.id
        ''')
        summary_table(('Control', 'Linked risks', 'Risk severity'), [
            (row['id']+' '+row['name'], row['risks'], risk_level(row['score'])) for row in gaps
        ], badge_columns=(2,))
    section('Top 5 Recommendations')
    summary_table(('Finding', 'Recommended action', 'Owner'), [
        (row['id'], row['recommendation'], row['owner'])
        for row in executive_recommendations(snapshot['findings'])
    ])
    for column, label, page in zip(st.columns(3),
            ('Review risk register', 'Analyze a scenario', 'Assess maturity'),
            ('Risk Register', 'AI Risk & Control Assistant', 'Maturity & Roadmap')):
        with column:
            quick_link(label, page, key=f'jump_{page}')
    from views.program import executive_exports
    executive_exports()
    with st.expander('Assessment scope and supporting indicators'):
        st.write('Documentary scores describe the reviewed design. Control effectiveness, residual risk, recovery readiness and AI workflow results require their corresponding assessments or measurements.')
        kpis(('Open corrective actions', snapshot['open_corrective_actions']),
             ('Closed external findings', snapshot['closed_findings']),
             ('PISF clause compliance', number(snapshot['pisf_compliance'], '%')))
        assessed = [row['residual_likelihood']*row['residual_impact'] for row in risks
                    if row['residual_likelihood'] is not None and row['residual_impact'] is not None]
        st.caption(f'{len(assessed)} of {len(risks)} risks have assessed residual scores.')
        if assessed:
            st.write('Mean assessed residual risk '+number(sum(assessed)/len(assessed), ' / 25'))
        roadmap = query('SELECT status FROM roadmap_actions')
        complete = sum(row['status'] == 'Complete' for row in roadmap)
        kpis(('Roadmap completion', number(100*complete/len(roadmap) if roadmap else None, '%')),
             ('OT security readiness', number(scores.get('OT Security'), ' / 5'), 'Documentary self-assessment'))
        st.caption('F-04 is a priority safety finding despite its High severity. The independent audit reported no Critical findings.')
