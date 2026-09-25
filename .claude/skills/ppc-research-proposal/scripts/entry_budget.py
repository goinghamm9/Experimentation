#!/usr/bin/env python3
"""Entry-point media budget from a research snapshot (coverage math, no funnel fantasy).

Usage:
    python3 entry_budget.py snapshot.csv [--priority 1] [--target-is 0.5] [--is-range 0.4,0.65]
        [--ctr 0.04,0.08] [--history history.json] [--xlsx out.xlsx] [--md out.md] [--json out.json]

Input: a research snapshot CSV (assets/research_snapshot_template.csv columns). Numbers must be
observed or forecast platform data, third-party tool data, or clearly labeled modeled figures; the
script reports the weakest evidence type present and labels the result PROVISIONAL unless every
priority cluster is backed by observed or forecast platform data for the target geography.

Method (transparent, reproducible):
    clicks available = monthly searches x target impression share x expected CTR
    spend to buy them = clicks x CPC
Summed over priority clusters, at low and high inputs, this is the media needed to cover the
market at the chosen impression share. The recommended entry budget is the rounded midpoint of
that range, with the range shown. Impression share and CTR are planning assumptions unless they
come from account history; say so in the output.

Downstream outcomes (contacts, leads, appointments, consults, sales) are computed ONLY when
--history supplies the client's own observed rates (JSON keys: cpc, ctr, conversion_rate,
cpl, qualification_rate, appointment_rate, close_rate, period, source). Without history the
output says those outcomes are measured during the first campaign, not forecast.
"""
import argparse
import csv
import json
import math
from pathlib import Path

EVIDENCE_RANK = {"observed": 0, "forecast": 1, "third_party": 2, "benchmark": 3, "modeled": 4}


def fnum(v):
    try:
        return float(str(v).replace("$", "").replace(",", ""))
    except (TypeError, ValueError):
        return None


def round_budget(x):
    step = 250 if x < 5000 else 500
    return max(step, int(round(x / step) * step))


def load_rows(path, priority):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if not r.get("cluster"):
                continue
            if priority and str(r.get("priority", "")).strip() not in priority:
                continue
            lo, hi = fnum(r.get("searches_low")), fnum(r.get("searches_high"))
            clo, chi = fnum(r.get("cpc_low")), fnum(r.get("cpc_high"))
            if None in (lo, hi, clo, chi):
                print(f"skip (missing numbers): {r.get('cluster')} / {r.get('keyword')}")
                continue
            r.update(searches_low=lo, searches_high=hi, cpc_low=clo, cpc_high=chi)
            rows.append(r)
    return rows


