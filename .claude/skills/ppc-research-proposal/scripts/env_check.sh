#!/usr/bin/env bash
# Environment check for a research-to-proposal run. Prints what works so the plan can
# route around what does not (this is read-only except for the optional LibreOffice install).
# Usage: bash env_check.sh [--install-libreoffice]
set -u
echo "== Python libraries =="
for m in docx openpyxl pymupdf; do python3 -c "import $m" 2>/dev/null && echo "ok  $m" || echo "MISSING $m  (pip install python-docx openpyxl pymupdf)"; done
echo "== LibreOffice =="
if command -v soffice >/dev/null; then
  soffice --version 2>/dev/null | head -1
  if dpkg -l 2>/dev/null | grep -qE "libreoffice-(writer|calc)"; then echo "ok  writer/calc packages present"; else
    echo "MISSING libreoffice-writer / libreoffice-calc: conversions will fail with 'source file could not be loaded'"
    if [ "${1:-}" = "--install-libreoffice" ]; then
      DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends libreoffice-writer libreoffice-calc >/dev/null 2>&1 && echo "installed writer and calc" || echo "install failed (apt blocked?)"
    else echo "    run: bash env_check.sh --install-libreoffice"; fi
  fi
else echo "MISSING soffice (LibreOffice): recalculation and render checks unavailable"; fi
echo "== Skill helper scripts =="
r=$(find /root/.claude/skills "$HOME/.claude/skills" -path "*/xlsx/scripts/recalc.py" 2>/dev/null | head -1); [ -n "$r" ] && echo "ok  xlsx recalc: $r" || echo "no xlsx recalc.py found (check_package.py falls back to a LibreOffice copy)"
w=$(find /root/.claude/skills "$HOME/.claude/skills" -path "*/docx/scripts/office/soffice.py" 2>/dev/null | head -1); [ -n "$w" ] && echo "ok  docx soffice wrapper: $w" || echo "no docx soffice.py wrapper (plain soffice will be used)"
echo "== Network (direct fetch) =="
for u in https://www.google.com https://support.google.com/adspolicy/answer/176031 https://www.hhs.gov; do
  code=$(curl -sS -o /dev/null -w "%{http_code}" --max-time 15 "$u" 2>/dev/null); [ -z "$code" ] && code=000
  echo "$code  $u"
done
echo "   (000 or 403 means direct fetches are blocked by the network policy: agents must verify through web search results and label depth)"
echo "== PageSpeed Insights API =="
code=$(curl -sS -o /tmp/psi.json -w "%{http_code}" --max-time 60 "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=https://example.com&strategy=mobile" 2>/dev/null); [ -z "$code" ] && code=000
echo "$code  (200 usable; 429 daily quota exhausted; 000/403 blocked)"
echo "== Google Ads Keyword Planner =="
echo "Live Keyword Planner needs a browser session already logged into a Google Ads account. Never create accounts or accept setup prompts. If no export was provided and no session exists, use source priority (c) benchmarks, (d) third-party tools, (e) modeled."
