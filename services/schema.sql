CREATE TABLE IF NOT EXISTS seed_versions (version INTEGER PRIMARY KEY);
CREATE TABLE IF NOT EXISTS assets (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, owner TEXT, type TEXT,
    criticality INTEGER CHECK (criticality BETWEEN 1 AND 5), environment TEXT, source TEXT
);
CREATE TABLE IF NOT EXISTS risks (
    id TEXT PRIMARY KEY, asset_id TEXT REFERENCES assets(id), scope TEXT, event TEXT NOT NULL,
    threat TEXT, vulnerability TEXT, likelihood INTEGER NOT NULL CHECK (likelihood BETWEEN 1 AND 5),
    impact INTEGER NOT NULL CHECK (impact BETWEEN 1 AND 5), treatment TEXT, treatment_action TEXT, owner TEXT,
    residual_target INTEGER CHECK (residual_target BETWEEN 1 AND 25),
    residual_likelihood INTEGER CHECK (residual_likelihood BETWEEN 1 AND 5),
    residual_impact INTEGER CHECK (residual_impact BETWEEN 1 AND 5), status TEXT, source TEXT,
    CHECK (asset_id IS NOT NULL OR scope IS NOT NULL),
    CHECK ((residual_likelihood IS NULL) = (residual_impact IS NULL))
);
CREATE TABLE IF NOT EXISTS controls (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, type TEXT, frameworks TEXT, owner TEXT,
    evidence_requirement TEXT, status TEXT, effectiveness TEXT,
    applicable INTEGER NOT NULL DEFAULT 1 CHECK (applicable IN (0, 1)), source TEXT
);
CREATE TABLE IF NOT EXISTS risk_rationales (
    risk_id TEXT PRIMARY KEY REFERENCES risks(id), likelihood_basis TEXT NOT NULL, impact_basis TEXT NOT NULL,
    source TEXT
);
CREATE TABLE IF NOT EXISTS risk_controls (
    risk_id TEXT REFERENCES risks(id), control_id TEXT REFERENCES controls(id), PRIMARY KEY (risk_id, control_id)
);
CREATE TABLE IF NOT EXISTS compliance_requirements (
    id TEXT PRIMARY KEY, framework TEXT NOT NULL, requirement TEXT NOT NULL, purpose TEXT, status TEXT,
    gap TEXT, recommendation TEXT, applicable INTEGER NOT NULL DEFAULT 1 CHECK (applicable IN (0, 1)), source TEXT
);
CREATE TABLE IF NOT EXISTS compliance_controls (
    requirement_id TEXT REFERENCES compliance_requirements(id), control_id TEXT REFERENCES controls(id),
    PRIMARY KEY (requirement_id, control_id)
);
CREATE TABLE IF NOT EXISTS audit_findings (
    id TEXT PRIMARY KEY, control_id TEXT REFERENCES controls(id), requirement TEXT NOT NULL, audit_control TEXT,
    evidence_requested TEXT, test TEXT, finding TEXT NOT NULL, severity TEXT, recommendation TEXT, source TEXT
);
CREATE TABLE IF NOT EXISTS evidence (
    id TEXT PRIMARY KEY, control_id TEXT REFERENCES controls(id), type TEXT, description TEXT NOT NULL,
    owner TEXT, last_reviewed TEXT, status TEXT, finding_id TEXT REFERENCES audit_findings(id), source TEXT
);
CREATE TABLE IF NOT EXISTS corrective_actions (
    id TEXT PRIMARY KEY, finding_id TEXT NOT NULL REFERENCES audit_findings(id), action TEXT NOT NULL,
    owner TEXT, target_date TEXT, status TEXT, expected_risk_reduction TEXT, source TEXT
);
CREATE TABLE IF NOT EXISTS governance_roles (role TEXT PRIMARY KEY, responsibility TEXT, source TEXT);
CREATE TABLE IF NOT EXISTS iam_roles (role TEXT PRIMARY KEY, permissions TEXT, restriction TEXT, source TEXT);
CREATE TABLE IF NOT EXISTS iam_permissions (policy TEXT PRIMARY KEY, context TEXT, outcome TEXT, source TEXT);
CREATE TABLE IF NOT EXISTS access_reviews (account TEXT PRIMARY KEY, frequency TEXT, owner TEXT, source TEXT);
CREATE TABLE IF NOT EXISTS data_inventory (
    name TEXT PRIMARY KEY, classification TEXT, owner TEXT, access TEXT, encryption TEXT, retention TEXT,
    handling TEXT, source TEXT
);
CREATE TABLE IF NOT EXISTS data_items (
    name TEXT PRIMARY KEY, classification TEXT NOT NULL, owner TEXT, source TEXT
);
CREATE TABLE IF NOT EXISTS bcdr_services (
    asset_id TEXT PRIMARY KEY REFERENCES assets(id), service TEXT, criticality INTEGER, rto TEXT, rpo TEXT,
    priority INTEGER, business_impact TEXT, backup_status TEXT, restore_test TEXT, source TEXT
);
CREATE TABLE IF NOT EXISTS incidents (
    id TEXT PRIMARY KEY, risk_id TEXT REFERENCES risks(id), name TEXT, severity TEXT, affected_assets TEXT,
    owner TEXT, status TEXT, source TEXT
);
CREATE TABLE IF NOT EXISTS incident_stages (stage TEXT PRIMARY KEY, action TEXT, evidence TEXT, source TEXT);
CREATE TABLE IF NOT EXISTS soc_sources (source_name TEXT PRIMARY KEY, purpose TEXT, source TEXT);
CREATE TABLE IF NOT EXISTS ai_systems (
    asset_id TEXT PRIMARY KEY REFERENCES assets(id), system TEXT, owner TEXT, purpose TEXT, data_used TEXT,
    ai_risk TEXT, oversight TEXT, privacy TEXT, monitoring TEXT, incident_handling TEXT, governance_status TEXT, source TEXT
);
CREATE TABLE IF NOT EXISTS ai_risk_reviews (
    topic TEXT PRIMARY KEY, crowd_prediction_review TEXT NOT NULL, assistant_review TEXT NOT NULL,
    crowd_assessment TEXT, assistant_assessment TEXT, source TEXT
);
CREATE TABLE IF NOT EXISTS maturity_scores (
    dimension TEXT PRIMARY KEY, score INTEGER CHECK (score BETWEEN 1 AND 5), rationale TEXT, source TEXT
);
CREATE TABLE IF NOT EXISTS roadmap (
    year INTEGER PRIMARY KEY CHECK (year BETWEEN 1 AND 3), phase TEXT NOT NULL, activities TEXT, source TEXT
);
CREATE TABLE IF NOT EXISTS assurance_priorities (priority INTEGER PRIMARY KEY, recommendation TEXT, source TEXT);
CREATE TABLE IF NOT EXISTS roadmap_actions (
    id TEXT PRIMARY KEY, year INTEGER NOT NULL REFERENCES roadmap(year), action TEXT NOT NULL,
    owner TEXT, target_date TEXT, status TEXT CHECK (status IN ('Planned', 'In Progress', 'Complete', 'Deferred')),
    success_criterion TEXT, risk_id TEXT REFERENCES risks(id), evidence_id TEXT REFERENCES evidence(id), source TEXT
);
CREATE TABLE IF NOT EXISTS recovery_tests (
    id TEXT PRIMARY KEY, asset_id TEXT NOT NULL REFERENCES bcdr_services(asset_id), tested_on TEXT NOT NULL,
    restore_result TEXT NOT NULL CHECK (restore_result IN ('Restored', 'Failed')),
    actual_rto_minutes REAL CHECK (actual_rto_minutes >= 0),
    actual_rpo_minutes REAL CHECK (actual_rpo_minutes >= 0),
    reviewer TEXT, evidence_id TEXT REFERENCES evidence(id), notes TEXT, source TEXT,
    CHECK (restore_result = 'Failed' OR actual_rto_minutes IS NOT NULL)
);
CREATE TABLE IF NOT EXISTS ai_evaluations (
    id INTEGER PRIMARY KEY, test_case TEXT NOT NULL, mode TEXT NOT NULL, reference TEXT NOT NULL, ai_result TEXT NOT NULL,
    correct INTEGER CHECK (correct IN (0,1)), false_positive INTEGER NOT NULL CHECK (false_positive IN (0,1)),
    false_negative INTEGER NOT NULL CHECK (false_negative IN (0,1)),
    human_verified INTEGER NOT NULL CHECK (human_verified IN (0,1)),
    manual_seconds REAL CHECK (manual_seconds > 0), ai_seconds REAL CHECK (ai_seconds >= 0),
    CHECK ((manual_seconds IS NULL) = (ai_seconds IS NULL))
);
