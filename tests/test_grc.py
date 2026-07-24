"""Acceptance tests for the GRC QBR page and engine (v4.0, Part 5).

Two contracts: the isolation guarantee (§0.5 — the engineering profile is
untouched by the QBR corpus) and the page/metric acceptance (Part 5).
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import pytest

from risk_ledger import dashboard
from risk_ledger.config import Config
from risk_ledger.graph_engine import GraphEngine
from risk_ledger.grc import QBREngine, load_grc_graph
from risk_ledger.loader import load_graph
from risk_ledger.render_grc import build_qbr_page
from risk_ledger.validation import validate_graph

DATA = Path(__file__).resolve().parent.parent / "data"
AS_OF = dt.date(2026, 6, 18)


@pytest.fixture(scope="module")
def cfg() -> Config:
    return Config(as_of=AS_OF)


@pytest.fixture(scope="module")
def e(cfg) -> QBREngine:
    return QBREngine(load_grc_graph(DATA), cfg)


@pytest.fixture(scope="module")
def page(e) -> str:
    return build_qbr_page(e)


# --- Isolation (§0.5 / acceptance 1) ---------------------------------------


def test_engineering_profile_byte_identical_under_qbr_loader(cfg):
    g_eng = load_graph(DATA)
    validate_graph(g_eng, cfg)
    eng_page = dashboard.build_dashboard(g_eng, GraphEngine(g_eng, cfg))

    g_qbr = load_grc_graph(DATA)
    validate_graph(g_qbr, cfg)
    via_qbr = dashboard.build_dashboard(g_qbr, GraphEngine(g_qbr, cfg))
    assert eng_page == via_qbr  # the QBR loader/registers are invisible to eng


def test_deviations_never_on_the_issues_floor(e):
    assert not any(i.id.startswith("DEV-") for i in e.graph.issues)
    assert len(e.graph.deviations) == 5


def test_vuln_type_is_gone(e):
    # acceptance 11: no vuln issue type remains.
    from risk_ledger.models import FACTOR_MOVING_ISSUE_TYPES
    assert FACTOR_MOVING_ISSUE_TYPES == ("exception",)
    assert not any(i.type == "vuln" for i in e.graph.issues)


# --- The fifteen metrics compute (Part 2 / acceptance 2) -------------------


def test_estate_coverage_catches_the_gap(e):
    ec = e.estate_coverage()
    assert ec.d == 8 and ec.detail == ["mobile"]  # the deliberate coverage hole


def test_business_raised_and_speed(e):
    br = e.business_raised()
    assert br.n == 5 and br.d == 8
    median, n = e.time_to_understand()
    assert median == 14 and n == 7


def test_defense_reported_as_two_figures(e):
    # acceptance 3: 2a is two figures, never one.
    assert e.defended_top_risks().d == 3
    assert e.defended_obligations().d == 8


def test_owned_in_business_and_the_hole(e):
    own = e.owned_in_business()
    assert own.d == 93 and 40 <= own.n <= 60
    a58 = e.graph.controls["A.8.8"]  # sanity: some controls carry a business owner
    assert e.graph.controls["A.5.8"].raw.get("business_owner")  # named ...
    assert not e.graph.controls["A.5.8"].raw.get("owner_confirmed_on")  # ... but unconfirmed


def test_confirm_it_holds(e):
    assert e.proof_automated().n == 9  # api evidence relabelled automated
    ret = e.problems_returned()
    assert ret.d == 3 and ret.n == 1  # one recurrence among three closed


def test_act_when_it_slips(e):
    exc_d, dev_d, _ = e.days_to_decide()
    assert exc_d == 4  # within the 5-day authored target
    assert any(c > 2 for _id, _o, c in e.can_kicking())


def test_prove_it(e):
    assert e.answered_from_existing().n == 9
    assert e.turnaround() == 1
    now, ret = e.consumers()
    assert len(now) == 4 and ret.n == ret.d == 2  # all prior consumers returned


def test_team_okrs_wins(e):
    t = e.team_health()
    assert t["no_time_off"] == 1 and t["dev_budget_pct"] == 38
    assert len(t["open_roles"]) == 2
    assert sum(len(v) for v in e.okrs_by_theme().values()) == 2
    assert len(e.wins()) == 3


# --- Page acceptance (Part 5) ----------------------------------------------


def test_page_shell_and_wip(page):
    assert page.startswith("<!doctype html>")
    assert 'name="robots" content="noindex, nofollow"' in page
    assert page.count("[WIP]") >= 1  # acceptance 9: once, in the title
    assert 'href="dashboard.html"' in page  # tab to the engineering profile


def test_no_banned_vocabulary(page):
    # acceptance 6 / §0.1. Framework acronyms are allowed only in the one
    # traceability line; everything else is banned outright.
    lower = page.lower()
    for term in ("residual", "hygiene", "disposition", "provenance",
                 "second line", "factor-moving", "fair", "model b"):
        assert term not in lower, f"banned term on page: {term}"
    # framework acronyms only inside the single traceability sentence
    body = re.sub(r"map to the NIST Risk Management Framework.*?ISO 31000\.", "", page)
    for ac in ("DORA", "PCI", "NIST", "AAGATE", "CSA"):
        assert ac not in body, f"framework acronym outside traceability line: {ac}"


def test_no_composite_score(page):
    # acceptance 4: no blended program-health score is rendered anywhere.
    assert "health score" not in page.lower()


def test_every_status_carries_a_word(page):
    # acceptance 5: fifteen grid cells, each with a status word span.
    assert page.count('class="st ') >= 15


def test_two_figure_defense_on_page(page):
    assert "top risks" in page and "obligations" in page


def test_standards_traceability_line_once(page):
    assert page.count("NIST Risk Management Framework (SP 800-37 Rev 2) and ISO 31000") == 1


def test_find_the_number_in_two_places(page, e):
    # acceptance 8: a figure reads consistently where it appears.
    ec = e.estate_coverage()
    assert f"{ec.n}/{ec.d}" in page          # estate coverage on the grid
    assert "mobile uncovered" in page        # and its gap named
    assert "62%" in page                     # business-raised share
