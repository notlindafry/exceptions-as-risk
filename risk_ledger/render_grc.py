"""The GRC QBR page — a quarterly business review for the head of GRC (v4.0).

Reader (§0.1): the head of GRC, presenting to the CISO, who is GRC-adjacent, not
GRC-deep. Every label is legible without GRC vocabulary. The page answers three
questions about the program (§0.2): is it doing its job, is it efficient, does it
add value — as three columns over five program elements (the operating loop),
giving a fifteen-metric grid. Below it: team health, the team's own OKRs, and
three wins. Nothing else.

Structure (§0.3, §2.6): grid, then team health, then OKRs, then wins. Team health
sits below the program evidence on purpose — the same numbers read as a complaint
above the evidence and as a justified ask below it.

Isolation (§0.5): this is a separate page from the engineering profile, which
stays byte-identical. It reads registers the engineering build never opens.

Design: shared :root tokens, no raw hex in components. RAG (§0.10) is conventional
for coverage / currency / speed (green means healthy) and two-sided for control
right-sizing (over-built reads amber, never green). Every status carries its word.
WCAG contrast on the status trio verified against --bg/--surface (worst 6.04:1,
above the 4.5:1 AA bar) at the 10–12px label sizes this page is dense with.
"""

from __future__ import annotations

from pathlib import Path

from .config import Config
from .dashboard import _ANALYTICS, _REPO_URL, _ROOT, _TABS_CSS, _esc, _tab_bar
from .grc import QBREngine, load_grc_graph

_CSS = _ROOT + """
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--text); border-top:3px solid var(--accent);
  font-family:var(--font-body); font-size:15px; line-height:1.5; -webkit-font-smoothing:antialiased; }
h1,h2,h3,h4,.fig { font-family:var(--font-display); font-weight:600; letter-spacing:-0.01em; }
a { color:var(--accent); text-decoration:none; } a:hover { text-decoration:underline; }
:focus-visible { outline:2px solid var(--accent); outline-offset:2px; }
.wrap { max-width:1120px; margin:0 auto; padding:40px 24px 80px; }
header .eyebrow { color:var(--accent); font-size:10.5px; font-weight:600; letter-spacing:0.07em; text-transform:uppercase; }
header h1 { font-size:30px; margin:6px 0 4px; color:var(--text-strong); }
header .meta { color:var(--text-muted); font-size:13.5px; }
.wip-tag { font-size:28px; vertical-align:middle; letter-spacing:0.04em; color:var(--status-below-tint); font-weight:600; }
.lede { color:var(--text); font-size:13.5px; margin:16px 0 0; max-width:900px; }
/* grid: three question columns; each element is a full-width header over its row */
.qgrid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; margin:24px 0 0; }
.qh { color:var(--text); font-size:12px; font-weight:600; text-transform:uppercase; letter-spacing:0.05em;
  padding:0 2px 2px; }
.elhead { grid-column:1 / -1; margin-top:14px; }
.elhead .en { font-family:var(--font-display); font-weight:600; font-size:16px; color:var(--text-strong); }
.elhead .eq { color:var(--text-muted); font-size:12.5px; margin-left:10px; }
.cell { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius); padding:14px 16px; }
.cell .fig { font-size:23px; color:var(--text-strong); line-height:1.2; }
.cell .fig .unit { color:var(--text); font-weight:500; font-size:15px; }
.cell .two { font-size:16px; color:var(--text-strong); font-family:var(--font-display); font-weight:600; }
.cell .cap { color:var(--text-muted); font-size:11.5px; margin-top:8px; line-height:1.5; }
.st { display:inline-flex; align-items:baseline; gap:5px; font-size:11.5px; font-weight:600; margin-top:8px; }
.st .dot { width:8px; height:8px; border-radius:50%; display:inline-block; }
.st-at { color:var(--status-at); } .st-below { color:var(--status-below-tint); } .st-over { color:var(--status-over); }
/* blocks below the grid */
.block { margin:30px 0 0; }
.block h2 { font-size:16px; color:var(--text-strong); margin:0 0 4px; }
.block .why { color:var(--text-muted); font-size:12.5px; margin:0 0 14px; max-width:900px; }
.tri { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; }
.card { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius); padding:16px 18px; }
.card .fig { font-size:22px; color:var(--text-strong); }
.card .k { color:var(--text-muted); font-size:10.5px; text-transform:uppercase; letter-spacing:0.06em; }
.card .cap { color:var(--text-muted); font-size:12px; margin-top:6px; }
.objgrp { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius);
  padding:16px 20px; margin-top:12px; }
.objgrp .obj { font-family:var(--font-display); font-weight:600; font-size:13px; color:var(--text-muted);
  text-transform:uppercase; letter-spacing:0.04em; margin:0 0 8px; }
.kr { font-size:13px; color:var(--text-muted); margin:9px 0; line-height:1.55; max-width:940px; }
.kr b { color:var(--text); }
.kr .pct { font-family:var(--font-display); color:var(--status-at); font-weight:600; }
.wins { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; }
.win { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius); padding:16px 18px; }
.win .team { color:var(--accent); font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.05em; }
.win .txt { color:var(--text); font-size:13px; margin-top:7px; line-height:1.5; }
.absent { margin:26px 0 0; color:var(--text-muted); font-size:12px; line-height:1.6; max-width:900px; }
.absent b { color:var(--text); }
footer { margin-top:34px; color:var(--text-faint); font-size:12px; max-width:900px; line-height:1.6; }
.trace { color:var(--text-faint); font-size:10.5px; margin-top:10px; }
@media (max-width:900px){ .qgrid{grid-template-columns:1fr;} .tri,.wins{display:block;} .tri>*,.wins>*{margin-bottom:10px;} }
"""