def aggregate(rows):
    clusters = {}
    for r in rows:
        c = clusters.setdefault(r["cluster"], {"searches_low": 0, "searches_high": 0, "cpc_lo": [], "cpc_hi": [],
                                               "evidence": set(), "sources": set(), "geo": set(), "keywords": 0})
        c["searches_low"] += r["searches_low"]
        c["searches_high"] += r["searches_high"]
        c["cpc_lo"].append(r["cpc_low"])
        c["cpc_hi"].append(r["cpc_high"])
        c["evidence"].add((r.get("evidence_type") or "modeled").strip().lower())
        c["sources"].add((r.get("source") or "").strip())
        c["geo"].add((r.get("geography") or "").strip())
        c["keywords"] += 1
    return clusters


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("snapshot")
    ap.add_argument("--priority", default="1", help="comma list of priority values to include, default 1")
    ap.add_argument("--target-is", type=float, default=0.5)
    ap.add_argument("--is-range", default="0.4,0.65")
    ap.add_argument("--ctr", default="0.04,0.08", help="low,high expected search CTR unless history supplies one")
    ap.add_argument("--history")
    ap.add_argument("--xlsx")
    ap.add_argument("--md")
    ap.add_argument("--json")
    a = ap.parse_args()
    priority = [p.strip() for p in a.priority.split(",") if p.strip()]
    rows = load_rows(a.snapshot, priority)
    if not rows:
        raise SystemExit("no usable rows: fill searches and CPC from platform data, or mark rows modeled")
    is_lo, is_hi = (float(x) for x in a.is_range.split(","))
    ctr_lo, ctr_hi = (float(x) for x in a.ctr.split(","))
    history = json.load(open(a.history)) if a.history else {}
    ctr_note = "planning assumption"
    if history.get("ctr"):
        ctr_lo = ctr_hi = float(history["ctr"])
        ctr_note = f"account history ({history.get('period', 'period not stated')})"

    clusters = aggregate(rows)
    out = {"clusters": {}, "assumptions": {"target_impression_share": a.target_is, "impression_share_range": [is_lo, is_hi],
                                           "ctr_range": [ctr_lo, ctr_hi], "ctr_basis": ctr_note}}
    tot_lo = tot_hi = tot_mid = 0.0
    weakest = "observed"
    for name, c in clusters.items():
        cpc_lo, cpc_hi = min(c["cpc_lo"]), max(c["cpc_hi"])
        cpc_mid = (sum(c["cpc_lo"]) / len(c["cpc_lo"]) + sum(c["cpc_hi"]) / len(c["cpc_hi"])) / 2
        clicks_lo = c["searches_low"] * is_lo * ctr_lo
        clicks_hi = c["searches_high"] * is_hi * ctr_hi
        clicks_mid = (c["searches_low"] + c["searches_high"]) / 2 * a.target_is * (ctr_lo + ctr_hi) / 2
        spend_lo, spend_hi, spend_mid = clicks_lo * cpc_lo, clicks_hi * cpc_hi, clicks_mid * cpc_mid
        ev = max(c["evidence"], key=lambda e: EVIDENCE_RANK.get(e, 4))
        if EVIDENCE_RANK.get(ev, 4) > EVIDENCE_RANK[weakest]:
            weakest = ev
        out["clusters"][name] = {"keywords": c["keywords"], "geography": sorted(c["geo"]), "searches": [c["searches_low"], c["searches_high"]],
                                 "cpc": [cpc_lo, cpc_hi], "clicks_at_target_is": [round(clicks_lo), round(clicks_hi)],
                                 "monthly_spend_to_cover": [round(spend_lo), round(spend_hi)], "evidence": sorted(c["evidence"]),
                                 "sources": sorted(s for s in c["sources"] if s)}
        tot_lo, tot_hi, tot_mid = tot_lo + spend_lo, tot_hi + spend_hi, tot_mid + spend_mid
    provisional = EVIDENCE_RANK[weakest] > 1
    rec = round_budget(tot_mid)
    out["entry_budget"] = {"recommended_monthly_media": rec, "range": [round_budget(tot_lo), round_budget(tot_hi)],
                           "status": "PROVISIONAL (weakest evidence: %s); replace with Keyword Planner data for the target geography before presenting as researched" % weakest if provisional else "evidence-backed (platform data for the target geography)",
                           "covers": "priority clusters %s at about %d%% impression share" % (", ".join(clusters), a.target_is * 100)}

    # optional funnel from client history only
    if history.get("conversion_rate") or history.get("cpl"):
        clicks_mid_total = sum((v["clicks_at_target_is"][0] + v["clicks_at_target_is"][1]) / 2 for v in out["clusters"].values())
        cvr = history.get("conversion_rate")
        contacts = clicks_mid_total * cvr if cvr else (rec / history["cpl"] if history.get("cpl") else None)
        funnel = {"basis": f"client history: {history.get('source', 'unstated')} {history.get('period', '')}".strip(),
                  "contacts_per_month_about": round(contacts) if contacts else None}
        if contacts and history.get("qualification_rate"):
            funnel["qualified_per_month_about"] = round(contacts * history["qualification_rate"])
            if history.get("appointment_rate"):
                funnel["appointments_per_month_about"] = round(contacts * history["qualification_rate"] * history["appointment_rate"])
        out["funnel"] = funnel
    else:
        out["funnel"] = {"basis": "no client history supplied", "note": "contacts, qualified leads, appointments, and sales are measured during the first campaign, not forecast"}

    md = [f"# Entry budget (coverage math)", "",
          f"Recommended monthly media: ${rec:,} (range ${out['entry_budget']['range'][0]:,} to ${out['entry_budget']['range'][1]:,}). Status: {out['entry_budget']['status']}.",
          f"Covers: {out['entry_budget']['covers']}. Impression share {is_lo:.0%} to {is_hi:.0%} (target {a.target_is:.0%}) and CTR {ctr_lo:.1%} to {ctr_hi:.1%} ({ctr_note}).", "",
          "| Cluster | Keywords | Monthly searches | CPC | Clicks at target IS | Spend to cover | Evidence |", "|---|---|---|---|---|---|---|"]
    for n, v in out["clusters"].items():
        md.append(f"| {n} | {v['keywords']} | {v['searches'][0]:,.0f} to {v['searches'][1]:,.0f} | ${v['cpc'][0]:.2f} to ${v['cpc'][1]:.2f} | {v['clicks_at_target_is'][0]} to {v['clicks_at_target_is'][1]} | ${v['monthly_spend_to_cover'][0]:,} to ${v['monthly_spend_to_cover'][1]:,} | {', '.join(v['evidence'])} |")
    md += ["", f"Funnel: {json.dumps(out['funnel'])}"]
    text = "\n".join(md)
    print(text)
    if a.md:
        Path(a.md).write_text(text + "\n", encoding="utf-8")
    if a.json:
        Path(a.json).write_text(json.dumps(out, indent=2), encoding="utf-8")
    if a.xlsx:
        write_xlsx(a.xlsx, out, clusters, is_lo, is_hi, a.target_is, ctr_lo, ctr_hi, ctr_note)


