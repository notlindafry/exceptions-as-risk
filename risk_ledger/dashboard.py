"""The hero artifact: an executive dashboard for a VP of Engineering (SPEC §6, §7).

Rendered from the derived graph and the engine, as a single self-contained dark
HTML page: a portfolio summary (the ten-second read) plus a **closed set of seven
views** and one worked AI example. No JS framework; charts are baked SVG. The
brand is the vibe-shelf design system adapted for a read-only report (SPEC §7):
dark surfaces, sage accent, Inter/Space Grotesk, flat, with the RAG status triad
held outside the five-colour palette and used only on risk indicators, never on
chrome, never colour-alone.

The set is closed at seven (SPEC v2.7 §8). The six-view ceiling held from Day 4
covered only the *breach-shaped* problems; view 2 ("Where you're over-investing")
was the one missing problem class — over-control — not scope creep. A view earns
its place by mapping to a question a VP actually asks; do not add an eighth unless
one genuinely does.
"""

from __future__ import annotations

import datetime as dt
import html as _html
import math
from pathlib import Path

from .config import Config
from .graph import Graph
from .graph_engine import GraphEngine
from .graph_views import flagged_renewals, slipped_remediations
from .loader import load_graph
from .validation import validate_graph

# Every colour is a design-system token, defined once in the ``:root`` block
# below and nowhere else — no raw hex lives in this module outside that block
# (SPEC v2.4 §1). Inline SVG inherits the document's custom properties, and while
# SVG *presentation* attributes (fill="…") can't take var(), the ``style``
# attribute can, so the baked charts reference the same tokens the CSS does.
# Contrast of the status trio and derived muted/faint inks is recorded in
# docs/brand.md (SPEC v2.4 §2).
RAG = {
    "over": ("OVER", "var(--status-over)"),
    "at": ("AT", "var(--status-at)"),
    "below": ("BELOW", "var(--status-below)"),
}


def _esc(s: object) -> str:
    return _html.escape(str(s), quote=True)


def money(x: float) -> str:
    ax = abs(x)
    if ax >= 1e6:
        s = f"${ax / 1e6:.1f}M"
    elif ax >= 1e3:
        s = f"${ax / 1e3:.0f}k"
    else:
        s = f"${ax:.0f}"
    return ("-" + s) if x < 0 else s


def band_str(low: float, high: float) -> str:
    return f"{money(low)}–{money(high)}"


def _article(n: int) -> str:
    """'a'/'an' for a spoken integer — 8, 11 and 18 take 'an' ('an 8% chance')."""
    return "an" if n in (8, 11, 18) or (str(n).startswith("8") and n >= 80) else "a"


def _pct(p: float) -> str:
    """A probability as a percentage, guarded at the extremes (SPEC v2.8 §6): a
    near-certainty printed as a bare ``100%`` (or a near-impossibility as ``0%``)
    reads like a broken number, so clamp to ``>99%`` / ``<1%`` instead."""
    if p >= 0.995:
        return ">99%"
    if p <= 0.005:
        return "<1%"
    return f"{round(p * 100)}%"


def _dot(state: str, label: bool = True) -> str:
    """A status dot beside a text label — never colour alone (SPEC §7)."""
    name, colour = RAG[state]
    lab = f'<span class="rag-l">{name}</span>' if label else ""
    return f'<span class="rag"><span class="dot" style="background:{colour}"></span>{lab}</span>'


# ---------------------------------------------------------------------------
# Small SVG helpers (dark theme, rectangles / lines / text only)
# ---------------------------------------------------------------------------


def _svg(w: int, h: int, body: str, title: str) -> str:
    return (f'<svg viewBox="0 0 {w} {h}" width="100%" role="img" '
            f'aria-label="{_esc(title)}" style="font-family:var(--font-body)">{body}</svg>')


def _t(x, y, s, *, size=12, fill="var(--text)", anchor="start", weight=400, display=False) -> str:
    # fill is a design-system token, so it rides in `style` (a var() cannot go in
    # the SVG `fill` presentation attribute). `display` switches to the display
    # face for numerals — NOT a monospace font; the design system has none.
    style = f"fill:{fill}" + (";font-family:var(--font-display)" if display else "")
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" '
            f'text-anchor="{anchor}" font-weight="{weight}" style="{style}">{_esc(s)}</text>')


def _rect(x, y, w, h, fill, *, rx=None, extra="") -> str:
    r = f' rx="{rx}"' if rx is not None else ""
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}"{r} style="fill:{fill}"{extra}/>'


def _pct_grid_step(span: float) -> float:
    """A nice gridline step (in appetite-percent points) for an axis of ``span``
    points: the smallest of 10/20/25/50/100 that keeps the line count at most 8."""
    for s in (10.0, 20.0, 25.0, 50.0, 100.0):
        if span / s <= 8:
            return s
    return 100.0


def _pct_axis_bounds(pcts: list[float]) -> tuple[float, float]:
    """View-1 axis bounds, derived from the rendered data, never hard-coded (SPEC
    v2.9 §2): pad the min/max by 5 points, then round outward to the nearest 10.
    The pad is the guaranteed clearance — rounding to 10 alone leaves data at 50.1%
    sitting on a 50% edge. Today this yields 40%–170% (data spans ~53%–156%)."""
    lo = math.floor((min(pcts) - 5.0) / 10.0) * 10.0
    hi = math.ceil((max(pcts) + 5.0) / 10.0) * 10.0
    return lo, hi


def exposure_interval_svg(rows: list[tuple], lo_b: float, hi_b: float) -> str:
    """View 1 as an interval plot, read against appetite (SPEC v2.9 §2). The x-axis
    is **percent of each row's own appetite**, so a single static appetite line at
    100% is shared by every row and the breach mass — the slice past 100% — is
    comparable across rows for the first time. Each row draws its **p5–p95
    interval** tinted by RAG state; the **mean is an interior tick carrying a dollar
    label** (the only absolute magnitude in the chart, and it matches the table's
    residual mean); the slice **beyond 100% is a stronger red** and IS the breach
    mass. The axis does not anchor at 0% — no risk has zero exposure, and the plot
    has no zero-originating marks. rows = [(name, low_pct, mean_pct, high_pct,
    state, p_exceed, mean_usd)]; bounds ``lo_b``/``hi_b`` are appetite-percent."""
    left, right, top = 172, 104, 8
    row_h, gap = 34, 10
    axis_h, caption_h = 16, 18
    plot_w = 640 - left - right
    plot_bottom = top + len(rows) * (row_h + gap)
    h = plot_bottom + axis_h + caption_h
    span = hi_b - lo_b

    def x(v):
        return left + plot_w * (v - lo_b) / span

    body = [_rect(0, 0, 640, h, "var(--surface)")]
    # Percent gridlines; 100 is handled separately as the appetite line so it is
    # never drawn (or labelled) as a bare "100%".
    step = _pct_grid_step(span)
    v = math.ceil(lo_b / step) * step
    while v <= hi_b + 1e-6:
        if abs(v - 100.0) > 1e-6:
            body.append(f'<line x1="{x(v):.1f}" y1="{top}" x2="{x(v):.1f}" y2="{plot_bottom}" style="stroke:var(--border)" stroke-width="1"/>')
            body.append(_t(x(v), plot_bottom + 12, f"{int(round(v))}%", size=10, fill="var(--text-muted)", anchor="middle"))
        v += step
    # The one appetite line, at 100% of every row's own appetite (SPEC v2.9 §2).
    xa = x(100.0)
    body.append(f'<line x1="{xa:.1f}" y1="{top}" x2="{xa:.1f}" y2="{plot_bottom}" '
                f'style="stroke:var(--text-strong)" stroke-width="1.25" stroke-dasharray="3 2" opacity="0.85"/>')
    body.append(_t(xa, plot_bottom + 12, "appetite", size=10, fill="var(--text-muted)", anchor="middle"))
    ivh = 12
    for i, (name, low, mean, high, state, p_exc, mean_usd) in enumerate(rows):
        y = top + i * (row_h + gap)
        cy = y + row_h / 2
        colour = RAG[state][1]
        ivy = cy - ivh / 2
        x0, x1 = x(low), x(high)
        body.append(_t(left - 10, cy + 4, name, size=12, anchor="end"))
        # the p5–p95 interval is the mark, RAG-tinted, with a defining outline
        body.append(f'<rect x="{x0:.1f}" y="{ivy:.1f}" width="{max(x1 - x0, 3):.1f}" height="{ivh}" rx="5" '
                    f'style="fill:{colour};stroke:{colour}" fill-opacity="0.32" stroke-opacity="0.9" stroke-width="1"/>')
        # the slice beyond the appetite line (100%) is the breach mass — stronger red
        if high > 100.0:
            xs = max(xa, x0)
            body.append(f'<rect x="{xs:.1f}" y="{ivy:.1f}" width="{max(x1 - xs, 1):.1f}" height="{ivh}" rx="0" '
                        f'style="fill:var(--status-over)" fill-opacity="0.58"/>')
        # the mean tick, carrying its dollar figure — the only absolute magnitude
        # in the chart, and the number the colour keys off
        body.append(f'<line x1="{x(mean):.1f}" y1="{cy - 9:.1f}" x2="{x(mean):.1f}" y2="{cy + 9:.1f}" '
                    f'style="stroke:var(--text-strong)" stroke-width="2"/>')
        body.append(_t(x(mean), cy - 12, money(mean_usd), size=9, anchor="middle",
                       fill="var(--text-strong)", weight=600))
        body.append(_t(636, cy + 1, RAG[state][0], size=10, fill=colour, anchor="end", weight=600))
        if p_exc >= 0.10:
            body.append(_t(636, cy + 12, f"{round(p_exc * 100)}% breach", size=9,
                           fill="var(--text-muted)", anchor="end"))
    cap_y = h - 5
    body.append(_t(636, cap_y, "interval = 5–95% · tick = mean ($) · red = breach mass",
                   size=10, fill="var(--text-muted)", anchor="end"))
    return _svg(640, h, "".join(body), "Residual interval (5–95%) as a percent of appetite, by named risk")