# Status level -> (css class, dot token). Conventional RAG (§0.10): green healthy,
# amber attention, red urgent. Two-sided for control right-sizing reuses amber.
_LEVELS = {
    "good": ("st-at", "var(--status-at)"),
    "watch": ("st-below", "var(--status-below)"),
    "bad": ("st-over", "var(--status-over)"),
}


def _status(level: str, word: str) -> str:
    cls, dot = _LEVELS[level]
    return (f'<span class="st {cls}"><span class="dot" style="background:{dot}"></span>'
            f'{_esc(word)}</span>')


def _cell(fig: str, unit: str, level: str, word: str, cap: str) -> str:
    """A grid cell: the number, a self-explanatory metric label beside it, the
    status word, then smaller supporting detail."""
    unit_html = f' <span class="unit">{_esc(unit)}</span>' if unit else ""
    cap_html = f'<div class="cap">{_esc(cap)}</div>' if cap else ""
    return (f'<div class="cell"><div class="fig">{fig}{unit_html}</div>'
            f'{_status(level, word)}{cap_html}</div>')


def _pct(n: int, d: int) -> str:
    return f"{round(n / d * 100)}%" if d else "—"


# ---------------------------------------------------------------------------
# The grid (§2.1): five elements x three questions.
# ---------------------------------------------------------------------------


