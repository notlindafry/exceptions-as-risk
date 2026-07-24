#!/usr/bin/env python3
"""Generate the v2 GRC-ecosystem corpus under ``data/`` (SPEC §2, §5).

This extends ``generate_corpus.py`` (which still writes the legacy risks /
exceptions / remediations / okrs the engine reads) with the new-model entities:
the enterprise anchor, the Tier-1 domains, Tier-2 named risks, Tier-3 scenarios,
the generalised issues floor (findings + accepted-vulnerability exceptions; other
exceptions stay in their own directory), the ISO 27001:2022 Annex A
control backbone, policies, evidence, KRIs, and the horizon watch list.

Day 1 scope: coherent, valid shapes that load, validate, and confirm the SPEC §3
cardinalities, with one populated example per entity. The fully designed corpus
that tells all ten SPEC §5 stories is Day-3 work; this is the foundation it
builds on. All data is synthetic (SPEC §11).

Run via ``python examples/generate_corpus.py`` (which calls ``build_ecosystem``),
or standalone with ``python examples/generate_ecosystem.py``.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path


def _plus_days(iso: str, n: int) -> str:
    """ISO date + n days. Used to author paired decision/closure dates."""
    return (dt.date.fromisoformat(iso) + dt.timedelta(days=n)).isoformat()

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SCN = DATA / "scenarios"
ISSUES = DATA / "issues"


# ---------------------------------------------------------------------------
# 1. Enterprise anchor (SPEC §2.1)
# ---------------------------------------------------------------------------

ENTERPRISE = """\
# The top-level appetite anchor (SPEC §2.1, §4). Two dollar figures:
#   capacity_materiality  -- the hard audit-materiality line the company cannot
#                            cross by choice (the binding, smaller number).
#   appetite (derived)    -- appetite_pct_of_revenue x revenue_annual, a
#                            revenue-percent figure set deliberately BENEATH
#                            capacity, that scales with the company and reads
#                            cleanly to a board.
# All figures synthetic.

revenue_annual: 2000000000          # $2B; the base for the appetite percentage
capacity_materiality: 15000000      # $15M hard line (audit materiality)
appetite_pct_of_revenue: 0.005      # 0.5% -> $10M declared appetite, set beneath capacity
green_band_floor: 0.75              # gate 2: mean >= 75% of appetite reads green (SPEC v2.6 §1)
appetite_red_prob: 0.33             # gate 1: P(loss > appetite) >= 1/3 reads red, whatever the mean (SPEC v2.6 §1)
"""


# ---------------------------------------------------------------------------
# 2. Domains -- Tier 1 (SPEC §1, §2.2)
# ---------------------------------------------------------------------------

DOMAINS = [
    ("TR-RESILIENCE", "Resilience", "down or cannot recover",
     "measured availability risk accepted to sustain launch velocity", "cro@company.com"),
    ("TR-DATA-INTEGRITY", "Data integrity", "data wrong, corrupted, or lost; includes analytics/ML input quality",
     "data-quality risk held low; correctness is a product promise", "cro@company.com"),
    ("TR-SECURITY", "Security", "adversarial compromise; unauthorized access or disclosure",
     "compromise tolerance kept tight; breaches are existential to trust", "ciso@company.com"),
    ("TR-PRIVACY", "Privacy", "misused regulated/personal data: residency, retention, consent, subprocessor governance",
     "regulated-data misuse held near zero; this is a licence-to-operate risk", "dpo@company.com"),
    ("TR-CHANGE", "Change & delivery", "shipping or rebuilding breaks things: change failure, migration/cutover, launch readiness, velocity-driven debt",
     "elevated change risk knowingly accepted during the rebuild window", "cto@company.com"),
    ("TR-THIRDPARTY", "Third-party", "an external dependency's failure becomes yours; concentration risk",
     "concentration risk monitored; single-provider dependence flagged", "ciso@company.com"),
    ("TR-COMPLIANCE", "Compliance", "pure obligation failure with no technical trigger: missed filings, lapsed certifications, failed audits/attestations",
     "obligation failures not tolerated; these are binary pass/fail", "gc@company.com"),
]

DOMAIN_YAML_HEAD = """\
# Tier 1 -- where the risk manifests (board / portfolio altitude, SPEC §1, §2.2).
# The appetite_statement is board-facing narrative ONLY, never tested against a
# number (SPEC §4). Governance metadata (sign-off, last reviewed) sits here.
# All data synthetic.

"""


def render_domains() -> str:
    out = [DOMAIN_YAML_HEAD]
    for did, title, desc, statement, signer in DOMAINS:
        out.append(
            f"{did}:\n"
            f"  title: {title}\n"
            f'  description: "{desc}"\n'
            f'  appetite_statement: "{statement}"\n'
            f"  appetite_signed_off_by: {signer}\n"
            f"  appetite_last_reviewed: 2026-05-01\n"
        )
    return "\n".join(out)


# ---------------------------------------------------------------------------
# 3. Policies -- the governance layer above controls (SPEC §2.7)
# ---------------------------------------------------------------------------

# (id, title, owner, last_reviewed, review_cadence). Cadence (v4.0 §0.A) is the
# authored review commitment the GRC tab tests currency against; the eng build
# never reads it. POL-PHYSICAL / POL-HR-SECURITY / POL-ASSET-MGMT run a
# semiannual cycle (post-audit commitment) and deliberately read OVERDUE at the
# canonical 2026-06-18 reference date (v4.0 §0.H).
POLICIES = [
    ("POL-INFOSEC", "Information Security Policy", "ciso-office@company.com", "2026-02-01", "annual"),
    ("POL-ACCESS-CONTROL", "Access Control Policy", "ciso-office@company.com", "2026-02-01", "annual"),
    ("POL-CRYPTO", "Cryptography & Key Management Policy", "ciso-office@company.com", "2026-01-15", "annual"),
    ("POL-ASSET-MGMT", "Asset Management Policy", "it-office@company.com", "2025-11-10", "semiannual"),
    ("POL-DATA-CLASSIFICATION", "Data Classification & Handling Policy", "dpo@company.com", "2026-03-01", "annual"),
    ("POL-PRIVACY", "Privacy & Personal Data Policy", "dpo@company.com", "2026-03-01", "annual"),
    ("POL-SUPPLIER", "Supplier & Third-Party Security Policy", "procurement-office@company.com", "2025-12-05", "annual"),
    ("POL-INCIDENT", "Information Security Incident Management Policy", "ciso-office@company.com", "2026-02-20", "annual"),
    ("POL-BCP", "Business Continuity & ICT Readiness Policy", "resilience-office@company.com", "2026-01-30", "annual"),
    ("POL-HR-SECURITY", "Human Resources Security Policy", "people-office@company.com", "2025-10-12", "semiannual"),
    ("POL-PHYSICAL", "Physical & Environmental Security Policy", "facilities-office@company.com", "2025-09-20", "semiannual"),
    ("POL-SECURE-DEV", "Secure Development Policy", "eng-office@company.com", "2026-04-01", "annual"),
    ("POL-VULN-MGMT", "Technical Vulnerability Management Policy", "ciso-office@company.com", "2026-04-10", "annual"),
    ("POL-CHANGE-MGMT", "Change Management Policy", "eng-office@company.com", "2026-03-15", "annual"),
    ("POL-LOGGING-MONITORING", "Logging & Monitoring Policy", "soc-office@company.com", "2026-02-05", "annual"),
    ("POL-NETWORK", "Network Security Policy", "network-office@company.com", "2026-01-08", "annual"),
    ("POL-COMPLIANCE", "Legal & Regulatory Compliance Policy", "gc-office@company.com", "2026-02-28", "annual"),
    # v4.0 §0.F: the governing policy the agent guardrails trace up to. No
    # control references it, so it is inert for the eng build.
    ("POL-AI-USE", "AI & Agent Use Policy", "ciso-office@company.com", "2026-05-01", "annual"),
]

POLICY_YAML_HEAD = """\
# The governance layer above controls (SPEC §2.7, thin). The coverage read is
# "every control traces up to a governing policy." Links are placeholders.
# review_cadence (v4.0 §0.A) is the authored review commitment; overdue is
# DERIVED (as-of - last_reviewed > cadence) by the GRC build only.
# All data synthetic.

"""


def render_policies() -> str:
    out = [POLICY_YAML_HEAD]
    for pid, title, owner, reviewed, cadence in POLICIES:
        slug = pid.lower().replace("pol-", "")
        out.append(
            f"{pid}:\n"
            f"  title: {title}\n"
            f"  owner: {owner}\n"
            f"  last_reviewed: {reviewed}\n"
            f"  review_cadence: {cadence}\n"
            f"  link: https://policies.example.com/{slug}\n"
        )
    return "\n".join(out)


# ---------------------------------------------------------------------------
# 4. Controls -- the ISO 27001:2022 Annex A backbone, all 93 (SPEC §2.6)
# ---------------------------------------------------------------------------
# Four themes: Organizational (A.5.1-A.5.37, 37), People (A.6.1-A.6.8, 8),
# Physical (A.7.1-A.7.14, 14), Technological (A.8.1-A.8.34, 34) = 93.

ANNEX_A = {
    "Organizational": [
        "Policies for information security",
        "Information security roles and responsibilities",
        "Segregation of duties",
        "Management responsibilities",
        "Contact with authorities",
        "Contact with special interest groups",
        "Threat intelligence",
        "Information security in project management",
        "Inventory of information and other associated assets",
        "Acceptable use of information and other associated assets",
        "Return of assets",
        "Classification of information",
        "Labelling of information",
        "Information transfer",
        "Access control",
        "Identity management",
        "Authentication information",
        "Access rights",
        "Information security in supplier relationships",
        "Addressing information security within supplier agreements",
        "Managing information security in the ICT supply chain",
        "Monitoring, review and change management of supplier services",
        "Information security for use of cloud services",
        "Information security incident management planning and preparation",
        "Assessment and decision on information security events",
        "Response to information security incidents",
        "Learning from information security incidents",
        "Collection of evidence",
        "Information security during disruption",
        "ICT readiness for business continuity",
        "Legal, statutory, regulatory and contractual requirements",
        "Intellectual property rights",
        "Protection of records",
        "Privacy and protection of personal identifiable information (PII)",
        "Independent review of information security",
        "Compliance with policies, rules and standards for information security",
        "Documented operating procedures",
    ],
    "People": [
        "Screening",
        "Terms and conditions of employment",
        "Information security awareness, education and training",
        "Disciplinary process",
        "Responsibilities after termination or change of employment",
        "Confidentiality or non-disclosure agreements",
        "Remote working",
        "Information security event reporting",
    ],
    "Physical": [
        "Physical security perimeters",
        "Physical entry",
        "Securing offices, rooms and facilities",
        "Physical security monitoring",
        "Protecting against physical and environmental threats",
        "Working in secure areas",
        "Clear desk and clear screen",
        "Equipment siting and protection",
        "Security of assets off-premises",
        "Storage media",
        "Supporting utilities",
        "Cabling security",
        "Equipment maintenance",
        "Secure disposal or re-use of equipment",
    ],
    "Technological": [
        "User endpoint devices",
        "Privileged access rights",
        "Information access restriction",
        "Access to source code",
        "Secure authentication",
        "Capacity management",
        "Protection against malware",
        "Management of technical vulnerabilities",
        "Configuration management",
        "Information deletion",
        "Data masking",
        "Data leakage prevention",
        "Information backup",
        "Redundancy of information processing facilities",
        "Logging",
        "Monitoring activities",
        "Clock synchronization",
        "Use of privileged utility programs",
        "Installation of software on operational systems",
        "Networks security",
        "Security of network services",
        "Segregation of networks",
        "Web filtering",
        "Use of cryptography",
        "Secure development life cycle",
        "Application security requirements",
        "Secure system architecture and engineering principles",
        "Secure coding",
        "Security testing in development and acceptance",
        "Outsourced development",
        "Separation of development, test and production environments",
        "Change management",
        "Test information",
        "Protection of information systems during audit testing",
    ],
}
_THEME_CLAUSE = {"Organizational": 5, "People": 6, "Physical": 7, "Technological": 8}

# Governing policy per Annex A reference (SPEC §2.7 coverage: every control ->
# exactly one policy). Anything unlisted falls back to POL-INFOSEC.
CONTROL_POLICY = {
    "A.5.1": "POL-INFOSEC", "A.5.2": "POL-INFOSEC", "A.5.3": "POL-ACCESS-CONTROL",
    "A.5.4": "POL-INFOSEC", "A.5.5": "POL-COMPLIANCE", "A.5.6": "POL-INFOSEC",
    "A.5.7": "POL-LOGGING-MONITORING", "A.5.8": "POL-SECURE-DEV",
    "A.5.9": "POL-ASSET-MGMT", "A.5.10": "POL-ASSET-MGMT", "A.5.11": "POL-ASSET-MGMT",
    "A.5.12": "POL-DATA-CLASSIFICATION", "A.5.13": "POL-DATA-CLASSIFICATION",
    "A.5.14": "POL-DATA-CLASSIFICATION", "A.5.15": "POL-ACCESS-CONTROL",
    "A.5.16": "POL-ACCESS-CONTROL", "A.5.17": "POL-ACCESS-CONTROL", "A.5.18": "POL-ACCESS-CONTROL",
    "A.5.19": "POL-SUPPLIER", "A.5.20": "POL-SUPPLIER", "A.5.21": "POL-SUPPLIER",
    "A.5.22": "POL-SUPPLIER", "A.5.23": "POL-SUPPLIER",
    "A.5.24": "POL-INCIDENT", "A.5.25": "POL-INCIDENT", "A.5.26": "POL-INCIDENT",
    "A.5.27": "POL-INCIDENT", "A.5.28": "POL-INCIDENT",
    "A.5.29": "POL-BCP", "A.5.30": "POL-BCP",
    "A.5.31": "POL-COMPLIANCE", "A.5.32": "POL-COMPLIANCE", "A.5.33": "POL-COMPLIANCE",
    "A.5.34": "POL-PRIVACY", "A.5.35": "POL-INFOSEC", "A.5.36": "POL-COMPLIANCE",
    "A.5.37": "POL-INFOSEC",
    "A.6.1": "POL-HR-SECURITY", "A.6.2": "POL-HR-SECURITY", "A.6.3": "POL-HR-SECURITY",
    "A.6.4": "POL-HR-SECURITY", "A.6.5": "POL-HR-SECURITY", "A.6.6": "POL-HR-SECURITY",
    "A.6.7": "POL-HR-SECURITY", "A.6.8": "POL-INCIDENT",
    "A.7.1": "POL-PHYSICAL", "A.7.2": "POL-PHYSICAL", "A.7.3": "POL-PHYSICAL",
    "A.7.4": "POL-PHYSICAL", "A.7.5": "POL-PHYSICAL", "A.7.6": "POL-PHYSICAL",
    "A.7.7": "POL-PHYSICAL", "A.7.8": "POL-PHYSICAL", "A.7.9": "POL-PHYSICAL",
    "A.7.10": "POL-ASSET-MGMT", "A.7.11": "POL-PHYSICAL", "A.7.12": "POL-PHYSICAL",
    "A.7.13": "POL-PHYSICAL", "A.7.14": "POL-ASSET-MGMT",
    "A.8.1": "POL-ACCESS-CONTROL", "A.8.2": "POL-ACCESS-CONTROL", "A.8.3": "POL-ACCESS-CONTROL",
    "A.8.4": "POL-SECURE-DEV", "A.8.5": "POL-ACCESS-CONTROL", "A.8.6": "POL-BCP",
    "A.8.7": "POL-INFOSEC", "A.8.8": "POL-VULN-MGMT", "A.8.9": "POL-CHANGE-MGMT",
    "A.8.10": "POL-DATA-CLASSIFICATION", "A.8.11": "POL-PRIVACY", "A.8.12": "POL-DATA-CLASSIFICATION",
    "A.8.13": "POL-BCP", "A.8.14": "POL-BCP", "A.8.15": "POL-LOGGING-MONITORING",
    "A.8.16": "POL-LOGGING-MONITORING", "A.8.17": "POL-LOGGING-MONITORING", "A.8.18": "POL-ACCESS-CONTROL",
    "A.8.19": "POL-CHANGE-MGMT", "A.8.20": "POL-NETWORK", "A.8.21": "POL-NETWORK",
    "A.8.22": "POL-NETWORK", "A.8.23": "POL-NETWORK", "A.8.24": "POL-CRYPTO",
    "A.8.25": "POL-SECURE-DEV", "A.8.26": "POL-SECURE-DEV", "A.8.27": "POL-SECURE-DEV",
    "A.8.28": "POL-SECURE-DEV", "A.8.29": "POL-SECURE-DEV", "A.8.30": "POL-SUPPLIER",
    "A.8.31": "POL-CHANGE-MGMT", "A.8.32": "POL-CHANGE-MGMT", "A.8.33": "POL-SECURE-DEV",
    "A.8.34": "POL-COMPLIANCE",
}

# Named-risk mappings per control (SPEC §2.6, M2M), pruned to causally-defensible
# links only (SPEC v3.1 §1): a control is listed against a risk only where it
# prevents, detects, or limits that specific loss event. Controls with no listed
# risk are genuinely unmapped (~38 of 93) — the expected state of an illustration,
# not a flag; the unmapped-control check is retired (§2).
CONTROL_NAMED_RISKS = {
    "A.5.8": ["NR-PROD-COMPROMISE"],  # v3.1 §1a Prod keep-15
    "A.5.14": ["NR-DATA-EXFIL"],
    "A.5.15": ["NR-PROD-COMPROMISE"], "A.5.16": ["NR-PROD-COMPROMISE"],
    "A.5.17": ["NR-PROD-COMPROMISE"], "A.5.18": ["NR-PROD-COMPROMISE", "NR-VENDOR-ACCESS"],
    "A.5.19": ["NR-VENDOR-ACCESS"], "A.5.20": ["NR-VENDOR-ACCESS"],
    "A.5.21": ["NR-MODEL-SUPPLY", "NR-VENDOR-ACCESS"], "A.5.22": ["NR-VENDOR-ACCESS"],
    "A.5.23": ["NR-PLATFORM-OUTAGE", "NR-VENDOR-ACCESS"],
    "A.5.24": ["NR-PLATFORM-OUTAGE"], "A.5.25": ["NR-PROD-COMPROMISE"], "A.5.26": ["NR-PROD-COMPROMISE"],
    "A.5.29": ["NR-PLATFORM-OUTAGE", "NR-DATA-AVAILABILITY"],
    "A.5.30": ["NR-PLATFORM-OUTAGE"],
    "A.5.31": ["NR-REG-FILINGS", "NR-PCI-SCOPE"], "A.5.33": ["NR-REG-FILINGS"],
    "A.5.34": ["NR-DATA-RESIDENCY", "NR-SUBPROCESSOR-GOV"],
    "A.5.36": ["NR-PCI-SCOPE", "NR-REG-FILINGS"],
    "A.6.3": ["NR-ENDPOINT-MALWARE"],  # v3.1 §1b: the one People control retained (phishing-delivered malware)
    "A.8.1": ["NR-ENDPOINT-MALWARE"], "A.8.2": ["NR-PROD-COMPROMISE"],
    "A.8.3": ["NR-DATA-EXFIL"], "A.8.4": ["NR-MIGRATION-DATAINTEGRITY"],
    "A.8.5": ["NR-PROD-COMPROMISE"], "A.8.6": ["NR-PLATFORM-OUTAGE", "NR-DATA-AVAILABILITY"],
    "A.8.7": ["NR-ENDPOINT-MALWARE"], "A.8.8": ["NR-PROD-COMPROMISE", "NR-ENDPOINT-MALWARE"],
    "A.8.9": ["NR-MIGRATION-AVAILABILITY"], "A.8.11": ["NR-DATA-RESIDENCY", "NR-DATA-EXFIL"],
    "A.8.12": ["NR-DATA-EXFIL"], "A.8.13": ["NR-DATA-AVAILABILITY", "NR-MIGRATION-DATAINTEGRITY"],
    "A.8.14": ["NR-PLATFORM-OUTAGE"], "A.8.15": ["NR-ABUSE-DETECTION", "NR-PROD-COMPROMISE"],
    "A.8.16": ["NR-ABUSE-DETECTION", "NR-CARD-TESTING"], "A.8.18": ["NR-PROD-COMPROMISE"],
    "A.8.19": ["NR-ENDPOINT-MALWARE"],  # v3.1 §1a: software-installation control, moved Prod -> malware
    "A.8.20": ["NR-PROD-COMPROMISE"],
    "A.8.21": ["NR-PLATFORM-OUTAGE"], "A.8.22": ["NR-PROD-COMPROMISE"],
    "A.8.23": ["NR-ENDPOINT-MALWARE"], "A.8.24": ["NR-DATA-EXFIL", "NR-DATA-RESIDENCY"],
    "A.8.25": ["NR-MIGRATION-DATAINTEGRITY"], "A.8.26": ["NR-CARD-TESTING"],
    "A.8.27": ["NR-PROD-COMPROMISE"],  # v3.1 §1a Prod keep-15
    "A.8.28": ["NR-MIGRATION-DATAINTEGRITY"], "A.8.29": ["NR-MIGRATION-AVAILABILITY"],
    "A.8.30": ["NR-MODEL-SUPPLY"], "A.8.31": ["NR-MIGRATION-AVAILABILITY"],
    "A.8.32": ["NR-MIGRATION-AVAILABILITY", "NR-MIGRATION-DATAINTEGRITY"],
    "A.8.33": ["NR-DATA-QUALITY"], "A.8.34": ["NR-PCI-SCOPE"],
    # Data-quality / pipeline integrity controls:
    "A.5.12": ["NR-DATA-QUALITY"], "A.8.10": ["NR-DATA-RESIDENCY"],
}

def named_risks_for(ref: str, theme: str) -> list[str]:
    """Named risks a control mitigates: the explicit, causally-defensible map only
    (SPEC v3.1 §1). There is **no theme fallback** — whole-theme attachment (every
    A.5/A.8 to Prod-compromise, every A.6/A.7 to Endpoint-malware) was tags, not
    relatedness, and inflated two risks' maps to 32 and 25. A control with no
    listed risk is genuinely unmapped, which is the expected state of an
    illustration, not a finding (the unmapped-control flag is retired, §2).
    ``theme`` is unused, kept for the render signature."""
    return CONTROL_NAMED_RISKS.get(ref, [])

CONTROL_YAML_HEAD = """\
# The ISO/IEC 27001:2022 Annex A control backbone -- all 93 controls across the
# four themes (Organizational A.5, People A.6, Physical A.7, Technological A.8;
# 37/8/14/34). Keyed by Annex A reference so the full set is unambiguously
# seeded (SPEC §2.6). Each control names its governing policy (the "traces up to
# a policy" coverage read) and the named risks it mitigates (M2M), mapped only
# where there is a causal path (SPEC v3.1 §1). A control mapping to no named risk
# is simply unexercised in this illustration, not a flag. Control HEALTH is
# derived at build time (SPEC §4), never stored.
# All data synthetic.