def _predation(graph: Graph, eng: GraphEngine) -> list[dict]:
    """The ``diverted_to`` graph read as predation (SPEC v2.9, predation view).

    A ``diverted_to`` sink is a **black hole** — a project funded by starving
    others. Each exception filed on a starved project (``issue.okr``) and diverted
    here is a *forced* exception that sits on the **victim's** books, not the
    sink's. We never sum those onto the sink (the retired "true footprint" was that
    manufactured sum); we report the relationship — blast radius on the cause, the
    forced exceptions on the victims — with the RAG state of the risk each forced
    exception sits on, so an over-appetite casualty can read red. Black holes are
    ranked by blast radius (victims, then forced exceptions)."""
    st: dict[str, str | None] = {}
    for nid in graph.named_risks:
        r = eng.named_risk_residual(nid)
        st[nid] = r.state if r else None

    def risk_state(issue) -> str | None:
        for sid in graph.resolved_scenarios(issue):
            sc = graph.scenarios.get(sid)
            if sc and sc.named_risk:
                return st.get(sc.named_risk)
        return st.get(issue.mapped_risk)

    sinks: dict[str, list] = {}
    for i in graph.issues:
        if (i.type == "exception" and i.diverted_to and i.diverted_to != i.okr
                and eng.has_contribution(i.id)):
            sinks.setdefault(i.diverted_to, []).append(i)

    holes = []
    for sink, excs in sinks.items():
        vmap: dict[str, list] = {}
        for i in excs:
            vmap.setdefault(i.okr, []).append((i.id, risk_state(i)))
        victims = []
        for okr, forced in vmap.items():
            forced.sort(key=lambda t: t[0])
            victims.append({"okr": okr, "forced": forced,
                            "has_over": any(s == "over" for _, s in forced)})
        # over-appetite casualties first (the sharp end), then alphabetical
        victims.sort(key=lambda v: (not v["has_over"], v["okr"]))
        holes.append({
            "sink": sink,
            "n_victims": len(vmap),
            "n_exc": len(excs),
            "n_over": sum(1 for _i in excs if risk_state(_i) == "over"),
            "victims": victims,
        })
    holes.sort(key=lambda h: (h["n_victims"], h["n_exc"]), reverse=True)
    return holes


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------


def _okr_name(graph: Graph, okr_id: str) -> str:
    """The OKR's real name — its title if authored, else the id itself. The id
    (``gcloud-migration``) is the accepted display form (SPEC v2.4 §3.5); this
    never applies a cosmetic ``.title()`` filter."""
    okr = graph.okrs.get(okr_id)
    return okr.title if okr and okr.title else okr_id


def _join_names(names) -> str:
    """A prose list — ``A``, ``A and B``, ``A, B, and C`` — for naming a handful of
    risks inline without a table."""
    xs = list(names)
    if len(xs) <= 1:
        return xs[0] if xs else ""
    if len(xs) == 2:
        return f"{xs[0]} and {xs[1]}"
    return ", ".join(xs[:-1]) + f", and {xs[-1]}"


def _owner(owner: str) -> str:
    """The accountable owner as a handle, not an email (SPEC v3.2): ``platform-lead``,
    not ``platform-lead@company.example``. Owner is surfaced only where naming who is
    accountable changes what the reader does — never everywhere the field exists."""
    return owner.split("@")[0] if owner else ""


def _addressed_by_funded(graph: Graph, scenario_ids: list[str]) -> bool:
    funded = {"funded", "in_progress"}
    rem_ids = {rid for sid in scenario_ids for rid in graph.remediations_of_scenario.get(sid, [])}
    return any(r.status in funded for r in graph.remediations if r.id in rem_ids)


def _rag_counts_html(rag_counts: dict) -> str:
    """The domain's RAG mix as counted dots — every count carries its number, so
    identity is never colour-alone (SPEC §7). Zeros stay, faint, to keep the read."""
    parts = []
    for state in ("over", "at", "below"):
        n = rag_counts.get(state, 0)
        op = "" if n else ' style="opacity:.3"'
        parts.append(f'<span class="ragc"{op}><span class="dot" style="background:{RAG[state][1]}"></span>{n}</span>')
    return '<span class="ragcs">' + "".join(parts) + "</span>"


def _domain_idle(rollup, residuals: dict):
    """Idle tolerance and allocation status for a domain (SPEC v2.8 §3). Idle is a
    real quantity — `Σ (appetite − residual)` over the domain's BELOW-state risks
    only — that averages nothing, unlike the residual/appetite ratio it replaces
    (a Simpson's trap: Resilience's 59% blended a 102% breach with a 6% idle risk).

    Status is the sharper, actionable finding:
      * ``over-controlled`` — nothing at or above appetite anywhere (pure idle).
      * ``mis-allocated``   — a breach AND idle tolerance in the same domain.
      * ``balanced``        — a risk operating at appetite, no breach.
    """
    belows = [residuals[n] for n in rollup.named_risk_ids if residuals[n].state == "below"]
    overs = [residuals[n] for n in rollup.named_risk_ids if residuals[n].state == "over"]
    idle = sum(r.threshold - r.band.mean for r in belows)
    biggest = max(belows, key=lambda r: r.threshold - r.band.mean, default=None)
    rc = rollup.rag_counts
    if rc.get("over", 0) >= 1 and rc.get("below", 0) >= 1:
        status = "mis-allocated"
    elif rc.get("over", 0) == 0 and rc.get("at", 0) == 0:
        status = "over-controlled"
    else:
        status = "balanced"
    return idle, overs, biggest, status


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------

_UNFUNDED = {"proposed"}
_IN_PROGRESS = {"in_progress"}


def _funding_effect(live, res, appetite: float) -> str:
    """The computed what-if effect on one line: the live mean and breach, an arrow,
    the post-funding mean, and the RAG state it lands in (SPEC v3.0 §3a). Shown, not
    asserted — the number is what residual_if_funded actually returns."""
    landed = {"at": "now at appetite", "below": "now below appetite",
              "over": "still over"}.get(res.state, "")
    return (f"{money(live.band.mean)} ({_pct(live.p_over_appetite)} breach) &rarr; "
            f"<b>{money(res.band.mean)}</b>, within its {money(appetite)} appetite ({landed})")