def write_xlsx(path, out, clusters, is_lo, is_hi, is_t, ctr_lo, ctr_hi, ctr_note):
    """Live-formula workbook the sender can adjust on a call. Inputs blue on yellow; results are formulas."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    wb = Workbook()
    ws = wb.active
    ws.title = "Inputs"
    blue, fill = Font(color="0000FF", name="Arial"), PatternFill("solid", fgColor="FFF2CC")
    ws.append(["Edit the yellow cells. Coverage tab recalculates. Searches and CPC must come from platform data for the geography; modeled rows are provisional."])
    ws.append(["Assumption", "Low", "High", "Target", "Basis"])
    ws.append(["Impression share", is_lo, is_hi, is_t, "planning assumption unless from account history"])
    ws.append(["Search CTR", ctr_lo, ctr_hi, (ctr_lo + ctr_hi) / 2, ctr_note])
    for r in (3, 4):
        for col in "BCD":
            ws[f"{col}{r}"].font, ws[f"{col}{r}"].fill = blue, fill
            ws[f"{col}{r}"].number_format = "0.0%"
    ws.append([])
    ws.append(["Cluster", "Searches low", "Searches high", "CPC low", "CPC high", "Evidence", "Sources"])
    start = ws.max_row + 1
    for n, v in out["clusters"].items():
        ws.append([n, v["searches"][0], v["searches"][1], v["cpc"][0], v["cpc"][1], ", ".join(v["evidence"]), "; ".join(v["sources"])])
        r = ws.max_row
        for col in "BCDE":
            ws[f"{col}{r}"].font, ws[f"{col}{r}"].fill = blue, fill
    end = ws.max_row
    cv = wb.create_sheet("Coverage")
    cv.append(["Cluster", "Clicks low", "Clicks high", "Spend low $", "Spend high $", "Spend mid $"])
    for i, r in enumerate(range(start, end + 1), start=2):
        cv.append([f"=Inputs!A{r}", f"=Inputs!B{r}*Inputs!$B$3*Inputs!$B$4", f"=Inputs!C{r}*Inputs!$C$3*Inputs!$C$4",
                   f"=B{i}*Inputs!D{r}", f"=C{i}*Inputs!E{r}", f"=(Inputs!B{r}+Inputs!C{r})/2*Inputs!$D$3*Inputs!$D$4*(Inputs!D{r}+Inputs!E{r})/2"])
    last = cv.max_row
    cv.append(["Total", f"=SUM(B2:B{last})", f"=SUM(C2:C{last})", f"=SUM(D2:D{last})", f"=SUM(E2:E{last})", f"=SUM(F2:F{last})"])
    cv.append(["Recommended entry budget (mid, rounded to $250)", "", "", "", "", f"=ROUND(F{last + 1}/250,0)*250"])
    cv.append(["Status", out["entry_budget"]["status"]])
    for row in cv.iter_rows(min_row=2, max_row=last + 2):
        for c in row[3:]:
            c.number_format = "$#,##0"
    for sheet in (ws, cv):
        for col in sheet.columns:
            sheet.column_dimensions[col[0].column_letter].width = 22
    wb.properties.creator = "PPC research"
    wb.save(path)
    print(f"wrote {path} (recalculate with LibreOffice before reading values)")


if __name__ == "__main__":
    main()