"""


# External requirement ids a control satisfies (v4.0 §0.A) — the inverse of
# ``regulations.yaml``'s ``satisfied_by_controls`` and kept consistent with it
# (the GRC build cross-checks the two directions). Human-ratified illustrative
# mappings, not authored by the tool. Inert for the eng build (lands in .raw).
CONTROL_FRAMEWORK_REFS = {
    "A.5.1": ["DORA-P1-ICT-RISK-MGMT"],
    "A.5.6": ["DORA-P5-INFO-SHARING"],
    "A.5.16": ["PCI-REQ-8"],
    "A.5.17": ["PCI-REQ-8"],
    "A.5.19": ["DORA-P4-THIRD-PARTY-RISK"],
    "A.5.20": ["DORA-P4-THIRD-PARTY-RISK"],
    "A.5.21": ["DORA-P4-THIRD-PARTY-RISK"],
    "A.5.22": ["DORA-P4-THIRD-PARTY-RISK"],
    "A.5.24": ["DORA-P2-INCIDENT-REPORTING"],
    "A.5.26": ["DORA-P2-INCIDENT-REPORTING"],
    "A.5.30": ["DORA-P3-RESILIENCE-TESTING"],
    "A.8.5": ["PCI-REQ-8"],
    "A.8.8": ["DORA-P1-ICT-RISK-MGMT", "DORA-P3-RESILIENCE-TESTING", "PCI-REQ-11"],
    "A.8.15": ["DORA-P2-INCIDENT-REPORTING", "PCI-REQ-10"],
    "A.8.16": ["PCI-REQ-10"],
    "A.8.29": ["PCI-REQ-11"],
}


# QBR v4.0 §1.B: business ownership of a control lives in the business, not GRC.
# A mapped control's business_owner is the lead who owns the risk it defends;
# owner_confirmed_on is when they last re-affirmed it (drives metric 2c). Two
# controls are deliberately stale (confirmed long ago) and A.5.8 is the hole —
# a business_owner named but never confirmed (§1.G). All inert for eng.
_OWNER_UNCONFIRMED = {"A.5.8"}                 # named but no owner_confirmed_on
_OWNER_STALE = {"A.5.14", "A.8.3"}            # confirmed outside cadence


def render_controls() -> str:
    nr_owner = {t[0]: t[4] for t in NAMED_RISKS}
    out = [CONTROL_YAML_HEAD]
    for theme, titles in ANNEX_A.items():
        clause = _THEME_CLAUSE[theme]
        out.append(f"# --- {theme} (A.{clause}.1-A.{clause}.{len(titles)}, {len(titles)}) ---\n")
        for i, title in enumerate(titles, start=1):
            ref = f"A.{clause}.{i}"
            policy = CONTROL_POLICY.get(ref, "POL-INFOSEC")
            risks = named_risks_for(ref, theme)
            risks_render = "[" + ", ".join(risks) + "]" if risks else "[]"
            entry = (
                f'"{ref}":\n'
                f"  title: {title}\n"
                f"  theme: {theme}\n"
                f"  policy: {policy}\n"
                f"  mapped_named_risks: {risks_render}\n"
            )
            frefs = CONTROL_FRAMEWORK_REFS.get(ref)
            if frefs:
                entry += f"  framework_refs: [{', '.join(frefs)}]\n"
            if risks:  # a control that defends a risk has a business owner
                entry += f"  business_owner: {nr_owner.get(risks[0], '')}\n"
                if ref in _OWNER_UNCONFIRMED:
                    pass
                elif ref in _OWNER_STALE:
                    entry += "  owner_confirmed_on: 2024-10-15\n"
                else:
                    entry += "  owner_confirmed_on: 2026-03-01\n"
            out.append(entry)
        out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# 5. Named risks -- Tier 2 (SPEC §2.3). Appetite is AUTHORED, never derived
#    (SPEC v2.2 §D): each threshold is a round number a second line would set
#    from what Company Corp tolerates for that risk -- regulatory constraint,
#    strategic upside, reversibility, concentration -- with no reference to the
#    residual. The RAG colour is then an OUTCOME of that authored line meeting
#    tuned exposure (SPEC v2.2 §B), not a target fitted to.
# ---------------------------------------------------------------------------
# (id, title, short_title, domain, owner, appetite_threshold, appetite_rationale,
#  threatens_okrs). short_title is the two-to-four-word headline the dashboard
# shows (SPEC v2.4 §3); the full title stays for drill-down and tooltips.

NAMED_RISKS = [
    # TR-SECURITY (7)
    ("NR-PROD-COMPROMISE", "Compromise of production systems via credential or access failure",
     "Production compromise",
     "TR-SECURITY", "security-eng-lead@company.com", 1500000,
     "Core-launch risk; some tolerance during the rebuild, but production compromise erodes customer trust fast.",
     ["gcloud-migration", "core-platform"]),
    ("NR-DATA-EXFIL", "Exfiltration of regulated data from an analytics or export path",
     "Regulated data exfiltration",
     "TR-SECURITY", "security-eng-lead@company.com", 2000000,
     "Regulated data, but exfil is adversarial and partly insurable; moderate tolerance.",
     ["data-platform"]),
    ("NR-PAYMENT-FRAUD", "Fraudulent transactions against the payments platform",
     "Payment fraud",
     "TR-SECURITY", "payments-lead@company.com", 2500000,
     "Fraud is a managed cost of running payments; higher tolerance, tracked against margin.",
     ["payments-launch"]),
    ("NR-ENDPOINT-MALWARE", "Malware on a corporate endpoint leading to lateral movement",
     "Endpoint malware",
     "TR-SECURITY", "it-lead@company.com", 2000000,
     "Recoverable with EDR and reimaging; moderate tolerance.", ["internal-tools"]),
    ("NR-CARD-TESTING", "Automated card-testing against the public checkout flow",
     "Card-testing attacks",
     "TR-SECURITY", "payments-lead@company.com", 1500000,
     "Financial and recoverable; velocity limits cap the downside.", ["payments-launch"]),
    ("NR-ABUSE-ESCALATION", "Unmitigated abuse escalating on the platform",
     "Abuse escalation",
     "TR-SECURITY", "tns-lead@company.com", 1500000,
     "Reputational; moderate tolerance backed by an SLA-driven response.", ["trust-and-safety"]),
    ("NR-ABUSE-DETECTION", "Gaps in automated detection of policy-violating content",
     "Abuse-detection gaps",
     "TR-SECURITY", "tns-lead@company.com", 1500000,
     "Detection gaps are recoverable via retrain; moderate tolerance.", ["trust-and-safety"]),
    # TR-RESILIENCE (2)
    ("NR-PLATFORM-OUTAGE", "Customer-facing outage of a core platform service",
     "Platform outage",
     "TR-RESILIENCE", "platform-lead@company.com", 2500000,
     "Availability risk knowingly carried to sustain launch velocity; bounded by SLA credits.",
     ["core-platform"]),
    ("NR-DATA-AVAILABILITY", "Loss of availability of a core data platform service",
     "Data-platform outage",
     "TR-RESILIENCE", "data-platform-lead@company.com", 2000000,
     "Recoverable; failover reduces the blast radius.", ["data-platform"]),
    # TR-DATA-INTEGRITY (2) -- stays BELOW, but no longer the standout (SPEC v2.2 §F)
    ("NR-DATA-QUALITY", "Corrupted or unvalidated data feeding downstream decisions",
     "Data quality",
     "TR-DATA-INTEGRITY", "data-platform-lead@company.com", 2000000,
     "Correctness matters, but bad data is usually caught and reprocessed.", ["data-platform"]),
    ("NR-PIPELINE-INTEGRITY", "Schema-invalid or corrupted writes entering the data pipeline",
     "Pipeline integrity",
     "TR-DATA-INTEGRITY", "data-platform-lead@company.com", 2000000,
     "Recoverable via replay; write-time gates cap the downside.", ["data-platform"]),
    # TR-PRIVACY (5) -- regulated, low tolerance across the board; the standout
    # amber-end-to-end domain (SPEC v2.2 §F). Over-control is the canonical
    # regulated failure: gold-plating the domain no one thinks about.
    ("NR-DATA-RESIDENCY", "Regulated customer data processed or stored outside its required region",
     "Data residency",
     "TR-PRIVACY", "privacy-eng-lead@company.com", 650000,
     "Regulated data; low tolerance regardless of delivery upside.", ["data-platform", "data-residency"]),
    ("NR-SUBPROCESSOR-GOV", "Ungoverned subprocessor handling of regulated data",
     "Subprocessor governance",
     "TR-PRIVACY", "privacy-eng-lead@company.com", 500000,
     "Regulated third-party processing; low tolerance -- a licence-to-operate risk.", ["data-platform"]),
    ("NR-DATA-RETENTION", "Personal data retained beyond its lawful retention window",
     "Data over-retention",
     "TR-PRIVACY", "privacy-eng-lead@company.com", 600000,
     "Over-retention of PII is a pure obligation failure; low tolerance.", ["data-platform"]),
    ("NR-CONSENT-MGMT", "Tracking or processing without valid, current consent",
     "Consent management",
     "TR-PRIVACY", "privacy-eng-lead@company.com", 750000,
     "Consent and tracking are regulator-facing; low tolerance regardless of product upside.",
     ["mobile-app"]),
    ("NR-PII-MINIMIZATION", "Collecting or exposing more personal data than needed",
     "PII minimization",
     "TR-PRIVACY", "privacy-eng-lead@company.com", 500000,
     "Excess PII only adds liability; low tolerance.", ["data-platform"]),
    # TR-CHANGE (3; one emerging)
    ("NR-MIGRATION-AVAILABILITY", "Availability regressions introduced by the migration",
     "Migration availability",
     "TR-CHANGE", "platform-lead@company.com", 2000000,
     "Elevated change risk deliberately accepted during the rebuild window.", ["gcloud-migration"]),
    ("NR-MIGRATION-DATAINTEGRITY", "Data integrity loss during monolith-to-microservices cutover",
     "Cutover data integrity",
     "TR-CHANGE", "platform-lead@company.com", 1500000,
     "Cutover integrity issues are recoverable with dual-write checks.", ["gcloud-migration"]),
    ("NR-AI-AGENT-AUTONOMY", "Autonomous agents taking unsafe action in production",
     "Unsafe agent autonomy",
     "TR-CHANGE", "ai-platform-lead@company.com", 1500000,
     "Emerging; a nominal tolerance pending the calibration to trust the number.", ["ai-platform"]),
    # TR-THIRDPARTY (3; one emerging)
    ("NR-VENDOR-ACCESS", "Excessive third-party vendor access to internal systems",
     "Vendor access",
     "TR-THIRDPARTY", "ciso-office@company.com", 2000000,
     "Vendor access is scoped and revocable; moderate tolerance.", ["mobile-app", "internal-tools"]),
    ("NR-SUPPLIER-OUTAGE", "A critical supplier's outage cascades into our service",
     "Supplier outage",
     "TR-THIRDPARTY", "ciso-office@company.com", 2000000,
     "External dependency; tolerance bounded by tested fallbacks.", ["core-platform"]),
    ("NR-MODEL-SUPPLY", "Concentration on a single external model provider",
     "Model-provider concentration",
     "TR-THIRDPARTY", "ai-platform-lead@company.com", 1500000,
     "Emerging; a nominal tolerance pending a tested fallback.", ["ai-platform"]),
    # TR-COMPLIANCE (2) -- regulated, low tolerance
    ("NR-PCI-SCOPE", "PCI scope expansion / cardholder data handling gap",
     "PCI scope creep",
     "TR-COMPLIANCE", "payments-lead@company.com", 1000000,
     "PCI is pass/fail with the card schemes; low tolerance.", ["payments-launch"]),
    ("NR-REG-FILINGS", "Missed regulatory filing or lapsed certification",
     "Regulatory filings",
     "TR-COMPLIANCE", "compliance-lead@company.com", 1000000,
     "Filing obligations are binary; low tolerance.", ["run-the-business"]),
    # v4.0 §0.H: the deliberately UNSCORED named risk — registered and owned,
    # zero scenarios, so the GRC coverage tile has something real to catch. The
    # small placeholder appetite is authored ahead of the first quantified
    # scenario (still authored, never derived) and is deliberately small enough
    # not to move the eng dashboard's rendered bottom-up appetite total (P.4:
    # $36.55M and 3.655x still render as $36.5M / 3.65x).
    ("NR-AI-DISCLOSURE", "Undisclosed AI-generated content in regulated external communications",
     "AI disclosure",
     "TR-COMPLIANCE", "gc-office@company.com", 50000,
     "New obligation; provisionally low tolerance until the first scenario is scored.", []),
]

# v4.0 §0.A: risk-review currency (last_reviewed, review_cadence) per named
# risk, for the GRC tab's review-currency SLA. Derived overdue only; the eng
# build never reads these (they land in .raw). NR-DATA-RETENTION and
# NR-CONSENT-MGMT deliberately read overdue at the 2026-06-18 reference date.
NAMED_RISK_REVIEWS = {
    "NR-PROD-COMPROMISE": ("2026-05-12", "annual"),
    "NR-DATA-EXFIL": ("2026-04-21", "annual"),
    "NR-PAYMENT-FRAUD": ("2026-03-17", "annual"),
    "NR-ENDPOINT-MALWARE": ("2026-02-09", "annual"),
    "NR-CARD-TESTING": ("2026-03-17", "annual"),
    "NR-ABUSE-ESCALATION": ("2026-01-28", "annual"),
    "NR-ABUSE-DETECTION": ("2026-01-28", "annual"),
    "NR-PLATFORM-OUTAGE": ("2026-05-06", "annual"),
    "NR-DATA-AVAILABILITY": ("2026-02-25", "annual"),
    "NR-DATA-QUALITY": ("2026-02-25", "annual"),
    "NR-PIPELINE-INTEGRITY": ("2026-02-25", "annual"),
    "NR-DATA-RESIDENCY": ("2026-04-08", "annual"),
    "NR-SUBPROCESSOR-GOV": ("2026-04-08", "annual"),
    "NR-DATA-RETENTION": ("2025-05-14", "annual"),
    "NR-CONSENT-MGMT": ("2025-06-02", "annual"),
    "NR-PII-MINIMIZATION": ("2026-04-08", "annual"),
    "NR-MIGRATION-AVAILABILITY": ("2026-05-20", "annual"),
    "NR-MIGRATION-DATAINTEGRITY": ("2026-05-20", "annual"),
    "NR-AI-AGENT-AUTONOMY": ("2026-06-02", "annual"),
    "NR-VENDOR-ACCESS": ("2026-03-30", "annual"),
    "NR-SUPPLIER-OUTAGE": ("2026-03-30", "annual"),
    "NR-MODEL-SUPPLY": ("2026-06-02", "annual"),
    "NR-PCI-SCOPE": ("2026-04-15", "annual"),
    "NR-REG-FILINGS": ("2026-04-15", "annual"),
    "NR-AI-DISCLOSURE": ("2026-06-02", "annual"),
}

# QBR v4.0 §1.B: per-risk lifecycle + business linkage.
#   raised_on / scored_on -> the "time to understand" speed metric (1b);
#   source (business | grc)  -> the "business-raised share" value metric (1c);
#   estate_units             -> the coverage link (1a), populated with COARSE
#                               BUSINESS UNITS (the borrowed denominator), not a
#                               service inventory GRC would have to maintain.
# The business unit 'mobile' is deliberately unreferenced here: the org ships
# mobile (two mobile OKRs) but GRC owns no risk for it — the estate-coverage
# gap (§1.G). scored_on is None for the deliberately-unscored NR-AI-DISCLOSURE.
# All inert for the engineering build (land in .raw). Synthetic.
NAMED_RISK_QBR = {
    "NR-PROD-COMPROMISE": ("2025-11-03", "2025-11-18", "grc", ["platform"]),
    "NR-DATA-EXFIL": ("2025-11-10", "2025-11-24", "grc", ["data-platform"]),
    "NR-PAYMENT-FRAUD": ("2025-09-15", "2025-09-30", "business", ["payments"]),
    "NR-ENDPOINT-MALWARE": ("2025-10-01", "2025-10-14", "grc", ["corp-it"]),
    "NR-CARD-TESTING": ("2025-12-05", "2025-12-19", "business", ["payments"]),
    "NR-ABUSE-ESCALATION": ("2025-10-20", "2025-11-05", "grc", ["trust-and-safety"]),
    "NR-ABUSE-DETECTION": ("2025-10-20", "2025-11-06", "grc", ["trust-and-safety"]),
    "NR-PLATFORM-OUTAGE": ("2026-05-06", "2026-05-21", "business", ["platform"]),
    "NR-DATA-AVAILABILITY": ("2026-01-14", "2026-01-27", "grc", ["data-platform"]),
    "NR-DATA-QUALITY": ("2026-02-25", "2026-03-10", "grc", ["data-platform"]),
    "NR-PIPELINE-INTEGRITY": ("2026-02-25", "2026-03-11", "business", ["data-platform"]),
    "NR-DATA-RESIDENCY": ("2026-04-08", "2026-04-19", "business", ["privacy-legal"]),
    "NR-SUBPROCESSOR-GOV": ("2026-01-20", "2026-02-03", "grc", ["privacy-legal"]),
    "NR-DATA-RETENTION": ("2025-05-01", "2025-05-14", "grc", ["privacy-legal"]),
    "NR-CONSENT-MGMT": ("2025-06-01", "2025-06-15", "grc", ["privacy-legal"]),
    "NR-PII-MINIMIZATION": ("2026-04-08", "2026-04-20", "grc", ["privacy-legal"]),
    "NR-MIGRATION-AVAILABILITY": ("2026-05-20", "2026-06-05", "grc", ["platform"]),
    "NR-MIGRATION-DATAINTEGRITY": ("2026-05-20", "2026-06-03", "business", ["platform", "data-platform"]),
    "NR-AI-AGENT-AUTONOMY": ("2026-04-10", "2026-04-22", "business", ["ai-platform"]),
    "NR-VENDOR-ACCESS": ("2025-12-10", "2025-12-22", "grc", ["corp-it"]),
    "NR-SUPPLIER-OUTAGE": ("2025-12-10", "2025-12-23", "grc", ["platform"]),
    "NR-MODEL-SUPPLY": ("2026-04-15", "2026-05-02", "business", ["ai-platform"]),
    "NR-PCI-SCOPE": ("2026-01-05", "2026-01-19", "grc", ["payments"]),
    "NR-REG-FILINGS": ("2025-11-15", "2025-11-29", "grc", ["privacy-legal"]),
    "NR-AI-DISCLOSURE": ("2026-06-02", None, "grc", ["ai-platform"]),
}

# The coarse business-unit denominator (§2.2 feasibility rule: borrow, don't
# build). Held once here; also seeded into program_period.yaml. 'mobile' is the
# deliberate coverage gap. Labelled "business units" on the page.
BUSINESS_UNITS = ["payments", "platform", "data-platform", "trust-and-safety",
                  "privacy-legal", "ai-platform", "corp-it", "mobile"]

NAMED_RISK_YAML_HEAD = """\
# Tier 2 -- the owned, appetite-bearing risk (executive / VP altitude, SPEC §2.3).
# Each names its Tier-1 domain (many-to-one), the accountable owner, the OKRs it
# threatens (M2M, SPEC §2.12), and a per-risk dollar appetite. Appetite is
# AUTHORED, not derived (SPEC v2.2 §D): a round number a governance forum would
# set from what the company tolerates for that risk, with an appetite_rationale
# recording why. The RAG colour is an outcome of that line meeting tuned
# exposure, never a target the threshold was fitted to. Every threshold sits
# under the $15M enterprise capacity (SPEC v2.1 §D1). All data synthetic.