def _top5_recs(graph: Graph, eng: GraphEngine) -> list[str]:
    """The Top 5 (SPEC v3.0 §3): ranked plans, deduped by risk, each a one-line
    action + lever + risk + **computed** effect. Fund-rows are gated on
    residual_if_funded — a plan earns a slot only if the engine reproduces the
    within-appetite result (acceptance 2), never asserts it. Ranking is severity ×
    actionability: (1) over & unfunded, (2) predation with over-appetite casualties,
    (3) a domain over-built while breaches go unfunded, (4) the materiality tail,
    (5) steady-state (keep a funded fix on track)."""
    residuals = {r.named_risk.id: r for r in eng.all_named_risk_residuals()}
    over = sorted((r for r in residuals.values() if r.state == "over"),
                  key=lambda r: r.band.mean, reverse=True)
    recs: list[tuple[int, float, str, str]] = []  # (priority, tiebreak, subject, html)
    n_unfunded_over = 0

    for r in over:
        nid = r.named_risk.id
        # Over-appetite risks carry their accountable owner (SPEC v3.2 §2/§4) — the
        # who-to-summon handle on the rows a VP acts on. Predation and domain recs
        # below name a project/domain, not a single owner, so they do not.
        own = f' <span class="rec-own">owner: {_esc(_owner(r.named_risk.owner))}</span>' if r.named_risk.owner else ""
        plan = eng.plan_to_appetite(nid, _UNFUNDED)
        if plan and plan.sufficient:  # Type A / B — fund a sufficient unfunded plan
            n_unfunded_over += 1
            rems = [next(x for x in graph.remediations if x.id == rid) for rid in plan.remediation_ids]
            # Name the plan by its short title, not its record id — the exec read
            # wants the fix, not the ledger code (the id lives in view 4 / the data).
            names = " + ".join(f"{rm.title} (restore {rm.restores_control})" for rm in rems)
            verb = "Fund" if len(rems) == 1 else "Fund together"
            cleared = ", ".join(plan.result.cleared)
            # The row states where the residual lands and that it is under appetite
            # (via _funding_effect). It deliberately does NOT report the headroom it
            # opens: unused appetite is not a spendable figure, and the arithmetic
            # read like freed cash.
            recs.append((1, -r.band.mean, nid,
                         f'<b>{verb} {_esc(names)}</b> — clears {_esc(cleared)} and brings '
                         f'<b>{_esc(r.named_risk.label)}</b> {_funding_effect(r, plan.result, r.threshold)}.{own}'))
        else:
            inflight = eng.plan_to_appetite(nid, _IN_PROGRESS)
            if inflight and inflight.sufficient:  # steady-state — the sufficient fix is actively underway
                ip = [next(x for x in graph.remediations if x.id == rid) for rid in inflight.remediation_ids]
                names = " & ".join(rm.title for rm in ip)
                recs.append((5, -r.band.mean, nid,
                             f'<b>Keep {_esc(names)} on track</b> (in progress) — it brings '
                             f'<b>{_esc(r.named_risk.label)}</b> {_funding_effect(r, inflight.result, r.threshold)}; '
                             f"don't let the in-flight fix slip.{own}"))
            else:  # Type D — no funded path reaches appetite
                recs.append((1, -r.band.mean, nid,
                             f'<b>Accept or escalate {_esc(r.named_risk.label)}</b> — no funded path brings it '
                             f'within its {money(r.threshold)} appetite this cycle; decide at a board-signed '
                             f'threshold or escalate for budget.{own}'))

    # Priority 2 — predation with over-appetite casualties (Type C, a lever not a plan)
    for h in _predation(graph, eng):
        if h["n_over"] >= 1:
            casualties = ", ".join(v["okr"] for h2 in [h] for v in h2["victims"] if v["has_over"])
            recs.append((2, -float(h["n_exc"]), h["sink"],
                         f'<b>Reprioritize {_esc(h["sink"])}</b> — it is forcing {h["n_exc"]} exceptions on '
                         f'{h["n_victims"]} teams and pushing {_esc(casualties)} over their own appetite to hold its date.'))

    # Priority 3 — a domain over-built while breaches go unfunded (Type C, reallocation)
    resid = {r.named_risk.id: r for r in eng.all_named_risk_residuals()}
    oc, oc_idle = None, -1.0
    for d in eng.all_domain_rollups():
        idle, _o, _b, status = _domain_idle(d, resid)
        if status == "over-controlled" and idle > oc_idle:
            oc, oc_idle = d, idle
    if oc is not None:
        nids = graph.named_risks_of_domain.get(oc.domain.id, [])
        tol = sum(graph.named_risks[n].appetite_threshold for n in nids
                  if graph.named_risks[n].appetite_threshold)
        used = sum(resid[n].band.mean for n in nids if n in resid)
        util = round(used / tol * 100) if tol else 0
        recs.append((3, -oc_idle, oc.domain.id,
                     f'<b>Hold {_esc(oc.domain.title)} investment flat</b> — it runs at '
                     f'{util}% of its {money(tol)} declared tolerance while {n_unfunded_over} '
                     f'{"breach sits" if n_unfunded_over == 1 else "breaches sit"} unfunded over appetite.'))

    recs.sort(key=lambda t: (t[0], t[1]))
    out, seen = [], set()
    for _pri, _tb, subject, html in recs:
        if subject in seen:
            continue
        seen.add(subject)
        out.append(html)
        if len(out) == 5:
            break

    # Priority 4 — the materiality tail is a FALLBACK only: it fills a slot when
    # fewer than five real findings exist, and never bumps a live steady-state fix
    # off the list. On this corpus the five above are all real, so it does not show.
    if len(out) < 5:
        p = eng.portfolio()
        if p and p.capacity:
            out.append(
                f'<b>Govern the materiality tail</b> — a {_pct(p.p_over_capacity)} chance the portfolio crosses its '
                f'{money(p.capacity)} audit-materiality line this year; nothing to fund, but the board-level number to hold to.')
    return out[:5]


def _top5_section(graph: Graph, eng: GraphEngine) -> str:
    """The banner above the summary: what to do, before what is true (SPEC v3.0 §3b).
    Unnumbered — it is not one of the seven views, it is the executive's first read."""
    items = "".join(f'<li><span class="t5n">{i}</span><span class="t5t">{line}</span></li>'
                    for i, line in enumerate(_top5_recs(graph, eng), 1))
    return (f'<section class="top5" aria-label="Top 5 — do this first">'
            f'<h2>Do this first <span class="t5sub">the five highest-leverage moves, ranked · '
            f'fund-rows are computed, not asserted</span></h2><ol>{items}</ol></section>')


def _summary(graph: Graph, eng: GraphEngine) -> str:
    p = eng.portfolio()
    over = [r for r in eng.all_named_risk_residuals() if r.state == "over"]
    over.sort(key=lambda r: r.band.mean, reverse=True)
    orphans = [r for r in over if not _addressed_by_funded(graph, r.scenario_ids)]
    n_renew = len(flagged_renewals(graph, eng.config))
    n_slip = len(slipped_remediations(graph, eng.config))
    # the black hole: the project starving the most others (SPEC v2.9 predation §3c)
    holes = _predation(graph, eng)
    hole = holes[0] if holes else None
    # over-investing is a problem too (SPEC v2.7 §3): the over-controlled domain is
    # the one with nothing at or above appetite, reported by its idle tolerance (a
    # real quantity, not the Simpson's-trap ratio, SPEC v2.8 §3).
    residuals = {r.named_risk.id: r for r in eng.all_named_risk_residuals()}
    oc, oc_idle = None, 0.0
    ma, ma_idle, ma_overs = None, -1.0, []
    for d in eng.all_domain_rollups():
        idle, overs, _big, status = _domain_idle(d, residuals)
        if status == "over-controlled" and idle > oc_idle:
            oc, oc_idle = d, idle
        elif status == "mis-allocated" and idle > ma_idle:
            ma, ma_idle, ma_overs = d, idle, overs

    pos = RAG[p.appetite_state]
    cards = []
    cards.append(
        f'<div class="hero"><div class="hero-num" style="color:{pos[1]}">{band_str(p.band.low, p.band.high)}</div>'
        f'<div class="hero-cap">residual exposure this year, against a {money(p.appetite)} appetite'
        f' &nbsp;{_dot(p.appetite_state)}</div>'
        f'<div class="hero-sub">Over appetite — the signal: '
        f'{"the entire residual range sits above the " + money(p.appetite) + " line" if p.p_over_appetite >= 0.99 else _pct(p.p_over_appetite) + " of the range is over the line"}. '
        f'Roughly {_article(round(p.p_over_capacity * 100))} '
        f'<b style="color:var(--status-below-tint)">{_pct(p.p_over_capacity)} chance</b> of crossing the '
        f'{money(p.capacity)} materiality line this year. '
        f'{round(p.band.mean / graph.enterprise.revenue_annual * 1000) / 10}% of revenue.</div></div>'
    )
    # Four peer tiles, four genuinely different asks (SPEC v2.9 §5). "Top fixes"
    # (over[:3], a table of contents for the chart six inches below) and "Falling
    # through cracks" (both orphans are already mis-allocation drivers) are gone;
    # mis-allocation leads because it is the sharpest read — the money to cover a
    # breach is already sitting idle in the same domain, under the same owner.
    # Over-control does NOT fold in: Privacy has nothing at or above appetite, so
    # there is no breach to reallocate toward — it keeps its own slot.
    ma_over = ", ".join(o.named_risk.label for o in ma_overs) if ma_overs else "—"
    tiles = [
        ("Mis-allocated", ma.domain.title if ma else "—",
         (f"{money(ma_idle)} idle beside a breach ({ma_over}) — the same owner can shift the control effort to it"
          if ma else "—"), True),
        ("Over-controlled", oc.domain.title if oc else "—",
         (f"{money(oc_idle)} idle — nothing at or above appetite" if oc else "—"), True),
        ("Eating other teams", hole["sink"] if hole else "—",
         (f'starving {hole["n_victims"]} projects · {hole["n_over"]} over appetite' if hole else "no diverted debt"), False),
        ("The can you keep kicking", f"{n_renew} renewed · {n_slip} slipped",
         "temporary-forever + slipped dates", False),
    ]
    tile_html = "".join(
        f'<div class="tile{" warn" if warn else ""}"><div class="tile-k">{_esc(k)}</div>'
        f'<div class="tile-v">{_esc(v)}</div><div class="tile-s">{_esc(s)}</div></div>'
        for k, v, s, warn in tiles
    )
    return (f'<section class="summary"><h2>Where are we weakest, what do we fix first, '
            f'and why does it matter to what&nbsp;we\'re&nbsp;shipping?</h2>{cards[0]}'
            f'<div class="tiles">{tile_html}</div></section>')


