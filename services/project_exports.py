"""Printable assignment-backed reports and register exports."""
from io import BytesIO, StringIO
from datetime import date
import csv
import zipfile
from xml.sax.saxutils import escape
from services.database import query
from services.final_program import assurance_snapshot, executive_recommendations

AUTOMATION_CARD = [
 ('IA phase','Risk assessment and control/evidence mapping'),
 ('Existing problem','An analyst manually traces threats and vulnerabilities to the PASS risk and control registers.'),
 ('Input','Selected asset/scope, synthetic threat and vulnerability, existing controls, likelihood and impact.'),
 ('AI method','Local Python rule-based decision support, optionally combined with an LLM ranking validated against the local catalog.'),
 ('Processing','Calculate L x I locally, rank supported control matches, exclude existing controls and attach references and evidence requirements.'),
 ('Output','Risk score/band, treatment suggestion, supported control IDs, frameworks, rationale and evidence requests.'),
 ('Human role','Analyst checks applicability and reference results. Authorized owners approve treatment and high-impact actions.'),
 ('Security risk','Hallucination, bias, leakage, injection, drift, over-reliance, poor explanation, outage and provider changes.'),
 ('Accuracy','Fixed source-reference cases plus negative/adversarial cases. Human-reviewed correctness, false positives/negatives and verification rate are tracked separately.'),
 ('Benefit','Compare paired end-to-end manual and assisted times, including human review. Gain = (manual - assisted) / manual x 100.'),
 ('Limitation','Catalog matching has limited context, can miss novel threats and cannot establish legal compliance or operating effectiveness.'),
 ('Governance','CISO owns the assistant; Privacy reviews external data use; Risk and Compliance governs changes and approvals.'),
]


def value(number, suffix=''):
    return 'Not yet assessed' if number is None else f'{number:.1f}{suffix}'


def register_zip():
    buffer = BytesIO()
    tables = ('assets','risks','controls','risk_controls','compliance_requirements','compliance_controls',
              'evidence','audit_findings','corrective_actions','external_findings','audit_tests','audit_test_plan',
              'external_finding_evidence','recovery_design','risk_decisions','project_coverage','supplier_reviews','maturity_scores','roadmap_actions','ai_evaluations','project_benchmark')
    with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED) as archive:
        for table in tables:
            rows = query(f'SELECT * FROM {table}')
            output = StringIO(newline='')
            if rows:
                writer = csv.DictWriter(output, fieldnames=list(rows[0]))
                writer.writeheader()
                for row in rows:
                    # CSV cells that begin with formula markers must remain text.
                    writer.writerow({k: "'"+v if isinstance(v,str) and v.startswith(('=','+','-','@')) else v for k,v in row.items()})
            archive.writestr(table+'.csv',output.getvalue().encode('utf-8-sig'))
    return buffer.getvalue()


def _pdf():
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Compact',fontName='Helvetica',fontSize=8,leading=10,spaceAfter=4))
    styles.add(ParagraphStyle(name='SmallHeading',fontName='Helvetica-Bold',fontSize=11,leading=14,spaceBefore=10,spaceAfter=5,textColor=colors.HexColor('#086b70')))
    return styles


