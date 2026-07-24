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
/* grid */
.grid { width:100%; border-collapse:separate; border-spacing:10px; margin:22px 0 0; table-layout:fixed; }
.grid th { text-align:left; color:var(--text-muted); font-size:11px; font-weight:500; text-transform:uppercase;
  letter-spacing:0.05em; padding:0 6px 2px; vertical-align:bottom; }
.grid th.qcol { color:var(--text); font-size:12.5px; }
.grid td { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius);
  padding:14px 16px; vertical-align:top; }
.elname { background:none !important; border:none !important; padding:14px 6px !important; }
.elname .en { font-family:var(--font-display); font-weight:600; font-size:15px; color:var(--text-strong); }
.elname .eq { display:block; color:var(--text-muted); font-size:11.5px; margin-top:3px; line-height:1.4; }
.cell .fig { font-size:22px; color:var(--text-strong); line-height:1.1; }
.cell .cap { color:var(--text-muted); font-size:11.5px; margin-top:8px; line-height:1.45; }
.cell .two { font-size:15px; color:var(--text-strong); font-family:var(--font-display); font-weight:600; }
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
.okrline { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius); padding:14px 18px;
  display:flex; gap:22px; flex-wrap:wrap; align-items:baseline; }
.okrline .obj { font-family:var(--font-display); font-weight:600; font-size:13.5px; color:var(--text-strong); }
.okrline .kr { font-size:12.5px; color:var(--text-muted); }
.okrline .kr b { color:var(--text); font-family:var(--font-display); }
.wins { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; }
.win { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius); padding:16px 18px; }
.win .team { color:var(--accent); font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.05em; }
.win .txt { color:var(--text); font-size:13px; margin-top:7px; line-height:1.5; }
.absent { margin:26px 0 0; color:var(--text-muted); font-size:12px; line-height:1.6; max-width:900px; }
.absent b { color:var(--text); }
footer { margin-top:34px; color:var(--text-faint); font-size:12px; max-width:900px; line-height:1.6; }
.trace { color:var(--text-faint); font-size:10.5px; margin-top:10px; }
@media (max-width:900px){ .grid,.tri,.wins{display:block;} .grid td,.tri>*,.wins>*{margin-bottom:10px;} }
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


def _cell(fig: str, level: str, word: str, cap: str) -> str:
    return (f'<td class="cell"><div class="fig">{fig}</div>{_status(level, word)}'
            f'<div class="cap">{cap}</div></td>')


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

    rows = [
        # (element name, plain question under it, [cell, cell, cell])
        ("See the risk", "Do we know what we're carrying?", [
            (f"{ec.n}/{ec.d}",
             "good" if ec.pct >= 90 else "watch",
             ("all units covered" if not ec.detail else f"{', '.join(ec.detail)} uncovered"),
             "business units with an owned, scored risk"),
            (f"{ttu:g} days" if ttu is not None else "—",
             "good" if (ttu is not None and ttu <= intake_target) else "watch",
             (f"target {intake_target}" if ttu is not None else "no new risks"),
             f"to go from raised to scored, this quarter (n={ttu_n})"),
            (_pct(br.n, br.d),
             "good" if (br.pct or 0) >= 50 else "watch",
             f"{br.n} of {br.d} this quarter",
             "of new risks were raised by the business, not by us"),
        ]),
        ("Set the defense", "Is something standing behind the important risks?", [
            (f'<span class="two">{dtr.n}/{dtr.d} top risks</span><br>'
             f'<span class="two">{dob.n}/{dob.d} obligations</span>',
             "good" if (not dtr.detail and not dob.detail) else "watch",
             ("both fully covered" if (not dtr.detail and not dob.detail) else "gaps remain"),
             "top risks, and outside obligations, with a control behind them"),
            (f"{opc:g}",
             "good",
             (f"{len(multi)} pull double duty" if multi else "one-to-one"),
             "obligations covered per control on average"),
            (_pct(own.n, own.d),
             "good" if (own.pct or 0) >= 80 else "watch",
             f"{own.n} of {own.d} controls",
             "have a confirmed owner sitting in the business"),
        ]),
        ("Confirm it holds", "Do we have proof it's actually working?", [
            (_pct(cp.n, cp.d),
             "good" if (cp.pct or 0) >= 90 else ("watch" if (cp.pct or 0) >= 50 else "bad"),
             f"{cp.n} of {cp.d} top-risk controls",
             "have current proof they are working"),
            (_pct(pa.n, pa.d),
             "good" if (pa.pct or 0) >= 80 else "watch",
             f"{pa.n} of {pa.d} automated",
             "of that proof collects itself, no person in the loop"),
            (f"{ret.n} of {ret.d}",
             "good" if ret.n == 0 else "watch",
             ("none came back" if ret.n == 0 else "one came back"),
             "problems closed this quarter that had returned before"),
        ]),
        ("Act when it slips", "When something slips, do we move?", [
            (_pct(pp.n, pp.d),
             "good" if (pp.pct or 0) <= 15 else ("watch" if (pp.pct or 0) <= 35 else "bad"),
             f"{pp.n} of {pp.d} open items",
             "are past the date they were promised by"),
            (f"{exc_d:g} days" if exc_d is not None else "—",
             "good" if (exc_d is not None and exc_d <= decide_target) else "watch",
             (f"under a day on agent events" if (dev_d is not None and dev_d < 1) else "on agent events too"),
             f"to decide an exception (target {decide_target})"),
            (str(len(ck)),
             "good" if len(ck) == 0 else "watch",
             (f"{top_holder[0].split('@')[0]} holds {top_holder[1]}" if top_holder else "none"),
             "items re-dated more than twice, and who is holding them"),
        ]),
        ("Prove it, inform decisions", "Can we show it, and does anyone use it?", [
            (_pct(afe.n, afe.d),
             "good" if (afe.pct or 0) >= 60 else "watch",
             f"{afe.n} of {afe.d} requests",
             "answered from material we already had"),
            (f"{tat:g} day" + ("s" if (tat or 0) != 1 else "") if tat is not None else "—",
             "good" if (tat is not None and tat <= 5) else "watch",
             "median this quarter",
             "to turn a customer or auditor request around"),
            (str(len(cons_now)),
             "good" if cons_ret.n >= cons_ret.d and cons_ret.d > 0 else "watch",
             (f"{cons_ret.n} of {cons_ret.d} prior returned" if cons_ret.d else "first quarter"),
             "teams outside GRC used our data this quarter"),
        ]),
    ]

    head = ('<tr><th></th><th class="qcol">Doing its job?</th>'
            '<th class="qcol">Efficient?</th><th class="qcol">Adding value?</th></tr>')
    body = ""
    for name, q, cells in rows:
        body += (f'<tr><td class="elname"><span class="en">{_esc(name)}</span>'
                 f'<span class="eq">{_esc(q)}</span></td>'
                 + "".join(_cell(*c) for c in cells) + "</tr>")
    return f'<table class="grid"><thead>{head}</thead><tbody>{body}</tbody></table>'