def _view1_key(r) -> tuple:
    """Rank/select by position against appetite, not by absolute dollars (SPEC v2.9
    §3/§4): ``(-round(100·mean/appetite), -p_exceed)``. Rounding to the displayed
    precision **before** comparing is not cosmetic — the raw top-two ratio gap
    (103.2% vs 102.9%) is inside the Monte Carlo's own noise, so a raw key lets the
    seed decide row 1. Rounded, the three OVER risks lock to Platform > PCI >
    Production across seeds; the AT block still shuffles, which is correct — the
    model cannot tell risks 2.8 points apart, and asserting an order would describe
    nothing."""
    return (-round(100 * r.band.mean / r.threshold), -r.p_over_appetite)


def _view1(graph: Graph, eng: GraphEngine) -> str:
    ranked = sorted(eng.all_named_risk_residuals(), key=_view1_key)[:8]
    rows = [(r.named_risk.label, 100 * r.band.low / r.threshold, 100 * r.band.mean / r.threshold,
             100 * r.band.high / r.threshold, r.state, r.p_over_appetite, r.band.mean)
            for r in ranked]
    lo_b, hi_b = _pct_axis_bounds([p for row in rows for p in (row[1], row[3])])
    items = []
    for r in ranked:
        # Each atom (an issue id, the position phrase, the probability phrase, the
        # plan status) is kept whole with nowrap, so a cell only ever wraps at a
        # " · " or ", " separator — never mid-phrase or mid-id.
        driver_ids = [c.issue.id for c in r.drivers[:2]] or ["baseline exposure"]
        drivers = ", ".join(f'<span class="nb">{_esc(d)}</span>' for d in driver_ids)
        if _addressed_by_funded(graph, r.scenario_ids):
            funded = '<span class="nb">funded plan</span>'
        else:
            funded = '<span class="nb" style="color:var(--status-over)">no funded plan</span>'
        # Position and probability, side by side but never conflated (SPEC v2.5 §2b/§2a):
        # mean/appetite distinguishes a mild amber from the standout; P(exceed) is the tail.
        ratio = f"{round(r.band.mean / r.threshold * 100)}% of appetite"
        pos = f'<span class="nb">{_esc(ratio)}</span>'
        if r.p_over_appetite >= 0.10:
            pos += f' · <span class="nb">{_pct(r.p_over_appetite)} chance of appetite breach</span>'
        items.append(
            f'<tr><td>{_dot(r.state)}</td><td class="nm" title="{_esc(r.named_risk.title)}">{_esc(r.named_risk.label)}</td>'
            f'<td class="num">{band_str(r.band.low, r.band.high)}</td>'
            f'<td class="num">{money(r.threshold)}</td>'
            f'<td class="drv">{pos}</td>'
            f'<td class="drv">{drivers} · {funded}</td></tr>')
    # The orphan finding (SPEC v3.3 §2: the retired "falling through the cracks"
    # card, folded in): a risk over appetite with no funded remediation behind it —
    # the exposure the exception lens alone would miss. It is already visible in the
    # Driven-by column ("no funded plan", red); the callout names it as a finding so
    # a whole card is not spent on a filtered slice of this list.
    orphans = [r for r in eng.all_named_risk_residuals()
               if r.state == "over" and not _addressed_by_funded(graph, r.scenario_ids)]
    orphans.sort(key=lambda r: r.band.mean, reverse=True)
    orphan_callout = ""
    if orphans:
        names = _join_names(o.named_risk.label for o in orphans)
        verb = "is" if len(orphans) == 1 else "are"
        orphan_callout = (f'<p class="callout"><b>{_esc(names)} {verb} over appetite with no funded '
                          f'remediation</b> behind {"it" if len(orphans) == 1 else "them"} — the exposure the '
                          f'exception lens alone would miss. Flagged <span style="color:var(--status-over)">no '
                          f'funded plan</span> in the list below; the Top-5 banner says what to do about '
                          f'{"it" if len(orphans) == 1 else "each"}.</p>')
    return _card(
        "1", "Your biggest exposures now",
        "Named risks by position against their own appetite: the 5–95% interval tinted by state, the mean as an interior tick with its dollar figure, and the slice past the appetite line (red) as the breach mass.",
        orphan_callout
        + exposure_interval_svg(rows, lo_b, hi_b)
        + f'<table class="tbl"><thead><tr><th></th><th>Named risk</th><th class="num">Residual (90% CI)</th>'
        f'<th class="num">Appetite</th><th>Position</th><th>Driven by</th></tr></thead><tbody>{"".join(items)}</tbody></table>')


_DOM_STATUS = {  # (label, RAG-token colour, row-highlight class)
    "over-controlled": ("OVER-CONTROLLED", "var(--status-below)", " class=\"row-amber\""),
    "mis-allocated": ("MIS-ALLOCATED", "var(--status-over)", ""),
    "balanced": ("Balanced", "var(--status-at)", ""),
}
_DOM_ORDER = {"over-controlled": 0, "mis-allocated": 1, "balanced": 2}


def _view_domains(graph: Graph, eng: GraphEngine) -> str:
    """View 2 (SPEC v2.8 §3, refined): the over-investment / mis-allocation view,
    and the only place Tier 1 (domains) appears. There is **no domain-level metric
    column** — neither idle dollars (risk is not a spendable pot) nor a
    residual/appetite ratio (a Simpson's blend of a breach and idle headroom on a
    mis-allocated domain, matching no single risk). The STATUS carries the finding
    and the detail names the specific risks, with their own % of appetite where
    that is a clean per-risk read. Over-controlled leads; mis-allocated (a breach
    beside idle headroom, the same owner) is the sharper second act."""
    residuals = {r.named_risk.id: r for r in eng.all_named_risk_residuals()}
    data = []
    for d in eng.all_domain_rollups():
        _idle, overs, biggest, status = _domain_idle(d, residuals)
        rs = [residuals[n] for n in d.named_risk_ids if n in residuals]
        tol = sum(r.threshold for r in rs)
        util = (sum(r.band.mean for r in rs) / tol) if tol else 0.0
        data.append((_DOM_ORDER[status], util, d, overs, biggest, status))
    data.sort(key=lambda t: (t[0], t[1]))  # status group, then most over-invested first
    rows = []
    for _, _, d, overs, biggest, status in data:
        label, colour, rowcls = _DOM_STATUS[status]
        if status == "mis-allocated":
            ov = ", ".join(o.named_risk.label for o in overs)
            if biggest and biggest.threshold:
                bu = round(biggest.band.mean / biggest.threshold * 100)
                detail = (f"<b>{_esc(ov)}</b> is breached, while <b>{_esc(biggest.named_risk.label)}</b> "
                          f"— a separate risk here — runs at just <b>{bu}%</b> of its appetite")
            else:
                detail = f"<b>{_esc(ov)}</b> is breached, while another risk here sits well under appetite"
        elif status == "over-controlled":
            rs = [residuals[n] for n in d.named_risk_ids if n in residuals]
            tol = sum(r.threshold for r in rs)
            used = round((sum(r.band.mean for r in rs) / tol) * 100) if tol else 0
            detail = (f"nothing at or above appetite anywhere — using <b>{used}%</b> of its declared "
                      f"tolerance across {d.rag_counts['below']} risks")
        else:
            detail = "a risk operating at appetite, no breach"
        pill = (f'<span class="rag"><span class="dot" style="background:{colour}"></span>'
                f'<span class="rag-l" style="color:{colour}">{label}</span></span>')
        rows.append(
            f'<tr{rowcls}><td class="nm">{_esc(d.domain.title)}</td>'
            f'<td>{pill}</td>'
            f'<td class="drv">{detail}</td>'
            f'<td>{_rag_counts_html(d.rag_counts)}</td></tr>')
    total_thr = sum(nr.appetite_threshold or 0 for nr in graph.named_risks.values())
    app = eng.portfolio().appetite
    flag = (f'<p class="chain">Bottom-up appetite totals <b>{money(total_thr)}</b> against a {money(app)} declared '
            f'enterprise appetite (<b>{total_thr / app:.2f}×</b>). Either the risk-level thresholds are generous, '
            f'or the enterprise line is not what the business actually tolerates.</p>')
    inner = (f'<p class="lede">Where control effort is out of proportion to the risk. <b>Over-controlled</b> is a '
             f'domain with nothing at or above appetite; <b>mis-allocated</b> is a breach and idle headroom in the '
             f'same domain, under the same owner. The status names the finding and the detail names the specific '
             f'risks — a breach and an idle risk are never blended into one domain number. RAG mix is over / at / '
             f'below, each with its count.</p>'
             f'<table class="tbl"><thead><tr><th>Domain (Tier 1)</th>'
             f'<th>Status</th><th>What it means</th><th>Risk mix (R/G/A)</th></tr></thead>'
             f'<tbody>{"".join(rows)}</tbody></table>{flag}')
    return _card("2", "Where you're over-investing — and mis-allocating",
                 "Over-controlled where nothing is near the line, mis-allocated where a breach sits beside idle headroom — the status names the finding, the detail names the risks.",
                 inner)