def dashboard_pdf():
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import Paragraph
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    snapshot=assurance_snapshot()
    buffer=BytesIO()
    canvas=Canvas(buffer,pagesize=A4)
    width,height=A4
    body=ParagraphStyle('body',fontName='Helvetica',fontSize=8.2,leading=10.4)
    def text(message,x,y,w=520):
        paragraph=Paragraph(escape(message),body)
        _,h=paragraph.wrap(w,100)
        paragraph.drawOn(canvas,x,y-h)
        return y-h-5
    canvas.setTitle('PASS CISO Executive Dashboard')
    canvas.setFillColor(colors.HexColor('#172d3b'))
    canvas.setFont('Helvetica-Bold',19)
    canvas.drawString(36,height-48,'PASS | CISO Executive Dashboard')
    y=text('PakArena Smart Stadium | Documentary baseline and measured prototype results | '+str(date.today()),36,height-60)
    y=text('Independent audit 44.46/100 - Insufficient assurance under the audit scale. F-04 requires priority safety review. Overall operational assurance remains incomplete.',36,y)
    scores=snapshot['scores']
    metrics=[('Governance maturity (doc.)',value(snapshot['maturity'],' / 5')),('Mean inherent risk',f"{snapshot['risk_mean']:.2f} / 25" if snapshot['risk_mean'] is not None else 'Not yet assessed'),
      ('High / Critical risks',str(snapshot['high_critical'])),('External audit findings',str(len(snapshot['findings']))),
      ('Control effectiveness',value(snapshot['control_effectiveness'],'%')),('Controls tested',f"{snapshot['controls_assessed']}/{snapshot['controls_total']}"),
      ('Framework compliance',value(snapshot['compliance'],'%')),('Critical control gaps',str(snapshot['critical_gaps'])),
      ('IAM documentary maturity',value(scores.get('IAM'),' / 5')),('BC/DR tested readiness',value(snapshot['bcdr'],'%')),
      ('IR documentary maturity',value(scores.get('Incident Response'),' / 5')),('AI governance readiness',value(None if scores.get('AI Governance') is None else scores['AI Governance']*2,' / 10')),
      ('AI Trust / reviewed accuracy',value(snapshot['ai_accuracy'],'%')),('AI automation gain',value(snapshot['gain'],'%')),
      ('Correct / incorrect / reviewed',f"{snapshot['correct']} / {snapshot['incorrect']} / {snapshot['reviewed']}"),('Open corrective actions',str(snapshot['open_corrective_actions']))]
    for i,(label,result) in enumerate(metrics):
        column=i%4;row=i//4
        x=36+column*131;top=y-row*43
        canvas.setFillColor(colors.HexColor('#eef4f4'))
        canvas.roundRect(x,top-39,125,39,4,fill=1,stroke=0)
        canvas.setFillColor(colors.HexColor('#172d3b'))
        text(label,x+6,top-5,114)
        canvas.setFont('Helvetica-Bold',10)
        canvas.drawString(x+6,top-32,result)
    y-=4*43+10
    y=text('Maturity scores are documentary self-assessments awaiting reviewer sign-off. Control effectiveness is effective/applicable controls; zero tests displays Not yet assessed. Controls tested shows coverage. Compliance scope is the nine A2 framework areas.',36,y)
    def heading(title,y):
        canvas.setFont('Helvetica-Bold',11)
        canvas.drawString(36,y-12,title)
        return y-19
    y=heading('Top five inherent risks',y)
    for row in snapshot['risks'][:5]:
        y=text(f"{row['id']} | {row['score']}/25 | {row['event']}",36,y)
    y=heading('Top five decisions and actions',y)
    for row in executive_recommendations(snapshot['findings']):
        y=text(row['id']+' | '+row['recommendation'],36,y)
    y=heading('AI automation - risk and control mapping',y)
    y=text('Paired end-to-end manual time '+value(snapshot['manual_seconds'],' sec')+' | Assisted time '+value(snapshot['assisted_seconds'],' sec')+f" | Verified paired cases {snapshot['paired_cases']}. Human approval is required.",36,y)
    y=text('Gain = (manual - assisted) / manual x 100. Trust = correct / reviewed verdicts x 100. Prototype benchmark and catalog execution times are distinct from human workflow measurements.',36,y)
    canvas.setFont('Helvetica',7)
    canvas.drawString(36,24,'Sources A1-A4 and current registers. Relative deadlines start at an approved project start. Source audit date conflicts remain flagged.')
    if y<36:
        raise ValueError('Dashboard content exceeds the one-page layout. Shorten long source labels before export.')
    canvas.showPage();canvas.save()
    return buffer.getvalue()


def automation_pdf():
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
    from reportlab.lib.pagesizes import A4
    styles=_pdf();buffer=BytesIO()
    story=[Paragraph('PASS AI Automation Card',styles['Title'])]
    rows=[[Paragraph(escape(a),styles['Compact']),Paragraph(escape(b),styles['Compact'])] for a,b in AUTOMATION_CARD]
    table=Table(rows,colWidths=[105,410],hAlign='LEFT')
    table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,-1),.4,'#cbd9dc'),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
    story.append(table)
    SimpleDocTemplate(buffer,pagesize=A4,rightMargin=36,leftMargin=36,topMargin=32,bottomMargin=32).build(story)
    return buffer.getvalue()