"""


def render_named_risks() -> str:
    out = [NAMED_RISK_YAML_HEAD]
    for nid, title, short_title, domain, owner, threshold, rationale, okrs in NAMED_RISKS:
        okr_render = "[" + ", ".join(okrs) + "]"
        reviewed, cadence = NAMED_RISK_REVIEWS[nid]
        raised_on, scored_on, source, units = NAMED_RISK_QBR[nid]
        block = (
            f"{nid}:\n"
            f"  title: {title}\n"
            f"  short_title: {short_title}\n"
            f"  domain: {domain}\n"
            f"  owner: {owner}\n"
            f"  appetite_threshold: {threshold}\n"
            f'  appetite_rationale: "{rationale}"\n'
            f"  threatens_okrs: {okr_render}\n"
            f"  last_reviewed: {reviewed}\n"
            f"  review_cadence: {cadence}\n"
            f"  raised_on: {raised_on}\n"
            f"  source: {source}\n"
            f"  estate_units: [{', '.join(units)}]\n"
        )
        if scored_on is not None:
            block += f"  scored_on: {scored_on}\n"
        out.append(block)
    return "\n".join(out)


# ---------------------------------------------------------------------------
# 6. Scenarios -- Tier 3 (SPEC §2.4). Rescaled baselines (SPEC v2.1 §D4): loss
#    magnitudes brought down so the baseline-only aggregate sits under the $10M
#    appetite, leaving room for exceptions to push residual modestly over it.
# ---------------------------------------------------------------------------
# (id, title, named_risk, OF, PoR, LM, impact, vectors, lifecycle, trajectory)

SCENARIOS = [
    # --- TR-SECURITY ---
    # PROD-COMPROMISE trimmed toward its $1.5M appetite (SPEC v2.5 §3 rebalance):
    # it still reads OVER through gate 1 (a wide right tail keeps P(exceed) well
    # above 1/3), not because the mean sits far past the line — the canonical
    # gate-1 case. Accumulation story intact (nine legacy-auth exceptions move
    # PoR; LM is the trim lever, dominance preserved).
    ("SCN-2026-0001", "Account takeover of an internal admin console", "NR-PROD-COMPROMISE",
     [10, 40], [0.008, 0.024], [370000, 1200000], ["financial", "individual_harm"],
     ["adversarial"], "managed", "rising"),
    ("SCN-2026-0019", "Admin-console takeover via unrotated migrated service accounts", "NR-PROD-COMPROMISE",
     [8, 24], [0.007, 0.022], [270000, 910000], ["financial", "individual_harm"],
     ["adversarial"], "managed", "stable"),
    ("SCN-2026-0002", "Exfiltration of regulated data via an analytics export path", "NR-DATA-EXFIL",
     [20, 58], [0.008, 0.026], [120000, 1150000], ["financial", "individual_harm", "regulatory"],
     ["adversarial"], "managed", "stable"),
    ("SCN-2026-0003", "Fraudulent transactions against the payments platform", "NR-PAYMENT-FRAUD",
     [15, 45], [0.01, 0.03], [60000, 260000], ["financial", "public_market_harm"],
     ["adversarial"], "managed", "stable"),
    ("SCN-2026-0012", "Malware on a corporate endpoint leads to lateral movement", "NR-ENDPOINT-MALWARE",
     [30, 90], [0.008, 0.026], [50000, 190000], ["financial"],
     ["adversarial"], "managed", "stable"),
    ("SCN-2026-0015", "Automated card-testing lands fraudulent charges at checkout", "NR-CARD-TESTING",
     [20, 55], [0.012, 0.033], [70000, 300000], ["financial", "individual_harm"],
     ["adversarial"], "managed", "stable"),
    # ABUSE-ESCALATION retuned to sit AT its $1.5M appetite (mean ~78%), the
    # second Security green so the domain reads mixed (SPEC v2.5 §3). LM lever.
    ("SCN-2026-0007", "Unmitigated abuse escalating on the platform", "NR-ABUSE-ESCALATION",
     [34, 44], [0.024, 0.044], [740000, 940000], ["individual_harm", "reputational"],
     ["adversarial"], "managed", "stable"),
    # ABUSE-DETECTION sits AT its $1.5M appetite (mean ~78%, moderate uncertainty),
    # the second Security green so the domain reads mixed (SPEC v2.5 §3). No
    # exception here, so all three factors are tuned to a tight, controlled band.
    ("SCN-2026-0008", "Detection model misses policy-violating content at scale", "NR-ABUSE-DETECTION",
     [35, 42], [0.022, 0.04], [810000, 960000], ["individual_harm", "public_market_harm"],
     ["adversarial"], "managed", "stable"),
    # --- TR-RESILIENCE ---
    # PLATFORM-OUTAGE stays the clean OVER: mean above its $2.5M appetite, so the
    # bar sits past the tick on view 1 (the plain "over the line" case, next to
    # Prod-compromise's tail-driven one). Trimmed modestly in the v2.5 rebalance.
    # Mean just over its $2.5M appetite with a wide-enough tail to keep P(exceed)
    # past 1/3 — the clean OVER on view 1 (bar past the tick), trimmed in the v2.5
    # rebalance so the portfolio keeps headroom to the $15M capacity.
    # OVER via gate 0 (mean above its $2.5M appetite) with a deliberately TIGHT
    # tail, so it reads red on position without inflating the portfolio's
    # materiality tail (SPEC v2.8 §1). The clean "bar past the tick" case.
    ("SCN-2026-0013", "Customer-facing outage of a core platform service", "NR-PLATFORM-OUTAGE",
     [41, 46], [0.021, 0.026], [1240000, 1360000], ["financial", "public_market_harm"],
     [], "managed", "rising"),
    ("SCN-2026-0006", "Loss of availability of a core data platform service", "NR-DATA-AVAILABILITY",
     [10, 35], [0.01, 0.038], [70000, 300000], ["financial"],
     [], "managed", "stable"),
    # --- TR-DATA-INTEGRITY -- data-quality sits AT its $2M appetite (mean ~78%,
    # moderate uncertainty) so it reads green under the two-gate rule and the
    # domain is not amber end to end (SPEC v2.5 §3). LM lever. ---
    ("SCN-2026-0005", "Corrupted or unvalidated data feeds a downstream decision", "NR-DATA-QUALITY",
     [23, 26], [0.025, 0.043], [1580000, 1740000], ["financial", "individual_harm"],
     [], "managed", "stable"),
    ("SCN-2026-0016", "Schema-invalid writes corrupt a downstream pipeline decision", "NR-PIPELINE-INTEGRITY",
     [6, 18], [0.01, 0.035], [100000, 400000], ["financial"],
     [], "managed", "receding"),
    # --- TR-PRIVACY (5) -- deliberately LOW exposure: the over-controlled,
    # amber-end-to-end domain (SPEC v2.2 §F). Consent is the dramatic standout.
    ("SCN-2026-0014", "Regulated data leaves its required residency region", "NR-DATA-RESIDENCY",
     [6, 14], [0.02, 0.05], [150000, 600000], ["regulatory", "individual_harm"],
     [], "managed", "receding"),
    ("SCN-2026-0018", "Subprocessor mishandles regulated data without a governed DPA", "NR-SUBPROCESSOR-GOV",
     [4, 12], [0.02, 0.05], [120000, 500000], ["regulatory", "individual_harm"],
     ["third_party"], "managed", "receding"),
    ("SCN-2026-0021", "Personal data retained past its lawful retention window", "NR-DATA-RETENTION",
     [3, 10], [0.02, 0.05], [120000, 550000], ["regulatory"],
     [], "managed", "receding"),
    ("SCN-2026-0022", "Tracking pixel fires before consent is captured", "NR-CONSENT-MGMT",
     [4, 12], [0.02, 0.05], [120000, 480000], ["regulatory", "individual_harm"],
     [], "managed", "receding"),
    ("SCN-2026-0023", "A form collects more personal data than the feature needs", "NR-PII-MINIMIZATION",
     [3, 9], [0.02, 0.05], [100000, 450000], ["regulatory"],
     [], "managed", "stable"),
    # --- TR-CHANGE -- migration-availability sits AT its $2M appetite (mean ~80%,
    # moderate uncertainty) so it reads green and Change is not amber end to end
    # (SPEC v2.5 §3). No exception here, so all three factors are tuned. ---
    ("SCN-2026-0009", "Availability regression introduced by the migration", "NR-MIGRATION-AVAILABILITY",
     [24, 28], [0.033, 0.045], [1360000, 1650000], ["financial"],
     [], "managed", "rising"),
    ("SCN-2026-0010", "Data integrity loss during monolith-to-microservices cutover", "NR-MIGRATION-DATAINTEGRITY",
     [5, 16], [0.01, 0.035], [150000, 650000], ["financial", "individual_harm"],
     [], "managed", "rising"),
    # --- TR-THIRDPARTY ---
    ("SCN-2026-0011", "Excessive third-party vendor access to internal systems", "NR-VENDOR-ACCESS",
     [5, 18], [0.008, 0.03], [150000, 700000], ["financial", "individual_harm"],
     ["third_party"], "managed", "stable"),
    # SUPPLIER sits AT its $2M appetite (mean ~78%, moderate uncertainty) so it
    # reads green and Third-party is not amber end to end (SPEC v2.5 §3). LM lever
    # (EXC-0164 moves PoR).
    ("SCN-2026-0020", "A critical supplier outage cascades into our service", "NR-SUPPLIER-OUTAGE",
     [18, 23], [0.03, 0.048], [1720000, 1910000], ["financial"],
     ["third_party"], "managed", "stable"),
    # --- TR-COMPLIANCE -- PCI raised so it reads OVER its $1M low tolerance (an
    # orphan: no funded remediation addresses it, §E story 3). ---
    # PCI-SCOPE trimmed toward its $1M appetite (v2.5 §3 rebalance); still OVER
    # through gate 1 via a wide tail. Remains an orphan (no funded remediation).
    ("SCN-2026-0004", "Cardholder data handling gap expands PCI scope", "NR-PCI-SCOPE",
     [9, 13], [0.032, 0.062], [640000, 1560000], ["financial", "regulatory"],
     [], "managed", "rising"),
    ("SCN-2026-0017", "Missed quarterly regulatory filing triggers a penalty", "NR-REG-FILINGS",
     [2, 6], [0.03, 0.1], [150000, 700000], ["regulatory", "financial"],
     [], "managed", "stable"),
    # --- Emerging: wide, moving intervals, AI vector (held out of appetite math).
    # Deliberately NOT uniform (SPEC v2.8 §5b): one rising and breach-if-promoted,
    # one stable, one receding that would stay within appetite if it firmed up. ---
    ("SCN-2026-0031", "Confidently-wrong automated decisioning at scale on a single model provider", "NR-MODEL-SUPPLY",
     [5, 60], [0.02, 0.30], [400000, 9000000], ["financial", "individual_harm", "public_market_harm"],
     ["ai", "third_party"], "emerging", "rising"),
    ("SCN-2026-0032", "Autonomous agent triggers an unsafe production action", "NR-AI-AGENT-AUTONOMY",
     [3, 40], [0.01, 0.25], [300000, 7000000], ["financial", "individual_harm"],
     ["ai"], "emerging", "stable"),
    # Receding and modest: mitigations are landing, and even if promoted its band
    # stays under the $1.5M abuse-detection appetite — an emerging item that is NOT
    # a foregone breach.
    ("SCN-2026-0033", "Silent training-data drift degrades the abuse-detection model", "NR-ABUSE-DETECTION",
     [8, 40], [0.01, 0.05], [120000, 700000], ["individual_harm", "public_market_harm"],
     ["ai"], "emerging", "receding"),
    # --- Internal-operations AI (SPEC v3.4 §2, built per the v3.4 sizing decision):
    # small, real, and EMERGING. AI as an operational *practice*, not a product
    # feature — the median blind spot the product lens alone misses. Each attaches
    # to an existing named risk in the right domain and is authored at honest,
    # modest exposure; deliberately NOT sized up to balance the product lens (the
    # asymmetry is the point, §4). Each carries the `ai` causation vector so the
    # coverage lens (§3) picks it up. They are `emerging`, not managed: at their
    # honest ~$0.7M size, folding them into the live appetite math pushed the
    # portfolio's P(>capacity) from 6% to 28% (the corpus runs a deliberately tight
    # $15M materiality headroom, v2.8 §1). Held out, they keep that invariant intact
    # and still answer the coverage question — internal AI exposure is real, small,
    # and not yet in the live numbers. Factors authored to plausible CIs, not
    # reverse-solved to a target (v2.2 §B).
    # The `internal_ops` vector marks these as AI in *how we build*, not in the
    # product — the coverage lens (§3) splits the two blocks on it. A locus marker,
    # the same shape as `third_party` (where the risk originates), not a causation
    # mechanism like `ai`/`adversarial`.
    ("SCN-2026-0034", "AI-generated code introduces a vulnerability into production", "NR-PROD-COMPROMISE",
     [9, 22], [0.035, 0.09], [260000, 820000], ["financial", "individual_harm"],
     ["ai", "internal_ops"], "emerging", "rising"),
    ("SCN-2026-0035", "Regulated data pasted into an external LLM", "NR-DATA-EXFIL",
     [6, 16], [0.032, 0.085], [210000, 780000], ["financial", "regulatory", "individual_harm"],
     ["ai", "internal_ops"], "emerging", "rising"),
    ("SCN-2026-0036", "Copilot-accelerated shipping outpaces review", "NR-PIPELINE-INTEGRITY",
     [6, 16], [0.024, 0.062], [140000, 520000], ["financial"],
     ["ai", "internal_ops"], "emerging", "stable"),
]

# Short display headlines for the internal-ops AI scenarios (SPEC v3.4 §2). Kept
# as a side-table so the existing scenario files are untouched (acceptance 8: the
# corpus gains three files, no others change). Emitted as `short_title` by
# render_scenario; scenarios without one fall back to their full title.
SCENARIO_SHORT_TITLES = {
    "SCN-2026-0034": "AI-generated code vuln",
    "SCN-2026-0035": "Data into an external LLM",
    "SCN-2026-0036": "Copilot outpaces review",
}

# The stored output of the offline AI incident->scenario mapping step, keyed by
# the scenario it produced. See ``map_incident_to_scenario`` for the seam.
SCENARIO_INCIDENTS = {
    "SCN-2026-0019": {
        "ticket_id": "INC-2026-0442",
        "description": "Migrated batch workloads authenticated with long-lived service "
                       "accounts that were never rotated; one leaked in a repo and granted "
                       "console-adjacent access before revocation.",
        "suggested_domain": "TR-SECURITY",
        "suggested_named_risk": "NR-PROD-COMPROMISE",
        "suggested_factor": "probability_of_realization",
        "suggested_band": [0.03, 0.09],
        "mapped_by": "offline-ai-incident-mapper",
        "mapped_on": "2026-06-10",
        "note": "Synthetic; produced once offline by the corpus generator seam (SPEC §8).",
    }
}


def map_incident_to_scenario(scenario_id: str) -> dict | None:
    """SEAM — incident → scenario AI mapping, stubbed as data (SPEC §8, §5 story 8).

    *Automation as data plus a documented extension point* (SPEC §1.4): this is
    the seam, not the machine. In a real build this step runs **once, offline**,
    calling the Anthropic API (the newsletter/profiler pattern): given a
    free-text incident ticket it proposes a domain, named risk, target scenario,
    the single factor it moves, and a band — which a human confirms before the
    record is written into the corpus. The output carries ``mapped_by`` /
    ``mapped_on`` provenance so a reader can see it came from the model, not a
    person.

    Here no API is called at generation time; the one offline result is stored
    in ``SCENARIO_INCIDENTS`` and returned verbatim, so the dashboard's worked
    AI example (SPEC §6) shows an incident-linked scenario with no live
    dependency and a deterministic corpus.

    **To make it live:** repoint the input at a real incident queue (PagerDuty /
    Jira / ServiceNow), call the model per new ticket, and keep this return
    shape — the loader, the ``incident`` block written below, and the dashboard
    all read it unchanged. The mapping stays advisory: it moves an existing
    factor, never adds a term, and never auto-writes without confirmation.
    """
    return SCENARIO_INCIDENTS.get(scenario_id)

SCENARIO_HEAD = """\
# Tier 3 -- the quantified loss event the Monte Carlo runs on (SPEC §2.4). The
# baseline OF/PoR/LM lives here. Baselines are rescaled (SPEC v2.1 §D4) so the
# aggregate sits near the enterprise appetite rather than 12-30x over it. Each
# scenario names its Tier-2 named_risk, carries impact + vector tags, and a
# lifecycle_state (managed | emerging) with a trajectory. All synthetic.
"""


def render_scenario(spec) -> str:
    sid, title, nr, of, por, lm, impact, vectors, lifecycle, trajectory = spec
    impact_render = "[" + ", ".join(impact) + "]"
    vectors_render = "[" + ", ".join(vectors) + "]" if vectors else "[]"
    lines = [
        SCENARIO_HEAD,
        f"id: {sid}",
        f"title: {title}",
    ]
    if sid in SCENARIO_SHORT_TITLES:
        lines.append(f"short_title: {SCENARIO_SHORT_TITLES[sid]}")
    lines += [
        f"named_risk: {nr}",
        "baseline:",
        f"  opportunity_frequency_90ci: [{of[0]}, {of[1]}]",
        f"  probability_of_realization_90ci: [{por[0]}, {por[1]}]",
        f"  loss_magnitude_90ci: [{lm[0]}, {lm[1]}]",
        f"impact: {impact_render}",
        f"vectors: {vectors_render}",
        f"lifecycle_state: {lifecycle}",
        f"trajectory: {trajectory}",
    ]
    incident = map_incident_to_scenario(sid)  # SEAM (SPEC §8): offline AI mapping, stubbed as data
    if incident:
        lines.append("incident:")
        for k, v in incident.items():
            if k in ("description", "note"):
                lines.append(f'  {k}: "{v}"')
            else:
                lines.append(f"  {k}: {v}")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 7. Issues -- exceptions (self-contained, rescaled effects; including accepted
# vulnerabilities, v4.0 §0.0) and findings.
# ---------------------------------------------------------------------------
# Exception effects are rescaled (SPEC v2.1 §D3): each with_exception band is a
# plausible consequence of its control gap -- most a 1.2-2x move on the scenario,
# a few 3-5x for the severe cases. No 15-20x PoR jumps.

CAL = ["r.chen@company.com", "j.okafor@company.com", "p.nguyen@company.com",
       "a.silva@company.com", "m.haddad@company.com"]


def _exc(eid, title, owner, scn, control, moves, ci, est, *, filed_on, okr=None,
         reason="timeline", diverted_to=None, assets=None, mechanism="remediate_gap",
         target_date="2026-09-01", status="active", expires_on="2026-09-01",
         renewals=0, justification_changed_last=None, non_plan=False, decided_offset=4):
    """A self-contained v2 exception issue (type: exception).

    ``decided_on`` (QBR §1.B, filed_on + decided_offset) pairs with filed_on for
    the decision-speed metric (4b). Additive; inert for the engineering build.
    """
    lines = [
        f"id: {eid}",
        "type: exception",
        f"title: {title}",
        f"owner: {owner}",
        f"filed_on: {filed_on}",
        f"decided_on: {_plus_days(filed_on, decided_offset)}",
        f"status: {status}",
        f"mapped_scenarios: [{scn}]",
        f"control: [{control}]",
    ]
    if okr:
        lines.append(f"okr: {okr}")
    lines += [
        "exception_effect:",
        f"  moves: {moves}",
        f"  with_exception_90ci: [{ci[0]}, {ci[1]}]",
        f"  estimated_by: {est}",
        f"  estimated_on: {filed_on}",
        f"reason: {reason}",
    ]
    if reason == "resource_reallocation" and diverted_to:
        lines += ["reason_detail:", f"  diverted_to: {diverted_to}"]
    lines += ["scope:", "  type: enumerated", f"  assets: [{', '.join(assets or [scn.lower()])}]"]
    lines.append("remediation:")
    if non_plan:
        lines.append("  # NON-PLAN: no target_date and no mechanism -- sent back.")
        lines.append(f"  reduces: {moves}")
    else:
        lines += [f"  target_date: {target_date}", f"  mechanism: {mechanism}", f"  reduces: {moves}"]
    lines += [
        f"expires_on: {expires_on}",
        "renewals:",
        f"  count: {renewals}",
        f"  justification_changed_last: {justification_changed_last or 'null'}",
        "",
    ]
    return eid, "\n".join(lines)


def build_exceptions():
    """Return a list of (id, yaml_text) exceptions telling the designed stories."""
    out = []
    # --- Story 2: ACCUMULATION on NR-PROD-COMPROMISE (SCN-0001). Nine small
    # legacy-auth exceptions, each a modest 1.3-1.7x PoR move; together they take
    # the named risk over appetite. Four are diverted_to launches (story 7).
    # Spread across the two PROD-COMPROMISE scenarios so neither single scenario's
    # residual/baseline multiplier runs above ~5x (SPEC v2.1 §F check 7); the named
    # risk still sums OVER appetite.
    accum = [
        ("EXC-2026-0101", "Skip MFA on internal analytics console for cutover", "A.8.5", [0.016, 0.034], "SCN-2026-0001"),
        ("EXC-2026-0102", "Relax session timeout on legacy admin portal", "A.8.5", [0.015, 0.032], "SCN-2026-0001"),
        ("EXC-2026-0103", "Defer MFA rollout on internal wiki", "A.8.5", [0.014, 0.030], "SCN-2026-0001"),
        ("EXC-2026-0104", "Allow shared break-glass account on legacy jobs runner", "A.8.2", [0.016, 0.034], "SCN-2026-0001"),
        ("EXC-2026-0105", "Keep password-only auth on legacy build server", "A.8.5", [0.015, 0.032], "SCN-2026-0001"),
        ("EXC-2026-0106", "Defer MFA on internal feature-flag console", "A.8.5", [0.014, 0.030], "SCN-2026-0001"),
        ("EXC-2026-0107", "Allow legacy API keys on internal data browser", "A.5.17", [0.015, 0.033], "SCN-2026-0019"),
        ("EXC-2026-0108", "Skip MFA on legacy reporting console", "A.8.5", [0.015, 0.032], "SCN-2026-0019"),
        ("EXC-2026-0109", "Defer privileged-access review on migrated workloads", "A.8.2", [0.014, 0.030], "SCN-2026-0019"),
    ]
    dates = ["2026-01-14", "2026-02-06", "2026-02-22", "2026-03-08", "2026-03-20",
             "2026-05-08", "2026-05-14", "2026-05-21", "2026-05-27"]
    renew = {"EXC-2026-0102": 3, "EXC-2026-0105": 4}  # can-kicking (story 5)
    for i, (eid, title, ctrl, ci, scn) in enumerate(accum):
        out.append(_exc(
            eid, title, "platform-lead@company.com", scn, ctrl,
            "probability_of_realization", ci, CAL[i % len(CAL)], filed_on=dates[i],
            okr="gcloud-migration", reason="timeline" if i % 3 else "technical_constraint",
            mechanism="enforce_sso_via_idp", renewals=renew.get(eid, 0)))

    # --- Story 1 + single-large: NR-PLATFORM-OUTAGE (SCN-0013). One severe (~3-4x)
    # single-region acceptance dominates. ORPHAN: no funded remediation addresses it.
    out.append(_exc(
        "EXC-2026-0130", "Run core services single-region to cut infrastructure cost",
        "platform-lead@company.com", "SCN-2026-0013", "A.8.14",
        "probability_of_realization", [0.0345, 0.0425], "j.okafor@company.com",
        filed_on="2026-04-20", okr="gcloud-migration", reason="cost",
        mechanism="deploy_multi_region_active_active", target_date="2026-12-01",
        expires_on="2026-12-01"))
    out.append(_exc(
        "EXC-2026-0131", "Skip quarterly platform DR test to free the team for migration",
        "platform-lead@company.com", "SCN-2026-0013", "A.5.30",
        "probability_of_realization", [0.025, 0.037], "p.nguyen@company.com",
        filed_on="2026-05-20", okr="core-platform", reason="resource_reallocation",
        diverted_to="gcloud-migration", mechanism="resume_quarterly_dr_tests",
        target_date="2026-09-30", expires_on="2026-09-30", renewals=3))

    # --- DLP cluster on NR-DATA-EXFIL (SCN-0002): moderate LM moves. Both effects
    # must DOMINATE the SCN-0002 baseline LM [160k, 1900k] on loss_magnitude (SPEC
    # v2.3 §B3): disabling/sampling-down DLP can only raise the magnitude of an
    # exfiltration. 0140 (fully disabled) is the more severe. Data-exfil reads
    # BELOW under the v2.5 rule (mean ~50% of appetite, breach unlikely).
    dlp = [
        ("EXC-2026-0140", "DLP disabled on the analytics export path", [260000, 1350000], "cost"),
        ("EXC-2026-0141", "DLP sampling reduced on warehouse export job", [200000, 1200000], "technical_constraint"),
    ]
    for i, (eid, title, ci, reason) in enumerate(dlp):
        out.append(_exc(
            eid, title, "data-platform-lead@company.com", "SCN-2026-0002", "A.8.12",
            "loss_magnitude", ci, "a.silva@company.com", filed_on="2026-05-02",
            okr="data-platform", reason=reason, mechanism="re_enable_dlp_with_tuned_rules"))

    # --- Story 7: diverted_to starvation chain. Exceptions filed on STARVED OKRs
    # (payments-launch, trust-and-safety, data-platform) whose resources went TO
    # gcloud-migration. Modest PoR moves. ---
    diverted = [
        ("EXC-2026-0150", "Deferred fraud-rule tuning -- team pulled to migration",
         "payments-lead@company.com", "SCN-2026-0003", "A.8.16", [0.02, 0.05],
         "payments-launch", "tune_fraud_rules"),
        ("EXC-2026-0151", "Deferred PCI segmentation work -- staff on migration",
         "payments-lead@company.com", "SCN-2026-0004", "A.8.22", [0.06, 0.13],
         "payments-launch", "complete_network_segmentation"),
        ("EXC-2026-0152", "Delayed detection-model retrain -- ML team pulled to migration",
         "tns-lead@company.com", "SCN-2026-0008", "A.8.16", [0.026, 0.044],
         "trust-and-safety", "retrain_detection_model"),
        ("EXC-2026-0153", "Deferred data-validation checks -- engineers on migration",
         "data-platform-lead@company.com", "SCN-2026-0005", "A.8.33", [0.028, 0.05],
         "data-platform", "restore_validation_suite"),
        ("EXC-2026-0154", "Deferred HA failover testing -- on-call pulled to migration",
         "data-platform-lead@company.com", "SCN-2026-0006", "A.8.14", [0.02, 0.06],
         "data-platform", "schedule_failover_drills"),
    ]
    for i, (eid, title, owner, scn, ctrl, ci, okr, mech) in enumerate(diverted):
        moves = "probability_of_realization"
        out.append(_exc(
            eid, title, owner, scn, ctrl, moves, ci, CAL[i % len(CAL)],
            filed_on="2026-05-18", okr=okr, reason="resource_reallocation",
            diverted_to="gcloud-migration", mechanism=mech))

    # --- A spread of small within-appetite exceptions across the other risks,
    # some renewed (can-kicking), one uncalibrated + one stale (trust flags),
    # one non-plan (action flag). ---
    misc = [
        ("EXC-2026-0160", "Broad vendor VPN access retained on mobile build farm",
         "mobile-lead@company.com", "SCN-2026-0011", "A.5.18", "probability_of_realization",
         [0.015, 0.04], "l.romano@company.com", "mobile-app", "cost", 4, None, False),  # stale est
        ("EXC-2026-0161", "Defer endpoint EDR upgrade on team laptops",
         "it-lead@company.com", "SCN-2026-0012", "A.8.7", "probability_of_realization",
         [0.012, 0.035], "t.brooks@company.com", "internal-tools", "cost", 0, None, False),  # uncalibrated
        ("EXC-2026-0162", "Temporary vendor access for analytics SDK",
         "mobile-lead@company.com", "SCN-2026-0011", "A.5.19", "probability_of_realization",
         [0.010, 0.03], "p.nguyen@company.com", "mobile-app", "cost", 5, None, False),  # renewed 5x
        ("EXC-2026-0163", "Defer secondary reviewer on low-severity abuse queue",
         "tns-lead@company.com", "SCN-2026-0007", "A.8.16", "probability_of_realization",
         [0.026, 0.046], "a.silva@company.com", "trust-and-safety", "timeline", 0, None, True),  # non-plan
        ("EXC-2026-0164", "Accept legacy TLS on an internal supplier gateway",
         "it-lead@company.com", "SCN-2026-0020", "A.8.24", "probability_of_realization",
         [0.034, 0.052], "m.haddad@company.com", "internal-tools", "technical_constraint", 3, None, False),
        ("EXC-2026-0165", "Deferred residency tagging on a new export connector",
         "data-platform-lead@company.com", "SCN-2026-0014", "A.8.11", "probability_of_realization",
         [0.04, 0.10], "r.chen@company.com", "data-platform", "timeline", 0, None, False),
        ("EXC-2026-0166", "Deferred DPA refresh for a low-volume subprocessor",
         "dpo@company.com", "SCN-2026-0018", "A.5.20", "probability_of_realization",
         [0.03, 0.08], "j.okafor@company.com", "data-platform", "cost", 2, None, False),
        ("EXC-2026-0167", "Skip dual-write verification during inventory cutover",
         "platform-lead@company.com", "SCN-2026-0010", "A.8.28", "probability_of_realization",
         [0.015, 0.045], "p.nguyen@company.com", "gcloud-migration", "technical_constraint", 0, None, False),
        ("EXC-2026-0168", "Deferred schema-validation gate on a new pipeline writer",
         "data-platform-lead@company.com", "SCN-2026-0016", "A.8.33", "opportunity_frequency",
         [8, 22], "m.haddad@company.com", "data-platform", "timeline", 0, None, False),
        ("EXC-2026-0169", "Reduced fraud-review staffing on off-peak checkout",
         "payments-lead@company.com", "SCN-2026-0015", "A.8.16", "probability_of_realization",
         [0.015, 0.045], "a.silva@company.com", "payments-launch", "cost", 0, None, False),
    ]
    misc_dates = ["2024-06-03", "2026-04-14", "2024-11-18", "2026-05-01", "2025-03-09",
                  "2026-04-16", "2026-03-22", "2026-04-18", "2026-05-06", "2026-05-09"]
    for i, (eid, title, owner, scn, ctrl, moves, ci, est, okr, reason, renews, jcl, non_plan) in enumerate(misc):
        out.append(_exc(
            eid, title, owner, scn, ctrl, moves, ci, est, filed_on=misc_dates[i],
            okr=okr, reason=reason, mechanism="remediate_gap", renewals=renews,
            justification_changed_last=jcl, non_plan=non_plan))
    return out


# Won't-fix vulnerability acceptances, filed as exceptions with
# ``reason: accepted_vulnerability`` (v4.0 §0.0 retired the separate vuln type:
# a risk acceptance is an exception; patching-SLA state is a first-line signal).
ACCEPTED_VULN_EXCEPTIONS = [
    ("EXC-2026-0170", "Accepted RCE on a migrated jobs runner",
     "platform-lead@company.com", "SCN-2026-0001", ["A.8.8"], "probability_of_realization",
     [0.015, 0.04], "r.chen@company.com", "2026-05-18", "legacy-jobs-runner", "2026-08-15"),
    ("EXC-2026-0171", "Accepted privilege-escalation CVE on the endpoint fleet",
     "it-lead@company.com", "SCN-2026-0012", ["A.8.8", "A.8.7"], "probability_of_realization",
     [0.02, 0.05], "j.okafor@company.com", "2026-05-22", "corp-endpoint-fleet", "2026-09-30"),
    ("EXC-2026-0172", "Accepted deferred dependency patch on the checkout service",
     "payments-lead@company.com", "SCN-2026-0015", ["A.8.8"], "probability_of_realization",
     [0.015, 0.045], "p.nguyen@company.com", "2026-06-01", "checkout-service", "2026-08-31"),
]

FINDINGS = [
    ("FND-2026-0001", "Audit: legacy consoles permit password-only authentication",
     "security-eng-lead@company.com", "audit", "high", ["SCN-2026-0001"], ["A.8.5"], "2026-04-30"),
    ("FND-2026-0002", "Audit: MFA not enforced on several internal admin tools",
     "security-eng-lead@company.com", "audit", "high", ["SCN-2026-0001"], ["A.8.5"], "2026-05-04"),
    ("FND-2026-0003", "Self-identified: shared break-glass account lacks session logging",
     "iam-lead@company.com", "self-identified", "medium", ["SCN-2026-0001", "SCN-2026-0019"],
     ["A.8.5", "A.8.15"], "2026-05-11"),
    ("FND-2026-0004", "Incident PMAI: detection model retrain slipped two cycles",
     "tns-lead@company.com", "incident-PMAI", "medium", ["SCN-2026-0008"], ["A.8.16"], "2026-05-15"),
    ("FND-2026-0005", "Incident PMAI: quarterly DR test deferred, failover unproven",
     "platform-lead@company.com", "incident-PMAI", "high", ["SCN-2026-0013"], ["A.5.30"], "2026-05-20"),
    # v4.0 §0.H: the deliberate no-action-plan hole — no remediation's
    # addresses_issues points at this finding, so the GRC "findings without an
    # action plan" tile catches something real.
    ("FND-2026-0006", "Self-identified: supply-chain security reviews not completed for two new vendors",
     "procurement-office@company.com", "self-identified", "medium", ["SCN-2026-0018"], ["A.5.21"], "2026-06-10"),
    # QBR §1.B/§1.G: closed findings give the "problems that came back" metric (3c)
    # a real denominator (findings closed this quarter), and FND-2026-0008 carries
    # recurrence_of — a problem that had been closed before and returned. These
    # are RESOLVED, so they are not open and do not touch engineering control
    # health (verified the byte-gate holds after adding them).
    ("FND-2026-0007", "Audit: log-retention window below policy on two services",
     "soc-office@company.com", "audit", "medium", ["SCN-2026-0008"], ["A.8.16"], "2026-05-19"),
    ("FND-2026-0008", "Self-identified: detection-model eval gate bypassed on a hotfix",
     "tns-lead@company.com", "self-identified", "medium", ["SCN-2026-0008"], ["A.8.16"], "2026-05-22"),
    ("FND-2026-0009", "Audit: DR runbook out of date after the failover redesign",
     "platform-lead@company.com", "audit", "low", ["SCN-2026-0013"], ["A.5.30"], "2026-05-08"),
]

# QBR §1.B: per-finding lifecycle for the recurrence metric (3c). status/closed_on
# for findings resolved this quarter (the denominator); recurrence_of points at a
# prior-quarter finding that had been closed and came back (the numerator). Only
# RESOLVED findings carry these — resolved findings are excluded from engineering
# control health, so this is inert for the byte-gate. Everything else stays open.
FINDING_QBR = {
    "FND-2026-0007": ("resolved", "2026-06-04", None),
    "FND-2026-0008": ("resolved", "2026-06-09", "FND-2025-0044"),
    "FND-2026-0009": ("resolved", "2026-05-30", None),
}


def render_accepted_vuln_exception(spec) -> str:
    (eid, title, owner, scn, controls, moves, ci, est_by, est_on, asset, expires) = spec
    controls_render = "[" + ", ".join(controls) + "]"
    return "\n".join([
        "# A won't-fix vulnerability the org decided to accept: a risk acceptance, so",
        "# an exception (v4.0 §0.0 retired the separate vuln type; patching-SLA state",
        "# is a first-line vulnerability-management signal, not a second-line risk",
        "# model fact). Folds into the mapped scenario's PoR. Synthetic.",
        f"id: {eid}", "type: exception", f"title: {title}", f"owner: {owner}",
        f"filed_on: {est_on}", f"decided_on: {_plus_days(est_on, 4)}",
        "status: active", f"mapped_scenarios: [{scn}]",
        f"control: {controls_render}",
        "exception_effect:", f"  moves: {moves}",
        f"  with_exception_90ci: [{ci[0]}, {ci[1]}]", f"  estimated_by: {est_by}",
        f"  estimated_on: {est_on}",
        "reason: accepted_vulnerability",
        "scope:", "  type: enumerated", f"  assets: [{asset}]",
        f"expires_on: {expires}",
        "renewals:", "  count: 0", "  justification_changed_last: null", "",
    ])


def render_finding(spec) -> str:
    (fid, title, owner, source, severity, scns, controls, filed) = spec
    scns_render = "[" + ", ".join(scns) + "]"
    controls_render = "[" + ", ".join(controls) + "]"
    status, closed_on, recurrence_of = FINDING_QBR.get(fid, ("open", None, None))
    lines = [
        "# An audit / incident-PMAI / self-identified finding (SPEC §2.5). Carries a",
        "# bounded severity that informs control health and the residual NARRATIVE,",
        "# but is NOT simulated -- it never enters the residual bands. Synthetic.",
        f"id: {fid}", "type: finding", f'title: "{title}"', f"owner: {owner}",
        f"filed_on: {filed}", f"status: {status}", f"source: {source}", f"severity: {severity}",
        f"mapped_scenarios: {scns_render}", f"control: {controls_render}",
    ]
    if closed_on:
        lines.append(f"closed_on: {closed_on}")
    if recurrence_of:
        lines.append(f"recurrence_of: {recurrence_of}")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 8. OKRs -- expanded to a launch/rebuild portfolio (SPEC v2.1 §D6).
# ---------------------------------------------------------------------------

OKRS = """\
# OKRs the named risks threaten and the exceptions attach to (SPEC §2.12).
# Expanded to a launch/rebuild portfolio so the "risk riding on your launches"
# view has a real set to draw from (SPEC v2.1 §D6). All synthetic.