_STATE_RANK = {"over": 0, "at": 1, "below": 2}
_HEALTH_RANK = {"red": 0, "amber": 1, "green": 2}
_HEALTH_COLOUR = {"red": "var(--status-over)", "amber": "var(--status-below)"}
_EV_RANK = {"none": 0, "missing": 0, "stale": 1, "fresh": 2}  # worst evidence first


def _view3(graph: Graph, eng: GraphEngine) -> str:
    """View 4, reframed (SPEC v3.1 §3): a control inventory scoped to the breaches,
    not a re-ranking of risks already ranked in view 1. For each over-appetite
    risk: how many controls are mapped to it (credible counts post-prune, §1), and
    only the weak ones named — red/amber on health, or unproven on evidence, since
    a healthy control needs no line. A risk whose mapped controls are all healthy
    is a scope problem, not a safeguard failure — the compliance framework is wired
    in, its exposure is elsewhere. Unmapped controls never appear; they are a
    compliance-completeness concern, not this reader's problem."""
    residuals = {r.named_risk.id: r for r in eng.all_named_risk_residuals()}
    over = sorted((r for r in residuals.values() if r.state == "over"),
                  key=lambda r: r.band.mean, reverse=True)
    blocks = []
    for r in over:
        cids = graph.controls_of_named_risk.get(r.named_risk.id, [])
        healths = [h for h in (eng.control_health(c) for c in cids) if h]
        weak = sorted((h for h in healths if h.health in ("red", "amber")),
                      key=lambda h: (_HEALTH_RANK[h.health], _EV_RANK.get(h.evidence_status, 9)))
        # Over-appetite risks carry their accountable owner (SPEC v3.2 §4) — the
        # who-to-summon handle, on the inventory and the top-5 but not view 1's scan.
        own = f' <span class="rec-own">owner: {_esc(_owner(r.named_risk.owner))}</span>' if r.named_risk.owner else ""
        if weak:
            head = (f'<h4>{_esc(r.named_risk.label)}{own} — {len(cids)} controls mapped, '
                    f'<b style="color:var(--status-over)">{len(weak)} can\'t currently do the job</b></h4>')
            rows = "".join(
                f'<tr><td class="nm">{_esc(h.control.id)} {_esc(h.control.title)}</td>'
                f'<td><span class="dot" style="background:{_HEALTH_COLOUR[h.health]}"></span> '
                f'<b style="color:{_HEALTH_COLOUR[h.health]}">{h.health.upper()}</b></td>'
                f'<td class="drv">evidence {h.evidence_status}</td></tr>'
                for h in weak)
            block = head + f'<table class="tbl"><tbody>{rows}</tbody></table>'
        else:
            head = (f'<h4>{_esc(r.named_risk.label)}{own} — {len(cids)} controls mapped, '
                    f'<b style="color:var(--status-at)">all healthy</b></h4>')
            names = ", ".join(_esc(graph.controls[c].title) for c in cids)
            block = (head + f'<p class="drv">Over appetite, but every mapped control is healthy — so this is '
                     f'<b>scope creep to contain, not a safeguard to fix</b>. The controls wired to it '
                     f'({names}) show the ISO compliance framework is in place; the exposure is scope, not a gap.</p>')
        blocks.append(block)
    inner = (f'<p class="lede">For each risk over appetite, the controls meant to hold it: how many are mapped, and '
             f'only the ones that <b>can\'t currently do the job</b> — red or amber on health, or unproven on '
             f'evidence. A healthy control needs no line, and a risk whose controls are all healthy is a scope '
             f'problem, not a safeguard failure. Never colour alone — each marker carries its word.</p>'
             + "".join(blocks))
    return _card("3", "Are the controls holding each appetite breach?",
                 "For each risk over appetite, the controls meant to hold it — how many, and which ones can't currently do the job.",
                 inner)


def _exc_tag(eid: str, state: str | None) -> str:
    """A forced exception, tagged with the RAG state of the risk it sits on. Over
    appetite is the escalation, so it reads red (``--status-over``); at/below stay
    muted, because amber is unused-tolerance everywhere else and must never stand
    in for caused-harm (SPEC v2.9 predation view, acceptance 5)."""
    if state == "over":
        return f'<span class="nb" style="color:var(--status-over)">{_esc(eid)} · OVER</span>'
    label = {"at": "at appetite", "below": "below"}.get(state, "—")
    return f'<span class="nb" style="color:var(--text-muted)">{_esc(eid)} · {label}</span>'


def _view4(graph: Graph, eng: GraphEngine) -> str:
    holes = _predation(graph, eng)
    if not holes:
        return _card("4", "Which project is eating the others",
                     "No project is funded by starving others in this corpus.",
                     '<p class="empty">No <code>diverted_to</code> predation to show.</p>')

    # Panel A — black holes (the cause), ranked by blast radius.
    a_rows = "".join(
        f'<tr><td class="nm">{_esc(h["sink"])}</td>'
        f'<td class="drv"><span class="nb">starving {h["n_victims"]} projects · {h["n_exc"]} exceptions</span></td>'
        f'<td class="drv">'
        + (f'<span class="nb" style="color:var(--status-over)">{h["n_over"]} over appetite</span>'
           if h["n_over"] else '<span class="nb">0 over appetite</span>')
        + '</td></tr>'
        for h in holes)
    panel_a = (f'<h4>Black holes — a project funded by starving others</h4>'
               f'<table class="tbl"><thead><tr><th>Project</th><th>Blast radius</th>'
               f'<th>Escalation</th></tr></thead><tbody>{a_rows}</tbody></table>')

    # Panel B — eaten alive (the casualties): the forced exceptions on the victims'
    # own books, where they actually sit. No summed bar; over-appetite casualties red.
    # The victim's owner is the accountable lead the exception lands on (SPEC v3.2 §3)
    # — read off the forced exceptions themselves, since an OKR carries no owner.
    issue_by_id = {i.id: i for i in graph.issues}

    def victim_owner(v) -> str:
        owns = sorted({_owner(issue_by_id[eid].owner) for eid, _ in v["forced"]
                       if eid in issue_by_id and issue_by_id[eid].owner})
        return ", ".join(owns)

    b_rows = "".join(
        f'<tr><td class="nm">'
        + (f'<span style="color:var(--status-over)">{_esc(v["okr"])}</span>' if v["has_over"] else _esc(v["okr"]))
        + f'</td><td>{_esc(victim_owner(v)) or "&mdash;"}</td>'
        f'<td class="drv"><span class="nb">{_esc(h["sink"])}</span></td>'
        f'<td class="drv">' + ", ".join(_exc_tag(eid, s) for eid, s in v["forced"]) + '</td></tr>'
        for h in holes for v in h["victims"])
    panel_b = (f'<h4>Eaten alive — where the forced exceptions actually sit</h4>'
               f'<table class="tbl"><thead><tr><th>Project</th><th>Owner</th><th>Starved by</th>'
               f'<th>Exceptions forced on it</th></tr></thead><tbody>{b_rows}</tbody></table>')

    # The concentration-vs-distribution contrast (SPEC v3.2 §3): the can-kicking view
    # concentrates on one overloaded function (a resourcing problem); this one
    # distributes one project's cost across separate owners who had no say (a
    # governance problem). Compute the distinct victim owners so the count is real.
    top_hole = holes[0]
    distinct = sorted({o for v in top_hole["victims"] for o in (victim_owner(v).split(", ") if victim_owner(v) else [])})
    n_owners = len(distinct)
    contrast = ""
    if n_owners >= 2:
        contrast = (f'<p class="callout"><b>{_esc(top_hole["sink"])}’s deadline is generating risk on '
                    f'{n_owners} other leads’ books.</b> This is the mirror image of the deferral view: '
                    f'can-kicking <b>concentrates</b> on one overloaded function (resource it), predation '
                    f'<b>distributes</b> one project’s cost onto separate owners who had no say (govern it). '
                    f'Two findings, not one fact twice.</p>')

    inner = (f'<p class="lede">One project is buying its deadline with other teams\' risk. '
             f'The exceptions land on the teams that were deprioritized — some of them over '
             f'appetite. Each team\'s own risk stays in view 1, on its own owner; this view draws '
             f'only the predation.</p>{contrast}{panel_a}{panel_b}')
    return _card("4", "Which project is eating the others",
                 "The diverted_to graph as predation, not a summed footprint: one project's "
                 "resource-grab, and the forced exceptions it pushed onto the teams it starved.",
                 inner)


def _slip_exposure(eng: GraphEngine, graph: Graph, rem) -> tuple[float, str | None]:
    """The residual a slipped remediation would retire if it shipped (SPEC v3.1
    §4b), via the v3.0 ``residual_if_funded`` what-if — computed, not invented.
    Returns (reduction, nid) for the risk it helps most, or (0, None) if it clears
    nothing on a managed risk (forward-looking work that doesn't move the aggregate)."""
    cleared = eng._cleared_issue_ids(rem)
    nids = set()
    for i in graph.issues:
        if i.id in cleared:
            for sid in graph.resolved_scenarios(i):
                sc = graph.scenarios.get(sid)
                if sc and sc.named_risk:
                    nids.add(sc.named_risk)
    if rem.type == "strengthen" and rem.mapped_risk:
        nids.add(rem.mapped_risk)
    best = (0.0, None)
    for nid in nids:
        live = eng.named_risk_residual(nid)
        after = eng.residual_if_funded(nid, [rem.id])
        if live and after:
            red = live.band.mean - after.band.mean
            if red > best[0]:
                best = (red, nid)
    return best