def _grid(e: QBREngine) -> str:
    ec = e.estate_coverage()
    ttu, ttu_n = e.time_to_understand()
    br = e.business_raised()
    dtr = e.defended_top_risks()
    dob = e.defended_obligations()
    opc, multi = e.obligations_per_control()
    own = e.owned_in_business()
    cp = e.current_proof()
    pa = e.proof_automated()
    ret = e.problems_returned()
    pp = e.past_promised()
    exc_d, dev_d, _ = e.days_to_decide()
    ck = e.can_kicking()
    afe = e.answered_from_existing()
    tat = e.turnaround()
    cons_now, cons_ret = e.consumers()

    intake_target = e.graph.sla.raw.get("risk_intake_to_scored_days", 10)
    decide_target = e.graph.sla.exception_raised_to_decided_days

    # owner concentration for 4c
    holders: dict[str, int] = {}
    for _id, owner, _c in ck:
        holders[owner] = holders.get(owner, 0) + 1
    top_holder = max(holders.items(), key=lambda kv: kv[1]) if holders else None

    dev_note = "under a day on agent events" if (dev_d is not None and dev_d < 1) else "same on agent events"
    rows = [
        # element, question, [(figure, metric label, level, status word, supporting detail)]
        ("See the risk", "Do we know what we're carrying?", [
            (f"{ec.n}/{ec.d}", "business units covered",
             "good" if ec.pct >= 90 else "watch",
             ("all covered" if not ec.detail else f"{', '.join(ec.detail)} uncovered"),
             f"of {ec.d} business units, only {', '.join(ec.detail) or 'none'} has no owned, scored risk"),
            (f"{ttu:g} days" if ttu is not None else "—", "to score a new risk",
             "good" if (ttu is not None and ttu <= intake_target) else "watch",
             (f"target {intake_target} days" if ttu is not None else "no new risks"),
             "average from a risk being identified to scored and owned, this quarter"),
            (_pct(br.n, br.d), "raised by the business",
             "good" if (br.pct or 0) >= 50 else "watch",
             f"{br.n} of {br.d} new risks",
             "new risks the business flagged itself this quarter, rather than us finding them"),
        ]),
        ("Set the defense", "Is something standing behind the important risks?", [
            (f'<span class="two">{dtr.n}/{dtr.d} top risks · {dob.n}/{dob.d} obligations</span>', "covered",
             "good" if (not dtr.detail and not dob.detail) else "watch",
             ("both fully covered" if (not dtr.detail and not dob.detail) else "gaps remain"),
             "top risks, and outside obligations, with at least one control behind them"),
            (f"{opc:g}", "obligations per control",
             "good", (f"{len(multi)} do double duty" if multi else "one-to-one"),
             "how many outside obligations each mapped control covers, on average"),
            (_pct(own.n, own.d), "controls owned in the business",
             "good" if (own.pct or 0) >= 80 else "watch",
             f"{own.n} of {own.d} controls",
             "controls with a named owner in the business who has confirmed it recently"),
        ]),
        ("Confirm it holds", "Do we have proof it's actually working?", [
            (_pct(cp.n, cp.d), "top-risk controls proven",
             "good" if (cp.pct or 0) >= 90 else ("watch" if (cp.pct or 0) >= 50 else "bad"),
             f"{cp.n} of {cp.d} controls",
             "of the controls behind our top risks, the share with current proof they work"),
            (_pct(pa.n, pa.d), "of evidence collection automated",
             "good" if (pa.pct or 0) >= 80 else "watch",
             f"{pa.n} of {pa.d} sources",
             "evidence sources that collect without a person in the loop"),
            (f"{ret.n} of {ret.d}", "closed problems recurred",
             "good" if ret.n == 0 else "watch",
             ("none returned" if ret.n == 0 else "one returned"),
             "problems we closed this quarter that had been closed once before"),
        ]),
        ("Act when it slips", "When something slips, do we move?", [
            (_pct(pp.n, pp.d), "commitments past due",
             "good" if (pp.pct or 0) <= 15 else ("watch" if (pp.pct or 0) <= 35 else "bad"),
             f"{pp.n} of {pp.d} open items",
             "open fixes and acceptances past the date they were promised by"),
            (f"{exc_d:g} days" if exc_d is not None else "—", "to decide an exception",
             "good" if (exc_d is not None and exc_d <= decide_target) else "watch",
             dev_note,
             f"median time to make the call; target {decide_target} days"),
            (str(len(ck)), "items re-dated 3+ times",
             "good" if len(ck) == 0 else "watch",
             (f"{top_holder[0].split('@')[0]} holds {top_holder[1]}" if top_holder else "none"),
             "acceptances pushed out again and again instead of being resolved"),
        ]),
        ("Prove it, inform decisions", "Can we show it, and does anyone use it?", [
            (_pct(afe.n, afe.d), "artifact reuse",
             "good" if (afe.pct or 0) >= 60 else "watch",
             f"{afe.n} of {afe.d} requests",
             "customer and auditor requests satisfied by an existing artifact, not net-new work"),
            (f"{tat:g} day" + ("s" if (tat or 0) != 1 else "") if tat is not None else "—",
             "average customer inquiry turnaround",
             "good" if (tat is not None and tat <= 5) else "watch",
             "median this quarter",
             "median across customer and auditor requests closed this quarter"),
            (str(len(cons_now)), "teams consuming our data",
             "good" if cons_ret.n >= cons_ret.d and cons_ret.d > 0 else "watch",
             (f"{cons_ret.n} of {cons_ret.d} prior returned" if cons_ret.d else "first quarter"),
             "downstream teams whose dashboards or pipelines pull GRC data, tracked automatically"),
        ]),
    ]

    qh = ('<div class="qh">Doing its job?</div><div class="qh">Efficient?</div>'
          '<div class="qh">Adding value?</div>')
    parts = [qh]
    for name, q, cells in rows:
        parts.append(f'<div class="elhead"><span class="en">{_esc(name)}</span>'
                     f'<span class="eq">{_esc(q)}</span></div>')
        parts += [_cell(*c) for c in cells]
    return f'<div class="qgrid">{"".join(parts)}</div>'


# ---------------------------------------------------------------------------
# Team health (§2.3), OKR line (§2.4), wins (§2.5)
# ---------------------------------------------------------------------------


