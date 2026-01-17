from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable

from scanner import Finding


def write_html_report(
    findings: Iterable[Finding],
    project_root: str,
    out_dir: str,
) -> Path:
    outp = Path(out_dir).expanduser().resolve()
    outp.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    project_name = Path(project_root).name
    report_file = outp / f"{ts}_{project_name}.html"

    risks = [f for f in findings if f.kind == "RISK"]
    todos = [f for f in findings if f.kind == "TODO"]
    infos = [f for f in findings if f.kind == "INFO"]

    # ---------------- Health score
    score = max(0, 100 - (len(risks) * 15) - (len(todos) * 5))
    if score >= 80:
        score_color = "success"
        score_label = "Healthy"
    elif score >= 50:
        score_color = "warning"
        score_label = "Needs Attention"
    else:
        score_color = "danger"
        score_label = "Critical"

    def render_items(items: list[Finding], kind: str) -> str:
        if not items:
            return """
            <div class="soft-muted fst-italic py-3">
                ✔ No issues found in this section
            </div>
            """

        rows = []
        for i, f in enumerate(items[:500]):
            path = f"{f.path}:{f.line}" if f.line else f.path
            vscode = f"vscode://file/{f.path}:{f.line}" if f.line else "#"

            rows.append(f"""
            <div class="accordion-item report-item">
                <h2 class="accordion-header">
                    <button class="accordion-button collapsed report-btn"
                            type="button"
                            data-bs-toggle="collapse"
                            data-bs-target="#{kind}-{i}">
                        <span class="badge badge-{kind} me-2">{kind.upper()}</span>
                        <span class="title">{f.title}</span>
                    </button>
                </h2>
                <div id="{kind}-{i}" class="accordion-collapse collapse">
                    <div class="accordion-body report-body">
                        <p class="detail">{f.detail}</p>
                        <a href="{vscode}" class="path">{path}</a>
                    </div>
                </div>
            </div>
            """)

        return "\n".join(rows)

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Zinkx Dev Assistant – Scan Report</title>
<meta name="viewport" content="width=device-width, initial-scale=1">

<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">

<style>
:root {{
    --bg: #020617;
    --panel: #020617;
    --border: #1e293b;

    --text-main: #e5e7eb;
    --text-soft: #cbd5f5;
    --text-muted: #94a3b8;

    --risk: #ef4444;
    --todo: #facc15;
    --info: #38bdf8;
}}

body {{
    background: var(--bg);
    color: var(--text-main);
}}

.card {{
    background: var(--panel);
    border: 1px solid var(--border);
}}

.soft-muted {{
    color: var(--text-soft);
    font-size: 14px;
}}

h1, h4 {{
    color: #f8fafc;
}}

.accordion-item.report-item {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 12px;
    margin-bottom: 8px;
    overflow: hidden;
}}

.accordion-button.report-btn {{
    background: var(--panel);
    color: var(--text-main);
    font-weight: 600;
    box-shadow: none;
}}

.accordion-button.report-btn:hover {{
    background: rgba(255,255,255,0.04);
}}

.accordion-button::after {{
    filter: invert(1);
}}

.accordion-body.report-body {{
    background: rgba(255,255,255,0.02);
}}

.detail {{
    color: var(--text-soft);
    font-size: 14px;
    line-height: 1.6;
}}

.path {{
    font-size: 13px;
    color: var(--info);
    word-break: break-all;
}}

.badge-risk {{ background: var(--risk); }}
.badge-todo {{ background: var(--todo); color:#000; }}
.badge-info {{ background: var(--info); color:#000; }}

@media print {{
    .no-print {{ display: none !important; }}
    body {{ background: white; color: black; }}
}}
</style>
</head>

<body>
<div class="container py-4">

<!-- Header -->
<div class="mb-4">
    <h1 class="fw-bold">Zinkx Dev Assistant</h1>
    <div class="soft-muted">
        Project: <b>{project_name}</b><br>
        Path: {project_root}<br>
        Date: {datetime.now().isoformat(timespec="seconds")}
    </div>
</div>

<!-- Stats -->
<div class="row g-3 mb-4">
    <div class="col-md-3">
        <div class="card p-3 text-center">
            <div class="soft-muted">Health</div>
            <div class="display-6 fw-bold text-{score_color}">{score}</div>
            <div class="soft-muted">{score_label}</div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card p-3 text-center">
            <div class="soft-muted">Risks</div>
            <div class="display-6 fw-bold text-danger">{len(risks)}</div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card p-3 text-center">
            <div class="soft-muted">TODO</div>
            <div class="display-6 fw-bold text-warning">{len(todos)}</div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card p-3 text-center">
            <div class="soft-muted">Info</div>
            <div class="display-6 fw-bold text-info">{len(infos)}</div>
        </div>
    </div>
</div>

<!-- Toolbar -->
<div class="mb-4 no-print">
    <button class="btn btn-outline-light btn-sm me-2" onclick="showAll()">All</button>
    <button class="btn btn-outline-danger btn-sm me-2" onclick="filter('risk')">Risks</button>
    <button class="btn btn-outline-warning btn-sm me-2" onclick="filter('todo')">TODO</button>
    <button class="btn btn-outline-info btn-sm me-2" onclick="filter('info')">Info</button>
    <button class="btn btn-outline-secondary btn-sm" onclick="window.print()">Print / PDF</button>
</div>

<h4 class="mt-4">🚨 Risks</h4>
<div class="accordion section-risk mb-4">
{render_items(risks, "risk")}
</div>

<h4 class="mt-4">🧩 TODO / FIXME</h4>
<div class="accordion section-todo mb-4">
{render_items(todos, "todo")}
</div>

<h4 class="mt-4">ℹ️ Info</h4>
<div class="accordion section-info mb-4">
{render_items(infos, "info")}
</div>

<footer class="text-center soft-muted mt-5">
    Generated by Zinkx Dev Assistant
</footer>

</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
<script>
function showAll() {{
    document.querySelectorAll('.accordion').forEach(el => el.style.display = '');
}}
function filter(kind) {{
    document.querySelectorAll('.accordion').forEach(el => el.style.display = 'none');
    document.querySelector('.section-' + kind).style.display = '';
}}
</script>
</body>
</html>
"""

    report_file.write_text(html, encoding="utf-8")
    return report_file