def _view5(graph: Graph, eng: GraphEngine) -> str:
    """One deferral list, ranked (SPEC v3.2 §1). The scatter is gone: age and
    exposure are uncorrelated here (the expensive slips are new, the old renewals
    are cheap), so a 2-D plot showed two independent facts a sorted table shows
    better, over 27 near-identical unlabelled shapes. Rank by annualized exposure,
    show the top 5, name the owner. Two kinds of deferral share the column — a
    **renewal** carries exposure *held*, a **slip** carries exposure that *would be
    retired* — so the Type tag and the caption keep the two quantities distinct even
    though they sit on one ranked axis."""
    as_of = eng.config.as_of
    lbl = {nid: nr.label for nid, nr in graph.named_risks.items()}
    rows = []  # (typ, id, age, exposure, owner, handle, sub, detail)
    for e in flagged_renewals(graph, eng.config):
        band = eng.contribution_band(e.id)
        exp = band.mean if band else 0.0
        age = (as_of - e.filed_on).days if e.filed_on else 0
        sub = f"renewed &times;{e.renewal_count} unrevisited"
        rows.append(("Renewal", e.id, age, exp, _owner(e.owner),
                     e.title or e.id, sub, "exposure held — carried, not revisited"))
    n_slip_total = 0
    for r in slipped_remediations(graph, eng.config):
        n_slip_total += 1
        red, nid = _slip_exposure(eng, graph, r)
        if red <= 1000:  # no residual to retire: forward-looking work, not "at stake"
            continue
        age = (as_of - r.target_date).days if r.target_date else 0
        sub = f"stalled fix on {_esc(lbl.get(nid, nid))}"
        rows.append(("Slip", r.id, age, red, _owner(r.owner),
                     r.title or r.id, sub, "exposure that would retire if the fix shipped"))
    n_slip_priced = sum(1 for t in rows if t[0] == "Slip")

    rows.sort(key=lambda t: t[3], reverse=True)  # annualized exposure, desc
    top = rows[:5]

    trows = "".join(
        f'<tr><td>{"● " if typ == "Renewal" else "▫ "}{typ}</td>'
        f'<td class="nm">{_esc(handle)}<span class="sub">{sub} · {_esc(rid)}</span></td>'
        f'<td class="num">{age}d</td>'
        f'<td class="num">{money(exp)}</td>'
        f'<td>{_esc(owner) if owner else "&mdash;"}</td>'
        f'<td class="drv">{detail}</td></tr>'
        for typ, rid, age, exp, owner, handle, sub, detail in top)

    # Tail: the deferrals below the top 5, bounded — a silent cut would read as
    # "these are all of them" (dataviz anti-pattern), so name the count and the cap.
    tail = ""
    if len(rows) > 5:
        cap = math.ceil(rows[5][3] / 1000) * 1000
        n_more = len(rows) - 5
        tail = (f'<p class="drv" style="margin-top:8px">{n_more} more '
                f'{"deferral" if n_more == 1 else "deferrals"}, all under {money(cap)}.</p>')

    # §1c concentration callout — computed on the actual top 5, rendered only if one
    # owner holds 3+ (the honesty gate: a named pattern must be in the data). On this
    # corpus platform-lead holds 4 of 5, so it fires; framed structurally, not as blame.
    callout = ""
    owners = [t[4] for t in top if t[4]]
    if owners:
        dom = max(set(owners), key=owners.count)
        n = owners.count(dom)
        if n >= 3:
            lever = (f"Platform carries the shared tech debt the rest of the org builds on, "
                     f"so the load-bearing function is where deferral piles up — resourcing "
                     f"platform is the lever, not chasing the individual items."
                     if dom == "platform-lead" else
                     f"The deferred risk concentrates on one function — resourcing {_esc(dom)} "
                     f"is the lever, not chasing the individual items.")
            callout = (f'<p class="callout"><b>{n} of these {len(top)} sit with '
                       f'{_esc(dom)}</b> — not because one person is behind, but because the '
                       f'deferred risk concentrates where the load-bearing function is. {lever}</p>')

    inner = (f'<p class="lede">The deferrals that carry the most exposure, ranked. '
             f'<b>Renewals show exposure you\'re holding; slips show exposure you\'d retire.</b> '
             f'They rank on one column but are not the same quantity, so the Type tag (● renewal, '
             f'▫ slip) keeps them distinct. Slip exposure is the <code>residual_if_funded</code> '
             f'what-if; {n_slip_priced} of {n_slip_total} slipped remediations carry residual to '
             f'retire, the rest defer work that does not move the current aggregate.</p>'
             + callout
             + f'<table class="tbl"><thead><tr><th>Type</th><th>Item</th><th class="num">Age</th>'
             f'<th class="num">Annualized exposure</th><th>Owner</th><th>What it is</th></tr></thead>'
             f'<tbody>{trows}</tbody></table>'
             + tail)
    return _card("5", "The can you keep kicking",
                 "The deferrals carrying the most exposure, ranked — renewed exceptions (exposure held) "
                 "and slipped remediations (exposure retirable), with the accountable owner.",
                 inner)


def _ai_lens(graph: Graph, eng: GraphEngine) -> str:
    """The AI coverage lens (SPEC v3.4). Not a prioritization view — it answers a
    *coverage* question ("is our AI usage accounted for?"), so it sits outside the
    numbered set and carries no rank. It filters the corpus by the ``ai`` causation
    vector (AI stays a cross-cutting cause, never a domain or a named risk) and
    splits it on the ``internal_ops`` locus marker: AI *in the product* vs AI in
    *how we build*. The split is deliberately lopsided and shown, not balanced
    (§4): the honest picture is one big concentration in the product and a small,
    real internal tail — and both are **emerging**, held out of the live appetite
    math, which the view says plainly."""
    ai = [(sid, sc) for sid, sc in graph.scenarios.items() if "ai" in (sc.vectors or [])]
    if not ai:
        return ""

    def rows(internal: bool) -> list[tuple]:
        out = []
        for sid, sc in ai:
            if ("internal_ops" in sc.vectors) != internal:
                continue
            r = eng.scenario_residual(sid)
            if not r:
                continue
            nr = graph.named_risks[sc.named_risk]
            dom = graph.domains[nr.domain].title
            out.append((sc.label, nr.label, dom, r.band))
        out.sort(key=lambda t: t[3].mean, reverse=True)
        return out

    product, internal = rows(False), rows(True)
    p_sum = sum(t[3].mean for t in product)
    i_sum = sum(t[3].mean for t in internal) or 1.0
    ratio = p_sum / i_sum

    def block(title: str, note: str, data: list[tuple], agg: float) -> str:
        body = "".join(
            f'<tr><td class="nm">{_esc(lbl)}</td><td class="drv">{_esc(nr)}</td>'
            f'<td class="drv">{_esc(dom)}</td>'
            f'<td class="num">{band_str(b.low, b.high)}</td></tr>'
            for lbl, nr, dom, b in data)
        return (f'<h4>{title} <span class="ail-agg">{len(data)} AI-vectored · ~{money(agg)}</span></h4>'
                f'<p class="ail-note">{note}</p>'
                f'<table class="tbl"><thead><tr><th>Scenario</th><th>Host named risk</th>'
                f'<th>Domain</th><th class="num">Exposure (90% CI)</th></tr></thead><tbody>{body}</tbody></table>')

    # The asymmetry, led with as a proportion (§4): a two-slice pie, product
    # dominating and the internal sliver visibly present — shown, not balanced.
    total = p_sum + i_sum
    fp = p_sum / total
    prod_fill, intl_fill = "var(--accent)", "color-mix(in srgb, var(--accent), var(--bg) 58%)"

    def wedge(a: float, b: float, fill: str) -> str:
        def pt(f):
            ang = 2 * math.pi * f - math.pi / 2  # 0 at 12 o'clock, clockwise
            return 70 + 64 * math.cos(ang), 70 + 64 * math.sin(ang)
        x0, y0 = pt(a)
        x1, y1 = pt(b)
        large = 1 if (b - a) > 0.5 else 0
        return (f'<path d="M70,70 L{x0:.2f},{y0:.2f} A64,64 0 {large} 1 {x1:.2f},{y1:.2f} Z" '
                f'fill="{fill}" stroke="var(--surface)" stroke-width="2"/>')

    p_pct = round(100 * fp)
    pie = (
        '<div class="ail-pie-wrap">'
        f'<svg class="ail-pie" viewBox="0 0 140 140" role="img" '
        f'aria-label="Product AI {money(p_sum)} ({p_pct}%) versus internal AI {money(i_sum)} ({100 - p_pct}%)">'
        f'{wedge(0.0, fp, prod_fill)}{wedge(fp, 1.0, intl_fill)}</svg>'
        '<div class="ail-legend">'
        f'<div><span class="sw" style="background:{prod_fill}"></span>'
        f'<b>In the product</b><span class="ail-lv">{money(p_sum)} · {p_pct}%</span></div>'
        f'<div><span class="sw" style="background:{intl_fill}"></span>'
        f'<b>In how we build</b><span class="ail-lv">{money(i_sum)} · {100 - p_pct}%</span></div>'
        '</div></div>'
        f'<p class="ail-cap"><b>Product AI is ~{ratio:.0f}× internal AI</b> '
        f'({money(p_sum)} vs {money(i_sum)}).</p>')

    inner = (
        '<p class="lede">AI is not a category of risk; it is a cause that runs through the ones you already '
        'have. Here is everywhere it drives exposure — in the product and in how we build. '
        '<b>All of it is emerging</b>: wide, forward-looking, and deliberately held out of the live appetite '
        'math, so none of it moves the portfolio numbers yet. This view answers coverage, not priority.</p>'
        + pie
        + block("In the product", "The model making customer decisions, the autonomous agent, the "
                "abuse-detection model — where AI already shapes what ships.", product, p_sum)
        + block("In how we build (internal operations)", "AI as an operational practice, not a product "
                "feature: generated code, data pasted into external LLMs, copilot velocity. The blind spot "
                "the product lens alone misses.", internal, i_sum))
    return ('<section class="card ai-lens"><div class="vhdr"><span class="seam alt">AI COVERAGE</span>'
            '<div><h3>Is our AI usage accounted for?</h3>'
            '<p class="vsub">AI as a cross-cutting cause, surfaced — not a domain, not a named risk. '
            'The shape is lopsided, and that is the honest answer.</p></div></div>'
            f'{inner}</section>')


