from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable, List

from scanner import Finding


# ==================================================
# Public API
# ==================================================
def write_report(
    findings: Iterable[Finding],
    project_root: str,
    out_dir: str,
) -> Path:
    out_dir = Path(out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    project_name = Path(project_root).name
    report_file = out_dir / f"{ts}_{project_name}.html"

    risks, todos, infos = _group(findings)
    score, label, color = _health(len(risks), len(todos))

    html = _render_html(
        project_name=project_name,
        project_root=project_root,
        created_at=datetime.now(),
        score=score,
        score_label=label,
        score_color=color,
        risks=risks,
        todos=todos,
        infos=infos,
    )

    report_file.write_text(html, encoding="utf-8")
    return report_file


# ==================================================
# Helpers
# ==================================================
def _group(findings: Iterable[Finding]):
    r, t, i = [], [], []
    for f in findings:
        if f.kind == "RISK":
            r.append(f)
        elif f.kind == "TODO":
            t.append(f)
        elif f.kind == "INFO":
            i.append(f)
    return r, t, i


def _health(risks: int, todos: int):
    score = max(0, 100 - risks * 15 - todos * 5)
    if score >= 80:
        return score, "Healthy", "#22c55e"
    if score >= 50:
        return score, "Needs Attention", "#facc15"
    return score, "Critical", "#ef4444"


def _render_section(title: str, icon: str, items: List[Finding], kind: str) -> str:
    if not items:
        return f"""
        <div class="section">
          <h2>{icon} {title}</h2>
          <div class="empty">✔ No issues found</div>
        </div>
        """

    rows = []
    for idx, f in enumerate(items[:400]):
        path = f"{f.path}:{f.line}" if f.line else f.path
        vscode = f"vscode://file/{f.path}:{f.line}" if f.line else "#"

        rows.append(f"""
        <div class="item {kind}">
          <div class="item-head" onclick="toggle(this)">
            <span class="badge">{kind}</span>
            <span class="item-title">{f.title}</span>
          </div>
          <div class="item-body">
            <div class="detail">{f.detail}</div>
            <a class="path" href="{vscode}">{path}</a>
          </div>
        </div>
        """)

    return f"""
    <div class="section">
      <h2>{icon} {title}</h2>
      {''.join(rows)}
    </div>
    """


# ==================================================
# HTML
# ==================================================
def _render_html(
    *,
    project_name: str,
    project_root: str,
    created_at: datetime,
    score: int,
    score_label: str,
    score_color: str,
    risks: List[Finding],
    todos: List[Finding],
    infos: List[Finding],
) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Zinkx Dev Assistant – Report</title>
<meta name="viewport" content="width=device-width, initial-scale=1">

<style>
:root {{
  --bg: #020617;
  --panel: #030712;
  --border: #1e293b;

  --text: #e5e7eb;
  --muted: #9ca3af;

  --risk: #ef4444;
  --todo: #facc15;
  --info: #38bdf8;
}}

* {{
  box-sizing: border-box;
}}

body {{
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "Inter", sans-serif;
  font-size: 14px;
}}

.wrapper {{
  padding: 20px;
}}

h1 {{
  margin: 0 0 4px 0;
  font-size: 22px;
}}

.meta {{
  color: var(--muted);
  font-size: 12px;
  line-height: 1.5;
  margin-bottom: 20px;
}}

.stats {{
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 24px;
}}

.stat {{
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 12px;
  text-align: center;
}}

.stat-value {{
  font-size: 22px;
  font-weight: 700;
}}

.section {{
  margin-bottom: 28px;
}}

.section h2 {{
  font-size: 16px;
  margin-bottom: 10px;
}}

.item {{
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 10px;
  margin-bottom: 8px;
  overflow: hidden;
}}

.item-head {{
  padding: 10px 12px;
  display: flex;
  gap: 8px;
  cursor: pointer;
  align-items: center;
}}

.item-head:hover {{
  background: rgba(255,255,255,0.03);
}}

.badge {{
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 6px;
  text-transform: uppercase;
}}

.item.risk .badge {{ background: var(--risk); }}
.item.todo .badge {{ background: var(--todo); color: #000; }}
.item.info .badge {{ background: var(--info); color: #000; }}

.item-title {{
  font-weight: 600;
  line-height: 1.4;
}}

.item-body {{
  display: none;
  padding: 10px 12px;
  border-top: 1px solid var(--border);
}}

.item.open .item-body {{
  display: block;
}}

.detail {{
  color: #d1d5db;
  margin-bottom: 6px;
  line-height: 1.6;
}}

.path {{
  font-size: 12px;
  color: var(--info);
  word-break: break-all;
}}

.empty {{
  color: var(--muted);
  font-style: italic;
  padding: 8px 4px;
}}

footer {{
  margin-top: 40px;
  text-align: center;
  color: var(--muted);
  font-size: 12px;
}}

@media print {{
  body {{ background: white; color: black; }}
}}
</style>

<script>
function toggle(el) {{
  el.parentElement.classList.toggle("open");
}}
</script>
</head>

<body>
<div class="wrapper">

<h1>Zinkx Dev Assistant</h1>
<div class="meta">
Project: <b>{project_name}</b><br>
Path: {project_root}<br>
Date: {created_at.isoformat(timespec="seconds")}
</div>

<div class="stats">
  <div class="stat">
    <div class="stat-value" style="color:{score_color}">{score}</div>
    <div>{score_label}</div>
  </div>
  <div class="stat">
    <div class="stat-value" style="color:var(--risk)">{len(risks)}</div>
    <div>Risks</div>
  </div>
  <div class="stat">
    <div class="stat-value" style="color:var(--todo)">{len(todos)}</div>
    <div>TODO</div>
  </div>
  <div class="stat">
    <div class="stat-value" style="color:var(--info)">{len(infos)}</div>
    <div>Info</div>
  </div>
</div>

{_render_section("Risks", "🚨", risks, "risk")}
{_render_section("TODO / FIXME", "🧩", todos, "todo")}
{_render_section("Info", "ℹ️", infos, "info")}

<footer>
Generated by Zinkx Dev Assistant
</footer>

</div>
</body>
</html>
"""
