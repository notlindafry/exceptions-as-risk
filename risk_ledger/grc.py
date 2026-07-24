"""The GRC-program derivation layer (v4.0 Spec 1 §1.A–§1.C).

This module serves the GRC tab: the health of the program itself — coverage,
hygiene, throughput, and the governance of AI — for a GRC Manager. It is NOT
the eng view: the residual number belongs to the eng tab and does not lead
here. Every derivation below is a **diagnostic**; none moves residual (the
one-path rule, SPEC §4, holds — the only factor-moving issue type is
``exception``, and the deviation overlay in §1.C is provisional, bounded, and
never added to the eng portfolio).

Isolation (P.4): the eng build path is not called through here and is
unchanged. This module loads the same corpus via :func:`load_graph`, then
*additionally* reads the v4.0 registers the eng loader never opens —
``regulations.yaml``, ``sla_config.yaml``, ``guardrails.yaml``,
``agent_inventory.yaml``, and ``guardrail_events/`` (never ``issues/``).
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

from .config import Config
from .graph import Graph
from .graph_engine import GraphEngine
from .loader import load_graph
from .models import ISSUE_FINDING, Issue, IssueRecord, _as_date, _ci, _str_list
from .validation import validate_graph

# ---------------------------------------------------------------------------
# v4.0 register records (§0.B–§0.E). Parsed defensively, like everything else.
# ---------------------------------------------------------------------------

# Review cadence -> allowed age in days before a review is overdue. Mirrors the
# evidence cadence windows; ``annual`` is the sla_config default (12 months).
_CADENCE_DAYS = {"monthly": 31, "quarterly": 92, "semiannual": 184, "annual": 366}

# The four rungs a complete response ladder declares (§0.D).
LADDER_RUNGS = ("low", "medium", "high", "critical")

# Dispositions that contribute to the provisional overlay (§1.C): a proposed
# deviation awaits ratification, an accepted one is ratified; dismissed and
# remediated contribute nothing.
CONTRIBUTING_DISPOSITIONS = ("proposed", "accepted")
DISPOSITIONS = ("proposed", "dismissed", "accepted", "remediated")


@dataclass
class Requirement:
    """One external obligation (§0.B): framework + requirement, satisfied by
    existing ISO controls (map once, satisfy many)."""

    id: str
    framework: str
    requirement_ref: str
    title: str
    satisfied_by_controls: list[str]
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def parse(cls, rid: str, raw: dict[str, Any]) -> "Requirement":
        return cls(
            id=rid,
            framework=str(raw.get("framework", "")),
            requirement_ref=str(raw.get("requirement_ref", "")),
            title=str(raw.get("title", rid)),
            satisfied_by_controls=_str_list(raw.get("satisfied_by_controls")),
            raw=raw,
        )


@dataclass
class SLAConfig:
    """Authored service-level targets (§0.C) — commitments, never derived."""

    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def parse(cls, raw: dict[str, Any]) -> "SLAConfig":
        return cls(raw=raw or {})

    def _int(self, key: str, default: int) -> int:
        try:
            return int(self.raw.get(key, default))
        except (TypeError, ValueError):
            return default

    @property
    def policy_review_cadence_months(self) -> int:
        return self._int("policy_review_cadence_months", 12)

    @property
    def exception_raised_to_decided_days(self) -> int:
        return self._int("exception_raised_to_decided_days", 5)

    @property
    def finding_to_remediation_plan_days(self) -> int:
        return self._int("finding_to_remediation_plan_days", 15)


@dataclass
class Guardrail:
    """A declared agent guardrail (§0.D): policy-as-code for agents, traced up
    to a governing policy and mapped to the named risk its violation moves."""

    id: str
    title: str
    layer: str
    assertion: str
    policy: str
    mapped_named_risks: list[str]
    applies_to: list[str]
    autonomy_tier: Optional[int]
    owner: str
    rmf_functions: list[str]
    monitoring: dict[str, Any] = field(default_factory=dict)
    provisional_move: dict[str, Any] = field(default_factory=dict)
    response_ladder: dict[str, str] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def parse(cls, gid: str, raw: dict[str, Any]) -> "Guardrail":
        tier = raw.get("autonomy_tier")
        monitoring = raw.get("monitoring") if isinstance(raw.get("monitoring"), dict) else {}
        move = raw.get("provisional_move") if isinstance(raw.get("provisional_move"), dict) else {}
        ladder_raw = raw.get("response_ladder") if isinstance(raw.get("response_ladder"), dict) else {}
        return cls(
            id=gid,
            title=str(raw.get("title", gid)),
            layer=str(raw.get("layer", "")),
            assertion=str(raw.get("assertion", "")),
            policy=str(raw.get("policy", "")),
            mapped_named_risks=_str_list(raw.get("mapped_named_risks")),
            applies_to=_str_list(raw.get("applies_to")),
            autonomy_tier=int(tier) if isinstance(tier, int) else None,
            owner=str(raw.get("owner", "")),
            rmf_functions=_str_list(raw.get("rmf_functions")),
            monitoring=monitoring or {},
            provisional_move=move or {},
            response_ladder={str(k): str(v) for k, v in (ladder_raw or {}).items()},
            raw=raw,
        )

    @property
    def telemetry_kris(self) -> list[str]:
        return _str_list(self.monitoring.get("telemetry_kris"))

    @property
    def max_band_90ci(self) -> Optional[list[float]]:
        return _ci(self.provisional_move.get("max_band_90ci"))

    @property
    def moved_factor(self) -> str:
        return str(self.provisional_move.get("factor", ""))

    @property
    def disposition_sla_hours(self) -> Optional[int]:
        v = self.provisional_move.get("disposition_sla_hours")
        return int(v) if isinstance(v, (int, float)) else None

    @property
    def missing_ladder_rungs(self) -> list[str]:
        return [r for r in LADDER_RUNGS if r not in self.response_ladder]

    @property
    def ladder_complete(self) -> bool:
        return not self.missing_ladder_rungs


@dataclass
class AgentRecord:
    """One entry of the security-fed detected-agent set (§0.H seam)."""

    id: str
    description: str
    first_detected: Optional[dt.date]
    source: str
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def parse(cls, aid: str, raw: dict[str, Any]) -> "AgentRecord":
        return cls(
            id=aid,
            description=str(raw.get("description", "")),
            first_detected=_as_date(raw.get("first_detected")),
            source=str(raw.get("source", "")),
            raw=raw,
        )


@dataclass
class Deviation:
    """A guardrail deviation (§0.E): a *provisional* exception, machine-proposed
    and awaiting (or past) human disposition. Wraps the shape-compatible
    :class:`IssueRecord` and reads the deviation-specific fields from ``.raw``.
    Lives in ``guardrail_events/``, never ``issues/`` — so the eng residual
    cannot see it (P.4)."""

    record: IssueRecord

    @classmethod
    def parse(cls, raw: dict[str, Any], path: str) -> "Deviation":
        return cls(record=IssueRecord.parse(raw, path))

    # -- shared shape -------------------------------------------------------
    @property
    def id(self) -> str:
        return self.record.id

    @property
    def title(self) -> str:
        return self.record.title

    @property
    def filed_on(self) -> Optional[dt.date]:
        return self.record.filed_on

    @property
    def mapped_scenarios(self) -> list[str]:
        return self.record.mapped_scenarios

    @property
    def moves(self) -> str:
        return self.record.moves

    @property
    def with_ci_90ci(self) -> Optional[list[float]]:
        return self.record.with_ci_90ci

    # -- deviation-specific (.raw) ------------------------------------------
    @property
    def guardrail(self) -> str:
        return str(self.record.raw.get("guardrail", ""))

    @property
    def disposition(self) -> str:
        return str(self.record.raw.get("disposition", ""))

    @property
    def severity(self) -> str:
        return str(self.record.raw.get("severity", ""))

    @property
    def response_invoked(self) -> str:
        return str(self.record.raw.get("response_invoked", ""))

    @property
    def detected_by(self) -> str:
        return str(self.record.raw.get("detected_by", ""))

    @property
    def disposition_due(self) -> Optional[dt.date]:
        return _as_date(self.record.raw.get("disposition_due"))

    @property
    def disposition_on(self) -> Optional[dt.date]:
        return _as_date(self.record.raw.get("disposition_on"))

    @property
    def is_open(self) -> bool:
        """Still awaiting a human decision."""
        return self.disposition == "proposed"

    @property
    def contributes(self) -> bool:
        """Counts toward the provisional overlay (§1.C): proposed or accepted."""
        return self.disposition in CONTRIBUTING_DISPOSITIONS


# ---------------------------------------------------------------------------
# Loading (§1.A). The existing graph via load_graph, then the new registers
# into new collections. The eng build path is not called through here.
# ---------------------------------------------------------------------------


def _load_register_file(path: Path, parse, errors: list[str], label: str) -> dict:
    out: dict = {}
    if not path.exists():
        return out
    try:
        raw = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError as exc:
        errors.append(f"{path}: invalid YAML ({exc})")
        return out
    if not isinstance(raw, dict):
        errors.append(f"{path}: expected a mapping of {label}-id -> spec")
        return out
    for key, spec in raw.items():
        out[str(key)] = parse(str(key), spec or {})
    return out


def load_grc_graph(data_dir: Path) -> Graph:
    """Load the extended corpus: the assembled eng graph plus the GRC-only
    registers as new collections (``graph.regulations``, ``graph.sla``,
    ``graph.guardrails``, ``graph.agents``, ``graph.deviations``)."""
    data_dir = Path(data_dir)
    graph = load_graph(data_dir)
    errors = graph.load_errors

    graph.regulations = _load_register_file(
        data_dir / "regulations.yaml", Requirement.parse, errors, "requirement")
    graph.guardrails = _load_register_file(
        data_dir / "guardrails.yaml", Guardrail.parse, errors, "guardrail")
    graph.agents = _load_register_file(
        data_dir / "agent_inventory.yaml", AgentRecord.parse, errors, "agent")

    sla_path = data_dir / "sla_config.yaml"
    sla_raw: dict[str, Any] = {}
    if sla_path.exists():
        try:
            loaded = yaml.safe_load(sla_path.read_text())
            if isinstance(loaded, dict):
                sla_raw = loaded
            else:
                errors.append(f"{sla_path}: expected a mapping")
        except yaml.YAMLError as exc:
            errors.append(f"{sla_path}: invalid YAML ({exc})")
    graph.sla = SLAConfig.parse(sla_raw)

    # Deviations: their own directory, NEVER data/issues/ (P.4). Reuses the
    # IssueRecord shape so the engine's per-issue FAIR contribution applies.
    deviations: list[Deviation] = []
    dev_dir = data_dir / "guardrail_events"
    if dev_dir.exists():
        for path in sorted(dev_dir.glob("*.yaml")):
            try:
                raw = yaml.safe_load(path.read_text())
            except yaml.YAMLError as exc:
                errors.append(f"{path}: invalid YAML ({exc})")
                continue
            if not isinstance(raw, dict):
                errors.append(f"{path}: expected a mapping at the top level")
                continue
            deviations.append(Deviation.parse(raw, str(path)))
    graph.deviations = deviations

    # QBR v4.0 files (§1.D–§1.F): the assurance-request log, the hand-kept
    # per-quarter numbers, and the GRC team's own OKRs. Plain structures.
    graph.assurance_requests = _load_yaml_seq(data_dir / "assurance_requests.yaml", errors)
    graph.program_period = _load_yaml_map(data_dir / "program_period.yaml", errors)
    graph.grc_okrs = _load_yaml_seq(data_dir / "grc_okrs.yaml", errors)
    return graph


def _load_yaml_seq(path: Path, errors: list[str]) -> list:
    if not path.exists():
        return []
    try:
        raw = yaml.safe_load(path.read_text()) or []
    except yaml.YAMLError as exc:
        errors.append(f"{path}: invalid YAML ({exc})")
        return []
    return raw if isinstance(raw, list) else []


def _load_yaml_map(path: Path, errors: list[str]) -> dict:
    if not path.exists():
        return {}
    try:
        raw = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError as exc:
        errors.append(f"{path}: invalid YAML ({exc})")
        return {}
    return raw if isinstance(raw, dict) else {}


# ===========================================================================
# QBR v4.0 — the business-review engine (Part 2). Fifteen metrics across five
# program elements (the operating loop) and three questions, plus team health,
# the GRC team's own OKRs, and the wins. Every figure names a denominator; no
# composite. Reuses the engineering residual only to read which named risks sit
# over appetite (for the "top risks" metrics 2a/3a); nothing here moves a number.
# ===========================================================================


def _median(xs: list[float]) -> Optional[float]:
    xs = sorted(xs)
    n = len(xs)
    if n == 0:
        return None
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2.0


def _period_of(d: dt.date) -> tuple[str, dt.date, dt.date]:
    """(key, start, end) of the calendar quarter containing ``d``."""
    q = (d.month - 1) // 3 + 1
    start = dt.date(d.year, 3 * (q - 1) + 1, 1)
    if q == 4:
        end = dt.date(d.year, 12, 31)
    else:
        end = dt.date(d.year, 3 * q + 1, 1) - dt.timedelta(days=1)
    return f"{d.year}-Q{q}", start, end


def _prior_period_key(key: str) -> str:
    y, q = key.split("-Q")
    y, q = int(y), int(q) - 1
    if q == 0:
        y, q = y - 1, 4
    return f"{y}-Q{q}"


@dataclass
class Ratio:
    """A coverage/currency figure and the exact set behind its denominator."""
    n: int
    d: int
    note: str = ""
    detail: list = field(default_factory=list)  # the items behind n or (d - n)

    @property
    def pct(self) -> Optional[int]:
        return round(self.n / self.d * 100) if self.d else None


class QBREngine:
    """Computes the QBR page (Part 2) over the extended, validated corpus."""

    def __init__(self, graph: Graph, config: Config):
        self.graph = graph
        self.config = config
        self.problems: list[Issue] = validate_graph(graph, config)
        self.eng = GraphEngine(graph, config)
        self.as_of = config.as_of
        self.period_key, self.p_start, self.p_end = _period_of(config.as_of)
        self.prior_key = _prior_period_key(self.period_key)
        self.period = graph.program_period.get(self.period_key, {}) or {}
        self.prior = graph.program_period.get(self.prior_key, {}) or {}

    # -- shared reads -------------------------------------------------------
    def _over_appetite_risks(self) -> set[str]:
        return {r.named_risk.id for r in self.eng.all_named_risk_residuals()
                if r.state == "over"}

    def _in_period(self, d) -> bool:
        return isinstance(d, dt.date) and self.p_start <= d <= self.p_end

    # -- Element 1: See the risk -------------------------------------------
    def estate_coverage(self) -> Ratio:
        """1a. Business units with >=1 owned, scored risk, over the unit list in
        the current period block (a borrowed denominator, labelled business units)."""
        units = self.period.get("estate_units", []) or []
        covered = {u for nr in self.graph.named_risks.values()
                   for u in _str_list(nr.raw.get("estate_units"))}
        uncovered = [u for u in units if u not in covered]
        return Ratio(len([u for u in units if u in covered]), len(units),
                     note="business units with an owned, scored risk", detail=uncovered)

    def time_to_understand(self) -> tuple[Optional[float], int]:
        """1b. Median days from a risk being raised to scored, over risks raised
        this quarter."""
        gaps = []
        for nr in self.graph.named_risks.values():
            raised, scored = _as_date(nr.raw.get("raised_on")), _as_date(nr.raw.get("scored_on"))
            if self._in_period(raised) and isinstance(scored, dt.date):
                gaps.append((scored - raised).days)
        return _median(gaps), len(gaps)

    def business_raised(self) -> Ratio:
        """1c. Risks raised by the business, not by us, over all raised this quarter."""
        raised = [nr for nr in self.graph.named_risks.values()
                  if self._in_period(_as_date(nr.raw.get("raised_on")))]
        biz = [nr for nr in raised if str(nr.raw.get("source", "")) == "business"]
        return Ratio(len(biz), len(raised), note="new risks raised by the business")

    # -- Element 2: Set the defense ----------------------------------------
    def defended_top_risks(self) -> Ratio:
        """2a-i. Over-appetite named risks with >=1 mapped control."""
        over = self._over_appetite_risks()
        defended = [nid for nid in over if self.graph.controls_of_named_risk.get(nid)]
        undef = [nid for nid in over if not self.graph.controls_of_named_risk.get(nid)]
        return Ratio(len(defended), len(over),
                     note="top risks with a control behind them", detail=undef)

    def defended_obligations(self) -> Ratio:
        """2a-ii. External obligations with >=1 satisfying control present."""
        reqs = self.graph.regulations
        covered = [rid for rid, r in reqs.items()
                   if any(c in self.graph.controls for c in r.satisfied_by_controls)]
        uncovered = [rid for rid in reqs if rid not in covered]
        return Ratio(len(covered), len(reqs),
                     note="obligations with a control behind them", detail=uncovered)

    def obligations_per_control(self) -> tuple[float, list[str]]:
        """2b. Mean obligations satisfied per mapped control; controls serving
        more than one framework called out."""
        by_control: dict[str, set[str]] = {}
        frameworks: dict[str, set[str]] = {}
        for r in self.graph.regulations.values():
            for c in r.satisfied_by_controls:
                if c in self.graph.controls:
                    by_control.setdefault(c, set()).add(r.id)
                    frameworks.setdefault(c, set()).add(r.framework)
        if not by_control:
            return 0.0, []
        mean = sum(len(v) for v in by_control.values()) / len(by_control)
        multi = sorted(c for c, fw in frameworks.items() if len(fw) > 1)
        return round(mean, 1), multi

    def owned_in_business(self) -> Ratio:
        """2c. Controls with a confirmed business owner, over all controls."""
        confirmed = []
        for cid, c in self.graph.controls.items():
            owner = c.raw.get("business_owner")
            conf = _as_date(c.raw.get("owner_confirmed_on"))
            if owner and conf and (self.as_of - conf).days <= 366:
                confirmed.append(cid)
        return Ratio(len(confirmed), len(self.graph.controls),
                     note="controls with a confirmed owner in the business")

    # -- Element 3: Confirm it holds ---------------------------------------
    def _fresh(self, cid: str) -> bool:
        eids = self.graph.evidence_of_control.get(cid, [])
        if not eids:
            return False
        return all(self.graph.evidence[e].status(self.as_of) == "fresh" for e in eids)

    def current_proof(self) -> Ratio:
        """3a. Controls behind over-appetite risks that have current proof."""
        over = self._over_appetite_risks()
        controls = sorted({c for nid in over for c in self.graph.controls_of_named_risk.get(nid, [])})
        proven = [c for c in controls if self._fresh(c)]
        unproven = [c for c in controls if not self._fresh(c)]
        return Ratio(len(proven), len(controls),
                     note="controls behind top risks with current proof", detail=unproven)

    def proof_automated(self) -> Ratio:
        """3b. Evidence collected automatically, over all evidence."""
        auto = [e for e, ev in self.graph.evidence.items()
                if ev.collection_method.lower() == "automated"]
        return Ratio(len(auto), len(self.graph.evidence),
                     note="proof that collects itself")

    def problems_returned(self) -> Ratio:
        """3c. Findings that came back (carry recurrence_of) over findings closed
        this quarter."""
        closed = [i for i in self.graph.issues
                  if i.type == ISSUE_FINDING and self._in_period(_as_date(i.raw.get("closed_on")))]
        recurred = [i for i in closed if i.raw.get("recurrence_of")]
        return Ratio(len(recurred), len(closed),
                     note="closed problems that had come back", detail=[i.id for i in recurred])

    # -- Element 4: Act when it slips --------------------------------------
    def past_promised(self) -> Ratio:
        """4a. Open commitments past their promised date (overdue remediations +
        expired exceptions) over all open commitments."""
        open_rem = [r for r in self.graph.remediations if r.is_active]
        overdue_rem = [r for r in open_rem if r.target_date and r.target_date < self.as_of]
        open_exc = [i for i in self.graph.issues if i.type == "exception" and i.is_active]
        expired_exc = [i for i in open_exc if i.expires_on and i.expires_on < self.as_of]
        n_over = len(overdue_rem) + len(expired_exc)
        n_all = len(open_rem) + len(open_exc)
        return Ratio(n_over, n_all, note="open commitments past their promised date")

    def days_to_decide(self) -> tuple[Optional[float], Optional[float], int]:
        """4b. Median days to decide an exception; median days to decide a
        deviation (both against their promised turnaround)."""
        exc_gaps = []
        for i in self.graph.issues:
            if i.type != "exception":
                continue
            filed, decided = i.filed_on, _as_date(i.raw.get("decided_on"))
            if isinstance(filed, dt.date) and isinstance(decided, dt.date):
                exc_gaps.append((decided - filed).days)
        dev_gaps = []
        for d in self.graph.deviations:
            filed, decided = d.filed_on, d.disposition_on
            if isinstance(filed, dt.date) and isinstance(decided, dt.date):
                dev_gaps.append((decided - filed).days)
        return _median(exc_gaps), _median(dev_gaps), len(exc_gaps)

    def can_kicking(self) -> list[tuple[str, str, int]]:
        """4c. Items re-dated more than twice, with who is holding them."""
        out = []
        for i in self.graph.issues:
            if i.type == "exception" and i.is_active and i.renewal_count > 2:
                out.append((i.id, i.owner, i.renewal_count))
        out.sort(key=lambda t: t[2], reverse=True)
        return out

    # -- Element 5: Prove it, inform decisions -----------------------------
    def _requests_in_period(self) -> list[dict]:
        return [r for r in self.graph.assurance_requests
                if self._in_period(_as_date(r.get("received_on")))]

    def answered_from_existing(self) -> Ratio:
        """5a. Requests answered from material we already had."""
        reqs = self._requests_in_period()
        existing = [r for r in reqs if r.get("answered_from") == "existing"]
        return Ratio(len(existing), len(reqs), note="requests answered from what we already had")

    def handled_by_ai(self) -> Ratio:
        """5b. Requests resolved end to end by the AI responder, no person in loop."""
        reqs = self._requests_in_period()
        ai = [r for r in reqs if r.get("handled_by") == "ai"]
        return Ratio(len(ai), len(reqs), note="requests handled end to end by AI")

    def consumers(self) -> tuple[list[str], Ratio]:
        """5c. Teams outside GRC using our data, and how many came back."""
        now = self.period.get("consumers", []) or []
        prior = self.prior.get("consumers", []) or []
        returned = [c for c in now if c in prior]
        return now, Ratio(len(returned), len(prior), note="of last quarter's teams came back")

    # -- Team health, OKRs, wins -------------------------------------------
    def team_health(self) -> dict:
        team = self.period.get("team", {}) or {}
        roles = []
        for r in team.get("open_roles", []) or []:
            opened = _as_date(r.get("opened_on"))
            age = (self.as_of - opened).days if isinstance(opened, dt.date) else None
            roles.append((str(r.get("title", "")), age))
        roles.sort(key=lambda t: (t[1] is not None, t[1]), reverse=True)
        head = int(team.get("headcount", 0) or 0)
        prof_dev = int(team.get("prof_dev_requests", 0) or 0)
        return {
            "open_roles": roles,
            "no_time_off": int(team.get("no_time_off_count", 0) or 0),
            "prof_dev_requests": prof_dev,
            "prof_dev_pct": round(prof_dev / head * 100) if head else 0,
            "headcount": head,
        }

    def okrs_by_theme(self) -> dict[str, list]:
        out: dict[str, list] = {}
        for okr in self.graph.grc_okrs:
            out.setdefault(str(okr.get("theme", "other")), []).append(okr)
        return out

    def wins(self) -> list[dict]:
        return list(self.period.get("wins", []) or [])