gcloud-migration:
  title: gcloud-migration
  objective: a quality rebuild from monolith to microservices
  key_results:
    - all services decomposed and hardened by cutover
    - maintain 99.9% availability through and after cutover
    - zero critical security findings at cutover
  period_end: 2026-06-30
payments-launch:
  title: payments-launch
  objective: launch the new payments platform to general availability
  key_results:
    - pass the external PCI assessment before launch
    - fraud loss rate under target at GA
  period_end: 2026-07-31
data-platform:
  title: data-platform
  objective: a governed, reliable central data platform
  key_results:
    - DLP enforced on every export path
    - 99.9% pipeline availability
  period_end: 2026-09-30
trust-and-safety:
  title: trust-and-safety
  objective: keep abuse and policy-violating content off the platform
  key_results:
    - abuse-escalation SLA met
    - detection-model recall above target
  period_end: 2026-09-30
mobile-app:
  title: mobile-app
  objective: ship the redesigned mobile application
  key_results:
    - redesigned app in general availability
    - crash-free sessions above target
  period_end: 2026-08-31
internal-tools:
  title: internal-tools
  objective: modernize internal developer and operations tooling
  key_results:
    - legacy toolchain decommissioned
    - TLS 1.3 enforced across internal tools
  period_end: 2026-10-31