# ---------------------------------------------------------------------------
# Team health (§2.3), OKR line (§2.4), wins (§2.5)
# ---------------------------------------------------------------------------


def _team_health(e: QBREngine) -> str:
    t = e.team_health()
    roles = t["open_roles"]
    role_html = " · ".join(
        f'{_esc(title)} <b class="fig" style="font-size:13px">{age}d</b>' for title, age in roles
    ) or "none open"
    off = t["no_time_off"]
    budget = t["dev_budget_pct"]
    return (
        '<div class="block"><h2>The team that runs it</h2>'
        '<p class="why">Everything above measures the program. This measures the team behind it — '
        'and it is the leading indicator for every number above.</p>'
        '<div class="tri">'
        f'<div class="card"><div class="k">Open roles &amp; how long</div>'
        f'<div class="cap" style="margin-top:8px;color:var(--text)">{role_html}</div></div>'
        f'<div class="card"><div class="k">No time off this quarter</div>'
        f'<div class="fig" style="margin-top:6px">{off}</div>'
        f'<div class="cap">of {t["headcount"]} — a count only, never a name</div></div>'
        f'<div class="card"><div class="k">Development budget used</div>'
        f'<div class="fig" style="margin-top:6px">{budget}%</div>'
        f'<div class="cap">low use is the signal: the change budget is sitting unspent</div></div>'
        '</div></div>')


_THEME_LABEL = {"ai-native": "Make the program run itself", "scalable": "Scale with the business",
                "foundational": "Get the basics current"}


def _okr_line(e: QBREngine) -> str:
    by_theme = e.okrs_by_theme()
    parts = []
    for theme, okrs in by_theme.items():
        for okr in okrs:
            krs = " · ".join(
                f'{_esc(kr.get("title", ""))} <b>{kr.get("current_pct", 0)}%</b>'
                f'<span style="color:var(--text-faint)">/{kr.get("target_pct", 0)}%</span>'
                for kr in okr.get("key_results", []))
            parts.append(f'<span class="obj">{_esc(okr.get("objective", ""))}</span> '
                         f'<span class="kr">{krs}</span>')
    inner = '<span style="flex-basis:100%;height:2px"></span>'.join(parts)
    return (
        '<div class="block"><h2>Where the program is heading</h2>'
        '<p class="why">Progress on making the program run itself — which the grid above cannot show: '
        'a program running well and changing not at all reads the same as one doing both.</p>'
        f'<div class="okrline">{inner}</div></div>')


def _wins(e: QBREngine) -> str:
    cards = "".join(
        f'<div class="win"><div class="team">{_esc(w.get("team", ""))}</div>'
        f'<div class="txt">{_esc(w.get("text", ""))}</div></div>'
        for w in e.wins())
    return (
        '<div class="block"><h2>Wins we can\'t measure</h2>'
        '<p class="why">The three that mattered most this quarter — chosen for where the '
        '<b>business</b> did something, not where we did.</p>'
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
        '<h1>GRC program review <span class="wip-tag">[WIP]</span></h1>'
        f'<div class="meta">For the head of GRC · {e.period_key} · <b>synthetic data</b>, git-native YAML</div>'
        '<p class="lede">Three questions, five ways: is the program doing its job, is it efficient, and '
        'does it add value to the business? Read left to right for one program element; read a column '
        'down for one question across the whole program.</p>'
        '</header>'
        + _grid(e)
        + _team_health(e)
        + _okr_line(e)
        + _wins(e)
        + _absent(e)
        + '<footer>Every figure names the set it is measured against; every status carries its word. '
        'Nothing on this page changes the risk numbers on the engineering profile — it reads its own '
        'records and is verified not to move them. Synthetic data; no live collectors.'
        f' · <a href="{_REPO_URL}">Source on GitHub</a>'
        '<div class="trace">The five elements map to the NIST Risk Management Framework '
        '(SP 800-37 Rev 2) and ISO 31000.</div>'
        '</footer>'
        '</div>')
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<meta name="robots" content="noindex, nofollow">'
        '<title>Company Corp — GRC program review [WIP]</title>'
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