def final_report_pdf():
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Flowable
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    styles=_pdf();buffer=BytesIO()
    class ArchitectureDiagram(Flowable):
        width=515
        height=180
        def draw(self):
            canvas=self.canv
            nodes=[(10,120,'Spectators / guest zone'),(185,120,'Ticketing / mobile DMZ'),(360,120,'Protected core / IAM / DB'),
                   (10,30,'Independent backup / DR'),(185,30,'Collectors / SOC / SIEM'),(360,30,'OT gateway / local systems')]
            canvas.setFont('Helvetica',8)
            for x,y,label in nodes:
                canvas.setStrokeColor(colors.HexColor('#086b70'))
                canvas.roundRect(x,y,145,34,5,stroke=1,fill=0)
                canvas.drawCentredString(x+72.5,y+13,label)
            def arrow(x1,y1,x2,y2):
                canvas.line(x1,y1,x2,y2)
                import math
                angle=math.atan2(y2-y1,x2-x1)
                for turn in (-.5,.5):
                    canvas.line(x2,y2,x2-6*math.cos(angle+turn),y2-6*math.sin(angle+turn))
            arrow(155,137,185,137);arrow(330,137,360,137)
            arrow(432,120,432,64);arrow(360,120,330,64)
            arrow(360,47,330,47);arrow(360,120,155,64)
            canvas.setFont('Helvetica',7)
            canvas.drawString(10,8,'Approved application paths and conduits only. Protected telemetry feeds SOC; isolated copies support controlled restoration.')
    story=[Paragraph('PakArena Smart Stadium',styles['Title']),Paragraph('Enterprise Information Assurance, GRC and AI-Assisted Cybersecurity Program',styles['Heading1']),
      Paragraph('Final project design and prototype | 22 November 2026',styles['Normal']),Spacer(1,12),
      Paragraph('Group 10 - Roshni Fawad, Anum Ali, Furqan Haider, Muhammad Abdullah and Aatif Ali Khan',styles['Normal']),Spacer(1,12),
      Paragraph('Built from Assignments 1-3 and the independent third-party documentary audit. The 44.46/100 audit baseline and 13 findings retain their original provenance. Proposed improvements require owner approval; operational validation requires dated evidence and review.',styles['Normal'])]
    def section(title,content):
        story.append(Paragraph(escape(title),styles['Heading1']))
        for paragraph in content.split('\n'):
            if paragraph.strip():story.append(Paragraph(escape(paragraph),styles['BodyText']))
    def tabulate(headers,rows,widths):
        grid=[[Paragraph(escape(str(v if v is not None else 'Not yet assessed')),styles['Compact']) for v in row] for row in [headers,*rows]]
        table=Table(grid,colWidths=widths,repeatRows=1,hAlign='LEFT')
        table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eef4f4')),('LINEBELOW',(0,0),(-1,-1),.4,colors.HexColor('#cbd9dc')),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5)]))
        story.append(table)
    story.append(PageBreak())
    section('Scope, architecture and assurance chain','PASS is a hypothetical Pakistani multipurpose stadium for approximately 45,000 spectators, 350 permanent staff and 1,200 temporary event staff. Public ticketing/mobile services connect to controlled application and database services; payment processing crosses a provider boundary. Guest, corporate, payment and OT networks are segregated. Controlled conduits connect entry gates, CCTV, BMS and IoT to approved management services. Protected collectors feed SOC/SIEM. Independent backup and DR support recovery. The assurance chain is business objective to requirement to asset/risk to control to evidence/test to residual decision and executive review.')
    story.append(ArchitectureDiagram())
    current=assurance_snapshot()
    section('Calculated documentary baseline',f"Mean inherent risk {current['risk_mean']:.2f}/25 across 16 source risks; 15 High/Critical risks. Independent audit 44.46/100, 13 findings. Documentary maturity {current['maturity']:.2f}/5 is a self-assessment with reviewer sign-off pending. Framework-area compliance is {current['compliance']:.1f}% satisfied across {current['requirements_total']} applicable A2 areas. Operating control assessment coverage is {current['controls_assessed']}/{current['controls_total']}. Human-reviewed AI accuracy and end-to-end automation gain remain pending.")
    section('Requirement coverage and remaining verification','The accompanying app provides all 27 deliverable areas. The table identifies original evidence and remaining validation. A design artifact is distinct from a successful operating test.')
    tabulate(['Deliverable','App route','Remaining validation'],[(r['component'],r['route'],r['remaining_evidence']) for r in query('SELECT * FROM project_coverage')],[115,135,265])
    for row in query('SELECT * FROM program_sections ORDER BY rowid'):
        section(row['title'],row['content'])
        story.append(Paragraph('Basis - '+escape(row['source'])+' | '+escape(row['status']),styles['Compact']))
    section('Five integrated registers','The downloadable CSV bundle contains the asset, risk, control, compliance and evidence registers and join tables. Original IDs and the 16-risk baseline are retained; evidence records identify source documents and operating artifacts separately.')
    tabulate(['Asset','Owner','Criticality'],[(r['id']+' '+r['name'],r['owner'],r['criticality']) for r in query('SELECT * FROM assets ORDER BY id')],[235,230,50])
    tabulate(['Risk','L','I','L x I','Planned residual'],[(r['id']+' '+r['event'],r['likelihood'],r['impact'],r['likelihood']*r['impact'],r['residual_target']) for r in query('SELECT * FROM risks ORDER BY id')],[325,30,30,45,85])
    section('Business impact analysis and proposed recovery design','The source A3 targets remain preserved in the app. The following final-design values include dependencies, impact and proposed maximum tolerable disruption. Approval and controlled testing remain pending. Life-safety functions require continuity under the venue safety plan.')
    tabulate(['Asset / impact','Dependencies','RTO / RPO / tolerable disruption'],[(r['asset_id']+' '+r['business_impact'],r['dependencies'],r['proposed_rto']+' / '+r['proposed_rpo']+' / '+r['proposed_mtd']) for r in query('SELECT * FROM recovery_design ORDER BY asset_id')],[150,160,205])
    section('Independent audit findings and corrective actions','Baseline 44.46/100, 5 High, 7 Medium, 1 Low and no Critical findings. F-04 remains priority safety escalation. Closure requires verified evidence and independent review.')
    for row in query('SELECT * FROM external_findings ORDER BY id'):
        section(row['id']+' - '+row['title'],row['severity']+' | '+row['observation']+'\nAction - '+row['recommendation']+'\nOwner - '+row['owner']+'; target '+row['period_days']+' days from approved start. Status '+row['status']+'. Evidence '+row['evidence_refs'])
    section('Expanded control test plan','All existing control packages have procedures, acceptance criteria, evidence requests and quarterly/change-triggered review. Execute tests in authorized laboratory or controlled exercise conditions.')
    tabulate(['Control / risks','Procedure','Pass criterion'],[(r['control_id']+' / '+r['risk_ids'],r['test_procedure'],r['pass_criterion']) for r in query('SELECT * FROM audit_test_plan ORDER BY control_id')],[80,225,210])
    section('AI Automation Card','The assistant produces demonstrable advisory output. Accuracy, trust and timing use the evaluation workflow and fixed prototype benchmark with explicit scope.')
    tabulate(['Item','Implementation'],AUTOMATION_CARD,[105,410])
    section('Prototype benchmark','Rows below are automated catalog-regression results. They do not substitute for human review, end-to-end automation timing or novel-threat evaluation.')
    rows=query('SELECT * FROM project_benchmark ORDER BY id')
    tabulate(['Case','Expected','Observed','Pass'],[(r['id'],r['expected'],r['observed'],r['passed']) for r in rows],[70,130,265,50])
    section('Sources','A1 Group 10 Assignment1 (1)(1).pdf, 13 pages.\nA2 Assignment2_IA (1)(1).pdf, 9 pages.\nA3 Assignment_03_PakArena_Group10(1).pdf, 11 pages.\nA4 IA_A4_23i2116-23i2127-23i2079.docx, independent audit, 27 pages.\nOfficial PISF 2026 page https://pkcert.gov.pk/grc-policies.asp and merged framework https://pkcert.gov.pk/uploads/2026/03/PISF-Merged-Version.pdf, checked 22 November 2026.\nProject requirements supplied by the instructor via the user. Extracted source text is included under docs/sources for verification.')
    def footer(canvas,doc):
        canvas.setFont('Helvetica',8);canvas.drawString(36,22,'PASS final project | '+str(doc.page))
    SimpleDocTemplate(buffer,pagesize=A4,leftMargin=36,rightMargin=36,topMargin=36,bottomMargin=36).build(story,onFirstPage=footer,onLaterPages=footer)
    return buffer.getvalue()