core-platform:
  title: core-platform
  objective: keep the core platform reliable and available
  key_results:
    - 99.9% availability across core services
    - quarterly DR test passing
  period_end: 2026-12-31
ai-platform:
  title: ai-platform
  objective: stand up a governed internal AI/ML platform
  key_results:
    - model registry and eval gates in place
    - agentic workflows behind guardrails before prod
  period_end: 2026-12-31
checkout-rebuild:
  title: checkout-rebuild
  objective: rebuild the checkout flow for conversion and resilience
  key_results:
    - new checkout at general availability
    - step-up 3DS on every high-risk transaction
  period_end: 2026-09-15
identity-platform:
  title: identity-platform
  objective: consolidate identity onto a single phishing-resistant IdP
  key_results:
    - passkeys enforced on all internal consoles
    - legacy auth paths decommissioned
  period_end: 2026-11-30
data-residency:
  title: data-residency
  objective: enforce regional data residency by default
  key_results:
    - residency tags on every regulated dataset
    - automated cross-region egress controls live
  period_end: 2026-10-31
observability:
  title: observability
  objective: unify logging, metrics, and tracing across services
  key_results:
    - SIEM coverage on all production services
    - p95 alert-to-ack under target
  period_end: 2026-11-15
vendor-consolidation:
  title: vendor-consolidation
  objective: reduce third-party concentration and standing access
  key_results:
    - standing vendor access reduced by half
    - tested fallback for every critical supplier
  period_end: 2026-12-15