def _team_health(e: QBREngine) -> str:
    t = e.team_health()
    role_html = " · ".join(
        f'{_esc(title)} <b class="fig" style="font-size:13px">{age}d</b>' for title, age in t["open_roles"]
    ) or "none open"
    head = t["headcount"] or 1
    took_off = round((head - t["no_time_off"]) / head * 100)
    return (
        '<div class="block"><h2>Team health</h2>'
        '<div class="tri">'
        f'<div class="card"><div class="k">Open roles &amp; how long</div>'
        f'<div class="cap" style="margin-top:8px;color:var(--text)">{role_html}</div></div>'
        f'<div class="card"><div class="k">GRC team took time off this quarter</div>'
        f'<div class="fig" style="margin-top:6px">{took_off}%</div></div>'
        f'<div class="card"><div class="k">Development budget used</div>'
        f'<div class="fig" style="margin-top:6px">{t["dev_budget_pct"]}%</div></div>'
        '</div></div>')


_THEME_LABEL = {"ai-native": "Make the program run itself", "scalable": "Scale with the business",
                "foundational": "Get the basics current"}


def _objectives(e: QBREngine) -> str:
    groups = []
    for okrs in e.okrs_by_theme().values():
        for okr in okrs:
            krs = ""
            for kr in okr.get("key_results", []):
                cur, tgt = kr.get("current_pct", 0), kr.get("target_pct", 0) or 1
                done = min(100, round(cur / tgt * 100))
                recent = kr.get("recent", "")
                tail = f" — {_esc(recent)}" if recent else ""
                krs += (f'<div class="kr"><b>{_esc(kr.get("title", ""))}</b> is '
                        f'<span class="pct">{done}% complete</span>{tail}</div>')
            groups.append(f'<div class="objgrp"><div class="obj">{_esc(okr.get("objective", ""))}</div>{krs}</div>')
    return ('<div class="block"><h2>2026 objectives progress</h2>' + "".join(groups) + '</div>')


def _wins(e: QBREngine) -> str:
    cards = "".join(
        f'<div class="win"><div class="team">{_esc(w.get("team", ""))}</div>'
        f'<div class="txt">{_esc(w.get("text", ""))}</div></div>'
        for w in e.wins())
    return (
        '<div class="block"><h2>Quarterly highlights</h2>'
        '<p class="why">The quarter\'s most significant developments, weighted toward the '
        '<b>business acting on its own risk</b> — the strongest evidence that the program creates '
        'value, not just activity.</p>'
        f'<div class="wins">{cards}</div></div>')


def _absent(e: QBREngine) -> str:
    return (
        '<div class="absent">'
        '<b>What\'s deliberately not here.</b> How much risk we\'re carrying against tolerance lives on '
        'the engineering profile — putting it here too would just start an argument about which number is '
        'right. There is <b>no single program-health score</b>: a blend of coverage, speed, and reuse '
        'would describe nothing. Vendor risk rides inside the coverage and control numbers above where '
        'vendors sit in a business unit, rather than getting its own line. How fast we notice a brand-new '
        'outside obligation is not tracked — a new one shows up above as a gap, but the speed of spotting '
        'it needs a watchlist we do not yet keep.'
        '</div>')


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------


def build_qbr_page(e: QBREngine) -> str:
    body = (
        '<div class="wrap">'
        + _tab_bar("grc")
        + '<header><div class="eyebrow">Company Corp · GRC quarterly review</div>'
        '<h1>GRC QBR <span class="wip-tag">[WIP]</span></h1>'
        f'<div class="meta">For the head of GRC · {e.period_key} · <b>synthetic data</b>, git-native YAML</div>'
        '<p class="lede">Three questions, five ways: is the program doing its job, is it efficient, and '
        'does it add value to the business? Read left to right for one program element; read a column '
        'down for one question across the whole program.</p>'
        '</header>'
        + _grid(e)
        + _team_health(e)
        + _objectives(e)
        + _wins(e)
        + _absent(e)
        + '<footer>Every figure names the set it is measured against; every status carries its word. '
        'Synthetic data; no live collectors.'
        f' · <a href="{_REPO_URL}">Source on GitHub</a>'
        '<div class="trace">The five elements map to the NIST Risk Management Framework '
        '(SP 800-37 Rev 2) and ISO 31000.</div>'
        '</footer>'
        '</div>')
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<meta name="robots" content="noindex, nofollow">'
        '<title>Company Corp — GRC QBR [WIP]</title>'
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&'
        'family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">'
        f'<style>{_CSS}{_TABS_CSS}</style>{_ANALYTICS}</head><body>{body}</body></html>'
    )


def render_grc_to(data_dir: Path, config: Config, out: Path) -> Path:
    """Load the extended corpus, compute the QBR metrics, render the page."""
    graph = load_grc_graph(data_dir)
    engine = QBREngine(graph, config)
    out.write_text(build_qbr_page(engine))
    return out
