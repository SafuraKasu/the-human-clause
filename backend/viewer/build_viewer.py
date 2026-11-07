"""Build a self-contained offline demo page from a recorded run.

    python -m backend.viewer.build_viewer [--run data/runs/<dir>] [--out docs/demo/index.html]

The page embeds the run, its audit trail, the cited passages and the gap report. No server, no network.
It replays a RECORDED run; it does not call any model.
"""
import argparse
import glob
import json
from pathlib import Path

from backend import config
from backend.kb.retrieve import KnowledgeBase
from backend.report import content as C
from backend.report.build import adjudicate
from backend.scenario import fatima


def cited_ids(run: dict) -> set:
    ids = set()
    for ev in run["events"]:
        p = ev["policy"]
        if p:
            for key in ("requirements", "conflicts", "gaps", "comparisons"):
                for item in p[key]:
                    ids.update(item.get("citations", []))
                    ids.update(c["chunk_id"] for c in item.get("unretrieved_candidates", []))
    for g in C.GAPS:
        ids.update(cid for _, cid, _ in g["evidence"] + g["comparison"])
    return ids


def build(run_dir: Path, out: Path) -> Path:
    run = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    audit = [json.loads(line) for line in (run_dir / "audit.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    kb = KnowledgeBase()
    chunks = {cid: {"document": kb.get(cid)["document"], "section": kb.get(cid)["section"], "page": kb.get(cid)["page"],
                    "scope": kb.get(cid)["scope"], "url": kb.get(cid)["url"], "text": kb.get(cid)["text"]}
              for cid in cited_ids(run) if kb.get(cid)}
    for ev in run["events"]:
        exp = fatima.EVENTS[ev["seq"] - 1].expected
        ev["expected_notes"] = exp["policy"]["must_note"]
        for c in ev["checks"]:
            if c["status"] in ("fail", "differs"):
                c["note"] = adjudicate(ev["seq"], c["description"])
        for entry in audit:
            pass
    gaps = [{"id": g["id"], "title": g["title"], "statement": g["statement"], "relevance": g["relevance"],
             "recommendation": g["recommendation"], "origin": g["origin"], "caveats": g["caveats"],
             "evidence": [{"label": l, "chunk_id": c} for l, c, _ in g["evidence"]],
             "comparison": [{"label": l, "chunk_id": c} for l, c, _ in g["comparison"]]} for g in C.GAPS]
    data = {"run_id": run_dir.name, "run": run, "audit": audit, "chunks": chunks, "gaps": gaps,
            "events_meta": [{"seq": e.seq, "title": e.title, "at": e.at, "narrative": e.narrative, "actor": e.actor}
                            for e in fatima.EVENTS]}
    blob = json.dumps(data, ensure_ascii=False, default=str).replace("</", "<\\/")
    html = TEMPLATE.replace("__DATA__", blob)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=None)
    ap.add_argument("--out", default=str(config.ROOT / "docs" / "demo" / "index.html"))
    args = ap.parse_args()
    run_dir = Path(args.run) if args.run else Path(sorted(glob.glob(str(config.ROOT / "data" / "runs" / "*-live")))[-1])
    out = build(run_dir, Path(args.out))
    print(f"wrote {out} ({out.stat().st_size // 1024} KB) from {run_dir.name}")
    return 0


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Human Clause: scenario replay</title>
<style>
:root{--bg:#f6f7f9;--surface:#fff;--text:#1b2230;--muted:#5b6475;--line:#dfe3ea;--accent:#1f5fbf;--accent-soft:#e8f0fc;
--crit:#9b1c1c;--crit-bg:#fde8e8;--high:#b4470b;--high-bg:#fdeede;--mod:#8a6d00;--mod-bg:#fdf6d8;--low:#2d6a4f;--low-bg:#e3f4ea;--info:#4a5568;--info-bg:#eceff3;
--ok:#1e6b3a;--ok-bg:#e3f4ea;--bad:#9b1c1c;--bad-bg:#fde8e8;--rev:#7a5a00;--rev-bg:#fdf6d8;--dif:#3b4a8a;--dif-bg:#e8ebfa}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#10141b;--surface:#171c26;--text:#e6e9ef;--muted:#9aa4b5;--line:#2a3140;--accent:#7fb0ff;--accent-soft:#1c2b45;
--crit:#ff9b9b;--crit-bg:#3a1a1a;--high:#ffb784;--high-bg:#3a2515;--mod:#f0d77a;--mod-bg:#38300f;--low:#8fd6b0;--low-bg:#173326;--info:#b4bccb;--info-bg:#232a37;
--ok:#8fd6b0;--ok-bg:#173326;--bad:#ff9b9b;--bad-bg:#3a1a1a;--rev:#f0d77a;--rev-bg:#38300f;--dif:#a9b6f5;--dif-bg:#1f2644}}
:root[data-theme="dark"]{--bg:#10141b;--surface:#171c26;--text:#e6e9ef;--muted:#9aa4b5;--line:#2a3140;--accent:#7fb0ff;--accent-soft:#1c2b45;
--crit:#ff9b9b;--crit-bg:#3a1a1a;--high:#ffb784;--high-bg:#3a2515;--mod:#f0d77a;--mod-bg:#38300f;--low:#8fd6b0;--low-bg:#173326;--info:#b4bccb;--info-bg:#232a37;
--ok:#8fd6b0;--ok-bg:#173326;--bad:#ff9b9b;--bad-bg:#3a1a1a;--rev:#f0d77a;--rev-bg:#38300f;--dif:#a9b6f5;--dif-bg:#1f2644}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:20px 16px 60px}
h1{font-size:22px;margin:0 0 4px}h2{font-size:17px;margin:0 0 10px}h3{font-size:14px;margin:0 0 6px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.sub{color:var(--muted);margin:0 0 14px}.banner{border:1px solid var(--line);background:var(--surface);border-radius:10px;padding:10px 14px;margin:10px 0;font-size:14px}
.banner.live{border-color:var(--ok);background:var(--ok-bg)}.banner.warn{border-color:var(--high);background:var(--high-bg)}.banner.esc{border-color:var(--crit);background:var(--crit-bg)}
.layout{display:grid;grid-template-columns:300px 1fr;gap:18px;align-items:start}@media(max-width:860px){.layout{grid-template-columns:1fr}}
.card{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin-bottom:14px}
.controls{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}
button{font:inherit;border:1px solid var(--line);background:var(--surface);color:var(--text);border-radius:8px;padding:7px 12px;cursor:pointer}
button.primary{background:var(--accent);border-color:var(--accent);color:#fff}button:focus-visible,summary:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
button:disabled{opacity:.45;cursor:not-allowed}
.tl{list-style:none;margin:0;padding:0}.tl li{border:1px solid var(--line);background:var(--surface);border-radius:10px;padding:9px 12px;margin-bottom:8px;cursor:pointer}
.tl li[aria-current="true"]{border-color:var(--accent);background:var(--accent-soft)}.tl li.locked{opacity:.5;cursor:default}
.tl .t{font-size:12px;color:var(--muted)}.tl .n{font-weight:600}
.chip{display:inline-block;padding:1px 8px;border-radius:999px;font-size:12px;font-weight:600;border:1px solid transparent;white-space:nowrap}
.sev-critical{color:var(--crit);background:var(--crit-bg)}.sev-high{color:var(--high);background:var(--high-bg)}.sev-moderate{color:var(--mod);background:var(--mod-bg)}.sev-low{color:var(--low);background:var(--low-bg)}.sev-informational{color:var(--info);background:var(--info-bg)}
.st-pass{color:var(--ok);background:var(--ok-bg)}.st-fail{color:var(--bad);background:var(--bad-bg)}.st-review{color:var(--rev);background:var(--rev-bg)}.st-differs{color:var(--dif);background:var(--dif-bg)}
.ok{color:var(--ok);background:var(--ok-bg)}.no{color:var(--bad);background:var(--bad-bg)}.new{color:var(--accent);background:var(--accent-soft)}.gone{color:var(--muted);background:var(--info-bg);text-decoration:line-through}
table{width:100%;border-collapse:collapse;font-size:13.5px}th,td{text-align:left;vertical-align:top;padding:7px 8px;border-bottom:1px solid var(--line)}th{color:var(--muted);font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:.04em}
.muted{color:var(--muted)}.small{font-size:13px}code{font:12.5px ui-monospace,Consolas,monospace;background:var(--info-bg);padding:1px 5px;border-radius:4px}
details{margin:4px 0}summary{cursor:pointer;color:var(--accent)}blockquote{margin:6px 0 8px;padding:8px 12px;border-left:3px solid var(--line);background:var(--bg);font-size:13px;white-space:pre-wrap}
.tabs{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px}.tabs button[aria-selected="true"]{background:var(--accent-soft);border-color:var(--accent);color:var(--accent)}
ul.tight{margin:4px 0 8px 18px;padding:0}.right{float:right}
</style>
</head>
<body>
<div class="wrap">
  <div class="right"><button id="theme" aria-label="Toggle colour theme">Theme</button></div>
  <h1>The Human Clause <span class="muted">· scenario replay</span></h1>
  <p class="sub">Three cooperating agents keep one patient's medications safe across hospitals in two emirates, and check what UAE rules and the patient's consent allow. Everything here is synthetic.</p>
  <div id="runbanner"></div>
  <div class="layout">
    <aside>
      <div class="controls">
        <button class="primary" id="next">Release next event ▶</button>
        <button id="all">Show all</button><button id="reset">Reset</button>
      </div>
      <ol class="tl" id="timeline"></ol>
      <div class="card small muted" id="legend"></div>
    </aside>
    <main id="main"></main>
  </div>
  <section id="gaps" class="card" style="margin-top:18px"></section>
  <p class="small muted">Limits: demonstration medication knowledge base (team-curated, not clinically validated); English-only policy texts; no authentication or encryption; free-tier language model. This page replays a recorded run and calls no model.</p>
</div>
<script id="data" type="application/json">__DATA__</script>
<script>
const D = JSON.parse(document.getElementById('data').textContent);
const R = D.run, EV = R.events, META = D.events_meta;
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let released = 1, current = 1, tab = 'safety';

const tabs = [['safety','What the system knew'],['consent','Consent decisions'],['policy','Policy agent'],['checks','Expected vs actual'],['audit','Audit trail']];
const sevChip = s => `<span class="chip sev-${esc(s)}">${esc(s)}</span>`;
const stChip = s => `<span class="chip st-${esc(s)}">${esc(s)}</span>`;

function runBanner(){
  const t = R.totals, live = R.mode === 'live';
  document.getElementById('runbanner').innerHTML = `<div class="banner ${live?'live':'warn'}"><strong>${live?'Recorded LIVE run':'MOCK run, not an observed outcome'}</strong>
   · models: ${esc(R.models.join(', '))} · run <code>${esc(D.run_id)}</code><br>
   Checks: <span class="chip st-pass">${t.pass} pass</span> <span class="chip st-fail">${t.fail} fail</span> <span class="chip st-review">${t.review} human review</span> <span class="chip st-differs">${t.differs} hypothesis not confirmed</span>
   <span class="muted small"> Expectations were written before the run and not changed; every non-pass was reviewed against the source text.</span></div>`;
  document.getElementById('legend').innerHTML = 'Severity: ' + ['critical','high','moderate','low','informational'].map(sevChip).join(' ') +
   '<br>Checks: ' + ['pass','fail','review','differs'].map(stChip).join(' ') + '<br><span class="small">review = a human must judge; differs = the agent did not confirm our written hypothesis.</span>';
}

function timeline(){
  document.getElementById('timeline').innerHTML = EV.map((e,i)=>{
    const n=e.seq, locked = n>released, cur = n===current && !locked;
    return `<li class="${locked?'locked':''}" ${cur?'aria-current="true"':''} data-n="${n}" tabindex="${locked?-1:0}" role="button" aria-disabled="${locked}">
      <div class="t">${esc(e.at.replace('T',' '))}</div><div class="n">${locked?'Event '+n+' (not yet released)':'E'+n+' · '+esc(e.title)}</div></li>`;}).join('');
  document.querySelectorAll('#timeline li:not(.locked)').forEach(li=>{
    const go=()=>{current=+li.dataset.n;render()}; li.onclick=go; li.onkeydown=ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();go()}};});
  document.getElementById('next').disabled = released>=EV.length;
}

function findingsDiff(n){
  const now = new Set(EV[n-1].safety.findings.map(f=>f.finding_id));
  const prev = n>1 ? new Set(EV[n-2].safety.findings.map(f=>f.finding_id)) : new Set();
  return {added:[...now].filter(x=>!prev.has(x)), removed:[...prev].filter(x=>!now.has(x))};
}

function citation(cid){
  const c = D.chunks[cid]; if(!c) return `<code>${esc(cid)}</code>`;
  const where = c.section.startsWith('p.') ? c.section : `${c.section}, p.${c.page}`;
  return `<details><summary><code>${esc(cid)}</code> ${esc(c.document)} · ${esc(where)}</summary><blockquote>${esc(c.text)}</blockquote><div class="small muted">${esc(c.scope)} · <a href="${esc(c.url)}" target="_blank" rel="noopener">source</a></div></details>`;
}

function paneSafety(e, m){
  const s = e.safety, d = findingsDiff(m.seq);
  let h = '';
  if (s.limitations.length) h += `<div class="banner warn"><strong>Assessment is incomplete.</strong> ${s.limitations.map(esc).join('<br>')}</div>`;
  h += `<p>${esc(s.summary)}</p>`;
  if (d.added.length||d.removed.length) h += `<p class="small">Since the previous event: ${d.added.map(x=>`<span class="chip new">new</span> <code>${esc(x)}</code>`).join(' ')} ${d.removed.map(x=>`<span class="chip gone">${esc(x)}</span> resolved or withheld`).join(' ')}</p>`;
  if (!s.findings.length) return h + '<p class="muted">No findings.</p>';
  h += '<table><thead><tr><th>Severity</th><th>Finding</th><th>Plain-language explanation</th></tr></thead><tbody>' + s.findings.map(f=>{
    const src = s.explanation_source[f.finding_id];
    return `<tr><td>${sevChip(f.severity)}<br><span class="small muted">${esc(f.certainty)}</span></td>
      <td><strong>${esc(f.title)}</strong><br><code>${esc(f.finding_id)}</code><br><span class="small muted">evidence: ${esc(f.evidence.reference_id||'n/a')} · KB ${esc(f.evidence.kb_version)} · demonstration data</span></td>
      <td>${esc(s.explanations[f.finding_id])}<br><span class="chip ${src==='llm'?'new':'sev-informational'}">${src==='llm'?'worded by the LLM':'engine text'}</span></td></tr>`;}).join('') + '</tbody></table>';
  if (s.issues.length) h += `<p class="small muted">Validation notes: ${s.issues.map(esc).join('; ')}</p>`;
  return h;
}

function paneConsent(e){
  const keys = Object.keys(e.consent);
  let h = '';
  if (e.escalations.length) h += `<div class="banner esc"><strong>Escalated to a human.</strong> ${e.escalations.map(x=>esc(x.reason)+(x.basis?'<br><span class="small">Rule: '+esc(x.basis)+'</span>':'')).join('<br>')}<br><span class="small">The system does not override either rule on its own.</span></div>`;
  if (!keys.length) return h + '<p class="muted">No access requests at this event.</p>';
  return h + '<table><thead><tr><th>Request</th><th>Decision</th><th>Why</th></tr></thead><tbody>' + keys.map(k=>{const d=e.consent[k];
    return `<tr><td><code>${esc(k)}</code></td><td><span class="chip ${d.allowed?'ok':'no'}">${d.allowed?'ALLOWED':'DENIED'}</span> <code>${esc(d.reason_code)}</code>${d.flagged_for_review?' <span class="chip st-review">flagged for review</span>':''}</td><td>${esc(d.reason)}${d.rule_basis?'<br><span class="small muted">'+esc(d.rule_basis)+'</span>':''}</td></tr>`;}).join('') + '</tbody></table>';
}

function paneDocs(items, key){
  return items.map(i=>`<li>${esc(i[key])}<div>${(i.citations||[]).map(citation).join('')}</div></li>`).join('');
}
function panePolicy(e){
  const p = e.policy;
  if (!p) return '<p class="muted">The Policy agent was not asked anything at this event (no policy question).</p>';
  let h = `<p class="small"><strong>Question:</strong> ${esc(p.question)}</p>`;
  h += `<details><summary>${p.searches.length} searches performed (real tool-call log)</summary><ul class="tight small">${p.searches.map(s=>`<li>[${esc(s.scope||'all jurisdictions')}] “${esc(s.query)}” → ${s.results.length} passages</li>`).join('')}</ul></details>`;
  if (p.requirements.length) h += `<h3>What the rules say</h3><ul class="tight">${paneDocs(p.requirements,'statement')}</ul>`;
  if (p.conflicts.length) h += `<h3>Conflicts</h3><ul class="tight">${paneDocs(p.conflicts,'description')}</ul>`;
  if (p.comparisons.length) h += `<h3>International comparison</h3><ul class="tight">${paneDocs(p.comparisons,'statement')}</ul>`;
  if (p.gaps.length) h += `<h3>Gaps raised</h3><ul class="tight">${p.gaps.map(g=>`<li><span class="chip st-differs">${esc(g.type)}</span> <strong>${esc(g.title)}</strong>: ${esc(g.description)}
     <div>${(g.citations||[]).map(citation).join('')}</div>${g.note?`<div class="small muted">${esc(g.note)}</div>`:''}
     ${(g.unretrieved_candidates||[]).length?`<div class="small"><strong>Independent check:</strong> passages the agent did not retrieve that may bear on this: ${g.unretrieved_candidates.map(c=>citation(c.chunk_id)).join('')}</div>`:''}</li>`).join('')}</ul>`;
  if (p.issues.length) h += `<details><summary>Guard-rail log (${p.issues.length})</summary><ul class="tight small">${p.issues.map(i=>`<li>${esc(i)}</li>`).join('')}</ul></details>`;
  if (!p.completed) h += '<div class="banner warn">The Policy agent did not complete at this event.</div>';
  return h;
}

function paneChecks(e){
  let h = `<p class="small">${['pass','fail','review','differs'].map(k=>`${stChip(k)} ${e.summary[k]}`).join(' &nbsp; ')}</p>`;
  if (e.expected_notes.length) h += `<p class="small"><strong>Expectations a human must judge:</strong></p><ul class="tight small">${e.expected_notes.map(n=>`<li>${esc(n)}</li>`).join('')}</ul>`;
  return h + '<table><thead><tr><th>Area</th><th>Check</th><th>Expected</th><th>Actual</th><th>Status</th></tr></thead><tbody>' + e.checks.map(c=>{
    const fmt = v => typeof v === 'object' ? esc(JSON.stringify(v)) : esc(v);
    return `<tr><td>${esc(c.area)}</td><td>${esc(c.description)}${c.note?`<div class="small muted">Review: ${esc(c.note)}</div>`:''}</td><td class="small">${fmt(c.expected)}</td><td class="small">${fmt(c.actual)}</td><td>${stChip(c.status)}</td></tr>`;}).join('') + '</tbody></table>';
}

function paneAudit(m){
  const rows = D.audit.filter(a=>a.event_seq===m.seq || (m.seq===1 && a.event_seq===0));
  return `<p class="small muted">${rows.length} entries. Decisions, evidence references, rule checks and handoffs. No hidden model reasoning is recorded.</p>` +
    rows.map(a=>{
      const extra = a.kind==='llm_call' ? `<div class="small muted">model ${esc(a.model)} · ${a.cached?'from cache':'network'} · ${esc(a.attempts)} attempt(s)</div><details><summary>request / response</summary><blockquote>${esc(a.request)}</blockquote><blockquote>${esc(a.response)}</blockquote></details>` : '';
      return `<div class="small" style="margin:6px 0"><span class="chip sev-informational">${esc(a.kind)}</span> <strong>${esc(a.actor)}</strong> · ${esc(a.summary)}${extra}</div>`;}).join('');
}

function render(){
  timeline();
  const e = EV[current-1], m = META[current-1];
  document.getElementById('main').innerHTML = `<div class="card"><h2>E${m.seq} · ${esc(m.title)}</h2><div class="small muted">${esc(m.at.replace('T',' '))} · ${esc(m.actor)}</div><p>${esc(m.narrative)}</p></div>
   <div class="tabs" role="tablist">${tabs.map(([k,l])=>`<button role="tab" aria-selected="${k===tab}" data-tab="${k}">${l}</button>`).join('')}</div>
   <div class="card" role="tabpanel">${tab==='safety'?paneSafety(e,m):tab==='consent'?paneConsent(e):tab==='policy'?panePolicy(e):tab==='checks'?paneChecks(e):paneAudit(m)}</div>`;
  document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>{tab=b.dataset.tab;render()});
}

function gaps(){
  document.getElementById('gaps').innerHTML = '<h2>Policy and standards gaps found</h2><p class="small muted">Each statement is checked against the ingested text; absence claims come with full-text scans in the report. Absence in our knowledge base is not proof that no rule exists.</p>' + D.gaps.map(g=>`<div style="margin-bottom:14px"><h3 style="text-transform:none;font-size:15px;color:var(--text)">${esc(g.id)} · ${esc(g.title)}</h3>
   <p>${esc(g.statement)}</p><p class="small"><strong>Why it matters here:</strong> ${esc(g.relevance)}<br><strong>Recommendation:</strong> ${esc(g.recommendation)}<br><span class="muted">Origin: ${esc(g.origin)} Caveats: ${esc(g.caveats)}</span></p>
   <details><summary>Evidence (${g.evidence.length})${g.comparison.length?' and international comparison':''}</summary>${g.evidence.map(x=>`<div class="small"><strong>${esc(x.label)}</strong>${citation(x.chunk_id)}</div>`).join('')}${g.comparison.map(x=>`<div class="small"><strong>Comparison: ${esc(x.label)}</strong>${citation(x.chunk_id)}</div>`).join('')}</details></div>`).join('');
}

document.getElementById('next').onclick=()=>{if(released<EV.length){released++;current=released;render()}};
document.getElementById('all').onclick=()=>{released=EV.length;render()};
document.getElementById('reset').onclick=()=>{released=1;current=1;tab='safety';render()};
document.getElementById('theme').onclick=()=>{const r=document.documentElement,dark=getComputedStyle(r).getPropertyValue('--bg').trim()==='#10141b';r.dataset.theme=dark?'light':'dark'};
(function(){const m=location.hash.match(/^#(\d)(?:\/(\w+))?$/);
  if(m&&+m[1]>=1&&+m[1]<=EV.length){released=EV.length;current=+m[1];if(m[2]&&tabs.some(t=>t[0]===m[2]))tab=m[2];}})();
runBanner(); gaps(); render();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    raise SystemExit(main())