mobile-launch:
  title: mobile-launch
  objective: launch the redesigned app in two new markets
  key_results:
    - localized app live in both markets
    - support SLA met at launch
  period_end: 2026-10-15
fraud-platform:
  title: fraud-platform
  objective: modernize the real-time fraud decisioning platform
  key_results:
    - device fingerprinting live at checkout
    - fraud model refresh cadence under a week
  period_end: 2026-11-01
run-the-business:
  title: run-the-business
  objective: maintain core operations otherwise not associated with a strategic objective
"""


# ---------------------------------------------------------------------------
# 9. Remediations -- native-queue work (SPEC v2.1 §D6). 40-60 records with a
#    status spread and slipped target dates for the can-kicking view. Orphan
#    scenarios (PLATFORM-OUTAGE, PCI-SCOPE) are deliberately left unaddressed.
# ---------------------------------------------------------------------------

AS_OF_STR = "2026-06-18"  # target dates before this are slipped


def render_remediation(rid, *, title, rtype, status, owner, operational_owner,
                       mechanism, target_date, addresses_scenarios=None,
                       addresses_issues=None, restores_control=None, mapped_risk=None,
                       moves=None, post_control_90ci=None, estimated_by=None,
                       estimated_on=None) -> str:
    lines = [
        f"id: {rid}", f"title: {title}", f"type: {rtype}", f"status: {status}",
        f"target_date: {target_date}", f"owner: {owner}",
        f"operational_owner: {operational_owner}", f"mechanism: {mechanism}",
    ]
    if rtype == "restore" and restores_control:
        lines.append(f"restores_control: {restores_control}")
    if rtype == "strengthen":
        lines += [f"mapped_risk: {mapped_risk}", f"moves: {moves}",
                  f"post_control_90ci: [{post_control_90ci[0]}, {post_control_90ci[1]}]",
                  f"estimated_by: {estimated_by}", f"estimated_on: {estimated_on}"]
    if addresses_scenarios:
        lines.append(f"addresses_scenarios: [{', '.join(addresses_scenarios)}]")
    if addresses_issues:
        lines.append(f"addresses_issues: [{', '.join(addresses_issues)}]")
    lines.append("")
    return "\n".join(lines)


def build_remediations():
    """~45 remediations: status spread, slipped dates, orphan gaps. Returns
    list of (id, yaml_text). PLATFORM-OUTAGE (SCN-0013) and PCI-SCOPE (SCN-0004)
    are intentionally NOT addressed -> the orphan story (SPEC §E story 3)."""
    R = []
    n = [100]

    def add(**kw):
        rid = f"REM-2026-0{n[0]}"
        n[0] += 1
        R.append(render_remediation(rid, **kw))
        return rid

    OPS = "platform-oncall@company.com"
    # Funded / in_progress work with sensible future dates.
    add(title="Enforce passkeys (FIDO2) across internal consoles", rtype="restore",
        status="funded", owner="iam-lead@company.com", operational_owner="iam-oncall@company.com",
        mechanism="deploy_phishing_resistant_mfa", target_date="2026-09-01",
        addresses_scenarios=["SCN-2026-0001", "SCN-2026-0019"], restores_control="A.8.5",
        # v4.0 §0.H: the passkey rollout is also the action plan for the two
        # A.8.5 audit findings — linked so "finding without an action plan"
        # stays a real signal, not an artifact of unlinked data.
        addresses_issues=["EXC-2026-0170", "FND-2026-0001", "FND-2026-0002"])
    add(title="Re-enable DLP with tuned rules on export paths", rtype="restore",
        status="funded", owner="data-platform-lead@company.com", operational_owner="data-oncall@company.com",
        mechanism="re_enable_dlp_with_tuned_rules", target_date="2026-09-01",
        addresses_scenarios=["SCN-2026-0002"], restores_control="A.8.12")
    add(title="Rotate and scope migrated service accounts", rtype="restore",
        status="in_progress", owner="iam-lead@company.com", operational_owner="iam-oncall@company.com",
        mechanism="rotate_and_scope_service_accounts", target_date="2026-08-15",
        addresses_scenarios=["SCN-2026-0019"], restores_control="A.8.2")
    add(title="Tokenize PII fields in the analytics warehouse", rtype="strengthen",
        status="funded", owner="data-platform-lead@company.com", operational_owner="data-oncall@company.com",
        mechanism="tokenize_pii_in_warehouse", target_date="2026-11-15",
        mapped_risk="NR-DATA-EXFIL", moves="loss_magnitude", post_control_90ci=[120000, 500000],
        estimated_by="r.chen@company.com", estimated_on="2026-06-01",
        addresses_scenarios=["SCN-2026-0002"])
    add(title="Automated data-residency egress controls", rtype="strengthen",
        status="funded", owner="dpo@company.com", operational_owner="data-oncall@company.com",
        mechanism="implement_automated_data_residency_controls", target_date="2026-10-01",
        mapped_risk="NR-DATA-RESIDENCY", moves="probability_of_realization",
        post_control_90ci=[0.01, 0.03], estimated_by="r.chen@company.com",
        estimated_on="2026-06-01", addresses_scenarios=["SCN-2026-0014"])
    add(title="Device fingerprinting + step-up 3DS at checkout", rtype="strengthen",
        status="funded", owner="payments-lead@company.com", operational_owner="payments-oncall@company.com",
        mechanism="deploy_device_fingerprinting_and_3ds", target_date="2026-10-15",
        mapped_risk="NR-CARD-TESTING", moves="probability_of_realization",
        post_control_90ci=[0.004, 0.02], estimated_by="p.nguyen@company.com",
        estimated_on="2026-06-01", addresses_scenarios=["SCN-2026-0015"],
        addresses_issues=["EXC-2026-0172"])
    add(title="Write-time schema validation and integrity gates", rtype="strengthen",
        status="in_progress", owner="data-platform-lead@company.com", operational_owner="data-oncall@company.com",
        mechanism="add_write_time_integrity_gates", target_date="2026-09-15",
        mapped_risk="NR-PIPELINE-INTEGRITY", moves="opportunity_frequency",
        post_control_90ci=[2, 8], estimated_by="m.haddad@company.com",
        estimated_on="2026-06-01", addresses_scenarios=["SCN-2026-0016"])

    # A batch of restores/strengthens against the accumulation cluster + others.
    templates = [
        ("Deploy EDR agent to the endpoint fleet", "restore", "funded", "A.8.7",
         ["SCN-2026-0012"], ["EXC-2026-0171"], "2026-08-20", OPS),
        ("Patch the out-of-SLA privilege-escalation CVE", "restore", "in_progress", "A.8.8",
         ["SCN-2026-0012"], ["EXC-2026-0171"], "2026-07-30", OPS),
        ("Restore the data-validation suite", "restore", "funded", "A.8.33",
         ["SCN-2026-0005"], None, "2026-09-10", "data-oncall@company.com"),
        ("Retrain the abuse-detection model", "restore", "proposed", "A.8.16",
         ["SCN-2026-0008"], ["FND-2026-0004"], "2026-05-01", "tns-oncall@company.com"),   # slipped; plan for FND-0004
        ("Refresh the abuse-escalation playbook", "restore", "in_progress", "A.8.16",
         ["SCN-2026-0007"], None, "2026-04-15", "tns-oncall@company.com"),   # slipped
        ("Complete network segmentation for PCI", "restore", "proposed", "A.8.22",
         ["SCN-2026-0004"], None, "2026-05-20", "payments-oncall@company.com"),  # slipped but PCI still orphan (proposed != funded)
        ("Scope vendor access on the mobile build farm", "restore", "in_progress", "A.5.18",
         ["SCN-2026-0011"], None, "2026-03-30", "it-oncall@company.com"),    # slipped
        ("Schedule HA failover drills", "restore", "proposed", "A.8.14",
         ["SCN-2026-0006"], None, "2026-06-30", "data-oncall@company.com"),
        ("Enforce TLS 1.3 on the supplier gateway", "restore", "funded", "A.8.24",
         ["SCN-2026-0020"], None, "2026-09-05", "it-oncall@company.com"),
        ("Residency tagging on new export connectors", "restore", "in_progress", "A.8.11",
         ["SCN-2026-0014"], None, "2026-02-28", "data-oncall@company.com"),  # slipped hard
        ("Refresh subprocessor DPAs", "restore", "proposed", "A.5.20",
         ["SCN-2026-0018"], None, "2026-05-10", "legal-oncall@company.com"),  # slipped
        ("Enable dual-write verification on cutover", "restore", "funded", "A.8.28",
         ["SCN-2026-0010"], None, "2026-08-25", OPS),
        ("Restore fraud-review staffing off-peak", "restore", "proposed", "A.8.16",
         ["SCN-2026-0015"], None, "2026-06-01", "payments-oncall@company.com"),
        ("Re-enable change-approval evidence export", "restore", "in_progress", "A.8.32",
         ["SCN-2026-0010"], None, "2026-04-01", OPS),                        # slipped
        ("Backfill privileged-access reviews", "restore", "funded", "A.8.2",
         ["SCN-2026-0001"], None, "2026-09-20", "iam-oncall@company.com"),
    ]
    for title, rtype, status, ctrl, scns, issues, td, ops in templates:
        add(title=title, rtype=rtype, status=status, owner="platform-lead@company.com",
            operational_owner=ops, mechanism=title.lower().replace(" ", "_")[:40],
            target_date=td, addresses_scenarios=scns, addresses_issues=issues,
            restores_control=ctrl)

    # A tail of smaller strengthens/restores to reach ~45, several slipped/proposed.
    tail = [
        ("Passkey rollout wave 2 (contractor consoles)", "in_progress", ["SCN-2026-0001"], "2026-05-05"),
        ("Legacy API-key decommission", "proposed", ["SCN-2026-0001"], "2026-04-20"),
        ("Session-timeout hardening on legacy portals", "in_progress", ["SCN-2026-0001"], "2026-03-15"),
        ("Break-glass session logging", "proposed", ["SCN-2026-0019"], "2026-05-25",
         ["FND-2026-0003"]),  # v4.0 §0.H: the action plan for the break-glass finding
        ("DLP coverage for ad-hoc BI connectors", "in_progress", ["SCN-2026-0002"], "2026-06-10"),
        ("Fraud-rule tuning backlog burn-down", "proposed", ["SCN-2026-0003"], "2026-04-30"),
        ("Detection-model eval-gate rollout", "in_progress", ["SCN-2026-0008"], "2026-06-05"),
        ("Endpoint EDR tuning wave 2", "proposed", ["SCN-2026-0012"], "2026-05-15"),
        ("Residency egress monitoring", "in_progress", ["SCN-2026-0014"], "2026-06-12"),
        ("Supplier fallback runbook", "proposed", ["SCN-2026-0020"], "2026-05-30"),
        ("Migration cutover integrity checks", "in_progress", ["SCN-2026-0010"], "2026-04-10"),
        ("Vendor access recertification", "proposed", ["SCN-2026-0011"], "2026-03-20"),
        ("Pipeline dead-letter validation", "in_progress", ["SCN-2026-0016"], "2026-06-08"),
        ("Abuse-queue reviewer staffing", "proposed", ["SCN-2026-0007"], "2026-05-18"),
        ("Regulatory filing calendar automation", "in_progress", ["SCN-2026-0017"], "2026-06-14"),
        ("Data-availability failover automation", "proposed", ["SCN-2026-0006"], "2026-05-22"),
        ("Subprocessor inventory reconciliation", "in_progress", ["SCN-2026-0018"], "2026-04-25"),
        ("Card-testing velocity limits", "proposed", ["SCN-2026-0015"], "2026-06-02"),
    ]
    for title, status, scns, td, *issues in tail:
        add(title=title, rtype="restore", status=status, owner="platform-lead@company.com",
            operational_owner=OPS, mechanism=title.lower().replace(" ", "_")[:40],
            target_date=td, addresses_scenarios=scns, restores_control=None,
            addresses_issues=(issues[0] if issues else None))
    return R


# ---------------------------------------------------------------------------
# 10. Evidence, KRIs, Horizon (SPEC §2.8-2.10). Scenario/control refs preserved.
# ---------------------------------------------------------------------------

EVIDENCE = [
    ("EV-IAM-0001", ["A.8.5"], "idp-config-export", "automated","quarterly", "2026-04-15"),
    ("EV-IAM-0002", ["A.8.2", "A.5.18"], "privileged-access-review", "manual", "quarterly", "2026-05-02"),
    ("EV-DLP-0001", ["A.8.12"], "dlp-policy-export", "automated","monthly", "2026-06-01"),
    ("EV-BACKUP-0001", ["A.8.13"], "backup-job-report", "automated","weekly", "2026-06-10"),
    ("EV-VULN-0001", ["A.8.8"], "scanner-export", "automated","weekly", "2026-06-11"),
    ("EV-LOG-0001", ["A.8.15", "A.8.16"], "siem-coverage-report", "automated","monthly", "2026-05-28"),
    ("EV-CRYPTO-0001", ["A.8.24"], "tls-scan", "automated","monthly", "2026-05-30"),
    ("EV-NET-0001", ["A.8.20", "A.8.22"], "firewall-ruleset-export", "automated","quarterly", "2026-03-20"),
    ("EV-DR-0001", ["A.5.30"], "dr-test-report", "manual", "quarterly", "2025-11-01"),
    ("EV-RESIDENCY-0001", ["A.8.11", "A.5.34"], "data-residency-audit", "manual", "semiannual", "2025-08-15"),
    ("EV-CHANGE-0001", ["A.8.32"], "change-approval-export", "automated","monthly", None),
    ("EV-SUPPLIER-0001", ["A.5.19", "A.5.20"], "vendor-attestation-register", "manual", "annual", "2026-01-10"),
    ("EV-BACKUP-0002", ["A.8.14"], "redundancy-drill-report", "manual", "quarterly", "2026-05-12"),
    ("EV-CODE-0001", ["A.8.28", "A.8.33"], "sast-coverage-report", "automated","monthly", "2026-06-03"),
]

EVIDENCE_HEAD = """\
# Proof a control operates (SPEC §2.8, thin -- DATA ONLY, no collector). status
# (fresh | stale | missing) is DERIVED from cadence + last_collected. A few are
# deliberately stale/missing to exercise the provability signal (SPEC §5.5).
# All synthetic.