def _ai_example(graph: Graph) -> str:
    scn = next((s for s in graph.scenarios.values() if s.incident), None)
    if scn is None:
        return ""
    inc = scn.incident
    return (
        '<section class="card ai"><div class="vhdr"><span class="seam">SHOW-LATER SEAM</span>'
        '<h3>Incident → scenario, mapped by the offline AI step</h3></div>'
        '<p class="lede">A single worked example, not a live feature: a synthetic incident ticket run once '
        'offline through the mapping step (SPEC §8), stored as data. A real incident queue repoints here later.</p>'
        '<div class="ai-flow">'
        f'<div class="ai-col"><div class="ai-k">Input ticket · {_esc(inc.get("ticket_id",""))}</div>'
        f'<div class="ai-v">{_esc(inc.get("description",""))}</div></div>'
        '<div class="ai-arrow">→</div>'
        f'<div class="ai-col"><div class="ai-k">Suggested mapping</div>'
        f'<div class="ai-v">domain <b>{_esc(inc.get("suggested_domain",""))}</b> · risk '
        f'<b>{_esc(inc.get("suggested_named_risk",""))}</b><br>factor '
        f'<b>{_esc(inc.get("suggested_factor",""))}</b> · band <b>{_esc(inc.get("suggested_band",""))}</b></div></div>'
        '<div class="ai-arrow">→</div>'
        f'<div class="ai-col"><div class="ai-k">Resulting entry</div>'
        f'<div class="ai-v"><b>{_esc(scn.id)}</b> — {_esc(scn.title)}<br>'
        f'<span class="mut">mapped_by {_esc(inc.get("mapped_by",""))} on {_esc(inc.get("mapped_on",""))}</span></div></div>'
        '</div></section>')


def _card(num: str, title: str, sub: str, inner: str) -> str:
    return (f'<section class="card"><div class="vhdr"><span class="vnum">{num}</span>'
            f'<div><h3>{_esc(title)}</h3><p class="vsub">{_esc(sub)}</p></div></div>{inner}</section>')


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

# The one place raw hex is allowed to live (SPEC v2.4 §1). This :root block is
# the vibe-shelf design system, verbatim (SPEC §7 / the shared design-system
# rules): five colours, every other shade derived with color-mix(), --danger the
# one reserved warning red. The RAG status triad is the one sanctioned extension
# — held OUTSIDE the five per SPEC §7, used only on risk indicators (dots, bars,
# labels), never on chrome; --status-over IS --danger. Everything else in this
# module — CSS and baked SVG alike — references these tokens through var().
_ROOT = """
:root {
  --bg:#0f120d; --surface:#1d231c; --accent:#7d9b83; --text:#e6e4db; --text-strong:#ffffff;
  --bg-raised:var(--surface);
  --surface-hover:color-mix(in srgb, var(--surface) 84%, var(--accent));
  --text-muted:color-mix(in srgb, var(--text), transparent 40%);
  --text-faint:color-mix(in srgb, var(--text), transparent 58%);
  --border:color-mix(in srgb, var(--accent), transparent 80%);
  --border-strong:color-mix(in srgb, var(--accent), transparent 62%);
  --accent-dim:color-mix(in srgb, var(--accent), transparent 84%);
  --accent-ink:var(--bg);
  --danger:#cf8f83;
  --radius:12px; --radius-sm:8px; --maxw:1000px;
  --font-display:"Space Grotesk", system-ui, sans-serif;
  --font-body:"Inter", system-ui, sans-serif;
  --status-over:var(--danger); --status-at:#5fc07e; --status-below:#cda23e; --status-below-tint:#ddb95f;
  color-scheme: dark;
}
"""

