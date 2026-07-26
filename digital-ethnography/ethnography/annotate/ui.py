"""The annotation interface.

Design constraints that come from the methodology rather than from taste:

* **Blind.** No machine label is ever sent to the browser. The template has no
  slot for one.
* **Fast.** Gold coding is expensive human time, so the whole flow is
  keyboard-driven — number keys assign a code, ``U`` marks uncertain, ``←``
  goes back. A mouse is never required.
* **The codebook is visible at all times**, because the rubric *is* the
  instrument and coders drift when it is out of sight.
* **Uncertain is a first-class answer.** Forcing a label manufactures agreement,
  and a high uncertain rate is a signal that the codebook doesn't fit — which is a
  contract defect worth surfacing, not noise to suppress.

Rendered as one self-contained page: no build step, no CDN, no dependencies.
"""

from __future__ import annotations

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Gold coding &mdash; {study_title}</title>
<style>
  :root {{
    color-scheme: light;
    --paper:#EDF1F2; --card:#F7FAFA; --ink:#101A22; --ink-2:#33454F; --ink-3:#5F727C;
    --rule:#CBD6D8; --accent:#125F66; --accent-wash:#DCEAEA;
    --uncertain:#8A5703; --uncertain-wash:#F2E7CF; --done:#2F6B45;
    --mono: ui-monospace,"SF Mono",SFMono-Regular,Menlo,Consolas,monospace;
    --sans: ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
    --serif:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      color-scheme: dark;
      --paper:#0E1519; --card:#162026; --ink:#E4EDEF; --ink-2:#B0C0C5; --ink-3:#7E9199;
      --rule:#2A3941; --accent:#4FB3B8; --accent-wash:#12333A;
      --uncertain:#D9A441; --uncertain-wash:#33270E; --done:#6DBE8C;
    }}
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--paper); color:var(--ink); font-family:var(--sans);
         font-size:16px; line-height:1.6; }}
  .wrap {{ max-width:60rem; margin:0 auto; padding:1.25rem clamp(1rem,4vw,2rem) 4rem; }}
  header {{ border-bottom:1px solid var(--rule); padding-bottom:.9rem; margin-bottom:1.5rem;
            display:flex; flex-wrap:wrap; gap:.75rem 1.5rem; align-items:baseline; }}
  h1 {{ font-family:var(--serif); font-size:1.35rem; margin:0; font-weight:600; }}
  .meta {{ font-family:var(--mono); font-size:.72rem; letter-spacing:.08em;
           text-transform:uppercase; color:var(--ink-3); }}
  .bar {{ height:5px; background:var(--rule); border-radius:3px; overflow:hidden; margin:.6rem 0 1.5rem; }}
  .bar>i {{ display:block; height:100%; background:var(--accent); transition:width .25s; }}
  .grid {{ display:grid; grid-template-columns:1fr 17rem; gap:1.5rem; align-items:start; }}
  @media (max-width:820px) {{ .grid {{ grid-template-columns:1fr; }} }}
  .unit {{ background:var(--card); border:1px solid var(--rule); border-left:3px solid var(--accent);
           border-radius:0 6px 6px 0; padding:1.25rem; }}
  .unit .src {{ font-family:var(--mono); font-size:.68rem; letter-spacing:.1em; text-transform:uppercase;
                color:var(--ink-3); margin-bottom:.6rem; }}
  .unit .text {{ font-size:1.06rem; white-space:pre-wrap; }}
  .unit .payload {{ margin-top:.9rem; padding-top:.9rem; border-top:1px solid var(--rule);
                    font-family:var(--mono); font-size:.78rem; color:var(--ink-2); }}
  .codes {{ display:flex; flex-direction:column; gap:.4rem; }}
  button.code {{ display:flex; gap:.6rem; align-items:baseline; text-align:left; width:100%;
        background:var(--card); border:1px solid var(--rule); border-radius:5px;
        padding:.55rem .7rem; cursor:pointer; color:var(--ink); font:inherit; font-size:.9rem; }}
  button.code:hover {{ border-color:var(--accent); background:var(--accent-wash); }}
  button.code kbd {{ font-family:var(--mono); font-size:.7rem; background:var(--paper);
        border:1px solid var(--rule); border-radius:3px; padding:.05rem .35rem; color:var(--ink-3); }}
  button.code .def {{ display:block; font-size:.74rem; color:var(--ink-3); margin-top:.15rem; }}
  button.uncertain {{ border-color:var(--uncertain); color:var(--uncertain); background:var(--uncertain-wash); }}
  .side h2 {{ font-family:var(--mono); font-size:.7rem; letter-spacing:.12em; text-transform:uppercase;
              color:var(--ink-3); margin:0 0 .5rem; font-weight:600; }}
  .side {{ position:sticky; top:1rem; }}
  .nav {{ margin-top:1.25rem; display:flex; gap:.75rem; align-items:center; }}
  .nav button {{ font:inherit; font-size:.85rem; background:none; border:1px solid var(--rule);
                 color:var(--ink-2); border-radius:5px; padding:.35rem .7rem; cursor:pointer; }}
  .nav button:hover {{ border-color:var(--accent); color:var(--accent); }}
  .done {{ text-align:center; padding:3rem 1rem; }}
  .done h2 {{ font-family:var(--serif); font-size:1.6rem; margin:0 0 .5rem; color:var(--done); }}
  .note {{ font-size:.82rem; color:var(--ink-3); margin-top:1.25rem; max-width:46ch; }}
  :where(button):focus-visible {{ outline:2px solid var(--accent); outline-offset:2px; }}
  @media (prefers-reduced-motion:reduce) {{ * {{ transition:none !important; }} }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>{study_title}</h1>
    <span class="meta">gold coding &middot; annotator <b id="who">{annotator}</b></span>
    <span class="meta" id="count"></span>
  </header>
  <div class="bar"><i id="prog" style="width:0%"></i></div>
  <div id="app"></div>
  <p class="note">
    You are coding a <strong>probability sample</strong> drawn for validity measurement.
    Machine labels are deliberately hidden &mdash; seeing them would anchor your judgement and
    the gold set would measure agreement with the model instead of truth.
    <strong>Uncertain is a real answer</strong>; a high uncertain rate tells us the codebook
    does not fit the material.
  </p>
</div>
<script>
const UNITS = {units_json};
const CODES = {codes_json};
const ANNOTATOR = {annotator_json};
const CBV = {codebook_version_json};
let done = {done_json};
let i = UNITS.findIndex(u => !(u.id in done));
if (i < 0) i = UNITS.length;
let shownAt = Date.now();

const app = document.getElementById('app');
const prog = document.getElementById('prog');
const count = document.getElementById('count');

function esc(s) {{
  return String(s).replace(/[&<>"']/g, c => (
    {{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
}}

function render() {{
  const n = Object.keys(done).length;
  prog.style.width = (UNITS.length ? (n / UNITS.length * 100) : 0) + '%';
  count.textContent = n + ' / ' + UNITS.length + ' coded';

  if (i >= UNITS.length) {{
    app.innerHTML = '<div class="done"><h2>Sample complete</h2>' +
      '<p>' + n + ' units coded. Run <code>ethnography validate</code> to compare ' +
      'machine coding against this gold standard.</p></div>';
    return;
  }}

  const u = UNITS[i];
  const payload = u.payload && Object.keys(u.payload).length
    ? '<div class="payload">' + esc(JSON.stringify(u.payload)) + '</div>' : '';
  const body = u.text ? esc(u.text) : '<em style="color:var(--ink-3)">(no free text — behavioural trace)</em>';

  app.innerHTML =
    '<div class="grid">' +
      '<div class="unit"><div class="src">' + esc(u.source) + ' &middot; ' + esc(u.kind) +
        ' &middot; ' + esc(u.timestamp) + '</div>' +
        '<div class="text">' + body + '</div>' + payload + '</div>' +
      '<div class="side"><h2>Codebook</h2><div class="codes">' +
        CODES.map((c, k) => '<button class="code" data-label="' + esc(c.label) + '">' +
          '<kbd>' + (k + 1) + '</kbd><span>' + esc(c.label) +
          (c.definition ? '<span class="def">' + esc(c.definition) + '</span>' : '') +
          '</span></button>').join('') +
        '<button class="code uncertain" data-uncertain="1"><kbd>U</kbd>' +
        '<span>Uncertain<span class="def">The codebook does not fit this unit</span></span></button>' +
      '</div></div>' +
    '</div>' +
    '<div class="nav"><button id="back">&larr; Back</button>' +
    '<span class="meta">' + (i + 1) + ' of ' + UNITS.length + '</span></div>';

  app.querySelectorAll('button.code').forEach(b => b.onclick = () =>
    submit(b.dataset.uncertain ? null : b.dataset.label));
  const back = document.getElementById('back');
  if (back) back.onclick = () => {{ if (i > 0) {{ i--; shownAt = Date.now(); render(); }} }};
  shownAt = Date.now();
}}

async function submit(label) {{
  const u = UNITS[i];
  const rec = {{
    unit_id: u.id, label: label, annotator: ANNOTATOR,
    codebook_version: CBV, seconds_on_task: (Date.now() - shownAt) / 1000
  }};
  done[u.id] = label;
  i++;
  render();
  try {{ await fetch('/annotate', {{
    method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify(rec)
  }}); }} catch (e) {{ console.error('save failed', e); }}
}}

document.addEventListener('keydown', e => {{
  if (i >= UNITS.length) return;
  if (e.key === 'u' || e.key === 'U') {{ submit(null); return; }}
  if (e.key === 'ArrowLeft' && i > 0) {{ i--; render(); return; }}
  const k = parseInt(e.key, 10);
  if (!isNaN(k) && k >= 1 && k <= CODES.length) submit(CODES[k - 1].label);
}});

render();
</script>
</body>
</html>
"""


def render_page(
    study_title: str,
    annotator: str,
    units_json: str,
    codes_json: str,
    annotator_json: str,
    codebook_version_json: str,
    done_json: str,
) -> str:
    return PAGE.format(
        study_title=study_title,
        annotator=annotator,
        units_json=units_json,
        codes_json=codes_json,
        annotator_json=annotator_json,
        codebook_version_json=codebook_version_json,
        done_json=done_json,
    )