"""


def render_evidence() -> str:
    out = [EVIDENCE_HEAD]
    for eid, controls, source, method, cadence, last in EVIDENCE:
        block = [f"{eid}:", f"  supports_controls: [{', '.join(controls)}]",
                 f"  source: {source}", f"  collection_method: {method}", f"  cadence: {cadence}"]
        block.append(f"  last_collected: {last}" if last else "  last_collected: null")
        out.append("\n".join(block) + "\n")
    return "\n".join(out)


KRIS = [
    ("KRI-MODEL-CONCENTRATION", "Share of critical paths dependent on a single model provider",
     ["SCN-2026-0031"], 0.62, 0.50, "rising", "over"),
    ("KRI-AGENTIC-WORKFLOWS", "Count of agentic workflows running in production without guardrails",
     ["SCN-2026-0032"], 7, 3, "rising", "over"),
    ("KRI-DETECTION-DRIFT", "Abuse-detection model recall drift since last retrain (pct pts)",
     ["SCN-2026-0033", "SCN-2026-0008"], 0.09, 0.05, "rising", "over"),
    ("KRI-MFA-COVERAGE", "Share of internal consoles NOT enforcing phishing-resistant MFA",
     ["SCN-2026-0001"], 0.34, 0.15, "rising", "over"),
    ("KRI-PATCH-SLA", "Share of critical vulns patched within SLA",
     ["SCN-2026-0012"], 0.82, 0.90, "receding", "under"),
    ("KRI-DR-CONFIDENCE", "Days since a successful full DR failover test",
     ["SCN-2026-0013"], 220, 120, "rising", "over"),
    ("KRI-RESIDENCY-FLOWS", "Cross-region regulated-data flows per quarter",
     ["SCN-2026-0014"], 14, 10, "rising", "over"),
    ("KRI-FRAUD-RATE", "Card-testing attempts landing a charge per 10k attempts",
     ["SCN-2026-0015"], 3.1, 5.0, "stable", "over"),
    ("KRI-VENDOR-ACCESS", "Count of vendor identities with standing internal access",
     ["SCN-2026-0011"], 41, 30, "rising", "over"),
    ("KRI-CHANGE-FAILURE", "Change-failure rate on migrated services (pct)",
     ["SCN-2026-0009"], 0.11, 0.10, "rising", "over"),
    ("KRI-PIPELINE-REJECTS", "Schema-invalid writes reaching the pipeline per week",
     ["SCN-2026-0016"], 6, 12, "receding", "over"),
    ("KRI-DPA-COVERAGE", "Share of subprocessors without a signed current DPA",
     ["SCN-2026-0018"], 0.18, 0.10, "rising", "over"),
    # v4.0 §0.G: agent-telemetry KRIs, siblings of KRI-AGENTIC-WORKFLOWS.
    # Standards-sourced examples (CSA agentic-profile telemetry); leading
    # indicators only, never additive terms. Fed by the security detection seam
    # (see guardrails.yaml monitoring.signal_source); no live ingestion is built.
    ("KRI-AGENT-ACTION-VELOCITY", "Agent-initiated production actions per hour (p95)",
     ["SCN-2026-0032"], 55, 60, "rising", "over"),
    ("KRI-AGENT-PERM-ESCALATION", "Agent permission-escalation requests per week",
     ["SCN-2026-0019", "SCN-2026-0032"], 2, 5, "stable", "over"),
    ("KRI-AGENT-DELEGATION-DEPTH", "Maximum observed agent delegation depth (7-day)",
     ["SCN-2026-0032"], 2, 3, "stable", "over"),
]

KRI_HEAD = """\
# Key risk indicators (SPEC §2.9, thin). A KRI INFORMS re-estimation of a factor
# (never an additive term, SPEC §4) and triggers emerging-risk changes. status
# (ok | amber | breached) is DERIVED from current_value vs threshold; direction
# `under` means a breach is a value at/below threshold. All synthetic.

"""


def render_kris() -> str:
    out = [KRI_HEAD]
    for kid, title, informs, value, threshold, trend, direction in KRIS:
        out.append(
            f"{kid}:\n  title: {title}\n  informs: [{', '.join(informs)}]\n"
            f"  current_value: {value}\n  threshold: {threshold}\n"
            f"  trend: {trend}\n  direction: {direction}\n")
    return "\n".join(out)


HORIZON = [
    ("HZN-AGENT-AUTONOMY", "Autonomous agents taking unsafe action in production",
     "TR-CHANGE", "KRI-AGENTIC-WORKFLOWS", "rising",
     "agentic workflows moving into prod ahead of guardrails"),
    ("HZN-MODEL-CONCENTRATION", "Systemic dependence on a single external model provider",
     "TR-THIRDPARTY", "KRI-MODEL-CONCENTRATION", "rising",
     "critical paths converging on one provider; no tested fallback"),
    ("HZN-DETECTION-DRIFT", "Silent drift degrading automated abuse detection",
     "TR-SECURITY", "KRI-DETECTION-DRIFT", "rising",
     "recall decaying between retrains; drift not yet alarmed"),
    ("HZN-PROMPT-INJECTION", "Prompt injection against customer-facing LLM features",
     "TR-SECURITY", "KRI-AGENTIC-WORKFLOWS", "stable",
     "injection surface growing as LLM features ship to users"),
]

HORIZON_HEAD = """\
# The emerging watch list at the edge (SPEC §2.10). Mechanistic-test fence: an
# item earns a slot ONLY if it names both a candidate_domain and a watched_kri.
# All synthetic.

"""


def render_horizon() -> str:
    out = [HORIZON_HEAD]
    for hid, title, domain, kri, trajectory, note in HORIZON:
        out.append(
            f"{hid}:\n  title: {title}\n  candidate_domain: {domain}\n"
            f"  watched_kri: {kri}\n  trajectory: {trajectory}\n  note: \"{note}\"\n")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# 11. Estimators + config (the calibration gate and the MC run config). Moved
#     here when the legacy generator was retired (SPEC v2.2 §C4).
# ---------------------------------------------------------------------------

ESTIMATORS = """\
# The calibration gate (SPEC §2.9 estimators). An estimate from someone
# uncalibrated, or whose calibration is older than the refresh window, is flagged
# and its factor move is held out of the trusted residual bands. All synthetic.

r.chen@company.com:
  calibrated: true
  calibrated_on: 2026-03-15
j.okafor@company.com:
  calibrated: true
  calibrated_on: 2025-11-20
p.nguyen@company.com:
  calibrated: true
  calibrated_on: 2026-01-10
a.silva@company.com:
  calibrated: true
  calibrated_on: 2025-09-05
m.haddad@company.com:
  calibrated: true
  calibrated_on: 2026-02-01

# Uncalibrated: any estimate from here is flagged low-confidence.
t.brooks@company.com:
  calibrated: false

# Stale: calibrated once, but longer ago than the refresh window (365d).
l.romano@company.com:
  calibrated: true
  calibrated_on: 2024-02-01
"""

CONFIG = """\
# Optional run configuration. CLI flags override these.
monte_carlo:
  iterations: 10000
  seed: 20260617
calibration:
  refresh_window_days: 365
renewals:
  # An active exception renewed at least this many times with its justification
  # never revisited is flagged "temporary forever" in the can-kicking view.
  alert_count: 3
"""


# ===========================================================================
# v4.0 SPEC 0 — GRC-tab registers (§0.B–§0.E). None of these files is read by
# the eng build (the loader opens a hardcoded file list plus scenarios/,
# issues/, remediations/ only — P.4), so they are inert for the dashboard.
# ===========================================================================

REGULATIONS = """\
# External requirement register (v4.0 §0.B): framework + requirement, each
# referencing existing ISO 27001:2022 Annex A controls so one control can
# satisfy many obligations (map once, satisfy many). DORA validated:
# Regulation (EU) 2022/2554, applicable to EU financial entities and their ICT
# providers since 17 January 2025; five pillars, the first four mandatory, the
# fifth voluntary. Company Corp is modelled EU-in-scope. requirement_ref stays
# at PILLAR level: DORA's RTS/ITS were still being finalized through 2026, so
# article-level detail is to-be-verified against the regulation text — do not
# fabricate article numbers. The satisfied_by_controls mappings are
# human-ratified illustrative mappings, not authored by the tool; each id must
# exist in controls.yaml. DORA maps primarily to the Resilience domain with
# Security / Third-party / incident threads crossing in (manifestation over
# cause: DORA is a cross-cutting obligation, not a domain). All data synthetic.

DORA-P1-ICT-RISK-MGMT:
  framework: DORA
  requirement_ref: "Pillar 1 — ICT risk management"      # article/RTS detail TBV vs Reg (EU) 2022/2554
  title: ICT risk management framework
  satisfied_by_controls: [A.5.1, A.8.8]
DORA-P2-INCIDENT-REPORTING:
  framework: DORA
  requirement_ref: "Pillar 2 — ICT-related incident management, classification & reporting"
  title: ICT-related incident management and reporting
  satisfied_by_controls: [A.5.24, A.5.26, A.8.15]         # A.8.15 shared with PCI-REQ-10 -> reuse
DORA-P3-RESILIENCE-TESTING:
  framework: DORA
  requirement_ref: "Pillar 3 — digital operational resilience testing"
  title: Digital operational resilience testing
  satisfied_by_controls: [A.5.30, A.8.8]
DORA-P4-THIRD-PARTY-RISK:
  framework: DORA
  requirement_ref: "Pillar 4 — ICT third-party risk management"
  title: ICT third-party risk management
  satisfied_by_controls: [A.5.19, A.5.20, A.5.21, A.5.22]
DORA-P5-INFO-SHARING:
  framework: DORA
  requirement_ref: "Pillar 5 — information & intelligence sharing"   # VOLUNTARY, not mandatory
  title: Information and intelligence sharing
  satisfied_by_controls: [A.5.6]
PCI-REQ-8:
  framework: PCI-DSS
  requirement_ref: "Req 8 — identify users and authenticate access"
  title: Identify users and authenticate access to system components
  satisfied_by_controls: [A.5.16, A.5.17, A.8.5]
PCI-REQ-10:
  framework: PCI-DSS
  requirement_ref: "Req 10 — logging & monitoring"
  title: Log and monitor all access to system components and cardholder data
  satisfied_by_controls: [A.8.15, A.8.16]                 # A.8.15 also under DORA-P2 -> reuse
PCI-REQ-11:
  framework: PCI-DSS
  requirement_ref: "Req 11 — test security of systems and networks regularly"
  title: Test security of systems and networks regularly
  satisfied_by_controls: [A.8.8, A.8.29]                  # A.8.8 also under DORA-P1/P3 -> reuse
"""

SLA_CONFIG = """\
# Service-level targets for the GRC program's own process steps (v4.0 §0.C).
# AUTHORED commitments, never derived from observed cycle times or from an
# outcome we want to show (the appetite rule, applied to process SLAs).
risk_intake_to_scored_days: 10
exception_raised_to_decided_days: 5
finding_to_remediation_plan_days: 15
policy_review_cadence_months: 12          # default; per-policy override via review_cadence
evidence_refresh: by_cadence               # per-evidence cadence field
remediation_target_date_adherence: true    # overdue = target_date < as-of
# guardrail-deviation disposition SLA is per-guardrail (see guardrails.yaml provisional_move)
"""

GUARDRAILS = """\
# Agent guardrails (v4.0 §0.D): policy-as-code assertions governing what
# autonomous agents may do, each tracing up to POL-AI-USE and mapped to the
# named risk its violation would move (action-consequence mapping, NIST AI RMF
# "Map"). rmf_functions anchor to the NIST-published AI RMF core (Govern, Map,
# Measure, Manage; AI RMF 1.0 / NIST AI 100-1, Jan 2023). autonomy_tier is a
# Cloud Security Alliance Agentic-Profile extension that aligns with and
# extends NIST RMF — CSA-attributed, v1/evolving, NOT NIST-published. The
# response_ladder is DECLARED, not built; its "intervene" rung defers to an
# AAGATE-style (CSA, Dec 2025) runtime enforcement overlay — an external seam,
# not something this repo builds. monitoring.signal_source is the INPUT seam
# from security's detection tooling. provisional_move is the Model B
# meta-guardrail: the most a single machine-proposed deviation may provisionally
# move the named factor, with a mandatory disposition SLA. All data synthetic.

GR-AGENT-PROD-WRITE:
  title: Coding agent may write to prod only behind an approved change ticket
  layer: intent-formation                 # intent-formation | runtime (defense-in-depth classification)
  assertion: "deploy.target != 'prod' OR change_ticket.approved == true"
  policy: POL-AI-USE
  mapped_named_risks: [NR-PROD-COMPROMISE]
  applies_to: [agent:code-assistant, agent:ci-bot]
  autonomy_tier: 3                        # CSA Agentic Profile tier (CSA-attributed, P.6)
  owner: platform-security-lead@company.com
  rmf_functions: [Govern, Map, Measure, Manage]
  monitoring:
    mode: continuous                      # continuous | periodic | manual-attestation
    signal_source: secops-agent-access-feed
    telemetry_kris: [KRI-AGENT-ACTION-VELOCITY, KRI-AGENT-PERM-ESCALATION]
  provisional_move:
    factor: probability_of_realization
    max_band_90ci: [0.02, 0.06]           # the most a single auto-registration may move
    disposition_sla_hours: 24
  response_ladder:                        # DECLARED, not built; severity x autonomy_tier
    low: monitor
    medium: monitor + notify_owner
    high: escalate + timebox
    critical: intervene                   # -> runtime enforcement seam (AAGATE-style), acknowledged-not-built

GR-AGENT-DATA-EXPORT:
  title: Support agent may not export regulated data outside approved stores
  layer: runtime
  assertion: "export.dataset.classification != 'regulated' OR export.destination in approved_stores"
  policy: POL-AI-USE
  mapped_named_risks: [NR-DATA-EXFIL]
  applies_to: [agent:support-triage-bot]
  autonomy_tier: 2
  owner: data-platform-lead@company.com
  rmf_functions: [Govern, Map, Measure]
  monitoring:
    mode: periodic
    signal_source: dlp-export-feed
    telemetry_kris: [KRI-AGENT-PERM-ESCALATION]
  provisional_move:
    factor: probability_of_realization
    max_band_90ci: [0.01, 0.04]
    disposition_sla_hours: 48
  response_ladder:                        # DELIBERATELY INCOMPLETE (no critical rung) — the
    low: monitor                          # ladder-completeness derivation catches it (§1.B)
    medium: monitor + notify_owner
    high: escalate + timebox

GR-AGENT-CODE-MERGE:
  title: AI-generated changes merge only with an approving human review
  layer: intent-formation
  assertion: "pr.author.is_agent == false OR pr.approvals.human >= 1"
  policy: POL-AI-USE
  mapped_named_risks: [NR-PROD-COMPROMISE]
  applies_to: [agent:code-assistant]
  autonomy_tier: 2
  owner: eng-office@company.com
  rmf_functions: [Govern, Map, Measure, Manage]
  monitoring:
    mode: continuous
    signal_source: ci-merge-audit-feed
    telemetry_kris: [KRI-AGENT-DELEGATION-DEPTH]
  provisional_move:
    factor: probability_of_realization
    max_band_90ci: [0.04, 0.10]
    disposition_sla_hours: 24
  response_ladder:
    low: monitor
    medium: monitor + notify_owner
    high: escalate + timebox
    critical: intervene

GR-AGENT-DELEGATION:
  title: Agent may not delegate to sub-agents beyond depth 2 without owner approval
  layer: runtime
  assertion: "delegation.depth <= 2 OR delegation.owner_approved == true"
  policy: POL-AI-USE
  mapped_named_risks: [NR-AI-AGENT-AUTONOMY]
  applies_to: [agent:ci-bot, agent:workflow-orchestrator]
  autonomy_tier: 3
  owner: platform-security-lead@company.com
  rmf_functions: [Govern, Map, Measure, Manage]
  monitoring:
    mode: continuous
    signal_source: agent-runtime-telemetry
    telemetry_kris: [KRI-AGENT-DELEGATION-DEPTH, KRI-AGENT-ACTION-VELOCITY]
  provisional_move:
    factor: probability_of_realization
    max_band_90ci: [0.03, 0.08]
    disposition_sla_hours: 12
  response_ladder:
    low: monitor
    medium: monitor + notify_owner
    high: escalate + timebox
    critical: intervene
"""

AGENT_INVENTORY = """\
# The security-fed detected-agent set (v4.0 §0.H / §1.B): agents and agentic
# use-cases OBSERVED in the environment by security tooling. This register is
# the security-to-GRC seam made concrete — the guardrail-coverage denominator
# ("of detected agents, the fraction with a declared, mapped guardrail") has to
# name a real set, and applies_to alone cannot be it (a set defined by the
# guardrails would always read 100% covered). No live feed is built; a real
# detection pipeline would repopulate this file. agent:data-migration-bot is
# the deliberate UNGOVERNED hole: detected, referenced by no guardrail's
# applies_to (v4.0 §0.H). All data synthetic.

agent:code-assistant:
  description: IDE/CI coding assistant raising and editing changes
  first_detected: 2026-02-10
  source: secops-agent-access-feed
agent:ci-bot:
  description: Pipeline agent executing builds, tests and deploys
  first_detected: 2026-02-10
  source: secops-agent-access-feed
agent:support-triage-bot:
  description: Support agent triaging tickets with data-store read access
  first_detected: 2026-04-02
  source: secops-agent-access-feed
agent:workflow-orchestrator:
  description: Orchestrator delegating tasks to tool-using sub-agents
  first_detected: 2026-05-11
  source: agent-runtime-telemetry
agent:data-migration-bot:
  description: Agentic ETL runner moving datasets between stores during the migration
  first_detected: 2026-06-04
  source: secops-agent-access-feed
"""

# Guardrail deviations (v4.0 §0.E): provisional exceptions, one per file, in
# their OWN directory — NEVER data/issues/ (P.4: a deviation placed in issues/
# enters the eng residual). Shape-compatible with IssueRecord.parse so the GRC
# build reuses the parser and the engine's per-issue FAIR contribution;
# deviation-specific fields are read from .raw. Spans severities and
# dispositions; exactly one invokes the "intervene" rung.
GUARDRAIL_EVENTS = {
    "DEV-2026-0001": """\