_CSS = _ROOT + """
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--text); border-top:3px solid var(--accent);
  font-family:var(--font-body); font-size:15px; line-height:1.5; -webkit-font-smoothing:antialiased; }
h1,h2,h3,h4,.hero-num,.tile-v { font-family:var(--font-display); font-weight:600; letter-spacing:-0.01em; }
a { color:var(--accent); text-decoration:none; }
a:hover { text-decoration:underline; }
:focus-visible { outline:2px solid var(--accent); outline-offset:2px; }
.wrap { max-width:var(--maxw); margin:0 auto; padding:40px 24px 80px; }
header .eyebrow { color:var(--accent); font-size:10.5px; font-weight:600; letter-spacing:0.07em; text-transform:uppercase; }
header h1 { font-size:30px; margin:6px 0 4px; color:var(--text-strong); }
header .meta { color:var(--text-muted); font-size:13.5px; }
.top5 { margin:26px 0 0; background:var(--surface); border:1px solid var(--border);
  border-radius:var(--radius); padding:22px 26px; }
.top5 > h2 { font-size:16px; font-weight:600; color:var(--text-strong); margin:0 0 14px;
  text-transform:uppercase; letter-spacing:0.04em; }
.top5 .t5sub { display:block; font-size:12px; font-weight:400; text-transform:none;
  letter-spacing:0; color:var(--text-muted); margin-top:4px; }
.top5 ol { list-style:none; margin:0; padding:0; }
.top5 li { display:flex; gap:14px; align-items:baseline; padding:11px 0; border-top:1px solid var(--border); }
.top5 li:first-child { border-top:none; }
.top5 .t5n { flex:0 0 auto; width:22px; height:22px; border-radius:50%; border:1.5px solid var(--accent);
  color:var(--accent); font-size:12px; font-weight:600; display:inline-flex; align-items:center;
  justify-content:center; }
.top5 .t5t { color:var(--text); font-size:13.5px; line-height:1.5; }
.rec-own { display:inline-block; margin-left:4px; color:var(--text-muted); font-size:11.5px;
  white-space:nowrap; border:1px solid var(--border); border-radius:var(--radius-sm); padding:1px 7px; }
.summary { margin:32px 0; }
.summary > h2 { font-size:17px; font-weight:500; color:var(--text); margin:0 0 16px; }
.hero { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius); padding:26px 28px; }
.hero-num { font-size:40px; line-height:1.1; }
.hero-cap { color:var(--text); font-size:15px; margin-top:8px; display:flex; align-items:center; gap:6px; flex-wrap:wrap; }
.hero-sub { color:var(--text-muted); font-size:13.5px; margin-top:12px; max-width:720px; }
.tiles { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-top:14px; }
.tile { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius); padding:14px 16px; }
.tile.warn { border-left:3px solid var(--status-below); }
.tile.warn .tile-k { color:var(--status-below-tint); }
.tile-k { color:var(--text-muted); font-size:11px; text-transform:uppercase; letter-spacing:0.06em; }
.tile-v { color:var(--text-strong); font-size:17px; margin:6px 0 4px; }
.tile-s { color:var(--text-muted); font-size:12px; }
.ragcs { display:inline-flex; gap:10px; }
.ragc { display:inline-flex; align-items:center; gap:4px; font-size:12px; color:var(--text); font-family:var(--font-display); }
.tbl tr.row-amber td { background:color-mix(in srgb, var(--status-below), transparent 90%); }
.tbl tr.row-amber td:first-child { box-shadow:inset 3px 0 0 var(--status-below); }
.grid { display:grid; gap:20px; }
.card { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius); padding:24px 26px; }
.vhdr { display:flex; gap:14px; align-items:flex-start; margin-bottom:14px; }
.vnum { flex:0 0 auto; width:28px; height:28px; border-radius:var(--radius-sm); background:var(--bg); border:1px solid var(--accent);
  color:var(--accent); font-family:var(--font-display); font-weight:600; display:grid; place-items:center; font-size:14px; }
.vhdr h3 { font-size:18px; margin:2px 0 2px; color:var(--text-strong); }
.vsub, .vhdr .vsub { color:var(--text-muted); font-size:13px; margin:0; }
.lede { color:var(--text); font-size:13.5px; margin:0 0 14px; max-width:760px; }
.chain { color:var(--text-muted); font-size:12.5px; margin-top:12px; }
.empty { color:var(--text-muted); }
svg { display:block; margin:6px 0 16px; border-radius:var(--radius-sm); }
table.tbl { width:100%; border-collapse:collapse; font-size:13px; }
.tbl th { text-align:left; color:var(--text-muted); font-weight:500; font-size:11px; text-transform:uppercase;
  letter-spacing:0.04em; padding:6px 10px; border-bottom:1px solid var(--border); }
.tbl td { padding:9px 10px; border-bottom:1px solid var(--border); vertical-align:top; }
.tbl tr:last-child td { border-bottom:none; }
.tbl .num { text-align:right; font-family:var(--font-display); white-space:nowrap; }
.tbl .nm { color:var(--text-strong); }
.tbl .drv { color:var(--text-muted); }
.tbl .nm .sub { display:block; color:var(--text-muted); font-size:11.5px; font-weight:400; margin-top:2px; }
.callout { border-left:3px solid var(--accent); background:var(--bg); padding:10px 14px; margin:0 0 14px;
  border-radius:var(--radius-sm); color:var(--text); font-size:13px; line-height:1.5; max-width:760px; }
.nb { white-space:nowrap; }
.tbl .pol { color:var(--accent); font-size:12px; }
.tbl .tag { color:var(--status-below-tint); font-size:12px; }
h4 { font-size:13px; color:var(--text); margin:18px 0 8px; }
.rag { display:inline-flex; align-items:center; gap:6px; white-space:nowrap; }
.rag-l { font-size:11px; font-weight:600; letter-spacing:0.03em; }
.dot { width:9px; height:9px; border-radius:50%; display:inline-block; flex:0 0 auto; }
.ai .seam { font-size:10px; letter-spacing:0.1em; color:var(--accent-ink); background:var(--accent); padding:3px 8px;
  border-radius:var(--radius-sm); font-weight:700; }
.ai .vhdr { align-items:center; }
.ai-flow { display:grid; grid-template-columns:1fr auto 1fr auto 1fr; gap:12px; align-items:center; margin-top:8px; }
.ai-col { background:var(--bg); border:1px solid var(--border); border-radius:var(--radius-sm); padding:14px; }
.ai-k { color:var(--accent); font-size:11px; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:6px; }
.ai-v { font-size:12.5px; color:var(--text); }
.ai-v .mut { color:var(--text-muted); font-size:11px; }
.ai-arrow { color:var(--text-muted); font-size:20px; text-align:center; }
.ai-lens .vhdr { align-items:center; }
.ai-lens .seam { font-size:10px; letter-spacing:0.1em; color:var(--accent); background:transparent;
  border:1px solid var(--accent); padding:3px 8px; border-radius:var(--radius-sm); font-weight:700; }
.ai-lens h4 { font-size:15px; font-weight:600; color:var(--text-strong); margin:22px 0 3px; }
.ai-lens h4 .ail-agg { color:var(--text-muted); font-weight:400; font-size:12px; margin-left:8px; }
.ail-note { color:var(--text-muted); font-size:12.5px; line-height:1.5; margin:0 0 10px; max-width:760px; }
.ail-pie-wrap { display:flex; align-items:center; gap:22px; margin:6px 0 12px; }
.ail-pie { width:132px; height:132px; flex:0 0 auto; }
.ail-legend { display:flex; flex-direction:column; gap:10px; font-size:13.5px; color:var(--text); }
.ail-legend > div { display:flex; align-items:center; gap:8px; }
.ail-legend .sw { width:12px; height:12px; border-radius:50%; flex:0 0 auto; }
.ail-legend .ail-lv { color:var(--text-muted); margin-left:6px; font-family:var(--font-display); }
.ail-cap { color:var(--text); font-size:13px; line-height:1.5; margin:0 0 6px; max-width:760px; }
footer { margin-top:40px; color:var(--text-muted); font-size:12.5px; border-top:1px solid var(--border); padding-top:18px; }
@media (max-width:720px) { .tiles { grid-template-columns:repeat(2,1fr); } .ai-flow { grid-template-columns:1fr; } .ai-arrow { transform:rotate(90deg); } }
"""


# The two-view tab bar, shared verbatim by the eng dashboard and the GRC tab so
# switching between them reads as switching tabs of one product. Both are
# separate HTML pages, so the "tabs" are links; the current page's tab is marked
# active (rendered as a non-link span). This is static chrome — it moves no
# number, so the GRC-isolation guarantee (the both-loaders render test) holds.
_TABS_CSS = """
.tabs { display:flex; gap:2px; margin:0 0 24px; border-bottom:1px solid var(--border); }
.tab { padding:9px 18px 11px; font-family:var(--font-display); font-weight:600; font-size:14px;
  color:var(--text-muted); text-decoration:none; border-bottom:2px solid transparent; margin-bottom:-1px;
  white-space:nowrap; }
.tab:hover { color:var(--text); text-decoration:none; }
.tab-active { color:var(--text-strong); border-bottom-color:var(--accent); }
"""

# Source repo, linked from both page footers so the live Vercel site points back
# to git (the reverse of the README's live-site links).
_REPO_URL = "https://github.com/notlindafry/grc-program"

# Vercel Web Analytics (visitor / page-view counts). This is a static,
# Python-generated HTML site — not a React/Next app — so the @vercel/analytics
# npm package and the <Analytics/> component do not apply. The equivalent for a
# static site is Vercel's insights script, served from the same origin at
# /_vercel/insights/script.js once Web Analytics is enabled on the project
# (Vercel dashboard → Project → Analytics). The window.va shim queues events
# before the script loads, exactly as Vercel's own injection does.
_ANALYTICS = (
    '<script>window.va=window.va||function(){(window.vaq=window.vaq||[]).push(arguments);};</script>'
    '<script defer src="/_vercel/insights/script.js"></script>'
)

_TAB_ENG = "Engineering Org GRC Profile"
_TAB_GRC = "GRC QBR"


def _tab_bar(active: str) -> str:
    """The shared view switcher. ``active`` is ``"eng"`` or ``"grc"``; the active
    view renders as a plain span, the other as a link to its page."""
    eng = (f'<span class="tab tab-active" aria-current="page">{_TAB_ENG}</span>'
           if active == "eng"
           else f'<a class="tab" href="dashboard.html">{_TAB_ENG}</a>')
    grc = (f'<span class="tab tab-active" aria-current="page">{_TAB_GRC}</span>'
           if active == "grc"
           else f'<a class="tab" href="grc.html">{_TAB_GRC}</a>')
    return f'<nav class="tabs" aria-label="Views">{eng}{grc}</nav>'


def build_dashboard(graph: Graph, eng: GraphEngine) -> str:
    p = eng.portfolio()
    body = (
        '<div class="wrap">'
        + _tab_bar("eng")
        + '<header><div class="eyebrow">Company Corp</div>'
        '<h1>GRC portfolio — the ten-second read for VP of Engineering</h1>'
        '<div class="meta">Executive view for engineering leadership · <b>synthetic data</b>, '
        'generated from git-native YAML</div></header>'
        + _top5_section(graph, eng)
        + _summary(graph, eng)
        + '<div class="grid">'
        + _view1(graph, eng) + _view_domains(graph, eng)
        + _view3(graph, eng) + _view4(graph, eng) + _view5(graph, eng)
        + _ai_lens(graph, eng)
        + _ai_example(graph)
        + '</div>'
        '<footer>Every figure is a 90% confidence interval from a light FAIR-shaped Monte Carlo, measured '
        'against an authored appetite; the corpus is synthetic and version-controlled. Appetite is a two-sided '
        'target: <b>at appetite is green, below appetite is amber</b> (unused tolerance), over is red. '
        'One position, one probability. No workflow engine, no live collectors — this is a model of the '
        'operating model, deliberately not a platform. · '
        f'<a href="{_REPO_URL}">Source on GitHub</a></footer>'
        '</div>'
    )
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<meta name="robots" content="noindex, nofollow">'
        '<title>Company Corp — GRC portfolio</title>'
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&'
        'family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">'
        f'<style>{_CSS}{_TABS_CSS}</style>{_ANALYTICS}</head><body>{body}</body></html>'
    )


def render_to(data_dir: Path, config: Config, out: Path) -> Path:
    graph = load_graph(data_dir)
    validate_graph(graph, config)
    eng = GraphEngine(graph, config)
    out.write_text(build_dashboard(graph, eng))
    return out