# Guardrail deviation (v4.0 §0.E): a provisional exception, machine-proposed by
# the offline deviation monitor and awaiting human disposition. Bounded by the
# guardrail's provisional_move; isolated by directory, so eng residual is
# untouched. Overdue for disposition at the 2026-06-18 reference date. Synthetic.
id: DEV-2026-0001
type: exception                            # provisional; isolated by directory (P.4)
title: Agent deploy to prod without an approved change ticket
filed_on: 2026-06-15                       # observed date (parses cleanly, drives aging)
status: active
mapped_scenarios: [SCN-2026-0019]
exception_effect:                          # bounded by GR-AGENT-PROD-WRITE provisional_move
  moves: probability_of_realization
  with_exception_90ci: [0.02, 0.05]
  estimated_by: offline-ai-deviation-monitor
# --- deviation-specific (read from .raw by the GRC build) ---
guardrail: GR-AGENT-PROD-WRITE
disposition: proposed                      # proposed | dismissed | accepted | remediated
severity: high                             # -> response_ladder rung
response_invoked: escalate + timebox
detected_by: offline-ai-deviation-monitor  # advisory; a human dispositions (propose -> ratify)
disposition_due: 2026-06-16                # filed_on + 24h SLA; OVERDUE at as-of 2026-06-18
""",
    "DEV-2026-0002": """\
# Guardrail deviation (v4.0 §0.E): dispositioned ACCEPTED within its SLA — a
# ratified provisional exception; contributes to the provisional deviation
# exposure overlay (§1.C), never to the eng residual. Synthetic.
id: DEV-2026-0002
type: exception
title: Regulated-table export by the support agent to an unapproved store
filed_on: 2026-06-05
status: active
mapped_scenarios: [SCN-2026-0002]
exception_effect:                          # bounded by GR-AGENT-DATA-EXPORT provisional_move
  moves: probability_of_realization
  with_exception_90ci: [0.01, 0.03]
  estimated_by: offline-ai-deviation-monitor
guardrail: GR-AGENT-DATA-EXPORT
disposition: accepted
severity: medium
response_invoked: monitor + notify_owner
detected_by: offline-ai-deviation-monitor
disposition_due: 2026-06-07                # filed_on + 48h SLA
disposition_on: 2026-06-06                 # decided within SLA
""",
    "DEV-2026-0003": """\
# Guardrail deviation (v4.0 §0.E): dispositioned DISMISSED (false positive —
# the approving review existed under a different account mapping). No
# contribution anywhere. Synthetic.
id: DEV-2026-0003
type: exception
title: Agent-authored change flagged as merged without human approval
filed_on: 2026-06-01
status: resolved
mapped_scenarios: [SCN-2026-0034]
exception_effect:
  moves: probability_of_realization
  with_exception_90ci: [0.04, 0.10]
  estimated_by: offline-ai-deviation-monitor
guardrail: GR-AGENT-CODE-MERGE
disposition: dismissed
severity: low
response_invoked: monitor
detected_by: offline-ai-deviation-monitor
disposition_due: 2026-06-02
disposition_on: 2026-06-01
""",
    "DEV-2026-0004": """\
# Guardrail deviation (v4.0 §0.E): the one INTERVENE — a critical deviation
# whose response rung fired the runtime intervention seam. The enforcement
# EXECUTION is an external, AAGATE-style overlay (CSA, Dec 2025): acknowledged,
# not built — no engine here. Dispositioned REMEDIATED same day. Synthetic.
id: DEV-2026-0004
type: exception
title: Orchestrator spawned a depth-4 delegation chain touching prod credentials
filed_on: 2026-05-28
status: resolved
mapped_scenarios: [SCN-2026-0032]
exception_effect:
  moves: probability_of_realization
  with_exception_90ci: [0.04, 0.08]
  estimated_by: offline-ai-deviation-monitor
guardrail: GR-AGENT-DELEGATION
disposition: remediated
severity: critical
response_invoked: intervene                # -> external runtime enforcement seam, acknowledged-not-built
detected_by: offline-ai-deviation-monitor
disposition_due: 2026-05-28                # 12h SLA
disposition_on: 2026-05-28
""",
    "DEV-2026-0005": """\
# Guardrail deviation (v4.0 §0.E): a second PROPOSED deviation, inside its
# disposition window at the 2026-06-18 reference date (due that day). Synthetic.
id: DEV-2026-0005
type: exception
title: Agent deploy to prod under an expired change-ticket approval
filed_on: 2026-06-17
status: active
mapped_scenarios: [SCN-2026-0019]
exception_effect:
  moves: probability_of_realization
  with_exception_90ci: [0.02, 0.04]
  estimated_by: offline-ai-deviation-monitor
guardrail: GR-AGENT-PROD-WRITE
disposition: proposed
severity: medium
response_invoked: monitor + notify_owner
detected_by: offline-ai-deviation-monitor
disposition_due: 2026-06-18                # filed_on + 24h SLA; due, not yet overdue
""",
}


# ---------------------------------------------------------------------------
# Build. Appetite is authored in the NAMED_RISKS table above (no calibration);
# the RAG colour is whatever the authored line and the tuned exposure produce.
# ---------------------------------------------------------------------------

REM_DIR = DATA / "remediations"


GUARDRAIL_EVENTS_DIR = DATA / "guardrail_events"

# ===========================================================================
# QBR v4.0 — the three new hand-authored files (§1.D–§1.F). None is read by the
# engineering build. All synthetic.
# ===========================================================================

# §1.D assurance_requests.yaml — a real log with real cardinality. Drives the
# value row: how much is answered from material we already had (5a) and how fast
# (5b). The story: most requests reuse existing artifacts; turnaround is a day
# or two. One request is still open (excluded from the turnaround median).
ASSURANCE_REQUESTS = """\
# Customer / auditor / regulator / prospect assurance requests (QBR §1.D).
# answered_from: existing = satisfied by an artifact we already had; bespoke =
# net-new work. Turnaround is closed_on - received_on. Synthetic.

- {id: AR-2026-0031, received_on: 2026-04-03, closed_on: 2026-04-04, requester_type: customer, answered_from: existing, artifact: soc2-report}
- {id: AR-2026-0032, received_on: 2026-04-10, closed_on: 2026-04-12, requester_type: prospect, answered_from: existing, artifact: security-whitepaper}
- {id: AR-2026-0033, received_on: 2026-04-18, closed_on: 2026-04-25, requester_type: auditor, answered_from: bespoke, artifact: access-review-evidence}
- {id: AR-2026-0034, received_on: 2026-04-22, closed_on: 2026-04-23, requester_type: customer, answered_from: existing, artifact: soc2-report}
- {id: AR-2026-0035, received_on: 2026-05-04, closed_on: 2026-05-06, requester_type: customer, answered_from: existing, artifact: pentest-summary}
- {id: AR-2026-0036, received_on: 2026-05-09, closed_on: 2026-05-10, requester_type: prospect, answered_from: existing, artifact: security-whitepaper}
- {id: AR-2026-0037, received_on: 2026-05-15, closed_on: 2026-05-22, requester_type: regulator, answered_from: bespoke, artifact: dora-mapping}
- {id: AR-2026-0038, received_on: 2026-05-20, closed_on: 2026-05-21, requester_type: customer, answered_from: existing, artifact: soc2-report}
- {id: AR-2026-0039, received_on: 2026-06-01, closed_on: 2026-06-02, requester_type: customer, answered_from: existing, artifact: subprocessor-list}
- {id: AR-2026-0040, received_on: 2026-06-08, closed_on: 2026-06-09, requester_type: prospect, answered_from: existing, artifact: security-whitepaper}
- {id: AR-2026-0041, received_on: 2026-06-11, closed_on: 2026-06-12, requester_type: customer, answered_from: existing, artifact: soc2-report}
- {id: AR-2026-0042, received_on: 2026-06-16, closed_on: null, requester_type: auditor, answered_from: bespoke, artifact: control-walkthrough}
"""

# §1.E program_period.yaml — the ONLY file holding numbers that cannot be
# re-derived from an --as-of date. One block per quarter; the head of GRC keeps
# it. Two quarters seeded (§4) so every hand-kept number has a delta and the
# consumer return rate (5c) is computable. consumers is a named list (a set
# intersection gives the return rate); no_time_off_count is a COUNT, never a
# name (§3 identifiability caution). 'mobile' is in the estate list but carries
# no named risk — the coverage gap (§1.G).
PROGRAM_PERIOD = """\
# Hand-kept per-quarter numbers that cannot be recomputed from a reference date
# (QBR §1.E). The head of GRC updates this once a quarter. Synthetic.

2026-Q2:
  estate_units: [payments, platform, data-platform, trust-and-safety, privacy-legal,
                 ai-platform, corp-it, mobile]
  consumers: [platform-eng, payments, legal, finance]   # non-GRC teams using GRC data
  team:
    headcount: 5
    open_roles:
      - {title: "Risk analyst", opened_on: 2026-02-04}
      - {title: "Controls engineer", opened_on: 2026-04-19}
    no_time_off_count: 1
    dev_budget_used_pct: 38
  # Wins we can't measure (§2.5): AI-harvested candidates, a human picked three.
  # Prefer wins where the BUSINESS did something. Each names a team + a specific
  # thing; where it explains a number that moved, it says so.
  wins:
    - {team: ai-platform, text: "Self-registered the agent-autonomy risk and drafted its own guardrail before we flagged it — part of why more than half of this quarter's new risks came from the business."}
    - {team: data-platform, text: "An engineer caught a data-residency gap mid-migration and raised it as a risk on the spot, rather than waiting to be asked."}
    - {team: platform-eng, text: "Wired the disaster-recovery failover test to emit its own proof automatically, closing a problem that had come back twice before."}
2026-Q1:
  estate_units: [payments, platform, data-platform, trust-and-safety, privacy-legal,
                 ai-platform, corp-it]
  consumers: [platform-eng, legal]
  team:
    headcount: 5
    open_roles:
      - {title: "Risk analyst", opened_on: 2026-02-04}
    no_time_off_count: 0
    dev_budget_used_pct: 25
"""

# §1.F grc_okrs.yaml — the GRC team's own OKRs, separate from business okrs.yaml
# (mixing them would corrupt the engineering profile's risk-footprint view).
# All ai-native this half: the program is automating its own hygiene.
GRC_OKRS = """\
# GRC team OKRs (QBR §1.F). Separate from business okrs.yaml. theme is one of
# ai-native | scalable | foundational. Progress is target vs current. Synthetic.

- id: OKR-GRC-2026-H1-01
  objective: "Automate 80% of all evidence collection"
  period_end: 2026-06-30
  theme: ai-native
  key_results:
    - title: "Evidence collected automatically"
      target_pct: 80
      current_pct: 64
      recent: "the payments team stood up a collector for their own controls, retiring a batch of manual pulls and returning audit hours to higher-value review."
    - title: "Controls carrying an automated test"
      target_pct: 40
      current_pct: 22
      recent: "the first self-testing controls went into production, surfacing two configuration drifts before they reached a customer."
- id: OKR-GRC-2026-H1-02
  objective: "Auto-draft 50% of new risk intake"
  period_end: 2026-06-30
  theme: ai-native
  key_results:
    - title: "New risk records auto-drafted for review"
      target_pct: 50
      current_pct: 30
      recent: "intake now opens from an AI-generated draft, compressing the time from identification to a scored, owned risk and returning analyst capacity to judgment work."
    - title: "Findings auto-routed to their control"
      target_pct: 80
      current_pct: 55
      recent: "findings now attach to the control they affect automatically, so none wait unrouted on manual filing."
"""


def build_ecosystem() -> None:
    """Write the full GRC-ecosystem corpus (the only corpus, post-retirement)."""
    DATA.mkdir(exist_ok=True)
    for d in (SCN, ISSUES, REM_DIR, GUARDRAIL_EVENTS_DIR):
        d.mkdir(exist_ok=True)
        for old in d.glob("*.yaml"):
            old.unlink()

    (DATA / "enterprise.yaml").write_text(ENTERPRISE)
    (DATA / "domains.yaml").write_text(render_domains())
    (DATA / "policies.yaml").write_text(render_policies())
    (DATA / "controls.yaml").write_text(render_controls())
    (DATA / "named_risks.yaml").write_text(render_named_risks())
    (DATA / "evidence.yaml").write_text(render_evidence())
    (DATA / "kris.yaml").write_text(render_kris())
    (DATA / "horizon.yaml").write_text(render_horizon())
    (DATA / "okrs.yaml").write_text(OKRS)
    (DATA / "estimators.yaml").write_text(ESTIMATORS)
    (DATA / "config.yaml").write_text(CONFIG)

    # v4.0 SPEC 0 GRC registers (never read by the eng build — P.4).
    (DATA / "regulations.yaml").write_text(REGULATIONS)
    (DATA / "sla_config.yaml").write_text(SLA_CONFIG)
    (DATA / "guardrails.yaml").write_text(GUARDRAILS)
    (DATA / "agent_inventory.yaml").write_text(AGENT_INVENTORY)
    for did, text in GUARDRAIL_EVENTS.items():
        (GUARDRAIL_EVENTS_DIR / f"{did}.yaml").write_text(text)

    # QBR v4.0 files (§1.D–§1.F). Never read by the eng build.
    (DATA / "assurance_requests.yaml").write_text(ASSURANCE_REQUESTS)
    (DATA / "program_period.yaml").write_text(PROGRAM_PERIOD)
    (DATA / "grc_okrs.yaml").write_text(GRC_OKRS)

    for spec in SCENARIOS:
        (SCN / f"{spec[0]}.yaml").write_text(render_scenario(spec))
    for eid, text in build_exceptions():
        (ISSUES / f"{eid}.yaml").write_text(text)
    for spec in ACCEPTED_VULN_EXCEPTIONS:
        (ISSUES / f"{spec[0]}.yaml").write_text(render_accepted_vuln_exception(spec))
    for spec in FINDINGS:
        (ISSUES / f"{spec[0]}.yaml").write_text(render_finding(spec))
    for text in build_remediations():
        rid = text.split("\n", 1)[0].split(": ", 1)[1]
        (REM_DIR / f"{rid}.yaml").write_text(text)

    n_scn = len(list(SCN.glob("*.yaml")))
    n_iss = len(list(ISSUES.glob("*.yaml")))
    n_rem = len(list(REM_DIR.glob("*.yaml")))
    print(f"Wrote {len(DOMAINS)} domains, {len(NAMED_RISKS)} named risks, {n_scn} scenarios")
    print(f"Wrote 93 ISO Annex A controls, {len(POLICIES)} policies, {len(EVIDENCE)} evidence records")
    print(f"Wrote {len(KRIS)} KRIs, {len(HORIZON)} horizon items, {n_iss} issues, {n_rem} remediations")
    _verify()


def _verify():
    """Print the RAG spread and portfolio read. The spread is a GUIDELINE to
    judge, not a target to fit (SPEC v2.2 §B): appetite is authored, so the
    colours are an outcome. Tune exposure -- never thresholds -- to move them."""
    import sys
    sys.path.insert(0, str(ROOT))
    from risk_ledger.config import Config
    from risk_ledger.graph_engine import GraphEngine, RAG_OVER, RAG_AT, RAG_BELOW
    from risk_ledger.loader import load_graph
    from risk_ledger.validation import validate_graph

    cfg = Config(as_of=__import__("datetime").date(2026, 6, 18))
    graph = load_graph(DATA)
    problems = validate_graph(graph, cfg)
    errs = [p for p in problems if p.severity == "error"]
    eng = GraphEngine(graph, cfg)
    from collections import Counter
    spread = Counter(r.state for r in eng.all_named_risk_residuals())
    p = eng.portfolio()
    amber = [d.domain.id for d in eng.all_domain_rollups() if d.amber_end_to_end]
    print(f"  hard validation errors: {len(errs)}")
    print(f"  RAG spread (outcome): {spread.get(RAG_OVER,0)} OVER / {spread.get(RAG_AT,0)} AT / "
          f"{spread.get(RAG_BELOW,0)} BELOW")
    print(f"  Portfolio {p.band.low/1e6:.1f}-{p.band.high/1e6:.1f}M ({p.appetite_state.upper()} "
          f"vs ${p.appetite/1e6:.0f}M appetite); "
          f"P(over capacity)={p.p_over_capacity*100:.0f}%; over_appetite={p.over_appetite}")
    print(f"  Amber end-to-end domains: {amber or 'none'}")


if __name__ == "__main__":
    build_ecosystem()
